# 16장 예제 실행 가이드

확인 시점 2026년 8월. Python 3.9 이상.

```bash
cd content/ch16/code
python3 ex1_two_axes.py       # 의존성 없음
python3 ex2_correction.py     # 의존성 없음
python3 ex3_string_dates.py   # 의존성 없음
pip install kuzu "rdflib>=7,<8"
python3 ex4_temporal_query.py # Cypher / SPARQL 시점 질의
python3 ex5_storage_cost.py   # 의존성 없음
```

| 파일 | 보여 주는 것 |
|---|---|
| `bitemporal.py` | 이중 시간 저장소 100줄 |
| `ex1` | 같은 저장소에 네 가지 시점 질문 |
| `ex2` | 만료와 정정을 섞으면 과거 재현이 깨진다 |
| `ex3` | 날짜를 문자열로 비교하면 6건 중 5건이 틀린다 |
| `ex4` | LPG는 엣지 속성으로, RDF는 사건 노드로 |
| `ex5` | 이중 시간의 저장 비용과 자르는 기준 |
