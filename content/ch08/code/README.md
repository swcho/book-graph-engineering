# 8장 — 그래프는 메모리에서 이렇게 생겼다

`2부 — 그래프의 기초 문법` | [책 전체 목차](../../../README.md) | [출처 링크 모음](../../../SOURCES.md)

> 같은 그래프를 두 라이브러리에 올렸습니다. 한쪽은 4.1GB를 먹고, 다른 쪽은 380MB를 먹었어요.

이 장은 그 그릇 이야기입니다. 왜 어떤 그래프는 100만 노드에서 멀쩡하고 어떤 건 10만에서 죽는지, 그 답이 여기 있습니다. 그리고 답은 대개 「노드 수」가 아니라 다른 데 있어요.

## 이 장의 절

| 절 | 제목 |
|---|---|
| 8.1 | 세 가지 그릇 |
| 8.2 | 왜 연속이면 빠른가 |
| 8.3 | 100만에서 멀쩡하고 10만에서 죽는 이유 |
| 8.4 | 인덱스 없는 인접성 |

## 한 장 요약

- 그래프를 담는 그릇은 셋입니다. 인접 행렬은 노드 수의 제곱이라 수천 개 이하에서만 쓸 만하고, 인접 리스트는 편하고, CSR은 정수 배열 두 개로 제일 조밀합니다. 같은 그래프가 4.1GB와 380MB로 갈릴 수 있습니다.
- CSR이 빠른 이유는 알고리즘이 아니라 메모리를 읽는 방식입니다. 이웃이 연속으로 놓이면 캐시 한 줄에 여러 개가 함께 옵니다.
- 노드 수는 성능을 별로 설명하지 못합니다. 차수의 제곱합이 설명합니다. 평균 차수가 같아도 2홉 비용이 200배 차이 날 수 있어요.
- 인덱스 없는 인접성은 두 번째 홉부터 이득입니다. 시작 노드를 찾는 데는 여전히 색인이 필요합니다.

## 키워드와 1차 출처

| 키워드 | 상태 | 출처 |
|---|---|---|
| 압축 희소 행 형식 | [사실상 표준] | [CSR, Compressed Sparse Row](https://docs.scipy.org/doc/scipy/reference/generated/scipy.sparse.csr_matrix.html) |
| 인덱스 없는 인접성 | [사실상 표준] | [index-free adjacency](https://neo4j.com/docs/getting-started/appendix/graphdb-concepts/) |
| 인접 행렬과 인접 리스트 | [사실상 표준] | [adjacency matrix / list](https://networkx.org/documentation/stable/reference/convert.html) |
| 슈퍼 노드 | [사실상 표준] | [super node](https://neo4j.com/docs/cypher-manual/current/planning-and-tuning/) |
| 그래프 재배치 | [실험] | [graph reordering](https://arxiv.org/abs/1602.08820) |
| 페이지 캐시와 지역성 | [사실상 표준] | [locality of reference](https://www.kernel.org/doc/html/latest/admin-guide/mm/index.html) |

상태 표시는 **[표준]** 공식 명세, **[사실상 표준]** 명세는 없지만 업계가 널리 쓰는 것, **[실험]** 아직 자리를 잡는 중이라는 뜻입니다.

## 예제 실행

<!-- 실행 가이드 시작 — 사람이 쓴 부분. gen-docs.py 가 건드리지 않는다. -->

확인 시점 2026년 8월. Python 3.9 이상. **의존성 없음.**

```bash
cd content/ch08/code
python3 graphgen.py        # 샘플 그래프 통계
python3 ex1_three_forms.py # 인접 행렬, 인접 리스트, CSR 메모리 비교
python3 ex2_csr_walk.py    # CSR 로 BFS
python3 ex3_degree_skew.py # 평균은 같은데 비용이 200배 다른 이유
python3 ex4_relabel.py     # 번호를 다시 매기면 지역성이 좋아진다
python3 ex5_index_free.py  # 인덱스 없는 인접성
```

측정값은 기계마다 다릅니다. **배수**만 보세요.

<!-- 실행 가이드 끝 -->

---

**다음 장에서 뒤집히는 것:** 이제 그래프가 메모리에 어떻게 놓이는지 알았으니, 그 위를 걸어 봅니다. 다음 장은 순회와 최단 경로인데, 「몇 다리 건너인지 세다가 서버가 죽는」 이야기부터 시작합니다.

---

이전 [7장 노드 하나 잘못 그려서 3주를 날렸다](../../ch07/code/README.md) | [전체 목차](../../../README.md) | 다음 [9장 몇 다리 건너인지 세다가 서버가 죽었다](../../ch09/code/README.md)

이 장에서 틀린 곳을 찾으셨다면 [사실 오류로](https://github.com/leaf-kit/book-graph-engineering/issues/new?template=01-fact-error.yml), 상태 라벨이 어긋났다면 [라벨 이의로](https://github.com/leaf-kit/book-graph-engineering/issues/new?template=03-status-label.yml) 적어 주세요.
