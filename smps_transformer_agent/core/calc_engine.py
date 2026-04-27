"""DCM Flyback Transformer Calculation Engine.

Based on "2an" sheet formulas. No LLM/API required.
All calculations are deterministic.
"""

import math
from dataclasses import dataclass, field
from typing import Optional

from core.database import CoreData, ICData


U0 = 4 * math.pi * 1e-7  # H/m, permeability of free space


# ─── Data Classes ────────────────────────────────────────────────

@dataclass
class OutputTab:
    """Single output winding definition."""
    name: str           # e.g. "PV15", "NV15", "IPV24"
    voltage: float      # V, output voltage
    current_ma: float   # mA, load current (design spec)
    is_isolated: bool = False  # True if isolated from other outputs
    ns_set: int = 0     # turns (user-set or auto)
    wire_dia_mm: float = 0.3   # wire diameter


@dataclass
class DesignInput:
    """All user inputs for the design."""
    # Output tabs
    outputs: list[OutputTab]
    # Input voltage (DC link)
    vin_min: float      # V
    vin_max: float      # V
    # IC
    ic_name: str
    # Core
    core_name: str
    air_gap_mm: float   # mm, minimum 0.1
    # Turns
    np: int             # primary turns
    # Wire
    primary_wire_dia_mm: float = 0.2  # mm
    barrier_height_mm: float = 2.0    # mm
    current_density: float = 7.0      # A/mm2 (5~7)
    # Shunt
    r_shunt_ohm: float = 2.0   # ohm
    # Flux
    bm_set: float = 0.3        # T, maximum flux density
    # Spike
    v_spike_margin: float = 150.0  # V
    # Lp override (None = auto)
    lp_set_uH: Optional[float] = None
    # MOSFET
    vds_max_rating: float = 1500.0  # V, MOSFET rating


@dataclass
class TurnsResult:
    """Turns ratio calculation results."""
    n_ratio_upper: float = 0.0   # max allowed Np/Ns (VDS protection)
    n_ratio_lower: float = 0.0   # min allowed Np/Ns (DCM condition)
    n_ratio_set: float = 0.0     # actual Np/Ns
    vr: float = 0.0              # V, reflected voltage
    v_spike_margin: float = 0.0  # V


@dataclass
class InductanceResult:
    """Inductance calculation results."""
    lp_magnetic_uH: float = 0.0  # from magnetic perspective
    lp_energy_uH: float = 0.0    # from energy perspective
    lp_set_uH: float = 0.0       # user/auto selected
    lp_set_source: str = ""      # "auto" or "manual"


@dataclass
class DutyResult:
    """Duty cycle results."""
    d_primary: float = 0.0       # primary on duty (fraction)
    d_secondary: float = 0.0     # secondary on duty (fraction)
    mode: str = "DCM"            # DCM or CCM


@dataclass
class CurrentResult:
    """Current stress results."""
    ip_peak: float = 0.0         # A, primary peak
    ip_rms: float = 0.0          # A, primary RMS


@dataclass
class Judgment:
    """Single pass/fail judgment."""
    name: str
    value: float
    limit: float
    unit: str
    passed: bool
    margin_pct: float  # positive = good


@dataclass
class WireCalc:
    """Wire calculation for a single output."""
    tab_name: str
    voltage: float       # V
    current_ma: float    # mA
    i_peak: float        # A
    i_rms: float         # A
    ns_calc: float       # calculated turns
    ns_set: int          # set turns
    vo_calc: float       # calculated output voltage
    vrrm_calc: float     # reverse voltage on diode
    wire_area_set: float  # mm2, set wire cross section
    wire_area_calc: float # mm2, calculated minimum
    wire_dia_set: float   # mm
    margin_pct: float     # wire area margin %


@dataclass
class GapResult:
    """Air gap related calculations."""
    al_zero: float = 0.0    # nH/N2, ungapped
    al_gapped: float = 0.0  # nH/N2, with gap
    air_gap_mm: float = 0.0


@dataclass
class FluxResult:
    """Flux density calculation."""
    delta_b: float = 0.0    # T, flux density swing
    bm_set: float = 0.0     # T, set maximum
    bsat: float = 0.0       # T, core saturation
    margin_pct: float = 0.0 # saturation margin


@dataclass
class DesignResult:
    """Complete design calculation output."""
    # Input summary
    pin: float = 0.0
    pout: float = 0.0
    efficiency: float = 0.0
    # Sub-results
    turns: TurnsResult = field(default_factory=TurnsResult)
    inductance: InductanceResult = field(default_factory=InductanceResult)
    duty: DutyResult = field(default_factory=DutyResult)
    current: CurrentResult = field(default_factory=CurrentResult)
    gap: GapResult = field(default_factory=GapResult)
    flux: FluxResult = field(default_factory=FluxResult)
    # Per-output wire calcs
    wire_calcs: list[WireCalc] = field(default_factory=list)
    # Judgments
    judgments: list[Judgment] = field(default_factory=list)
    # Power verification
    p_set: float = 0.0      # W, verified power from Lp.set
    vds_max: float = 0.0    # V, maximum drain-source voltage
    ipk_limit: float = 0.0  # A, OCP limit from shunt
    # Max turns check
    max_turns_in_bobbin: int = 0
    # Warnings
    warnings: list[str] = field(default_factory=list)


# ─── Recommendation Helpers ──────────────────────────────────────

def recommend_lp_set(lp_calc_uH: float, rounding: int = 10) -> float:
    """Round Lp to nearest specified increment (default 10uH), rounding up."""
    return math.ceil(lp_calc_uH / rounding) * rounding


def recommend_np_ns(
    vin_min: float, vin_max: float, vds_max_rating: float,
    vout_main: float, vd_f: float, duty_range: tuple[float, float],
    ipk_limit: float, pin: float,
) -> tuple[int, int, float, float]:
    """Recommend Np/Ns based on constraints.

    Returns (np_rec, ns_rec, n_upper, n_lower).
    """
    # Upper bound: VDS protection
    # n < (VDS_max - Vin_max) / (Vout + VD_F)  -- but we use rating - margin
    n_upper = (vds_max_rating - vin_max) / (vout_main + vd_f) if (vout_main + vd_f) > 0 else 999

    # Lower bound: DCM condition
    # n > Vin / ((Vout + VD_F) * (1/Duty_max - 1))
    d_max = duty_range[1] / 100.0
    if d_max > 0 and d_max < 1:
        n_lower = vin_min / ((vout_main + vd_f) * (1.0 / d_max - 1.0))
    else:
        n_lower = 1.0

    # Start from n_lower, find integer ratio where Ipeak is within limit
    # Ip_peak = 2*Pin/(Vin*D), D = sqrt(2*Pin*Lp*Fsw)/Vin
    # Higher turns ratio -> lower reflected voltage -> more margin
    # But also need to fit in bobbin

    # Simple heuristic: pick ratio in middle-upper range, prefer integer
    n_target = (n_lower + n_upper) / 2
    # Try integer ratios
    best_np, best_ns = 10, 1
    best_ratio = n_target
    for ns in range(1, 20):
        np = round(n_target * ns)
        if np < 1:
            continue
        ratio = np / ns
        if n_lower <= ratio <= n_upper:
            if abs(ratio - n_target) < abs(best_ratio - n_target):
                best_np, best_ns = np, ns
                best_ratio = ratio

    return best_np, best_ns, n_upper, n_lower


# ─── Main Calculation ────────────────────────────────────────────

def calculate(inp: DesignInput, core: CoreData, ic: ICData) -> DesignResult:
    """Run the full DCM Flyback transformer design calculation.

    Mirrors the "2an" sheet formulas exactly.
    """
    r = DesignResult()

    # ── Basic parameters ──
    pout_total = sum(abs(o.voltage) * o.current_ma / 1000.0 for o in inp.outputs)
    # Use first output as main for turns ratio
    main_out = inp.outputs[0]
    vd_f = 0.9  # diode forward voltage (typical, could be per-output)

    # Estimate efficiency from output power level
    if pout_total < 5:
        eta = 0.75
    elif pout_total < 10:
        eta = 0.80
    elif pout_total < 20:
        eta = 0.85
    else:
        eta = 0.88

    pin = pout_total / eta
    r.pout = round(pout_total, 4)
    r.pin = round(pin, 4)
    r.efficiency = eta

    # ── OCP / Shunt ──
    r.ipk_limit = ic.ocp_voltage / inp.r_shunt_ohm

    # ── Turns ratio ──
    np = inp.np
    ns_main = main_out.ns_set if main_out.ns_set > 0 else max(1, round(np / 9))
    n_ratio = np / ns_main if ns_main > 0 else 1

    # Upper bound: n < (VDS_rating - Vin_max) / (Vout + VD_F)
    n_upper = (inp.vds_max_rating - inp.vin_min) / (main_out.voltage + vd_f) \
        if (main_out.voltage + vd_f) > 0 else 999

    # Lower bound: n > Vin / ((Vout + VD_F) * (1/Duty_max - 1))
    d_max_frac = ic.duty_max / 100.0
    if d_max_frac > 0 and d_max_frac < 1:
        n_lower = inp.vin_min / ((main_out.voltage + vd_f) * (1.0 / d_max_frac - 1.0))
    else:
        n_lower = 1.0

    # Reflected voltage
    vr = n_ratio * (main_out.voltage + vd_f)

    r.turns = TurnsResult(
        n_ratio_upper=round(n_upper, 4),
        n_ratio_lower=round(n_lower, 4),
        n_ratio_set=round(n_ratio, 4),
        vr=round(vr, 2),
        v_spike_margin=inp.v_spike_margin,
    )

    # ── Air gap / AL ──
    # AL_g = 1 / (1/AL_zero + gap / (u0 * Ae))
    # Units: AL in nH/N2 -> convert
    al_zero_H = core.al_zero * 1e-9  # H/N2
    ae_m2 = core.ae * 1e-6           # m2
    gap_m = inp.air_gap_mm * 1e-3    # m

    if gap_m > 0:
        al_g_H = 1.0 / (1.0 / al_zero_H + gap_m / (U0 * ae_m2))
    else:
        al_g_H = al_zero_H
    al_g_nH = al_g_H * 1e9

    r.gap = GapResult(
        al_zero=core.al_zero,
        al_gapped=round(al_g_nH, 2),
        air_gap_mm=inp.air_gap_mm,
    )

    # ── Inductance ──
    # Lp [magnetic] = u0 * Np^2 * Ae / gap
    if gap_m > 0:
        lp_mag = U0 * np ** 2 * ae_m2 / gap_m * 1e6  # uH
    else:
        lp_mag = al_zero_H * np ** 2 * 1e6

    # Lp [energy] = Vin^2 * D^2 / (2 * Pin * Fsw)
    # But D depends on Lp... use magnetic Lp for initial D calc
    fsw_hz = ic.fsw * 1000

    # D = sqrt(2 * Pin * Lp * Fsw) / Vin
    lp_mag_H = lp_mag * 1e-6
    d_primary = math.sqrt(2 * pin * lp_mag_H * fsw_hz) / inp.vin_min if inp.vin_min > 0 else 0

    lp_energy = inp.vin_min ** 2 * d_primary ** 2 / (2 * pin * fsw_hz) * 1e6 if (pin * fsw_hz) > 0 else 0

    # Lp.set
    if inp.lp_set_uH is not None:
        lp_set = inp.lp_set_uH
        lp_source = "manual"
    else:
        lp_set = recommend_lp_set(lp_mag, rounding=10)
        lp_source = "auto (10uH ceil)"

    r.inductance = InductanceResult(
        lp_magnetic_uH=round(lp_mag, 2),
        lp_energy_uH=round(lp_energy, 2),
        lp_set_uH=round(lp_set, 2),
        lp_set_source=lp_source,
    )

    # ── Duty (recalc with Lp.set) ──
    lp_set_H = lp_set * 1e-6
    d_pri = math.sqrt(2 * pin * lp_set_H * fsw_hz) / inp.vin_min if inp.vin_min > 0 else 0
    d_sec = d_pri * inp.vin_min / (n_ratio * (main_out.voltage + vd_f)) if (n_ratio * (main_out.voltage + vd_f)) > 0 else 0

    mode = "DCM" if (d_pri + d_sec) <= 1 else "CCM"

    r.duty = DutyResult(
        d_primary=round(d_pri, 6),
        d_secondary=round(d_sec, 6),
        mode=mode,
    )

    # ── Current ──
    ip_peak = 2 * pin / (inp.vin_min * d_pri) if (inp.vin_min * d_pri) > 0 else 0
    ip_rms = ip_peak * math.sqrt(d_pri / 3) if d_pri > 0 else 0

    r.current = CurrentResult(
        ip_peak=round(ip_peak, 4),
        ip_rms=round(ip_rms, 4),
    )

    # ── Power verification ──
    p_set = 0.5 * lp_set_H * ip_peak ** 2 * fsw_hz
    r.p_set = round(p_set, 4)

    # ── VDS max ──
    vds_max = inp.vin_max + vr + inp.v_spike_margin
    r.vds_max = round(vds_max, 2)

    # ── Flux density ──
    delta_b = lp_set_H * ip_peak / (np * ae_m2) if (np * ae_m2) > 0 else 0
    sat_margin = (core.bsat - inp.bm_set) / core.bsat * 100 if core.bsat > 0 else 0

    r.flux = FluxResult(
        delta_b=round(delta_b, 6),
        bm_set=inp.bm_set,
        bsat=core.bsat,
        margin_pct=round(sat_margin, 1),
    )

    if delta_b > inp.bm_set:
        r.warnings.append(
            f"Delta_B ({delta_b:.4f}T) > BM_set ({inp.bm_set}T) - "
            f"코어 포화 위험. Np를 늘리거나 Air gap을 키우세요."
        )

    # ── Wire calculations per output ──
    for out in inp.outputs:
        ns = out.ns_set if out.ns_set > 0 else max(1, round(np * (out.voltage + vd_f) / vr)) if vr > 0 else 1
        i_out_a = out.current_ma / 1000.0
        i_sec_peak = i_out_a * 2 / d_sec if d_sec > 0 else 0
        i_sec_rms = i_sec_peak * math.sqrt(d_sec / 3) if d_sec > 0 else 0

        # Calculated output voltage from turns
        vo_calc = (ns * vr / np) - vd_f if np > 0 else 0
        # Reverse voltage on diode
        vrrm_calc = inp.vin_max / (np / ns) + vd_f if ns > 0 else 0

        # Wire area
        wire_area_set = math.pi * (out.wire_dia_mm / 2) ** 2
        wire_area_calc = i_sec_rms / inp.current_density if inp.current_density > 0 else 0
        margin = (wire_area_set - wire_area_calc) / wire_area_calc * 100 if wire_area_calc > 0 else 999

        # Ns from voltage calculation
        ns_calc = np * (abs(out.voltage) + vd_f) / vr if vr > 0 else 0

        r.wire_calcs.append(WireCalc(
            tab_name=out.name,
            voltage=out.voltage,
            current_ma=out.current_ma,
            i_peak=round(i_sec_peak, 4),
            i_rms=round(i_sec_rms, 4),
            ns_calc=round(ns_calc, 2),
            ns_set=ns,
            vo_calc=round(vo_calc, 2),
            vrrm_calc=round(vrrm_calc, 2),
            wire_area_set=round(wire_area_set, 6),
            wire_area_calc=round(wire_area_calc, 6),
            wire_dia_set=out.wire_dia_mm,
            margin_pct=round(margin, 1),
        ))

    # ── Max turns in bobbin ──
    usable_height = core.bobbin_height - inp.barrier_height_mm
    if inp.primary_wire_dia_mm > 0:
        r.max_turns_in_bobbin = int(usable_height / inp.primary_wire_dia_mm)
    if np > r.max_turns_in_bobbin:
        r.warnings.append(
            f"Np({np}) > 보빈 최대 턴수({r.max_turns_in_bobbin}) - "
            f"다층 권선 또는 더 가는 와이어 필요"
        )

    # ── Judgments ──
    # 1. DCM
    r.judgments.append(Judgment(
        name="DCM 판정",
        value=d_pri + d_sec,
        limit=1.0,
        unit="-",
        passed=(d_pri + d_sec) < 1.0,
        margin_pct=round((1.0 - (d_pri + d_sec)) / 1.0 * 100, 1),
    ))

    # 2. Ipeak vs OCP limit
    r.judgments.append(Judgment(
        name="Ipeak 판정",
        value=ip_peak,
        limit=r.ipk_limit,
        unit="A",
        passed=ip_peak < r.ipk_limit,
        margin_pct=round((r.ipk_limit - ip_peak) / r.ipk_limit * 100, 1) if r.ipk_limit > 0 else 0,
    ))

    # 3. Power verification
    r.judgments.append(Judgment(
        name="Power 검증 (P.set > Pin)",
        value=p_set,
        limit=pin,
        unit="W",
        passed=p_set >= pin,
        margin_pct=round((p_set - pin) / pin * 100, 1) if pin > 0 else 0,
    ))

    # 4. VDS
    r.judgments.append(Judgment(
        name="VDS 판정",
        value=vds_max,
        limit=inp.vds_max_rating,
        unit="V",
        passed=vds_max < inp.vds_max_rating,
        margin_pct=round((inp.vds_max_rating - vds_max) / inp.vds_max_rating * 100, 1) if inp.vds_max_rating > 0 else 0,
    ))

    # 5. Flux saturation
    r.judgments.append(Judgment(
        name="포화 판정 (delta_B < BM_set)",
        value=delta_b,
        limit=inp.bm_set,
        unit="T",
        passed=delta_b <= inp.bm_set,
        margin_pct=round((inp.bm_set - delta_b) / inp.bm_set * 100, 1) if inp.bm_set > 0 else 0,
    ))

    # 6. Turns ratio in range
    r.judgments.append(Judgment(
        name="턴수비 범위",
        value=n_ratio,
        limit=n_upper,  # upper bound
        unit="-",
        passed=n_lower <= n_ratio <= n_upper,
        margin_pct=round(min(
            (n_upper - n_ratio) / n_upper * 100 if n_upper > 0 else 0,
            (n_ratio - n_lower) / n_ratio * 100 if n_ratio > 0 else 0,
        ), 1),
    ))

    return r
