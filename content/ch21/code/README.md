# 21장 예제 실행 가이드

확인 시점 2026년 8월. Python 3.9 이상.

```bash
cd content/ch21/code
pip install "langgraph>=1.0,<2.0" "langgraph-checkpoint-sqlite<3"

bash run_crash_demo.sh          # 프로세스를 실제로 죽였다가 이어서 실행
python3 ex2_idempotency.py      # 의존성 없음
python3 ex3_side_effect_log.py  # 의존성 없음
python3 ex4_checkpointer_cost.py # 체크포인터별 지연 실측
python3 ex5_recovery_drill.py   # 의존성 없음
```

`langgraph-checkpoint-sqlite` 는 **3 미만**을 쓰세요.
3.x 는 `langgraph-checkpoint` 4.x 를 끌어오는데, 확인 시점의 langgraph 1.0.1 과
직렬화 계층이 맞지 않아 임포트에서 실패합니다.
