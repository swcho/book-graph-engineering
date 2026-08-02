# 28장 예제 실행 가이드

확인 시점 2026년 8월. Python 3.9 이상.

```bash
cd content/ch28/code
pip install kuzu

python3 ex1_write_loop.py         # 검증 없이 쓰면 10턴 만에 이렇게 된다
python3 ex2_write_gate.py         # 관문 넷이 각각 다른 것을 잡는다
python3 ex3_provenance.py         # 출처를 철회하면 무엇이 같이 무너지나
python3 ex4_drift.py              # 스스로 쓰는 루프의 분포 편향 (의존성 없음)
python3 ex5_expansion_budget.py   # 어디까지 넓힐 것인가 (의존성 없음)
```

`ex4` 는 시드를 3으로 고정했습니다. 시드를 바꾸면 숫자가 몇 %p 움직이는데
«제약이 줄고 사건이 는다»는 방향은 바뀌지 않습니다.

`ex5` 의 수확률과 정확도는 저희 도메인에서 잰 값을 단순화한 것입니다.
여러분 도메인에서는 홉별 정확도를 직접 재서 넣으세요.
