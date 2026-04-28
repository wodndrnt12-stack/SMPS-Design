# SMPS Design Project

## Git 멀티 PC 동기화 규칙 (회사 ↔ 집)

### 작업 시작 전 — 반드시 pull

```bash
git pull origin main
```

- **새 터미널 열자마자, 코드 수정 전에 pull부터**
- 충돌 방지의 90%는 이것으로 해결

### 작업 완료 후 — 반드시 commit + push

```bash
git add -A
git commit -m "작업 내용 요약"
git push origin main
```

- 작업 중단 시에도 WIP 커밋으로 push
- push 안 하고 퇴근/귀가 = 다른 PC에서 못 봄

### 커밋 메시지 규칙

```
<type>: <요약>

type:
  feat     새 기능 / 새 파일
  fix      버그 수정
  refactor 리팩토링
  docs     문서
  wip      작업 중 임시 저장
```

### 충돌 발생 시 절차

1. `git pull origin main` → 충돌 표시 확인
2. 충돌 파일 열어서 수동 해결 (<<<< / >>>> 마커 제거)
3. `git add .` → `git commit` → `git push`
4. **절대 `--force` 사용 금지** — 상대 PC 작업 날아감

### 브랜치 전략

- **main 단독 사용** (1인 개발, 브랜치 분리 불필요)
- 큰 실험은 `exp/실험명` 브랜치 생성 후 merge

### .gitignore 필수 항목

- `.env`, `.venv/`, `__pycache__/` — 환경별 다름, 절대 push 금지
- `.claude/` — PC별 로컬 설정, git에 넣지 않음
- `*.xlsx` 대용량 바이너리 — 변경 추적 불가, 가능하면 별도 관리

### Claude Code 관련

- `.claude/` 폴더는 PC별 로컬 전용 → `.gitignore`에 포함
- `CLAUDE.md`는 프로젝트 공통 지침이므로 git에 포함
- `.mcp.json`은 PC별 경로가 다를 수 있으므로 주의

---

## 버전 관리 규칙

### 버전 형식

- `v0.XX` (소수점 두 자리, 0.01 단위 증분)
- 사용자가 "버전 올려" / "커밋해" 등 **명시적으로 요청할 때만** 커밋/푸시
- 자동 커밋 금지

### 버전 업데이트 시 필수 작업

1. `index.html` — 헤더 subtitle 버전 변경 (`SMPS Design Tool · vX.XX`)
2. `smps_transformer_agent/PROJECT_STATUS.md` — Changelog 섹션에 버전 + 변경 내용
3. 메모리에 버전별 변경 기록 저장 (롤백용)

### 메모리 버전 기록 규칙 (롤백 대비)

- 버전 올릴 때마다 `memory/smps_version_log.md`에 해당 버전의 변경 내역 누적 기록
- 기록 항목: 버전, 날짜, 커밋 해시, 변경 파일, 변경 내용 요약
- 롤백 필요 시 이 기록을 참조하여 `git revert` 또는 `git checkout` 대상 특정

---

## 컨텍스트 관리

- **매 태스크 완료 즉시** `_working_state.md` 갱신 → `/compact` 실행 (80% 기준 아님, 무조건)
- 큰 파일 Read 전에 compact 여유 확인 — index.html 전체 읽기는 필요한 라인만 offset/limit 사용
- 서브에이전트 결과가 큰 경우: 요약만 받고 원문은 버리기
- context 폭증 위험 작업(3D 구현, 대규모 리팩토링): **새 대화에서 시작** 권장
