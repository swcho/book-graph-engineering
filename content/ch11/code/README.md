# 11장 — 같은 질문, 세 가지 언어

`2부 · 그래프의 기초 문법` · [책 전체 목차](../../../README.md) · [출처 링크 모음](../../../SOURCES.md)

> 면접에서 이런 질문을 받은 적이 있습니다. "Cypher랑 SPARQL 중에 뭐가 더 좋다고 생각하세요?"

이 장은 그 두 시간을 압축한 겁니다. 같은 질문을 세 언어로 쓰고, 2024년에 국제 표준이 된 언어가 그 셋과 어떻게 다른지 봅니다. 그리고 「표준이 나왔다」와 「표준대로 돌아간다」 사이에 몇 년이 있는지도요.

## 이 장의 절

| 절 | 제목 |
|---|---|
| 11.1 | 그림, 문장, 걸음 |
| 11.2 | 경로 표현에서 갈린다 |
| 11.3 | 2024년에 표준이 됐다. 그런데 |
| 11.4 | 테이블은 그대로 두고 그래프로 보기 |

## 한 장 요약

- 세 언어는 그래프를 다르게 생각합니다. Cypher는 그림, SPARQL은 문장, Gremlin은 걸음이에요. 앞의 둘은 선언형이고 셋째는 명령형에 가깝습니다.
- 차이가 제일 크게 벌어지는 건 경로 표현입니다. Cypher는 상한을 쓸 수 있고, SPARQL은 표준에 상한 표기가 없고, SQL은 재귀 CTE 스무 줄이 됩니다.
- GQL은 2024년에 국제 표준이 됐습니다. 그런데 표준 전용 문법은 아직 엔진들이 안 받아요. 표준의 효과는 「지금 코드가 바뀐다」가 아니라 「방향이 정해진다」입니다.
- SQL/PGQ는 데이터를 옮기지 않고 그래프 시각만 얹습니다. 매력적인데 구현이 아직 덜 퍼졌고, 조인 폭발은 그대로 남습니다.
- 이식을 대비하려면 질의문을 한곳에 모으고, `ORDER BY`를 강제하고, 엔진 고유 함수를 격리하고, 각 질의가 답하는 질문을 주석으로 남기세요.

## 키워드와 1차 출처

| 키워드 | 상태 | 출처 |
|---|---|---|
| 그래프 질의 언어 GQL | [표준] | [ISO/IEC 39075:2024](https://www.iso.org/standard/76120.html) |
| 속성 그래프 질의 SQL/PGQ | [표준] | [ISO/IEC 9075-16:2023](https://www.iso.org/standard/79473.html) |
| Cypher 질의 언어 | [사실상 표준] | [Cypher Manual](https://neo4j.com/docs/cypher-manual/current/) |
| SPARQL 1.1 질의 | [표준] | [SPARQL 1.1 Query Language](https://www.w3.org/TR/sparql11-query/) |
| SPARQL 속성 경로 | [표준] | [property paths](https://www.w3.org/TR/sparql11-query/#propertypaths) |
| Gremlin 순회 언어 | [사실상 표준] | [Apache TinkerPop](https://tinkerpop.apache.org/docs/current/reference/) |
| GQL 표준화 경과 | [사실상 표준] | [GQL Standards](https://www.gqlstandards.org/) |

상태 표시는 **[표준]** 공식 명세, **[사실상 표준]** 명세는 없지만 업계가 널리 쓰는 것, **[실험]** 아직 자리를 잡는 중이라는 뜻입니다.

## 예제 실행

<!-- 실행 가이드 시작 — 사람이 쓴 부분. gen-docs.py 가 건드리지 않는다. -->

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

<!-- 실행 가이드 끝 -->

---

**다음 장에서 뒤집히는 것:** 2부가 끝났습니다. 여기까지는 그래프를 「다루는」 법이었어요. 3부는 그래프를 「짓는」 법입니다. 그리고 첫 장은 제가 온톨로지를 3주 만에 갈아엎은 이야기로 시작합니다.

---

← [10장 누가 중요한 노드인가](../../ch10/code/README.md) · [전체 목차](../../../README.md) · [12장 온톨로지를 3주 만에 갈아엎은 이야기](../../ch12/code/README.md) →

이 장에서 틀린 곳을 찾으셨다면 [사실 오류로](https://github.com/leaf-kit/book-graph-engineering/issues/new?template=01-fact-error.yml), 상태 라벨이 어긋났다면 [라벨 이의로](https://github.com/leaf-kit/book-graph-engineering/issues/new?template=03-status-label.yml) 적어 주세요.
