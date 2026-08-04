# 18장 — 체인은 어디서 부러지는가

`4부 — 에이전트 그래프 엔지니어링 (트랙 2)` | **한국어** | [English](../../../content_en/ch18/code/README.md) | [책 전체 목차](../../../README.md) | [출처 링크 모음](../../../SOURCES.md)

> 51초를 기다린 사용자에게 "다시 시도해 주세요"를 보냈습니다.

이 장은 4부의 시작이고, 여기서부터는 「모델이 무엇을 하는가」입니다. 첫 질문은 이거예요. *한 줄로 이어 붙인 파이프라인은 어디서 부러지는가.*

## 이 장의 절

| 절 | 제목 |
|---|---|
| 18.1 | 실패했을 때 무엇을 버리는가 |
| 18.2 | if 문이 다섯 개를 넘으면 |
| 18.3 | 병렬로 돌렸는데 하나만 실패했다 |
| 18.4 | 같은 작업, 두 구조 |
| 18.5 | 언제 갈아탈까 |

## 한 장 요약

- 체인과 상태 그래프의 차이는 「실패했을 때 무엇을 버리는가」입니다. 체인은 앞 단계 결과를 버리고, 그래프는 실패한 단계만 다시 합니다. 뒤쪽이 자주 실패할수록, 단계가 많을수록 격차가 벌어집니다.
- 조건이 늘면 `if` 문의 경우의 수는 지수로 늘고 그래프의 엣지는 선형으로 늡니다. 다섯 개 근처에서 사람이 다 못 봅니다.
- 병렬 작업 중 하나가 실패하면 세 가지 선택지가 있는데, 체인에는 그걸 표현할 자리가 없습니다. 합류 노드가 그 결정을 맡습니다.
- 그렇다고 처음부터 그래프로 갈 일은 아닙니다. 단계가 두세 개고 실패가 드물면 체인이 쌉니다. 대신 바꿀 준비만 해 두세요. 단계를 함수로 분리하고 데이터를 딕셔너리로 통일하면 나중에 반나절입니다.
- 그리고 구조를 바꿔도 실패율은 안 줄어듭니다. 실패의 *값*이 줄 뿐이에요. 이 구분을 팀에 먼저 설명하세요.

## 키워드와 1차 출처

| 키워드 | 상태 | 출처 |
|---|---|---|
| 에이전트 설계 패턴 | [사실상 표준] | [agent workflow patterns](https://www.anthropic.com/engineering/building-effective-agents) |
| 상태 그래프 | [사실상 표준] | [StateGraph](https://docs.langchain.com/oss/python/langgraph/graph-api) |
| 체크포인트 | [사실상 표준] | [checkpointer](https://docs.langchain.com/oss/python/langgraph/persistence) |
| 프롬프트 연쇄 | [사실상 표준] | [prompt chaining](https://www.anthropic.com/engineering/building-effective-agents) |
| 순환 복잡도 | [표준] | [cyclomatic complexity](https://ieeexplore.ieee.org/document/1702388) |
| 내구성 있는 실행 | [사실상 표준] | [durable execution](https://docs.temporal.io/temporal) |
| 생각과 행동의 교차 | [사실상 표준] | [ReAct](https://arxiv.org/abs/2210.03629) |

상태 표시는 **[표준]** 공식 명세, **[사실상 표준]** 명세는 없지만 업계가 널리 쓰는 것, **[실험]** 아직 자리를 잡는 중이라는 뜻입니다.

## 예제 실행

<!-- 실행 가이드 시작 — 사람이 쓴 부분. gen-docs.py 가 건드리지 않는다. -->

확인 시점 2026년 8월. Python 3.9 이상.

```bash
cd content/ch18/code
python3 ex1_chain_vs_graph.py       # 의존성 없음
python3 ex2_if_explosion.py         # 의존성 없음
python3 ex3_partial_failure.py      # 의존성 없음
pip install "langgraph>=1.0,<2.0"
python3 ex4_same_task_two_ways.py   # 같은 작업, 두 구조
python3 ex5_when_to_switch.py       # 의존성 없음
```

<!-- 실행 가이드 끝 -->

---

**다음 장에서 뒤집히는 것:** 이 장에서 상태 그래프를 계속 말했는데, 정작 「상태」가 무엇인지는 안 정했습니다. 다음 장이 그 이야기예요. 두 노드가 같은 상태를 동시에 고치면 무슨 일이 생기는지부터 봅니다.

---

이전 [17장 벡터만으로 답이 안 나오는 질문들](../../ch17/code/README.md) | [전체 목차](../../../README.md) | 다음 [19장 상태 그래프와 리듀서, 그리고 슈퍼스텝](../../ch19/code/README.md)

이 장에서 틀린 곳을 찾으셨다면 [사실 오류로](https://github.com/leaf-kit/book-graph-engineering/issues/new?template=01-fact-error.yml), 상태 라벨이 어긋났다면 [라벨 이의로](https://github.com/leaf-kit/book-graph-engineering/issues/new?template=03-status-label.yml) 적어 주세요.
