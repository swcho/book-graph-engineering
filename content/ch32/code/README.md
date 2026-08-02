# 32장 예제 실행 가이드

확인 시점 2026년 8월. Python 3.9 이상.

```bash
cd content/ch32/code
pip install kuzu

python3 ex1_breaking_change.py    # 무엇이 깨지고, 누가 읽고 있나
python3 ex2_expand_contract.py    # 확장-수축 여섯 단계
python3 ex3_when_to_contract.py   # 「아무도 안 쓴다」를 확인하는 법 (의존성 없음)
python3 ex4_dual_read.py          # 이행 중 읽기 전략 넷 (의존성 없음)
python3 ex5_migration_plan.py     # 마이그레이션을 검사 가능한 형태로 (의존성 없음)
```

`ex1` 은 29장에서 만든 `Reads` 엣지를 그대로 씁니다. 그 장을 안 보셨으면
「실행이 무엇을 읽었는지 기록해 둔다」 정도로 이해하시면 됩니다.

`ex5` 는 일부러 `dual-read` 단계에서 막히게 해 두었습니다.
`STATE["불일치_건수"]` 를 0으로 바꾸면 다음 단계로 넘어갑니다.
