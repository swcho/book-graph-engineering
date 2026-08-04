# 7장 - 노드 하나 잘못 그려서 3주를 날렸다

`2부 - 그래프의 기초 문법` | **한국어** | [English](../../../content_en/ch07/code/README.md) | [책 전체 목차](../../../README.md) | [출처 링크 모음](../../../SOURCES.md)

> 계약을 엣지로 그렸습니다. `(회사)-[:계약]->(회사)`. 화이트보드에서는 예뻤어요.

이 장은 그 판단 기준을 다룹니다. 노드냐 엣지냐, 방향을 어느 쪽으로, 가중치는 무슨 뜻으로. 화이트보드에서는 다 비슷해 보이는데, 6개월 뒤에 갈립니다.

## 이 장의 절

| 절 | 제목 |
|---|---|
| 7.1 | 노드냐 엣지냐 |
| 7.2 | 방향을 어느 쪽으로 |
| 7.3 | 가중치가 거리인가 강도인가 |
| 7.4 | 두 종류만 있는 그래프, 그리고 겹치는 엣지 |

## 한 장 요약

- 관계를 엣지로 둘지 노드로 승격할지는 세 번 물어보면 정해집니다. 속성이 붙나, 제3의 대상과 이어지나, 그 속성으로 검색하나. 마지막 질문이 결정적이에요. 속성은 읽는 것이고 노드는 찾는 것입니다.
- 승격은 늦게 하되 미루지 마세요. 데이터가 쌓일수록 옮기는 값이 비례해서 오릅니다. 그리고 옮길 때 제일 오래 걸리는 건 데이터 이동이 아니라 표기 통일입니다.
- 방향은 자주 묻는 쪽을 나가는 방향으로 둡니다. 가중치는 이름에 뜻을 박아 넣으세요. `weight` 대신 `cost_minutes`나 `affinity_score`로요.
- 이분 그래프를 투영하면 정보가 사라지고 엣지가 제곱으로 늡니다. 다중 엣지와 자기 루프는 세는 방식이 흔들리니, 무엇을 세는지 먼저 정하세요.

## 키워드와 1차 출처

| 키워드 | 상태 | 출처 |
|---|---|---|
| 프로퍼티 그래프 자료 모델 | [표준] | [ISO/IEC 39075:2024 GQL](https://www.iso.org/standard/76120.html) |
| RDF 자료 모델 | [표준] | [RDF 1.2 Concepts](https://www.w3.org/TR/rdf12-concepts/) |
| 노드 라벨과 관계 타입 | [사실상 표준] | [Cypher: patterns](https://neo4j.com/docs/cypher-manual/current/patterns/) |
| 관계의 구체화 | [표준] | [reification](https://www.w3.org/TR/rdf12-schema/) |
| 이분 그래프 | [사실상 표준] | [bipartite graph](https://networkx.org/documentation/stable/reference/algorithms/bipartite.html) |
| 다중 그래프와 자기 루프 | [사실상 표준] | [multigraph, self-loop](https://networkx.org/documentation/stable/reference/classes/multigraph.html) |

상태 표시는 **[표준]** 공식 명세, **[사실상 표준]** 명세는 없지만 업계가 널리 쓰는 것, **[실험]** 아직 자리를 잡는 중이라는 뜻입니다.

## 예제 실행

<!-- 실행 가이드 시작 - 사람이 쓴 부분. gen-docs.py 가 건드리지 않는다. -->

확인 시점 2026년 8월. Python 3.9 이상. **의존성 없음.**

```bash
cd content/ch07/code
python3 ex1_node_or_edge.py   # 엣지로 둘까, 노드로 승격할까
python3 ex2_direction.py      # 방향을 어느 쪽으로
python3 ex3_weights.py        # 가중치가 거리인가 강도인가
python3 ex4_bipartite.py      # 이분 그래프와 투영 폭발
python3 ex5_multigraph.py     # 다중 엣지와 자기 루프
```

<!-- 실행 가이드 끝 -->

---

**다음 장에서 뒤집히는 것:** 이 장은 그래프를 「그리는」 이야기였습니다. 다음 장은 그 그림이 메모리와 디스크에서 실제로 어떻게 생겼는지 봅니다. 그리고 왜 어떤 그래프는 100만 노드에서 멀쩡하고 어떤 건 10만에서 죽는지 알게 됩니다.

---

이전 [6장 벡터에 녹인 관계를 되찾는 데 10년이 걸렸다](../../ch06/code/README.md) | [전체 목차](../../../README.md) | 다음 [8장 그래프는 메모리에서 이렇게 생겼다](../../ch08/code/README.md)

이 장에서 틀린 곳을 찾으셨다면 [사실 오류로](https://github.com/leaf-kit/book-graph-engineering/issues/new?template=01-fact-error.yml), 상태 라벨이 어긋났다면 [라벨 이의로](https://github.com/leaf-kit/book-graph-engineering/issues/new?template=03-status-label.yml) 적어 주세요.
