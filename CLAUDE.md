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
