# 19장 — 상태 그래프와 리듀서, 그리고 슈퍼스텝

`4부 — 에이전트 그래프 엔지니어링 (트랙 2)` | **한국어** | [English](../../../content_en/ch19/code/README.md) | [책 전체 목차](../../../README.md) | [출처 링크 모음](../../../SOURCES.md)

> 노드 셋을 병렬로 돌렸는데 로그가 하나만 남았습니다.

「덮였다」는 말이 정확하지도 않습니다. 누가 마지막이었는지도 매번 달랐거든요. 이 장은 그 이야기입니다. 상태가 무엇이고, 여럿이 동시에 고치면 어떻게 되고, 실행기가 어느 지점에서 경계를 긋는지요.

## 이 장의 절

| 절 | 제목 |
|---|---|
| 19.1 | 상태는 「전부」가 아니라 「바뀐 것」이다 |
| 19.2 | 슈퍼스텝 — 경계가 그어지는 자리 |
| 19.3 | 합치는 규칙이 도메인 지식이다 |
| 19.4 | 상태에 무엇을 넣을 것인가 |
| 19.5 | 체크포인트는 복구용만이 아니다 |

## 한 장 요약

- 노드는 상태 전체가 아니라 바꾼 부분만 돌려줍니다. 여럿이 같은 필드를 건드리면 리듀서가 합쳐요. 리듀서가 없으면 갱신이 사라지거나(운이 나쁘면) 예외가 납니다(운이 좋으면).
- 같은 슈퍼스텝의 노드들은 서로가 쓴 걸 못 봅니다. 같은 사본을 받으니까요. 순서가 필요하면 사이에 노드를 넣어 경계를 만드세요.
- 리듀서는 교환법칙을 지켜야 합니다. `f(a,b) == f(b,a)`가 아니면 실행 순서에 따라 답이 달라지고, 그 순서는 여러분이 못 정해요. 값 안에 판단 근거(시각, 출처, 신뢰도)를 넣으세요.
- 상태는 슈퍼스텝마다 통째로 저장됩니다. 「다음 노드가 읽는가」로 걸러 내면 크기가 수십 배 줄어요. 8KB가 제 기준입니다.
- 체크포인트는 복구보다 디버깅에 훨씬 자주 씁니다. 제 로그에서 여덟 배였어요. 그리고 켜는 코드와 지우는 코드를 같은 커밋에 쓰세요.

## 키워드와 1차 출처

| 키워드 | 상태 | 출처 |
|---|---|---|
| 상태 그래프 | [사실상 표준] | [StateGraph](https://docs.langchain.com/oss/python/langgraph/graph-api) |
| 리듀서 | [사실상 표준] | [reducer](https://docs.langchain.com/oss/python/langgraph/graph-api) |
| 슈퍼스텝 | [사실상 표준] | [superstep](https://docs.langchain.com/oss/python/langgraph/graph-api) |
| 프리겔 계산 모형 | [사실상 표준] | [Pregel](https://dl.acm.org/doi/10.1145/1807167.1807184) |
| 벌크 동기 병렬 | [사실상 표준] | [Bulk Synchronous Parallel](https://dl.acm.org/doi/10.1145/79173.79181) |
| 체크포인트와 지속성 | [사실상 표준] | [persistence](https://docs.langchain.com/oss/python/langgraph/persistence) |
| 갱신 유실 | [표준] | [lost update](https://www.iso.org/standard/76583.html) |

상태 표시는 **[표준]** 공식 명세, **[사실상 표준]** 명세는 없지만 업계가 널리 쓰는 것, **[실험]** 아직 자리를 잡는 중이라는 뜻입니다.

## 예제 실행

<!-- 실행 가이드 시작 — 사람이 쓴 부분. gen-docs.py 가 건드리지 않는다. -->

확인 시점 2026년 8월. Python 3.9 이상.

```bash
cd content/ch19/code
pip install "langgraph>=1.0,<2.0"
python3 ex1_lost_update.py      # 리듀서가 없으면 갱신이 사라진다
python3 ex2_superstep.py        # 슈퍼스텝 경계를 눈으로
python3 ex3_custom_reducer.py   # 필드마다 다른 합치기 규칙
python3 ex4_state_size.py       # 의존성 없음
python3 ex5_debug_state.py      # 체크포인트로 시간 여행
```

`ex1` 은 일부러 **예외가 나는** 경우를 포함합니다. 그게 이 예제의 결과입니다.

<!-- 실행 가이드 끝 -->

---

**다음 장에서 뒤집히는 것:** 여기까지 상태와 경계를 봤습니다. 다음 장은 「언제 멈출 것인가」예요. 종료 조건 하나가 41만 원을 막는다는 얘기를 [1장](../../ch01/code/README.md)에서 했는데, 그 조건을 제대로 설계하는 법을 봅니다.

---

이전 [18장 체인은 어디서 부러지는가](../../ch18/code/README.md) | [전체 목차](../../../README.md) | 다음 [20장 끝나지 않는 루프를 끝내는 법](../../ch20/code/README.md)

이 장에서 틀린 곳을 찾으셨다면 [사실 오류로](https://github.com/leaf-kit/book-graph-engineering/issues/new?template=01-fact-error.yml), 상태 라벨이 어긋났다면 [라벨 이의로](https://github.com/leaf-kit/book-graph-engineering/issues/new?template=03-status-label.yml) 적어 주세요.
