# 4장 예제 실행 가이드

확인 시점 2026년 8월. Python 3.9 이상.

```bash
cd content/ch04/code
python3 ex1_triples_by_hand.py    # 의존성 없음
pip install "rdflib>=7,<8"
python3 ex2_sparql.py             # sample.ttl 을 읽는다
python3 ex3_open_world.py         # 의존성 없음
python3 ex4_jsonld.py             # 의존성 없음
```

| 파일 | 보여 주는 것 |
|---|---|
| `sample.ttl` | 같은 회사 데이터를 Turtle 로. 38 트리플 |
| `ex1_triples_by_hand.py` | 트리플 저장소와 이행 폐포를 30줄로 |
| `ex2_sparql.py` | SPARQL 경로 질의 `+` 하나가 재귀 CTE 20줄을 대신한다 |
| `ex3_open_world.py` | 열린 세계 가정이 실무에서 사고가 되는 지점 |
| `ex4_jsonld.py` | 시맨틱 웹이 실제로 이긴 자리 (schema.org / JSON-LD) |
