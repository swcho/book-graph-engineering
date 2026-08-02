# 11장 예제 실행 가이드

확인 시점 2026년 8월. Python 3.9 이상.

```bash
cd content/ch11/code
pip install kuzu "rdflib>=7,<8"
python3 ex1_three_languages.py   # 같은 질문, 세 언어
python3 ex2_path_queries.py      # 가변 길이 경로 표기 비교
python3 ex3_gql_dialects.py      # GQL 표준 문법이 실제로 도는지
python3 ex4_sql_pgq.py           # SQL/PGQ (의존성 없음)
python3 ex5_read_plan.py         # 실행 계획 읽기
```

Cypher 는 서버 없이 돌리려고 임베디드 엔진 **Kuzu 0.11.3** 을 씁니다.
`ex3` 은 일부러 **실패하는 질의**를 포함합니다. 그게 이 예제의 결과입니다.
