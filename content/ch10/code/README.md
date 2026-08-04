# 10장 — 누가 중요한 노드인가

`2부 · 그래프의 기초 문법` · [책 전체 목차](../../../README.md) · [출처 링크 모음](../../../SOURCES.md)

> "우리 조직에서 제일 중요한 사람이 누군지 그래프로 뽑아 주세요."

이 장은 그 「다른 지표들」 이야기입니다. 중심성 네 가지가 각각 어떤 질문에 답하는지, 그리고 뭉치를 찾는 일이 왜 매번 다른 답을 내놓는지요.

## 이 장의 절

| 절 | 제목 |
|---|---|
| 10.1 | 네 가지 지표, 네 가지 질문 |
| 10.2 | 페이지랭크와 새는 점수 |
| 10.3 | 매개 중심성은 왜 비싼가 |
| 10.4 | 뭉치 찾기, 그리고 매번 다른 답 |

## 한 장 요약

- 중심성 지표는 「중요하다」의 서로 다른 정의입니다. 차수는 아는 사람 수, 근접은 퍼지는 속도, 매개는 없으면 갈라지는지, 고유벡터는 힘 있는 이웃을 가졌는지를 묻습니다.
- 제일 값어치 있는 정보는 1등이 아니라 *지표 사이의 순위 차이*입니다. 차수는 낮은데 매개가 높은 노드가 아무도 모르는 급소예요.
- 페이지랭크는 싱크 노드가 점수를 삼킵니다. 순위는 안 바뀌어서 발견이 늦지만, 절대 임계를 쓰고 있다면 조용히 의미를 잃습니다.
- 매개 중심성은 비쌉니다. 구조가 있는 그래프라면 표본 5%로도 상위권을 맞힙니다.
- 커뮤니티 탐지에 맞는 답은 없습니다. 라벨 전파는 시드에 따라 흔들리고, 모듈러리티는 해상도 한계로 작은 뭉치를 붙여 버립니다. 개수는 알고리즘이 아니라 쓰임새로 정하세요.

## 키워드와 1차 출처

| 키워드 | 상태 | 출처 |
|---|---|---|
| 중심성 지표들 | [사실상 표준] | [centrality measures](https://networkx.org/documentation/stable/reference/algorithms/centrality.html) |
| 매개 중심성 고속 계산 | [사실상 표준] | [Brandes' algorithm](https://www.tandfonline.com/doi/abs/10.1080/0022250X.2001.9990249) |
| 페이지랭크 | [사실상 표준] | [PageRank](http://ilpubs.stanford.edu:8090/422/) |
| 모듈러리티 | [사실상 표준] | [modularity](https://arxiv.org/abs/cond-mat/0308217) |
| 루뱅 커뮤니티 탐지 | [사실상 표준] | [Louvain method](https://arxiv.org/abs/0803.0476) |
| 라이덴 알고리즘 | [사실상 표준] | [Leiden algorithm](https://www.nature.com/articles/s41598-019-41695-z) |
| 해상도 한계 | [사실상 표준] | [resolution limit](https://www.pnas.org/doi/10.1073/pnas.0605965104) |
| 라벨 전파 | [사실상 표준] | [label propagation](https://arxiv.org/abs/0709.2938) |

상태 표시는 **[표준]** 공식 명세, **[사실상 표준]** 명세는 없지만 업계가 널리 쓰는 것, **[실험]** 아직 자리를 잡는 중이라는 뜻입니다.

## 예제 실행

<!-- 실행 가이드 시작 — 사람이 쓴 부분. gen-docs.py 가 건드리지 않는다. -->

확인 시점 2026년 8월. Python 3.9 이상. **의존성 없음.**

```bash
cd content/ch10/code
python3 ex1_centralities.py       # 네 가지 중심성, 1등이 서로 다르다
python3 ex2_pagerank.py           # 싱크 노드가 점수를 삼킨다
python3 ex3_betweenness_cost.py   # 매개 중심성의 비용과 근사
python3 ex4_communities.py        # 라벨 전파 vs 모듈러리티
python3 ex5_resolution.py         # 해상도 한계
```

`ex3` 은 노드 1,600개까지 전수 계산을 하므로 10초쯤 걸립니다.

<!-- 실행 가이드 끝 -->

---

**다음 장에서 뒤집히는 것:** 2부의 마지막입니다. 지금까지 그래프를 코드로 다뤘다면, 다음 장은 질의 언어로 다룹니다. 같은 질문을 세 가지 언어로 쓰고, 2024년에 국제 표준이 된 언어가 그 셋과 어떻게 다른지 봅니다.

---

← [9장 몇 다리 건너인지 세다가 서버가 죽었다](../../ch09/code/README.md) · [전체 목차](../../../README.md) · [11장 같은 질문, 세 가지 언어](../../ch11/code/README.md) →

이 장에서 틀린 곳을 찾으셨다면 [사실 오류로](https://github.com/leaf-kit/book-graph-engineering/issues/new?template=01-fact-error.yml), 상태 라벨이 어긋났다면 [라벨 이의로](https://github.com/leaf-kit/book-graph-engineering/issues/new?template=03-status-label.yml) 적어 주세요.
