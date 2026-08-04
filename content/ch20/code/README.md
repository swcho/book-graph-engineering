# 20장 - 끝나지 않는 루프를 끝내는 법

`4부 - 에이전트 그래프 엔지니어링 (트랙 2)` | **한국어** | [English](../../../content_en/ch20/code/README.md) | [책 전체 목차](../../../README.md) | [출처 링크 모음](../../../SOURCES.md)

> 층마다 상한을 다 걸어 뒀는데 240번을 돌았습니다.

[1장](../../ch01/code/README.md)에서 41만 원짜리 사고를 얘기하면서 "종료 조건이 없으면 종료를 모델이 정한다"고 썼는데, 이번엔 종료 조건이 *있었*습니다. 세 개나요. 그런데도 안 막혔어요. 이 장은 그 이야기입니다. 무엇으로 멈출지, 어디에 걸지, 그리고 왜 하나로는 부족한지요.

## 이 장의 절

| 절 | 제목 |
|---|---|
| 20.1 | 네 가지가 각각 다른 걸 잡는다 |
| 20.2 | 진전을 무엇으로 잴 것인가 |
| 20.3 | 예산을 안 나누면 뒤가 굶는다 |
| 20.4 | 네 조건을 다 붙인 루프 |
| 20.5 | 곱하기를 아무도 안 한다 |

## 한 장 요약

- 종료 조건은 넷입니다. 횟수, 예산, 시간, 그리고 진전 없음. 하나만 두면 나머지 셋이 못 잡는 경우가 남아요.
- 진전 척도는 「모델이 스스로 올릴 수 있는 값」이면 안 됩니다. 길이도 확신도도 모델이 마음대로 올려요. 규칙으로 세는 값을 쓰세요.
- 모델에게 「끝났나요?」를 묻지 마세요. 「무엇이 남았나요」만 묻고, 끝났는지는 코드가 정합니다. 그러면 남은 목록이 진전 척도도 됩니다.
- 예산을 안 나누면 뒤쪽 단계가 굶습니다. 그리고 대개 뒤쪽이 품질을 지키는 단계예요. 최소분을 먼저 떼어 두세요.
- 층마다 상한을 둬도 곱하면 커집니다. 전역 예산을 하나 더 두고 모든 층이 보게 하세요. 그리고 그 예산은 전역 변수가 아니라 *상태*에 둡니다. 안 그러면 재개할 때 리셋됩니다.
- 끝난 이유를 상태에 남기세요. 「상한」과 「정체」는 대응이 다릅니다.

## 키워드와 1차 출처

| 키워드 | 상태 | 출처 |
|---|---|---|
| 종료 조건 | [사실상 표준] | [termination condition](https://docs.langchain.com/oss/python/langgraph/graph-api) |
| 재귀 한도 | [사실상 표준] | [recursion limit](https://docs.langchain.com/oss/python/langgraph/graph-api) |
| 평가자-최적화 패턴 | [사실상 표준] | [evaluator-optimizer](https://www.anthropic.com/engineering/building-effective-agents) |
| 토큰 사용량 추적 | [사실상 표준] | [usage tracking](https://docs.claude.com/en/docs/build-with-claude/token-counting) |
| 조기 종료 | [사실상 표준] | [early stopping](https://www.deeplearningbook.org/contents/regularization.html) |
| 회로 차단기 | [사실상 표준] | [circuit breaker](https://martinfowler.com/bliki/CircuitBreaker.html) |
| 속도 제한 | [사실상 표준] | [rate limiting](https://datatracker.ietf.org/doc/html/rfc6585) |

상태 표시는 **[표준]** 공식 명세, **[사실상 표준]** 명세는 없지만 업계가 널리 쓰는 것, **[실험]** 아직 자리를 잡는 중이라는 뜻입니다.

## 예제 실행

<!-- 실행 가이드 시작 - 사람이 쓴 부분. gen-docs.py 가 건드리지 않는다. -->

확인 시점 2026년 8월. Python 3.9 이상.

```bash
cd content/ch20/code
python3 ex1_four_guards.py        # 의존성 없음
python3 ex2_stall_detection.py    # 의존성 없음
python3 ex3_budget_split.py       # 의존성 없음
pip install "langgraph>=1.0,<2.0"
python3 ex4_generator_critic.py   # 네 조건을 다 붙인 루프
python3 ex5_nested_loops.py       # 의존성 없음
```

<!-- 실행 가이드 끝 -->

---

**다음 장에서 뒤집히는 것:** 이 장에서 「재개하면 예산이 이어진다」를 전제로 얘기했습니다. 그러려면 죽었다 살아나도 상태가 남아 있어야 해요. 다음 장이 그 이야기입니다.

---

이전 [19장 상태 그래프와 리듀서, 그리고 슈퍼스텝](../../ch19/code/README.md) | [전체 목차](../../../README.md) | 다음 [21장 프로세스가 죽어도 작업은 살아 있어야 한다](../../ch21/code/README.md)

이 장에서 틀린 곳을 찾으셨다면 [사실 오류로](https://github.com/leaf-kit/book-graph-engineering/issues/new?template=01-fact-error.yml), 상태 라벨이 어긋났다면 [라벨 이의로](https://github.com/leaf-kit/book-graph-engineering/issues/new?template=03-status-label.yml) 적어 주세요.
