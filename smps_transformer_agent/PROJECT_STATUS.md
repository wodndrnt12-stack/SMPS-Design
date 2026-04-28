# DCM Flyback SMPS Transformer Designer — Project Status

> **현재 버전: v0.02**

## 프로젝트 개요

- **목적**: DCM Flyback 트랜스포머 설계 도구 (<20W, 사내 누구나 사용)
- **기반**: `2026.02.10 EC PFC SMPS 회로설계 기준서.xlsx` — "2안" 시트
- **구현**: **단일 HTML** (`index.html`, file:// 직접 실행)
- **이유**: Streamlit → HTML 전환. file:// CORS 문제로 별도 JS/JSON 분리 불가
- **테스트**: Playwright 66개 (Phase 1~4 + Wire DB 전체 커버)

---

## 파일 구조

```
SMPS Design/
├── index.html                 # 메인 설계 도구 (1777줄, Phase 1~4 통합)
├── CLAUDE.md                  # 프로젝트 지침 (Git 동기화 규칙)
├── playwright.config.js       # Playwright 설정
├── package.json               # npm (playwright 의존성)
├── .gitignore
├── tests/
│   └── smps.spec.js           # Playwright 테스트 56개
└── smps_transformer_agent/    # ⚠ Legacy (Streamlit 버전, 미사용)
    ├── PROJECT_STATUS.md      # 이 파일
    ├── app.py                 # Streamlit UI (폐기)
    ├── pyproject.toml
    └── core/
        ├── database.py        # Python Core/IC DB (참조용으로만 유지)
        └── calc_engine.py     # Python 계산 엔진 (폐기)
```

---

## index.html 내부 구조

### 레이아웃

```
#app
├── #hdr (고정 헤더: 브랜드 + 프리셋 관리 + Library/Compare 버튼)
└── #page1
    ├── #top-panels (flex)
    │   ├── #left   50%  입력/계산 테이블 (①~⑥ 섹션)
    │   ├── #center 25%  Dashboard (배지, KPI, Duty/Flux 바, Lp 비교)
    │   └── #right  25%  Loss/Stress/Core검증/RCD Snubber
    └── #bottom-wire 220px  Wire Table (Np + 2차 채널)
```

### 내장 DB

| DB | 내용 | 저장소 |
|----|------|--------|
| CORE_DB | EE/EI 10종 (TDK PC40/PC47) | JS 상수 |
| IC_DB | BD7F100HFN (ROHM) | JS 상수 |
| MOSFET_DB | STH3N150 (1500V/6Ω) | JS 상수 |
| STEINMETZ | PC40/PC47 Steinmetz 계수 | JS 상수 |
| WIRE_DB | 0.16~0.40φ 2UEW/TIW 피복 직경 10종 | JS 상수 |
| userCores/userMosfets | 사용자 추가 부품 | localStorage |
| Presets | 설계안 저장/비교 | localStorage |

### 핵심 함수

| 함수 | 역할 |
|------|------|
| `updateAll()` | 전체 재계산 엔진 (모든 입력 변경 시 호출) |
| `renderWireTable()` | Wire Table DOM 생성 |
| `captureSnapshot()` / `runCompare()` | Phase 4 비교 엔진 |
| `openLibrary()` / `showLibTab()` | 부품 DB 관리 모달 |
| `savePreset()` / `loadSelectedPreset()` | 프리셋 CRUD |

---

## Phase 진행 현황

### Phase 1 — Transformer Core Design ✅

- 입력: Vin(DC Link), Vout/Iout(채널), Core, IC, MOSFET, Np/Ns, Lp, Air gap
- 계산: n 상한/하한, Lp(자기적/에너지), D_on/D_off, Ipk, VDS, ΔB
- 판정: DCM / Ipk / Power / VDS / Flux (5개 PASS/FAIL)
- Dashboard: KPI 카드, Duty 바, Flux 마진 바
- Wire Table: Np + 2차 채널 (동적 추가/삭제)
- 프리셋: 저장/불러오기/삭제

### Phase 2 — Loss & Stress Analysis ✅

- MOSFET: Conduction (I²Rds, +0.4%/°C), Switching (½·Vds·Id·(tr+tf)·Fsw), Gate drive (Qg·Vgs·Fsw)
- Diode: VD_F × Iout
- Copper: Primary/Secondary (ρ·L/A, 온도 보정, 다층 보정)
- Core: Steinmetz (Pv = k·f^a·Bm^b, PC40/PC47, 온도 보정)
- Snubber R 손실
- Total Loss, η, MOSFET Pd/Tj 추정 (Rth=62°C/W)
- Stress 바: VDS/Ipk/Flux (safe/warn/danger 색상)
- Diode Vrrm 채널별 표시
- Bsat 온도 디레이팅, Window Utilization

### Phase 3 — RCD Snubber ✅

- 입력: Llk%, Vclamp, ΔVc 리플%
- 계산: Llk, P_snubber, R_snub, C_snub, VDS(clamped)
- Vclamp ≤ Vr 경고, Vclamp/Vr 비율 가이드 (1.2~1.5 권장)
- VDS clamped 스트레스 바

### Phase 4 — Preset Compare ✅

- A vs B 프리셋 비교 (또는 "현재 상태" 선택)
- DOM 스냅샷 방식: save → load → calc → capture → restore
- 7개 그룹, ~40개 파라미터 비교 테이블
- 색상 코딩: prefer:'low'(손실) → 낮은 쪽 green, prefer:'high'(η, margin) → 높은 쪽 green
- Δ(B−A) 표시, 입력값 포함 토글

---

## Changelog

### v0.02 (2026-04-28) — Wire DB 자동 연동

- feat: WIRE_DB 상수 추가 (0.16~0.40φ, 2UEW/TIW 피복 직경 10종)
- feat: Wire Type(2UEW/TIW) + Wire Size 드롭다운 자동 연동
- feat: Wire Table — Np/2차 채널별 와이어 규격 드롭다운 + Coat[mm] 컬럼
- feat: 양방향 동기화 (Wire & Bobbin ↔ Wire Table Np)
- feat: Window Utilization — 피복 직경 기반 계산으로 변경
- feat: 프리셋 저장/복원에 wireType, wireSize 포함
- test: Wire DB 테스트 10개 추가 (총 66개)

### v0.01 (2026-04-28) — 초기 통합 완료

- Phase 1~4 전체 구현 완료
- Playwright 테스트 56개 작성
- fix: Steinmetz k값 단위 불일치 (PC40: 5.87e-3→3.2e-4, PC47: 3.80e-3→1.4e-3, f:Hz/B:T)
- fix: OCP 전압 2V→1V (BD7F100HFN 데이터시트 기준)
- fix: Pout 음전압 채널 abs() 미적용

---

## 핵심 수식

### 턴수비 제약

- **상한**: `n < (VDS_limit − Vin_max) / (Vout + VD_F)`
- **하한**: `n > Vin_min / ((Vout + VD_F) × (1/D_on − 1))`

### 인덕턴스

- **자기적**: `Lp = μ₀ × Np² × Ae / gap`
- **에너지**: `Lp = Vin² × D² / (2 × Pin × Fsw)`

### Duty / 전류

- `D_on = √(2 × Pin × Lp × Fsw) / Vin_min`
- `D_off = D_on × Vin_min / Vr`
- `Ipk = 2 × Pin / (Vin_min × D_on)` = `√(2×Pin/(Lp×Fsw))` (Vin에 무관)

### VDS

- `VDS = Vin_max + Vr + V_spike`
- `VDS_limit = VDS_rating − VDS_margin`

### Flux

- `ΔB = Lp × Ipk / (Np × Ae)`
- `Bsat(T) = Bsat_25 × (1 − derating × (T − 25))`

### Steinmetz Core Loss

- `Pv[mW/cm³] = k × f[Hz]^α × Bm[T]^β × tempCorr`
- `Bm = ΔB / 2` (half-amplitude)
- `tempCorr = 1 + 0.003 × |T − 80|`
- PC40: k=3.2e-4, α=1.63, β=2.58
- PC47: k=1.4e-3, α=1.46, β=2.67

### RCD Snubber

- `P_snub = ½ × Llk × Ipk² × Fsw`
- `R_snub = Vclamp² / P_snub`
- `C_snub = 1 / (R × Fsw × ripple%)`
- `VDS_clamped = Vin_max + Vclamp`

---

## 코어 DB (TDK, <20W)

| Core | Type | Ae(mm²) | Ve(mm³) | AL₀(nH/N²) | Aw(mm²) | Bobbin(mm) | Material |
|------|------|---------|---------|-------------|---------|------------|----------|
| EE10 | EE | 12.1 | 316 | 850 | 11.2 | 5.5 | PC47 |
| EE13 | EE | 17.1 | 516 | 1130 | 15.4 | 7.0 | PC47 |
| EE16 | EE | 19.0 | 680 | 1140 | 19.7 | 8.0 | PC47 |
| EE19 | EE | 23.0 | 900 | 1250 | 26.2 | 9.0 | PC47 |
| EE2020 | EE | 30.5 | 1340 | 1550 | 28.0 | 12.4 | PC40 |
| EE22 | EE | 41.1 | 1610 | 1600 | 37.8 | 10.0 | PC40 |
| EE25 | EE | 40.2 | 1990 | 1900 | 44.2 | 12.2 | PC40 |
| EI16 | EI | 19.8 | 653 | 1100 | 18.0 | 8.0 | PC40 |
| EI19 | EI | 24.0 | 950 | 1250 | 24.0 | 9.5 | PC40 |
| EI22 | EI | 42.0 | 1651 | 1600 | 36.0 | 10.0 | PC40 |

## IC / MOSFET DB

| IC | Duty | Fsw | OCP | Note |
|----|------|-----|-----|------|
| BD7F100HFN | 20~50% | 60kHz fixed | 1.0V | ROHM Flyback Controller |

| MOSFET | VDS | Rds_on(typ) | Coss | Qg | tr/tf | Package |
|--------|-----|-------------|------|----|-------|---------|
| STH3N150 | 1500V | 6Ω | 102pF | 29.3nC | 47/61ns | H2PAK-2 |

---

## Playwright 테스트 (66개)

| 카테고리 | 수 | 내용 |
|---------|---|------|
| Phase 1 | 17 | 로드, 초기값, 계산, 드롭다운, Wire Table, KPI |
| Phase 2 | 14 | 손실 8항목, η, Stress 바, 온도 디레이팅, Window |
| Phase 3 | 9 | Llk, P_snub, R/C, VDS clamped, Vclamp 경고 |
| Phase 4 | 11 | Compare 모달, 프리셋 저장, 비교, 색상 코딩, 복원 |
| Integration | 5 | 연쇄 계산, 채널 추가, Library 모달 |
| Wire DB | 10 | 드롭다운, 자동연동, TIW/2UEW 전환, Np 동기화, maxTurns |

실행: `npx playwright test`

---

## 미구현 — 향후 작업

### 단기 (기능 보강)

- [ ] 엑셀 내보내기 (.xlsx) — 설계 결과를 xlsx로 export
- [ ] 부하사양 계산 시트 — 부품별 소모전류 합산 → 총 부하
- [ ] IC DB 확장 — NCP1234 등 추가 (10개 미만)
- [ ] MOSFET DB 확장 — 추가 MOSFET 등록
- [ ] Np/Ns 추천 로직 — n 범위 내 최적 Np/Ns 자동 제안

### 중기 (설계 시트 확장)

- [ ] 트랜스포머 구조 시트 — 권선 순서, 배리어 배치, 절연 구조
- [ ] 절연거리 계산 — UL 61800 강화절연 (8mm) 등
- [x] 와이어 타입 선택 — 2UEW / TIW 구분 ✅ v0.02
- [ ] 2D 트랜스포머 단면도 시각화
- [ ] Multi-output 정밀 계산 — 크로스 레귤레이션 고려

### 장기 (통합 설계 시스템)

- [ ] 전원 확인 시트 통합
- [ ] 수명 시트 통합
- [ ] Start up 시트 통합
- [ ] 주변회로 시트 (바이어스, 피드백 등)
- [ ] EMI 필터 설계 연동

---

## 참고 파일

- `2026.02.10 EC PFC SMPS 회로설계 기준서.xlsx` (9개 시트)
  - [0] 트랜스포머 구조 (2) — 권선 배치도
  - [1] 부하사양2 — 출력별 소모전류
  - [2] **2안** — 트랜스포머 설계 계산서 (이 도구의 기반)
  - [3] 전원 확인
  - [4] 수명
  - [5] 주변회로
  - [6] Start up
  - [7] Start up 검증
  - [8] Sheet1
