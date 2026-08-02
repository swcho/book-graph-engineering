# 34장 예제 실행 가이드

확인 시점 2026년 8월. Python 3.9 이상.

```bash
cd content/ch34/code
pip install kuzu

python3 ex1_delete_scope.py     # 노드만 지우면 무엇이 남나
python3 ex2_delete_levels.py    # 「지운다」의 네 수준 (의존성 없음)
python3 ex3_reidentify.py       # 이름을 지워도 특정된다 (의존성 없음)
python3 ex4_cascade.py          # 지우면 무엇이 같이 무너지나
python3 ex5_deletion_plan.py    # 삭제 절차를 검사 가능한 형태로 (의존성 없음)
```

이 장의 예제는 «구조»를 보여 주는 것이지 법적 조언이 아닙니다.
어느 수준까지 지워야 하는지는 관할과 업종에 따라 다르고, 그건 법무가 정할 일입니다.
엔지니어가 할 일은 「그 수준을 선택했을 때 무엇이 깨지는지」를 미리 세는 것입니다.

`ex5` 는 일부러 `Photo` 종류에서 막히게 해 두었습니다.
`POLICY` 에 한 줄 추가하면 통과합니다.
