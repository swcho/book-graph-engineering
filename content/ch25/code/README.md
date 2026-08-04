# 25장 - 여섯 가지 위상, 그리고 도구를 꽂는 구멍

`4부 - 에이전트 그래프 엔지니어링 (트랙 2)` | **한국어** | [English](../../../content_en/ch25/code/README.md) | [책 전체 목차](../../../README.md) | [출처 링크 모음](../../../SOURCES.md)

> 「에이전트를 몇 개로 나눌까요?」

이 장은 나누는 방법을 여섯 가지로 정리하고, 각각이 무엇을 얻고 무엇을 잃는지 재 봅니다. 그리고 후반부에서 이 에이전트들이 바깥 세상에 손을 뻗는 방법, 즉 도구 호출과 MCP를 다룹니다.

## 이 장의 절

| 절 | 제목 |
|---|---|
| 25.1 | 여섯 가지밖에 없다 |
| 25.2 | 펴는 값보다 합치는 값이 비싸다 |
| 25.3 | 라우터는 품질을 올리는 장치가 아니다 |
| 25.4 | 도구는 그래프 밖으로 나가는 엣지다 |
| 25.5 | 도구 설명이 곧 엣지 선택 함수다 |

## 한 장 요약

- 위상은 여섯 가지뿐입니다. 경로, 이분, 합류, 성형, 순환, 동적 엣지, 트리. 복잡해 보이는 구조는 전부 이 여섯의 조합이에요. 이름은 사람마다 다르니 그림으로 얘기하세요.
- 「좋은 위상」은 없습니다. 제일 빠른 것과 제일 싼 것과 품질 1등이 다 다릅니다. 제약이 무엇인지 먼저 정하고, 제약이 없으면 제일 단순한 경로를 쓰세요.
- 병렬은 시간을 사는 것이지 돈을 아끼는 게 아닙니다. 토큰은 그대로예요.
- 펴는 값보다 합치는 값이 천장을 만듭니다. 폭을 키우기 전에 합류를 프로파일하세요. 갈래끼리 비교하는 연산이 있으면 그건 제곱입니다.
- 폭을 키우면 총 시간은 줄지만 물결 하나가 길어집니다. 평균은 좋아지고 최악은 나빠져요. 사용자가 느끼는 건 대개 최악 쪽입니다.
- 라우터는 품질을 올리는 장치가 아니라 교환입니다. 얼마를 내주고 얼마를 아끼는지 계산하려면 채점 데이터셋이 먼저 있어야 합니다.
- 도구는 그래프 밖으로 나가는 엣지고, MCP는 그 엣지 목록을 실행 시점에 받아 오는 방식입니다. 대가는 컴파일 시점에 아무것도 모른다는 것이에요. 시작할 때 목록을 검증하세요.
- 도구 설명이 곧 엣지 선택 함수입니다. 무엇을 주는지, 어떤 말로 묻는지, *언제 안 쓰는지* 셋을 쓰세요. 셋째가 제일 자주 빠지고 제일 크게 듭니다.

## 키워드와 1차 출처

| 키워드 | 상태 | 출처 |
|---|---|---|
| 오케스트레이터-워커 | [사실상 표준] | [orchestrator-workers](https://www.anthropic.com/engineering/building-effective-agents) |
| 팬아웃, 팬인 | [사실상 표준] | [fan-out/fan-in](https://learn.microsoft.com/en-us/azure/azure-functions/durable/durable-functions-cloud-backup) |
| 라우팅 | [사실상 표준] | [routing](https://www.anthropic.com/engineering/building-effective-agents) |
| 평가자-최적화 | [사실상 표준] | [evaluator-optimizer](https://www.anthropic.com/engineering/building-effective-agents) |
| 꼬리 지연 | [사실상 표준] | [tail latency](https://research.google/pubs/the-tail-at-scale/) |
| 모델 컨텍스트 프로토콜 | [사실상 표준] | [Model Context Protocol](https://modelcontextprotocol.io/specification/2025-06-18) |
| 도구 스키마 | [사실상 표준] | [tool schema](https://modelcontextprotocol.io/specification/2025-06-18/server/tools) |
| Send API | [사실상 표준] | [Send](https://docs.langchain.com/oss/python/langgraph/graph-api) |

상태 표시는 **[표준]** 공식 명세, **[사실상 표준]** 명세는 없지만 업계가 널리 쓰는 것, **[실험]** 아직 자리를 잡는 중이라는 뜻입니다.

## 예제 실행

<!-- 실행 가이드 시작 - 사람이 쓴 부분. gen-docs.py 가 건드리지 않는다. -->

확인 시점 2026년 8월. Python 3.9 이상.

```bash
cd content/ch25/code
python3 ex1_topologies.py       # 여섯 위상 비교 (의존성 없음)
python3 ex2_fanout.py           # 펴는 값과 합류 값 (의존성 없음)
python3 ex3_router.py           # 라우터 정확도와 교환 (의존성 없음)

pip install mcp
python3 ex4_mcp_client.py       # 진짜 MCP 서버에 붙는다 (mcp_server.py 를 띄운다)

python3 ex5_tool_selection.py   # 도구 설명이 선택을 정한다 (의존성 없음)
```

`ex4` 는 `mcp_server.py` 를 자식 프로세스로 띄웁니다. 따로 실행하지 않아도 됩니다.
확인 시점의 mcp 파이썬 SDK 는 1.5.0 이고 프로토콜 버전은 2024-11-05 였습니다.

<!-- 실행 가이드 끝 -->

---

**다음 장에서 뒤집히는 것:** 이 장은 「무엇을 할 수 있게 할까」였습니다. 도구를 붙이고 에이전트를 나누고요. 다음 장은 반대입니다. *무엇을 못 하게 할 것인가.* 그리고 못 하게 하는 일이 왜 하게 하는 일보다 어려운지요.

---

이전 [24장 컨텍스트가 꽉 찼습니다](../../ch24/code/README.md) | [전체 목차](../../../README.md) | 다음 [26장 무엇을 못 하게 할 것인가](../../ch26/code/README.md)

이 장에서 틀린 곳을 찾으셨다면 [사실 오류로](https://github.com/leaf-kit/book-graph-engineering/issues/new?template=01-fact-error.yml), 상태 라벨이 어긋났다면 [라벨 이의로](https://github.com/leaf-kit/book-graph-engineering/issues/new?template=03-status-label.yml) 적어 주세요.
