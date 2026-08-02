# 22장 예제 실행 가이드

확인 시점 2026년 8월. Python 3.9 이상. 외부 의존성 없음.

```bash
cd content/ch22/code
python3 ex1_backoff.py          # 재시도 전략별 부하 봉우리
python3 ex2_timeout_budget.py   # 층별 타임아웃과 예산 배분
python3 ex3_saga.py             # 보상 트랜잭션과 단계 순서
python3 ex4_undo_fails.py       # 되갚기가 실패할 때
python3 ex5_dlq.py              # 데드레터 큐와 원인 분류
```

`ex1` 은 난수를 쓰지만 시드를 42로 고정했습니다. 시드를 바꾸면 숫자가
조금 달라지는데, 세 전략의 순서는 바뀌지 않습니다.
