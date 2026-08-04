# 4장 — 시맨틱 웹은 왜 실패한 것처럼 보였나

`1부 — 뿌리: 그래프는 어디에 있었나` | **한국어** | [English](../../../content_en/ch04/code/README.md) | [책 전체 목차](../../../README.md) | [출처 링크 모음](../../../SOURCES.md)

> 온톨로지를 6개월 만들었는데 아무도 안 썼습니다.

이게 시맨틱 웹이 20년 동안 겪은 일을 축소해 놓은 판입니다. 야심은 옳았습니다. 웹의 모든 것에 뜻을 달아서 기계가 읽게 하자. 그런데 뜻을 다는 일을 사람이 해야 했고, 사람은 그 값을 안 냈습니다. 재밌는 건 지금입니다. 그 값을 모델이 대신 내기 시작했거든요. 그래서 20년 동안 조롱받던 기술을 다시 꺼내 쓰고 있습니다.

## 이 장의 절

| 절 | 제목 |
|---|---|
| 4.1 | 층으로 쌓은 야심 |
| 4.2 | 다섯 가지가 발목을 잡았다 |
| 4.3 | 살아남은 것들 |
| 4.4 | 지금 다시 꺼내 쓰는 이유 |

## 한 장 요약

- 시맨틱 웹의 야심은 웹 전체에 뜻을 다는 것이었고, 그 일을 사람이 해야 해서 멈췄습니다.
- 발목을 잡은 건 다섯입니다. 태깅 값, 합의 비용, 열린 세계 가정, 무거운 도구, 남의 서버에 기대는 연합 질의.
- 그래도 남은 게 많습니다. RDF 자료 모델, SPARQL 경로 질의, SHACL 검증, JSON-LD와 schema.org. 남은 것들의 공통점은 지금 당장 이득이 있다는 겁니다.
- 지금 다시 꺼내 쓰는 이유는 첫 번째 발목이 풀렸기 때문입니다. 모델이 태깅을 대신하면서 트리플 하나당 원가가 두 자릿수 배로 떨어졌어요.

## 키워드와 1차 출처

| 키워드 | 상태 | 출처 |
|---|---|---|
| RDF 1.2 개념과 추상 구문 | [표준] | [RDF 1.2 Concepts](https://www.w3.org/TR/rdf12-concepts/) |
| Turtle 문법 | [표준] | [RDF 1.1 Turtle](https://www.w3.org/TR/turtle/) |
| SPARQL 1.1 질의 | [표준] | [SPARQL 1.1 Query Language](https://www.w3.org/TR/sparql11-query/) |
| OWL 2 개요 | [표준] | [OWL 2 Web Ontology Language](https://www.w3.org/TR/owl2-overview/) |
| SHACL 형태 제약 | [표준] | [Shapes Constraint Language](https://www.w3.org/TR/shacl/) |
| JSON-LD 1.1 | [표준] | [JSON for Linking Data](https://www.w3.org/TR/json-ld11/) |
| 공용 어휘 | [사실상 표준] | [schema.org](https://schema.org/docs/documents.html) |
| 연결 데이터 원칙 | [사실상 표준] | [Linked Data](https://www.w3.org/DesignIssues/LinkedData.html) |

상태 표시는 **[표준]** 공식 명세, **[사실상 표준]** 명세는 없지만 업계가 널리 쓰는 것, **[실험]** 아직 자리를 잡는 중이라는 뜻입니다.

## 예제 실행

<!-- 실행 가이드 시작 — 사람이 쓴 부분. gen-docs.py 가 건드리지 않는다. -->

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

<!-- 실행 가이드 끝 -->

---

**다음 장에서 뒤집히는 것:** 이 장은 「뜻을 정의하자」는 쪽 이야기였습니다. 다음 장은 정반대 진영을 봅니다. 뜻은 나중에 정하고 일단 노드에 아무 속성이나 붙이자는 쪽이요. 그쪽이 실무에서 먼저 이겼습니다.

---

이전 [3장 다리 일곱 개를 건널 수 없었던 이유, 그리고 표가 이긴 이유](../../ch03/code/README.md) | [전체 목차](../../../README.md) | 다음 [5장 문자열이 아니라 사물](../../ch05/code/README.md)

이 장에서 틀린 곳을 찾으셨다면 [사실 오류로](https://github.com/leaf-kit/book-graph-engineering/issues/new?template=01-fact-error.yml), 상태 라벨이 어긋났다면 [라벨 이의로](https://github.com/leaf-kit/book-graph-engineering/issues/new?template=03-status-label.yml) 적어 주세요.
