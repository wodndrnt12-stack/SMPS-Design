# DCM Flyback SMPS Transformer Designer - Project Status

## 프로젝트 개요
- **목적**: SMPS 트랜스포머 자동화 설계 도구 (회사 사내 누구나 사용)
- **기반**: `2026.02.10 EC PFC SMPS 회로설계 기준서.xlsx`의 "2안" 시트
- **프레임워크**: Streamlit (LLM/API 없음, 완전 무료)
- **Python**: 3.14 (`C:\Users\jwjeong\AppData\Local\Programs\Python\Python314\python.exe`)
- **실행**: `streamlit run app.py` -> http://localhost:8501

---

## 파일 구조
```
smps_transformer_agent/
├── app.py                  # Streamlit 스프레드시트형 UI (메인)
├── pyproject.toml           # 의존성 (streamlit, pandas, openpyxl)
├── core/
│   ├── __init__.py
│   ├── database.py          # 코어 DB (EE/EI 10종) + IC DB (BD7F100HFN)
│   └── calc_engine.py       # 계산 엔진 (2안 시트 수식 미러링)
└── output/
```

---

## 설계 흐름 (사용자 확정)
1. **Output Tab 정의** - 출력 전압/전류 동적 추가 (절연/비절연 구분)
2. **부하 선정** - 각 탭별 소모 전류 입력
3. **입력전압** - DC Link 전압 (예: 300~850V)
4. **IC 선택** - BD7F100HFN (Duty 20~50%, Fsw 60kHz 고정, OCP 1V)
5. **Np/Ns 선정** - 사용자 입력 + 추천 로직
6. **Air gap 지정** - 최소 0.1mm (가공 현실성), AL_g 자동 계산
7. **자동 계산** - Lp, Duty, Ipeak, VDS 등
8. **와이어/전류밀도** - 사용자 지정 (5~7 A/mm2 권장)
9. **와이어 사이즈** - 턴수 고려, 보빈 물리 제약 확인
10. **판정** - DCM/Ipeak/VDS/Power/Flux/턴수비 (PASS/FAIL + 마진%)

---

## 핵심 수식 (2안 시트 기반)

### 턴수비 제약
- **상한**: `n < (VDS_rating - Vin_max) / (Vout + VD_F)` (VDS 보호)
- **하한**: `n > Vin / ((Vout + VD_F) * (1/Duty_max - 1))` (DCM 조건)

### 인덕턴스
- **자기적**: `Lp = u0 * Np^2 * Ae / gap`
- **에너지**: `Lp = Vin^2 * D^2 / (2 * Pin * Fsw)`

### Duty / 전류
- `D = sqrt(2 * Pin * Lp * Fsw) / Vin`
- `D_sec = D * Vin / (n * (Vout + VD_F))`
- `Ip_peak = 2 * Pin / (Vin * D)`
- `Ip_rms = Ip_peak * sqrt(D/3)`

### Air Gap
- `AL_g = 1 / (1/AL_zero + gap / (u0 * Ae))`

### VDS
- `VDS_max = Vin_max + Vr + V_spike_margin`
- `Vr = n * (Vout + VD_F)`

### Flux
- `delta_B = Lp * Ip_peak / (Np * Ae)`

### Shunt
- `Ipk_limit = OCP_voltage / R_shunt` (BD7F100HFN: OCP = 1V)

---

## 코어 DB (TDK 기반, <20W)

| Core | Type | Ae(mm2) | Le(mm) | Ve(mm3) | AL_zero(nH/N2) | Aw(mm2) | Bobbin(mm) | Material |
|------|------|---------|--------|---------|----------------|---------|------------|----------|
| EE10 | EE | 12.1 | 26.1 | 316 | 850 | 11.2 | 5.5 | PC47 |
| EE13 | EE | 17.1 | 30.2 | 516 | 1130 | 15.4 | 7.0 | PC47 |
| EE16 | EE | 19.0 | 34.5 | 680 | 1140 | 19.7 | 8.0 | PC47 |
| EE19 | EE | 23.0 | 39.4 | 900 | 1250 | 26.2 | 9.0 | PC47 |
| EE2020 | EE | 30.5 | 43.0 | 1340 | 1550 | 28.0 | 12.4 | PC40 |
| EE22 | EE | 41.1 | 39.2 | 1610 | 1600 | 37.8 | 10.0 | PC40 |
| EE25 | EE | 40.2 | 49.4 | 1990 | 1900 | 44.2 | 12.2 | PC40 |
| EI16 | EI | 19.8 | 33.0 | 653 | 1100 | 18.0 | 8.0 | PC40 |
| EI19 | EI | 24.0 | 39.6 | 950 | 1250 | 24.0 | 9.5 | PC40 |
| EI22 | EI | 42.0 | 39.3 | 1651 | 1600 | 36.0 | 10.0 | PC40 |

## IC DB

| IC | Duty Range | Fsw | OCP | Note |
|----|-----------|-----|-----|------|
| BD7F100HFN | 20~50% | 60kHz (fixed) | 1V | ROHM Flyback Controller |
| (추후 추가) | - | - | - | 10개 미만 예정 |

---

## 판정 로직 (6개 항목)

| # | 판정 | 조건 | 비고 |
|---|------|------|------|
| 1 | DCM | D_pri + D_sec < 1.0 | DCM/CCM 판별 |
| 2 | Ipeak | Ip_peak < Ipk_limit | OCP = V_ocp / R_shunt |
| 3 | Power | P_set >= Pin | Lp.set 기준 전력 검증 |
| 4 | VDS | VDS_max < MOSFET_rating | Vin_max + Vr + Spike |
| 5 | Flux | delta_B <= BM_set | 기본 0.3T, 포화마진 확인 |
| 6 | 턴수비 | n_lower <= n <= n_upper | VDS/DCM 양측 제약 |

---

## 사용자 확정 사항

### 입력 방식
- **Vin**: DC Link 전압 (PFC 후단)
- **IC**: 선택하면 Duty/Fsw/OCP 자동 채워짐
- **Core**: 선택하면 Ae/AL_zero 자동 채워짐
- **Air gap**: 사용자 직접 지정 (최소 0.1mm)
- **Np**: 사용자 직접 입력 (추천 로직 제공)
- **R_shunt**: 사용자 입력 -> Ipk_limit 자동 계산
- **BM_set**: 기본 0.3T, 포화 마진 부족 시 사용자 변경 유도
- **Lp.set**: Auto (10/50uH 올림 토글) 또는 Manual 오버라이드
- **Wire dia**: 사용자 직접 지정
- **전류밀도**: 사용자 기입 (5~7 A/mm2 권장)
- **V Spike Margin**: 사용자 입력 (보통 100~200V)

### UI
- 스프레드시트형 (한눈에 입력/계산/판정 모두 표시)
- data_editor로 출력 탭 편집
- PASS/FAIL 색상 구분 + 마진% 표시

---

## 추후 작업 (기록만, 미구현)

### 근시일 내
- [ ] 엑셀 내보내기 (.xlsx)
- [ ] 부하사양 계산 시트 (부품별 소모전류 -> 총 부하)
- [ ] 추가 IC 등록 (10개 미만)
- [ ] Np/Ns 추천 로직 고도화 (ICL 기반)

### 중기
- [ ] 트랜스포머 구조 시트 (권선 순서, 배리어 배치, 절연)
- [ ] 절연거리 계산 (UL 61800, 강화절연 8mm 등)
- [ ] 와이어 타입 선택 (2UEW / TIW)
- [ ] 2D/3D 트랜스포머 구조 시각화

### 장기
- [ ] 전원 확인 시트 통합
- [ ] 수명 시트 통합
- [ ] Start up 시트 통합
- [ ] 주변회로 시트

---

## 참고 파일
- `2026.02.10 EC PFC SMPS 회로설계 기준서.xlsx` (9개 시트)
  - [0] 트랜스포머 구조 (2) - 권선 배치도
  - [1] 부하사양2 - 출력별 소모전류
  - [2] **2안** - 트랜스포머 설계 계산서 (이 도구의 기반)
  - [3] 전원 확인
  - [4] 수명
  - [5] 주변회로
  - [6] Start up
  - [7] Start up 검증
  - [8] Sheet1

## MCP
- Playwright MCP: `.mcp.json`에 설정됨
