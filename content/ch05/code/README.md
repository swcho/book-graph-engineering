# 5장 — 문자열이 아니라 사물

`1부 — 뿌리: 그래프는 어디에 있었나` | [책 전체 목차](../../../README.md) | [출처 링크 모음](../../../SOURCES.md)

> RDF로 시작했다가 4개월 만에 프로퍼티 그래프로 갈아탄 적이 있습니다.

이 장은 두 가지를 봅니다. 프로퍼티 그래프가 어떻게 실무를 가져갔는지, 그리고 2012년에 「문자열이 아니라 사물」이라는 선언이 실제로 무슨 뜻이었는지요. 두 번째가 이 책의 나머지에 계속 돌아옵니다.

## 이 장의 절

| 절 | 제목 |
|---|---|
| 5.1 | 2012년 선언이 실제로 뜻한 것 |
| 5.2 | 두 가지 모델, 다른 세는 단위 |
| 5.3 | 엣지에 속성을 달아야 할 때 |
| 5.4 | 같은 질문, 두 언어 |
| 5.5 | 그래서 무엇을 고를 것인가 |

## 한 장 요약

- 「문자열이 아니라 사물」의 핵심은 저장량이 아니라 구분입니다. 같은 이름 뒤에 다른 노드가 있고, 노드마다 다른 술어를 갖습니다. 술어 목록이 곧 그 사물의 정체예요.
- 프로퍼티 그래프와 RDF는 세는 단위가 다릅니다. 속성을 주머니에 담느냐 트리플로 펴느냐의 차이고, 그 차이가 드러나는 곳은 「속성 하나를 손가락으로 가리킬 수 있는가」입니다.
- 엣지에 속성을 달 때 LPG는 한 줄, RDF는 세 방법 중 하나를 골라야 합니다. 관계의 30% 이상에 속성이 붙으면 LPG 쪽이 편합니다.
- 모델은 표현력이 아니라 상황으로 고릅니다. 그리고 고르기 전에 질의 다섯 개를 두 언어로 써 보는 반나절이 4개월을 아낍니다.

## 키워드와 1차 출처

| 키워드 | 상태 | 출처 |
|---|---|---|
| 지식 그래프 선언 | [사실상 표준] | [things, not strings](https://blog.google/products/search/introducing-knowledge-graph-things-not/) |
| 그래프 질의 언어 GQL | [표준] | [ISO/IEC 39075:2024](https://www.iso.org/standard/76120.html) |
| Cypher 질의 언어 | [사실상 표준] | [Cypher Manual](https://neo4j.com/docs/cypher-manual/current/) |
| RDF-star 트리플 항 | [표준] | [RDF 1.2 triple terms](https://www.w3.org/TR/rdf12-concepts/) |
| 이름 붙인 그래프 | [표준] | [RDF Datasets](https://www.w3.org/TR/rdf11-datasets/) |
| 임베디드 그래프 엔진 | [사실상 표준] | [Kuzu](https://github.com/kuzudb/kuzu) |

상태 표시는 **[표준]** 공식 명세, **[사실상 표준]** 명세는 없지만 업계가 널리 쓰는 것, **[실험]** 아직 자리를 잡는 중이라는 뜻입니다.

## 예제 실행

<!-- 실행 가이드 시작 — 사람이 쓴 부분. gen-docs.py 가 건드리지 않는다. -->

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

<!-- 실행 가이드 끝 -->

---

**다음 장에서 뒤집히는 것:** 여기까지는 관계를 「적어 두는」 이야기였습니다. 다음 장은 그 관계를 숫자 벡터에 녹여 넣은 쪽을 봅니다. 녹이면 새 관계를 예측할 수 있게 되는데, 대신 왜 그런지 설명할 수 없게 됩니다.

---

이전 [4장 시맨틱 웹은 왜 실패한 것처럼 보였나](../../ch04/code/README.md) | [전체 목차](../../../README.md) | 다음 [6장 벡터에 녹인 관계를 되찾는 데 10년이 걸렸다](../../ch06/code/README.md)

이 장에서 틀린 곳을 찾으셨다면 [사실 오류로](https://github.com/leaf-kit/book-graph-engineering/issues/new?template=01-fact-error.yml), 상태 라벨이 어긋났다면 [라벨 이의로](https://github.com/leaf-kit/book-graph-engineering/issues/new?template=03-status-label.yml) 적어 주세요.
