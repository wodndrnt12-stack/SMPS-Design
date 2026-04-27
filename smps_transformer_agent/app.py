"""DCM Flyback Transformer Design Tool - Spreadsheet-style UI.

Run: streamlit run app.py
No API/LLM required.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import math
import streamlit as st
import pandas as pd
from core.database import CORE_DB, IC_DB, CoreData, ICData
from core.calc_engine import (
    DesignInput, OutputTab, DesignResult,
    calculate, recommend_lp_set, recommend_np_ns,
)

st.set_page_config(page_title="Flyback Transformer Designer", layout="wide")

# ─── CSS: Excel-like styling ─────────────────────────────────────
st.markdown("""
<style>
    .input-cell { background-color: #FFFFF0; font-weight: bold; }
    .calc-cell { background-color: #F0F8FF; }
    .pass-cell { background-color: #E8F5E9; color: #2E7D32; font-weight: bold; }
    .fail-cell { background-color: #FFEBEE; color: #C62828; font-weight: bold; }
    .warn-cell { background-color: #FFF8E1; color: #F57F17; font-weight: bold; }
    .section-header { background-color: #E3F2FD; padding: 4px 8px; font-weight: bold;
                       border-left: 4px solid #1976D2; margin: 8px 0; }
    .stDataFrame { font-size: 13px; }
    div[data-testid="stMetric"] { background-color: #FAFAFA; padding: 8px;
                                   border: 1px solid #E0E0E0; border-radius: 4px; }
</style>
""", unsafe_allow_html=True)

st.title("DCM Flyback Transformer Design Tool")
st.caption("LLM/API 불필요 | 순수 계산 엔진 | 2안 시트 수식 기반")


# ─── Session State Init ─────────────────────────────────────────
if "outputs" not in st.session_state:
    st.session_state.outputs = [
        {"name": "PV15", "voltage": 15.0, "current_ma": 200.0, "isolated": False, "ns_set": 10, "wire_dia": 0.3},
        {"name": "NV15", "voltage": -15.0, "current_ma": 10.0, "isolated": False, "ns_set": 10, "wire_dia": 0.3},
        {"name": "IPV24", "voltage": 24.0, "current_ma": 180.0, "isolated": True, "ns_set": 14, "wire_dia": 0.3},
    ]
if "calculated" not in st.session_state:
    st.session_state.calculated = False


# ═══════════════════════════════════════════════════════════════
# PHASE 1: Output Tab Definition
# ═══════════════════════════════════════════════════════════════
st.markdown('<div class="section-header">Phase 1: Output Tab (출력 탭) 정의</div>', unsafe_allow_html=True)

col_add, col_remove = st.columns([1, 1])
with col_add:
    if st.button("+ 출력 추가", use_container_width=True):
        n = len(st.session_state.outputs) + 1
        st.session_state.outputs.append(
            {"name": f"OUT{n}", "voltage": 12.0, "current_ma": 100.0,
             "isolated": False, "ns_set": 5, "wire_dia": 0.3}
        )
        st.rerun()
with col_remove:
    if len(st.session_state.outputs) > 1 and st.button("- 마지막 출력 제거", use_container_width=True):
        st.session_state.outputs.pop()
        st.rerun()

out_df = pd.DataFrame(st.session_state.outputs)
edited_out = st.data_editor(
    out_df,
    column_config={
        "name": st.column_config.TextColumn("Tab Name", width="small"),
        "voltage": st.column_config.NumberColumn("Voltage (V)", min_value=-100, max_value=100, step=0.1, format="%.1f"),
        "current_ma": st.column_config.NumberColumn("Load (mA)", min_value=0, max_value=10000, step=1, format="%.0f"),
        "isolated": st.column_config.CheckboxColumn("Isolated (절연)", default=False),
        "ns_set": st.column_config.NumberColumn("Ns (turns)", min_value=1, max_value=500, step=1),
        "wire_dia": st.column_config.NumberColumn("Wire dia (mm)", min_value=0.05, max_value=2.0, step=0.01, format="%.2f"),
    },
    num_rows="fixed",
    use_container_width=True,
    hide_index=True,
    key="output_editor",
)
# Sync back
st.session_state.outputs = edited_out.to_dict("records")

pout_total = sum(abs(o["voltage"]) * o["current_ma"] / 1000.0 for o in st.session_state.outputs)
st.metric("Total Output Power", f"{pout_total:.2f} W")

st.divider()

# ═══════════════════════════════════════════════════════════════
# PHASE 2~4: Input Parameters (spreadsheet grid)
# ═══════════════════════════════════════════════════════════════
st.markdown('<div class="section-header">Phase 2~4: Input Spec / IC / Core</div>', unsafe_allow_html=True)

col_left, col_right = st.columns(2)

with col_left:
    st.markdown("**Input Spec**")
    vin_min = st.number_input("Vin Min (V DC)", value=300.0, step=10.0, key="vin_min")
    vin_max = st.number_input("Vin Max (V DC)", value=850.0, step=10.0, key="vin_max")
    vd_f = st.number_input("VD_F Diode (V)", value=0.9, step=0.1, key="vd_f")

    st.markdown("**IC Selection**")
    ic_name = st.selectbox("Controller IC", list(IC_DB.keys()), key="ic_sel")
    ic = IC_DB[ic_name]
    ic_info = pd.DataFrame([{
        "Duty Range": f"{ic.duty_min}~{ic.duty_max}%",
        "Fsw": f"{ic.fsw} kHz {'(fixed)' if ic.fsw_fixed else '(variable)'}",
        "OCP Threshold": f"{ic.ocp_voltage} V",
    }])
    st.dataframe(ic_info, hide_index=True, use_container_width=True)

with col_right:
    st.markdown("**Core Selection**")
    core_name = st.selectbox("Core", list(CORE_DB.keys()), index=list(CORE_DB.keys()).index("EE2020"), key="core_sel")
    core = CORE_DB[core_name]
    core_info = pd.DataFrame([{
        "Ae (mm2)": core.ae,
        "Le (mm)": core.le,
        "Ve (mm3)": core.ve,
        "AL_zero (nH/N2)": core.al_zero,
        "Aw (mm2)": core.aw,
        "Bobbin H (mm)": core.bobbin_height,
        "Bsat (T)": core.bsat,
        "Material": core.material,
    }])
    st.dataframe(core_info, hide_index=True, use_container_width=True)

    air_gap = st.number_input("Air Gap (mm)", value=0.3, min_value=0.1, step=0.1, format="%.1f", key="airgap")

    st.markdown("**MOSFET**")
    vds_rating = st.number_input("VDS Rating (V)", value=1500.0, step=100.0, key="vds_rating")
    v_spike = st.number_input("V Spike Margin (V)", value=200.0, min_value=50.0, max_value=300.0, step=10.0, key="vspike")

st.divider()

# ═══════════════════════════════════════════════════════════════
# PHASE 5~6: Turns & Shunt
# ═══════════════════════════════════════════════════════════════
st.markdown('<div class="section-header">Phase 5~6: Np/Ns, Air gap, Shunt</div>', unsafe_allow_html=True)

col_t1, col_t2, col_t3 = st.columns(3)

with col_t1:
    np_val = st.number_input("Np (Primary Turns)", value=90, min_value=1, max_value=500, step=1, key="np")
with col_t2:
    r_shunt = st.number_input("R_shunt (ohm)", value=2.0, min_value=0.1, step=0.1, format="%.1f", key="rshunt")
    ipk_limit = ic.ocp_voltage / r_shunt
    st.metric("Ipeak Limit", f"{ipk_limit:.3f} A")
with col_t3:
    bm_set = st.number_input("BM_set (T)", value=0.3, min_value=0.1, max_value=0.4, step=0.01, format="%.2f", key="bm")
    st.caption(f"Bsat = {core.bsat}T, Margin = {(core.bsat - bm_set)/core.bsat*100:.0f}%")

st.divider()

# ═══════════════════════════════════════════════════════════════
# PHASE 7~8: Wire & Current Density
# ═══════════════════════════════════════════════════════════════
st.markdown('<div class="section-header">Phase 7~8: Wire / Current Density</div>', unsafe_allow_html=True)

col_w1, col_w2, col_w3 = st.columns(3)
with col_w1:
    pri_wire_dia = st.number_input("1st Wire Dia (mm)", value=0.2, min_value=0.05, step=0.01, format="%.2f", key="priwire")
with col_w2:
    barrier_h = st.number_input("Barrier Height (mm)", value=2.0, step=0.5, key="barrier")
with col_w3:
    j_density = st.number_input("Current Density (A/mm2)", value=7.0, min_value=3.0, max_value=10.0, step=0.5, key="jdensity")
    st.caption("5~7 권장, 낮을수록 마진 설계")

st.divider()

# ═══════════════════════════════════════════════════════════════
# Lp Control
# ═══════════════════════════════════════════════════════════════
st.markdown('<div class="section-header">Lp 설정</div>', unsafe_allow_html=True)
col_lp1, col_lp2 = st.columns(2)
with col_lp1:
    lp_mode = st.radio("Lp.set 방식", ["Auto (10uH 올림)", "Auto (50uH 올림)", "Manual"], index=1, horizontal=True, key="lp_mode")
with col_lp2:
    lp_manual = st.number_input("Lp.set Manual (uH)", value=1050.0, step=10.0, key="lp_manual", disabled=(lp_mode != "Manual"))

st.divider()

# ═══════════════════════════════════════════════════════════════
# CALCULATE
# ═══════════════════════════════════════════════════════════════
if st.button("Calculate", type="primary", use_container_width=True):
    outputs = [
        OutputTab(
            name=o["name"], voltage=o["voltage"], current_ma=o["current_ma"],
            is_isolated=o["isolated"], ns_set=o["ns_set"], wire_dia_mm=o["wire_dia"],
        )
        for o in st.session_state.outputs
    ]

    lp_override = None
    if lp_mode == "Manual":
        lp_override = lp_manual

    inp = DesignInput(
        outputs=outputs,
        vin_min=vin_min,
        vin_max=vin_max,
        ic_name=ic_name,
        core_name=core_name,
        air_gap_mm=air_gap,
        np=np_val,
        primary_wire_dia_mm=pri_wire_dia,
        barrier_height_mm=barrier_h,
        current_density=j_density,
        r_shunt_ohm=r_shunt,
        bm_set=bm_set,
        v_spike_margin=v_spike,
        lp_set_uH=lp_override,
        vds_max_rating=vds_rating,
    )

    result = calculate(inp, core, ic)

    # Apply Lp rounding mode
    if lp_mode == "Auto (50uH 올림)" and lp_override is None:
        result.inductance.lp_set_uH = recommend_lp_set(result.inductance.lp_magnetic_uH, 50)
        result.inductance.lp_set_source = "auto (50uH ceil)"
        # Recalculate with updated Lp
        inp.lp_set_uH = result.inductance.lp_set_uH
        result = calculate(inp, core, ic)

    st.session_state.result = result
    st.session_state.calculated = True


# ═══════════════════════════════════════════════════════════════
# RESULTS (Spreadsheet-style)
# ═══════════════════════════════════════════════════════════════
if st.session_state.calculated and "result" in st.session_state:
    r: DesignResult = st.session_state.result

    # ── Warnings ──
    for w in r.warnings:
        st.warning(w)

    # ── Phase B: Output Parameters (엑셀 우측 영역) ──
    st.markdown('<div class="section-header">Phase B: Calculation Results</div>', unsafe_allow_html=True)

    # ── Row 1: Summary metrics ──
    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("Pin", f"{r.pin:.2f} W")
    m2.metric("Pout", f"{r.pout:.2f} W")
    m3.metric("Mode", r.duty.mode)
    m4.metric("Np/Ns", f"{r.turns.n_ratio_set:.1f}")
    m5.metric("Lp.set", f"{r.inductance.lp_set_uH:.1f} uH")

    # ── Turns Ratio Section ──
    col_a, col_b = st.columns(2)

    with col_a:
        st.markdown("**Turns Ratio (턴수비)**")
        turns_data = pd.DataFrame([
            {"항목": "Np/Ns 상한 (VDS 보호)", "값": f"{r.turns.n_ratio_upper:.2f}", "단위": "-",
             "수식": "n < (VDS_rating - Vin) / (Vout + VD_F)"},
            {"항목": "Np/Ns 하한 (DCM 조건)", "값": f"{r.turns.n_ratio_lower:.4f}", "단위": "-",
             "수식": "n > Vin / ((Vout+VD_F)x(1/D-1))"},
            {"항목": "Np/Ns 설정값", "값": f"{r.turns.n_ratio_set:.1f}", "단위": "-", "수식": "Np/Ns"},
            {"항목": "Vr (Reflected voltage)", "값": f"{r.turns.vr:.1f}", "단위": "V", "수식": "n x (Vout+VD_F)"},
            {"항목": "V Spike Margin", "값": f"{r.turns.v_spike_margin:.0f}", "단위": "V", "수식": "-"},
        ])
        st.dataframe(turns_data, hide_index=True, use_container_width=True)

        st.markdown("**Inductance (Lp)**")
        lp_data = pd.DataFrame([
            {"항목": "Lp [자기적]", "값": f"{r.inductance.lp_magnetic_uH:.2f}", "단위": "uH",
             "수식": "u0 x Np2 x Ae / gap"},
            {"항목": "Lp [에너지]", "값": f"{r.inductance.lp_energy_uH:.2f}", "단위": "uH",
             "수식": "Vin2 x D2 / (2xPinxFsw)"},
            {"항목": "Lp.set", "값": f"{r.inductance.lp_set_uH:.1f}", "단위": "uH",
             "수식": r.inductance.lp_set_source},
        ])
        st.dataframe(lp_data, hide_index=True, use_container_width=True)

    with col_b:
        st.markdown("**Duty / Current**")
        duty_data = pd.DataFrame([
            {"항목": "1차측 Duty", "값": f"{r.duty.d_primary:.4f}", "단위": "-",
             "수식": "sqrt(2xPinxLpxFsw)/Vin"},
            {"항목": "2차측 Duty", "값": f"{r.duty.d_secondary:.4f}", "단위": "-",
             "수식": "DxVin/(nx(Vout+VD_F))"},
            {"항목": "Ipeak", "값": f"{r.current.ip_peak:.4f}", "단위": "A",
             "수식": "2xPin/(VinxD)"},
            {"항목": "Irms (1차)", "값": f"{r.current.ip_rms:.4f}", "단위": "A",
             "수식": "Ipk x sqrt(D/3)"},
            {"항목": "Ipk Limit (Shunt)", "값": f"{r.ipk_limit:.3f}", "단위": "A",
             "수식": f"OCP_V / R_shunt"},
        ])
        st.dataframe(duty_data, hide_index=True, use_container_width=True)

        st.markdown("**Gap / Flux**")
        gap_data = pd.DataFrame([
            {"항목": "AL_zero", "값": f"{r.gap.al_zero:.0f}", "단위": "nH/N2", "수식": "Core DB"},
            {"항목": "AL_gapped", "값": f"{r.gap.al_gapped:.2f}", "단위": "nH/N2",
             "수식": "1/(1/AL0 + gap/(u0xAe))"},
            {"항목": "Air Gap", "값": f"{r.gap.air_gap_mm:.1f}", "단위": "mm", "수식": "User input"},
            {"항목": "Delta_B", "값": f"{r.flux.delta_b:.6f}", "단위": "T",
             "수식": "LpxIpk/(NpxAe)"},
            {"항목": "BM_set", "값": f"{r.flux.bm_set:.2f}", "단위": "T", "수식": "User input"},
            {"항목": "Bsat", "값": f"{r.flux.bsat:.2f}", "단위": "T", "수식": "Core material"},
        ])
        st.dataframe(gap_data, hide_index=True, use_container_width=True)

    # ── Wire Section ──
    st.markdown("**Wire Calculation (출력별)**")
    wire_rows = []
    for wc in r.wire_calcs:
        wire_rows.append({
            "Tab": wc.tab_name,
            "Vo (V)": wc.voltage,
            "Iout (mA)": wc.current_ma,
            "Ipk (A)": f"{wc.i_peak:.4f}",
            "Irms (A)": f"{wc.i_rms:.4f}",
            "Ns.cal": f"{wc.ns_calc:.1f}",
            "Ns.set": wc.ns_set,
            "Vo.cal (V)": f"{wc.vo_calc:.1f}",
            "Vrrm (V)": f"{wc.vrrm_calc:.1f}",
            "Wire Set (mm2)": f"{wc.wire_area_set:.4f}",
            "Wire Cal (mm2)": f"{wc.wire_area_calc:.4f}",
            "Wire Dia (mm)": wc.wire_dia_set,
            "Margin (%)": f"{wc.margin_pct:.1f}",
        })
    st.dataframe(pd.DataFrame(wire_rows), hide_index=True, use_container_width=True)

    # ── Judgment Section ──
    st.markdown('<div class="section-header">Phase 10: Judgment (판정)</div>', unsafe_allow_html=True)

    judge_rows = []
    for j in r.judgments:
        status = "PASS" if j.passed else "FAIL"
        judge_rows.append({
            "판정 항목": j.name,
            "값": f"{j.value:.4f}",
            "기준": f"{j.limit:.4f}",
            "단위": j.unit,
            "결과": status,
            "마진": f"{j.margin_pct:.1f}%",
        })

    judge_df = pd.DataFrame(judge_rows)
    st.dataframe(
        judge_df.style.map(
            lambda v: "background-color: #E8F5E9; color: #2E7D32; font-weight: bold"
            if v == "PASS" else (
                "background-color: #FFEBEE; color: #C62828; font-weight: bold"
                if v == "FAIL" else ""
            ),
            subset=["결과"]
        ),
        hide_index=True,
        use_container_width=True,
    )

    # ── Additional Info ──
    st.markdown("**추가 정보**")
    extra = pd.DataFrame([
        {"항목": "P.set (Lp.set 기준 Power)", "값": f"{r.p_set:.4f} W"},
        {"항목": "VDS Max", "값": f"{r.vds_max:.1f} V"},
        {"항목": "보빈 최대 턴수", "값": f"{r.max_turns_in_bobbin} turns"},
        {"항목": "Estimated Efficiency", "값": f"{r.efficiency*100:.0f}%"},
    ])
    st.dataframe(extra, hide_index=True, use_container_width=True)
