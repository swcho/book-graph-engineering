# 27장 예제 실행 가이드

확인 시점 2026년 8월. Python 3.9 이상.

```bash
cd content/ch27/code
pip install kuzu

python3 ex1_memory_shapes.py     # 같은 기억을 세 모양으로
python3 ex2_graph_vs_vector.py   # 벡터와 그래프가 강한 질문이 다르다
python3 ex3_temporal_memory.py   # 「언제부터 언제까지 참이었나」
python3 ex4_memory_cost.py       # 사실 수에 따른 두 방식의 하루 비용
python3 ex5_forgetting.py        # 잊기 정책 세 가지 (의존성 없음)
```

`ex2` 의 «임베딩»은 손으로 적은 3차원 좌표입니다. 진짜 임베딩 모델을 쓰면
숫자는 달라지지만 «벡터가 못 하는 것»(전부 세기, 없음 확인)은 그대로입니다.

`ex4` 는 실행할 때마다 조회 시간이 조금씩 달라집니다. 이 규모에서는
측정 잡음이 지배하기 때문이고, 그 자체가 예제의 요점입니다.
