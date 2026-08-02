# 19장 예제 실행 가이드

확인 시점 2026년 8월. Python 3.9 이상.

```bash
cd content/ch19/code
pip install "langgraph>=1.0,<2.0"
python3 ex1_lost_update.py      # 리듀서가 없으면 갱신이 사라진다
python3 ex2_superstep.py        # 슈퍼스텝 경계를 눈으로
python3 ex3_custom_reducer.py   # 필드마다 다른 합치기 규칙
python3 ex4_state_size.py       # 의존성 없음
python3 ex5_debug_state.py      # 체크포인트로 시간 여행
```

`ex1` 은 일부러 **예외가 나는** 경우를 포함합니다. 그게 이 예제의 결과입니다.
