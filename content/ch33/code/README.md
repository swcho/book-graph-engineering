# 33장 예제 실행 가이드

확인 시점 2026년 8월. Python 3.9 이상.

```bash
cd content/ch33/code
pip install kuzu

python3 ex1_read_plan.py        # 진짜 EXPLAIN 출력을 읽는다
python3 ex2_index_effect.py     # 인덱스가 언제 듣고 언제 안 듣나
python3 ex3_cost_model.py       # 월 비용을 항목별로 (의존성 없음)
python3 ex4_hot_query.py        # 제일 느린 것과 제일 아픈 것 (의존성 없음)
python3 ex5_where_time_goes.py  # 한 요청의 시간 분해 (의존성 없음)
```

`ex1`, `ex2` 는 데이터를 만드는 데 몇 초 걸립니다. `COPY` 로 일괄 적재해서
한 건씩 넣는 것보다 훨씬 빠릅니다. 그 자체가 33장에서 다루는 얘기이기도 합니다.

`ex2` 의 결과는 「인덱스가 별 효과 없다」처럼 보이는데, 그건 규모가 작아서입니다.
`SIZES` 를 백만 단위로 키우면 갈라집니다. 다만 실행이 오래 걸립니다.

`ex3`~`ex5` 의 숫자는 저자 환경의 실측을 단순화한 «예시 워크로드»입니다.
여러분 시스템의 값을 넣어서 다시 돌려 보세요. 구조가 요점이지 숫자가 요점이 아닙니다.
