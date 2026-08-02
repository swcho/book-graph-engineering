# 30장 예제 실행 가이드

확인 시점 2026년 8월. Python 3.9 이상.

```bash
cd content/ch30/code
pip install kuzu

python3 ex1_no_history.py        # 현재 상태만 두면 못 하는 질문들
python3 ex2_replay_cost.py       # 재생 값과 스냅숏 (의존성 없음)
python3 ex3_temporal_query.py    # 「그때 그래프」를 되살리는 두 방법
python3 ex4_reducer_conflict.py  # 리듀서가 답을 정한다 (의존성 없음)
python3 ex5_audit_trail.py       # 해시 고리로 위변조를 드러내기 (의존성 없음)
```

`ex2` 는 실행할 때마다 시간이 조금씩 달라집니다. 첫 줄(1만 개)에서 배수가
1 근처거나 그보다 작게 나오는 것도 정상입니다. 스냅숏이 아직 안 찍혔거든요.

`ex3` 의 조회 시간 비교는 이벤트 9개짜리 장난감 규모입니다.
이 숫자로 「재생이 빠르다」고 결론 내지 마세요.
