# 9장 — 몇 다리 건너인지 세다가 서버가 죽었다

`2부 · 그래프의 기초 문법` · [책 전체 목차](../../../README.md) · [출처 링크 모음](../../../SOURCES.md)

> "이 사람과 연결된 사람들을 보여 주세요."

지금 생각하면 당연합니다. 평균 차수가 12면 한 홉마다 11배씩 늘어나니까요. 5홉이면 11의 4승, 약 1만 4천 배입니다. 이 장은 그래프 위를 걷는 이야기입니다. 어떻게 걷고, 어디서 멈추고, 언제 걷지 말아야 하는지요. 마지막이 제일 중요합니다.

## 이 장의 절

| 절 | 제목 |
|---|---|
| 9.1 | 한 홉마다 열한 배 |
| 9.2 | 양쪽에서 걸어오면 제곱근이 된다 |
| 9.3 | 가중치가 붙으면 |
| 9.4 | 경로 하나와 경로 전부 |
| 9.5 | 순서가 있는 그래프 — 위상 정렬 |

## 한 장 요약

- 평균 차수 12짜리 그래프에서는 한 홉마다 11배씩 늡니다. 5홉이면 전체의 68%, 6홉이면 전부예요. 상한 없는 순회는 사실상 전체 스캔입니다.
- 두 점 사이를 찾을 때는 양방향 탐색을 쓰세요. 반지름을 절반으로 줄이면 방문 수가 제곱근이 됩니다. 실측에서 75~88배 줄었습니다.
- 다익스트라는 음수 가중치에서 조용히 틀립니다. 예외도 안 나요. 확률에 로그를 취하는 곳이 있으면 특히 조심하세요.
- 「최단 경로 하나」와 「모든 경로」는 다른 문제입니다. 앞은 다항, 뒤는 지수예요. 「전부 보여 줘」라는 요구는 되물어야 합니다.
- 위상 정렬로 층을 만들면 병렬 실행이 되는데, 층 단위는 임계 경로보다 느립니다. 같은 층의 제일 느린 작업을 기다리기 때문이에요.

## 키워드와 1차 출처

| 키워드 | 상태 | 출처 |
|---|---|---|
| 너비 우선 탐색 | [사실상 표준] | [BFS](https://networkx.org/documentation/stable/reference/algorithms/traversal.html) |
| 양방향 탐색 | [사실상 표준] | [bidirectional search](https://networkx.org/documentation/stable/reference/algorithms/generated/networkx.algorithms.shortest_paths.unweighted.bidirectional_shortest_path.html) |
| 다익스트라 최단 경로 | [표준] | [Dijkstra's algorithm](https://link.springer.com/article/10.1007/BF01386390) |
| 벨만-포드 | [사실상 표준] | [Bellman-Ford](https://networkx.org/documentation/stable/reference/algorithms/generated/networkx.algorithms.shortest_paths.weighted.bellman_ford_path.html) |
| 휴리스틱 탐색 | [사실상 표준] | [A*](https://ieeexplore.ieee.org/document/4082128) |
| 위상 정렬 | [표준] | [topological sort](https://dl.acm.org/doi/10.1145/368996.369025) |
| 가변 길이 경로 질의 | [사실상 표준] | [Cypher variable-length patterns](https://neo4j.com/docs/cypher-manual/current/patterns/variable-length-patterns/) |

상태 표시는 **[표준]** 공식 명세, **[사실상 표준]** 명세는 없지만 업계가 널리 쓰는 것, **[실험]** 아직 자리를 잡는 중이라는 뜻입니다.

## 예제 실행

<!-- 실행 가이드 시작 — 사람이 쓴 부분. gen-docs.py 가 건드리지 않는다. -->

확인 시점 2026년 8월. Python 3.9 이상. **의존성 없음.**

```bash
cd content/ch09/code
python3 ex1_bfs_explosion.py        # 홉이 늘 때 방문 노드가 몇 배가 되나
python3 ex2_bidirectional.py        # 양방향 탐색이 75배 줄이는 이유
python3 ex3_dijkstra_negative.py    # 음수 가중치가 조용히 답을 틀리게 만든다
python3 ex4_path_explosion.py       # 최단 경로 하나와 모든 경로는 다른 문제
python3 ex5_toposort.py             # 위상 정렬, 슈퍼스텝, 임계 경로
```

`ex1` 과 `ex2` 는 노드 20만 개를 만듭니다. 메모리 1GB 정도 씁니다.

<!-- 실행 가이드 끝 -->

---

**다음 장에서 뒤집히는 것:** 지금까지는 「어디까지 갈 수 있나」를 봤습니다. 다음 장은 「누가 중요한가」입니다. 그런데 중요도 지표를 잘못 고르면, 회사에서 제일 중요한 사람이 청소 담당자로 나오는 일이 생깁니다.

---

← [8장 그래프는 메모리에서 이렇게 생겼다](../../ch08/code/README.md) · [전체 목차](../../../README.md) · [10장 누가 중요한 노드인가](../../ch10/code/README.md) →

이 장에서 틀린 곳을 찾으셨다면 [사실 오류로](https://github.com/leaf-kit/book-graph-engineering/issues/new?template=01-fact-error.yml), 상태 라벨이 어긋났다면 [라벨 이의로](https://github.com/leaf-kit/book-graph-engineering/issues/new?template=03-status-label.yml) 적어 주세요.
