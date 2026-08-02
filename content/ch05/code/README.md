# 5장 예제 실행 가이드

확인 시점 2026년 8월. Python 3.9 이상.

```bash
cd content/ch05/code
python3 ex1_two_models.py          # 의존성 없음
python3 ex2_edge_properties.py     # 의존성 없음
pip install kuzu "rdflib>=7,<8"
python3 ex3_cypher_vs_sparql.py    # 같은 질문을 두 언어로
python3 ex4_things_not_strings.py  # 의존성 없음
```

| 파일 | 보여 주는 것 |
|---|---|
| `model.py` | 같은 사실 여섯 개를 LPG 와 RDF 두 벌로 |
| `ex1_two_models.py` | 세는 «단위»가 다르다. 노드 3개 vs 트리플 12개 |
| `ex2_edge_properties.py` | 엣지 속성을 RDF 로 적는 세 가지 방법과 각각의 대가 |
| `ex3_cypher_vs_sparql.py` | 같은 질문, 같은 답, 다른 문장 모양 |
| `ex4_things_not_strings.py` | 술어 목록이 곧 사물의 정체다 |

Cypher 는 서버 없이 돌리려고 임베디드 엔진 **Kuzu 0.11.3** 을 씁니다.
Neo4j 5.x 와 문법이 갈리는 곳(노드 테이블 선언 등)은 코드 주석에 적어 두었습니다.
