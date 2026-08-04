# 2장 - 하네스 엔지니어링에서 그래프 엔지니어링으로

`1부 - 뿌리: 그래프는 어디에 있었나` | **한국어** | [English](../../../content_en/ch02/code/README.md) | [책 전체 목차](../../../README.md) | [출처 링크 모음](../../../SOURCES.md)

> 에이전트가 자기 작업 폴더를 지운 적이 있습니다. 제 것이었어요.

지난 장이 60년을 압축했다면 이 장은 최근 2년을 압축합니다. 사람들이 하네스라고 부르며 쌓아 온 실무 한 벌을 통째로 가져와서, 그 안의 모든 용어에 그래프 이름을 붙일 겁니다. 다 붙이고 나면 원래 열네 챕터쯤 되는 이야기가 표 하나로 접힙니다.

## 이 장의 절

| 절 | 제목 |
|---|---|
| 2.1 | around the model - 모델 바깥에 있는 것들 |
| 2.2 | 30분이면 됩니다 - 노드 두 개 |
| 2.3 | 순서를 정하는 일 = 위상 정렬 |
| 2.4 | 성형에서 메시로 - 위상이 곧 비용 |
| 2.5 | 여섯 가지 패턴은 사실 위상 여섯 개다 |
| 2.6 | 노드가 292개가 되는 날 |
| 2.7 | 그래프를 만드는 그래프 |
| 2.8 | 번역 대응표 |

## 한 장 요약

- 혼자 일하는 에이전트는 자기 실수를 못 봅니다. 같은 컨텍스트를 보니까요. 규칙을 프롬프트에 적으면 컨텍스트가 차는 날 잘려 나갑니다. 엣지에 붙이면 안 잘립니다.
- 에이전트 정의는 노드, 스킬은 서브그래프, 오케스트레이터는 실행기입니다. 선행 조건은 DAG 엣지고, 위상 정렬한 묶음이 슈퍼스텝입니다.
- 위상은 비용입니다. 성형은 팀원 수에 비례하고 메시는 제곱으로 늡니다. 대신 성형은 리더가 먼저 무너집니다.
- 여섯 가지 아키텍처 패턴은 그래프 위상 여섯 개고, 안티패턴 목록은 그래프 스멜입니다. 표 가 이 책의 목차이기도 합니다.

## 키워드와 1차 출처

| 키워드 | 상태 | 출처 |
|---|---|---|
| 에이전트 설계 패턴 | [사실상 표준] | [agent workflow patterns](https://www.anthropic.com/engineering/building-effective-agents) |
| 컨텍스트 엔지니어링 | [사실상 표준] | [context engineering](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents) |
| 에이전트 하네스 | [실험] | [agent harness](https://github.com/langchain-ai/deepagents) |
| 상태 그래프와 슈퍼스텝 | [사실상 표준] | [state graph, superstep](https://docs.langchain.com/oss/python/langgraph/graph-api) |
| 모델 컨텍스트 프로토콜 | [사실상 표준] | [MCP](https://modelcontextprotocol.io/specification/2026-07-28) |
| 에이전트 규약 파일 | [사실상 표준] | [AGENTS.md](https://agents.md/) |
| 에이전트 간 통신 프로토콜 | [실험] | [A2A](https://a2a-protocol.org/) |
| 위상 정렬 | [표준] | [topological sort](https://dl.acm.org/doi/10.1145/368996.369025) |
| 이벤트 소싱 | [사실상 표준] | [event sourcing](https://martinfowler.com/eaaDev/EventSourcing.html) |

상태 표시는 **[표준]** 공식 명세, **[사실상 표준]** 명세는 없지만 업계가 널리 쓰는 것, **[실험]** 아직 자리를 잡는 중이라는 뜻입니다.

## 예제 실행

<!-- 실행 가이드 시작 - 사람이 쓴 부분. gen-docs.py 가 건드리지 않는다. -->

확인 시점 2026년 8월. Python 3.9 이상.
예제 2만 LangGraph가 필요하고, 나머지는 **의존성 없음**입니다.

```bash
cd content/ch02/code
python3 ex1_one_file.py       # 한 파일에 다 넣은 단일 에이전트 - 30분 실습의 '전'
python3 ex2_two_nodes.py      # 노드 두 개짜리 그래프 - 30분 실습의 '후'
python3 ex3_depends_on.py     # depends_on 은 DAG 엣지다. 위상 정렬한 묶음이 슈퍼스텝
python3 ex4_star_vs_mesh.py   # 성형과 메시, 메시지 수를 세어 본다
```

## 예제 2만 설치가 필요합니다

```bash
pip install "langgraph>=1.0,<2.0"
```

확인 시점 LangGraph 1.0.1 기준입니다. **API 키는 필요 없습니다.**

## API 키 없이 어떻게 돌아가나

`harness.py`의 `fake_model`이 진짜 언어 모델을 대신합니다. 가짜지만 아무렇게나 만든 가짜는 아니고, 진짜 모델이 흔히 보이는 성질 두 가지를 흉내 냅니다.

1. 지시가 길어지면 뒤쪽 요구사항을 빠뜨린다.
2. 빠뜨린 걸 지적해 주면 그때 채운다.

이 두 성질이 2장 전체의 논거입니다. 모델을 바꿔도 정도만 달라지지 성질은 남습니다.

## 예제 1과 예제 2를 나란히 보세요

두 예제는 **프롬프트가 글자 하나까지 같습니다.** 달라진 건 구조뿐입니다. 그런데 산출물이 다릅니다. 2장이 하려는 말이 그겁니다.

```bash
python3 ex1_one_file.py  > /tmp/before.txt
python3 ex2_two_nodes.py > /tmp/after.txt
diff /tmp/before.txt /tmp/after.txt
```

## 숫자는 직접 바꿔서 보세요

`ex4_star_vs_mesh.py` 위쪽 두 상수는 팀마다 다릅니다. 자기 팀 값으로 바꿔서 돌려 보면 엣지 하나가 얼마짜리인지 나옵니다.

```python
AVG_TOKENS_PER_MSG = 1_200      # 요청 + 응답 합. 직접 재서 바꾸세요.
PRICE_PER_MTOK_KRW = 4_000      # 100만 토큰당 원. 2026년 8월 기준 대략치.
```

<!-- 실행 가이드 끝 -->

---

**다음 장에서 뒤집히는 것:** 여기까지 우리는 그래프를 당연한 도구처럼 썼습니다. 다음 장은 그 그래프가 언제 어떻게 발명됐는지, 그리고 왜 40년 동안 표(테이블)에 밀렸는지를 봅니다. 표가 이긴 이유를 모르면 같은 실수를 반복합니다.

---

이전 [1장 그래프로 다시 읽는 AI의 60년](../../ch01/code/README.md) | [전체 목차](../../../README.md) | 다음 [3장 다리 일곱 개를 건널 수 없었던 이유, 그리고 표가 이긴 이유](../../ch03/code/README.md)

이 장에서 틀린 곳을 찾으셨다면 [사실 오류로](https://github.com/leaf-kit/book-graph-engineering/issues/new?template=01-fact-error.yml), 상태 라벨이 어긋났다면 [라벨 이의로](https://github.com/leaf-kit/book-graph-engineering/issues/new?template=03-status-label.yml) 적어 주세요.
