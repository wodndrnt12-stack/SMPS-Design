"""Core and IC database for Flyback SMPS Transformer Design.

Sources:
- TDK PC40/PC47 ferrite core datasheets
- User-confirmed EE2020: Ae=30.5mm2, AL_zero=1550nH/N2
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class CoreData:
    name: str
    ae: float       # mm2, effective cross-sectional area
    le: float       # mm, effective magnetic path length
    ve: float       # mm3, effective volume
    al_zero: float  # nH/N2, ungapped inductance factor
    aw: float       # mm2, window area (bobbin-dependent)
    bobbin_height: float  # mm, winding window height
    bsat: float     # T, saturation flux density (at 100C)
    material: str
    core_type: str  # EE or EI


@dataclass(frozen=True)
class ICData:
    name: str
    duty_min: float     # %, minimum duty cycle
    duty_max: float     # %, maximum duty cycle
    fsw: float          # kHz, switching frequency
    fsw_fixed: bool     # True if fixed frequency
    ocp_voltage: float  # V, OCP threshold voltage (across shunt)
    vds_max_rating: float  # V, max VDS rating
    note: str


# ─── EE / EI Core Database (TDK, <20W, PC40/PC47 material) ──────

CORE_DB: dict[str, CoreData] = {
    # EE cores - TDK PC40/PC47
    "EE10": CoreData(
        name="EE10", ae=12.1, le=26.1, ve=316, al_zero=850,
        aw=11.2, bobbin_height=5.5, bsat=0.39, material="PC47", core_type="EE",
    ),
    "EE13": CoreData(
        name="EE13", ae=17.1, le=30.2, ve=516, al_zero=1130,
        aw=15.4, bobbin_height=7.0, bsat=0.39, material="PC47", core_type="EE",
    ),
    "EE16": CoreData(
        name="EE16", ae=19.0, le=34.5, ve=680, al_zero=1140,
        aw=19.7, bobbin_height=8.0, bsat=0.39, material="PC47", core_type="EE",
    ),
    "EE19": CoreData(
        name="EE19", ae=23.0, le=39.4, ve=900, al_zero=1250,
        aw=26.2, bobbin_height=9.0, bsat=0.39, material="PC47", core_type="EE",
    ),
    "EE2020": CoreData(
        name="EE2020", ae=30.5, le=43.0, ve=1340, al_zero=1550,
        aw=28.0, bobbin_height=12.4, bsat=0.39, material="PC40", core_type="EE",
    ),
    "EE22": CoreData(
        name="EE22", ae=41.1, le=39.2, ve=1610, al_zero=1600,
        aw=37.8, bobbin_height=10.0, bsat=0.39, material="PC40", core_type="EE",
    ),
    "EE25": CoreData(
        name="EE25", ae=40.2, le=49.4, ve=1990, al_zero=1900,
        aw=44.2, bobbin_height=12.2, bsat=0.39, material="PC40", core_type="EE",
    ),
    # EI cores - TDK
    "EI16": CoreData(
        name="EI16", ae=19.8, le=33.0, ve=653, al_zero=1100,
        aw=18.0, bobbin_height=8.0, bsat=0.39, material="PC40", core_type="EI",
    ),
    "EI19": CoreData(
        name="EI19", ae=24.0, le=39.6, ve=950, al_zero=1250,
        aw=24.0, bobbin_height=9.5, bsat=0.39, material="PC40", core_type="EI",
    ),
    "EI22": CoreData(
        name="EI22", ae=42.0, le=39.3, ve=1651, al_zero=1600,
        aw=36.0, bobbin_height=10.0, bsat=0.39, material="PC40", core_type="EI",
    ),
}


# ─── IC Database ─────────────────────────────────────────────────

IC_DB: dict[str, ICData] = {
    "BD7F100HFN": ICData(
        name="BD7F100HFN",
        duty_min=20.0,
        duty_max=50.0,
        fsw=60.0,
        fsw_fixed=True,
        ocp_voltage=2.0,
        vds_max_rating=0,  # external MOSFET
        note="ROHM Flyback Controller, Duty 20~50%, Fsw 60kHz fixed",
    ),
    # 추후 IC 추가 시 여기에 추가
    # "NCP1234": ICData(...),
}
