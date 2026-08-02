# 31장 예제 실행 가이드

확인 시점 2026년 8월. Python 3.9 이상.

```bash
cd content/ch31/code
pip install kuzu

python3 ex1_lost_update.py       # 진짜 스레드로 경쟁시킨다 (의존성 없음)
python3 ex2_optimistic.py        # 세 방식 비교 (의존성 없음)
python3 ex3_lock_contention.py   # 낙관적과 비관적이 뒤집히는 지점 (의존성 없음)
python3 ex4_conflict_shape.py    # 그래프에서 충돌 단위를 어디에 둘까
python3 ex5_merge_strategy.py    # 감지한 뒤에 무엇을 할까 (의존성 없음)
```

`ex1` 과 `ex2` 는 실제 스레드를 씁니다. 실행할 때마다 순서가 조금씩 달라질 수
있는데, 「하나가 사라진다」는 결과는 그대로입니다. 안 사라지면 `delay` 값을
키워서 다시 돌려 보세요.

`ex3` 의 값(판단 12ms, 잠금 획득 2.2ms)은 저희 환경에서 잰 것을 단순화한
것입니다. 뒤집히는 지점은 이 값에 따라 움직입니다. 직접 재서 넣으세요.
