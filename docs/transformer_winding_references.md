# Transformer Winding & 3D Visualization — Research References

> **NotebookLM Notebook:** [SMPS Transformer Winding & 3D Visualization Research](https://notebooklm.google.com/notebook/d1e780d5-1f0b-4969-8c76-3633aecd3c27)
> **리서치 일자:** 2026-04-28
> **모드:** Deep Research (web) × 3 queries
> **수집 소스:** 73개 → 핵심 22개 임포트

---

## 1. 권선 기법 (Winding Techniques)

### Application Notes & Industry Whitepapers

| # | 제목 | 출처 | 핵심 내용 |
|---|------|------|-----------|
| 1 | [Winding Architectures: Leakage & Parasitic Capacitance](https://www.powerelectronictips.com/how-do-different-winding-architectures-impact-transformer-leakage-inductance-and-parasitic-capacitance/) | Power Electronic Tips | Z-type vs U-type, interleaving, sandwich winding의 leakage/Cp 영향 비교 |
| 2 | [Transformer Construction and Core Design](https://www.electronics-tutorials.ws/transformer/transformer-construction.html) | Electronics Tutorials | Core/Shell type 구조, 권선 배치 기본 |
| 3 | [Transformer Parasitic Parameters & Equivalent Circuit](https://epci.eu/transformer-parasitic-parameters-and-equivalent-circuit/) | EPCI | 등가회로 모델, 기생 파라미터 체계적 정리 |

### IEEE / Academic Papers

| # | 제목 | 출처 | 핵심 내용 |
|---|------|------|-----------|
| 4 | [Parasitic Capacitance of Secondary Winding in HF HV Transformer (FEM)](https://www.researchgate.net/publication/322563120) | ResearchGate | 2D/3D FEA로 다층 2차 권선 기생 커패시턴스 모델링 |
| 5 | [Parasitic Capacitance of HF HV Transformers — Multi-Section Windings](https://scispace.com/pdf/investigation-on-the-parasitic-capacitance-of-high-frequency-4hz5rk3n08.pdf) | SciSpace | 다중 섹션 권선의 Cp 저감 기법 |
| 6 | [Parasitic Capacitance Modeling — Copper Foil, Fringe Field](https://vbn.aau.dk/ws/files/475862650/Parasitic_Capacitance_Modeling_of_Copper_Foiled_Medium_Voltage_Filter_Inductors_Considering_Fringe_Electrical_Field.pdf) | Aalborg Univ. | Edge effect 20% 기여, 스페이서/유전체 장벽 효과 |
| 7 | [Comparative Study: Parasitic Capacitance in Series vs Parallel Windings](https://vbn.aau.dk/ws/files/524595148/A_Comparative_Study_on_Parasitic_Capacitance_in_Inductors_With_Series_or_Parallel_Windings.pdf) | Aalborg Univ. | 직렬/병렬 권선의 에너지 저장 차이 |
| 8 | [Calculation Model — Parasitic Capacitance for HF Inductors & Transformers](https://www.researchgate.net/publication/376475136) | ResearchGate | Edge effect 포함 다층 권선 Cp 계산 모델 |
| 9 | [Transformer Parasitics for Resonant Converters — Stray Capacitance Review](https://www.ams-publications.ee.ethz.ch/uploads/tx_ethpublications/biela_IAS05.pdf) | ETH Zurich | 공진 컨버터용 stray capacitance 계산 방법론 총정리 |
| 10 | [Leakage Flux Modelling of Multi-Winding Transformer](https://infoscience.epfl.ch/bitstreams/55039624-8f42-4699-836b-9e7ce64833cc/download) | EPFL | 기하학적 누설 자속 모델링, permeance channel |

---

## 2. Skin Effect & Proximity Effect

| # | 제목 | 출처 | 핵심 내용 |
|---|------|------|-----------|
| 11 | [Skin and Proximity Effects of AC Current](https://www.allaboutcircuits.com/technical-articles/skin-and-proximity-effects-of-ac-current/) | All About Circuits | Skin depth 공식, Dowell 곡선, Litz wire 선정 가이드 |
| 12 | [Proximity Effect in Custom Magnetics](https://velatron.com/proximity-effect-in-custom-magnetics/) | Velatron | Skin vs Proximity 구분, current crowding 시각화 |
| 13 | [MIT OCW — Magnetics Lecture 12](https://ocw.mit.edu/courses/6-622-power-electronics-spring-2023/mit6_622_s23_lec122.pdf) | MIT | Power Electronics 강의, skin/proximity 이론 슬라이드 |
| 14 | [Skin & Proximity Effects — Analytical-Numerical Solution](https://www.mdpi.com/1996-1073/12/18/3584) | MDPI Energies | 두 병렬 원형 도체의 skin/proximity 해석해 |

### 주요 수식

- **Skin depth:** δ = √(2 / ωμσ) — Cu@100kHz ≈ **0.2mm**
- **AC/DC 저항비:** F_R = R_AC / R_DC (Dowell 곡선으로 산출)
- **도체 선택 기준:**

| 도체 | Skin 완화 | Proximity 완화 | 적용 |
|------|-----------|---------------|------|
| Solid Round | 나쁨 | 나쁨 | < 1kHz |
| Copper Foil | 우수 (폭방향) | 보통 | 고전류, 적은 레이어 |
| **Litz Wire** | **우수** | **우수** | **10kHz ~ 1MHz** |

---

## 3. 3D 시각화 & CAD 렌더링

| # | 제목 | 출처 | 핵심 내용 |
|---|------|------|-----------|
| 15 | [3D Modeling in Transformer Design](https://library.e.abb.com/public/934edb3ef800ba0c85257c21006857b9/3D+Modeling+in+Transformer+Design+(C).pdf) | ABB | 산업 실무 3D 모델링, stray flux 시각화 |
| 16 | [3D Transformer Simulation for Design Optimization](https://www.simscale.com/docs/simwiki/electromagnetics/3d-transformer-simulation-for-design-optimization/) | SimScale | 클라우드 3D 시뮬레이션, 커플링 최적화 |
| 17 | [Evaluating Transformer Designs with EM Simulation](https://www.comsol.com/blogs/evaluating-transformer-designs-with-electromagnetics-simulation) | COMSOL | 자기장/전기장 시각화, 코일 모델링 데모 |
| 18 | [3D EM and Thermal Behaviour Analysis of Magnetic Components](http://doi.fil.bg.ac.rs/pdf/journals/mtts_mr/2023-2/mtts_mr-2023-29-2-3.pdf) | ANSYS 기반 논문 | 3D ANSYS EM-열 연성 해석 |
| 19 | [3D Model of the Winding Product](http://sv-journal.org/2024-4/07/en.pdf) | Scientific Visualization | 권선 제품의 3D 모델 시각화 기법 |
| 20 | [3D Numerical Field Analysis — Tape Wound Cores](https://www.mdpi.com/1424-8220/24/10/3228) | MDPI Sensors | 3D 수치 해석으로 테이프 코어 손실 식별 |
| 21 | [Thermal Analysis — 2D and 3D FEM](https://www.mdpi.com/1996-1073/17/13/3203) | MDPI Energies | Hot spot 식별, 오일 점도 영향 (1mm²/s당 3°C) |
| 22 | [Creating Exploded Views — Onshape](https://www.onshape.com/en/resource-center/tech-tips/creating-exploded-views-cloud-native-cad) | Onshape | Exploded view 제작 가이드, 서브어셈블리 관리 |

---

## 4. 3D 뷰 보강 아이디어 (리서치 기반)

현재 구현된 기능과 추가 가능한 항목:

| 기능 | 현재 상태 | 보강 가능 |
|------|----------|-----------|
| 개별 와이어 턴 렌더링 | ✅ 구현 | — |
| Exploded View | ✅ 구현 | Explode line (조립 경로선) 추가 |
| 단면도 (Cross-section) | ✅ 2D 오버레이 | 3D 반단면 (half-section) 절단면 |
| 절연 테이프 레이어 | ❌ | Margin tape, insulation layer 시각화 |
| MMF 분포 그래프 | ❌ | 권선 레이어별 MMF 누적 그래프 |
| Skin depth 시각화 | ❌ | 도체 단면에 전류밀도 색상 그래디언트 |
| Leakage flux 경로 | ❌ | 코어-권선 간 자속 streamline |
| 기생 커패시턴스 표시 | ❌ | 레이어 간 Cp 값 오버레이 |
| 열지도 (Thermal map) | ❌ | 권선 온도 분포 히트맵 |
| 안전 거리 시각화 | ✅ IEC 규격 | Creepage/clearance 3D 마커 |

---

## 5. 검색 쿼리 (재사용용)

```
Query 1: SMPS flyback transformer winding technique interleaving sandwich winding EMI reduction leakage inductance application note Texas Instruments Infineon Wurth Elektronik IEEE paper

Query 2: transformer winding order primary secondary auxiliary safety isolation creepage clearance IEC 62368 UL bobbin margin tape triple insulated wire winding construction

Query 3: 3D transformer cross section visualization winding layer proximity effect skin effect parasitic capacitance coupling coefficient CAD rendering exploded view magnetic component design
```
