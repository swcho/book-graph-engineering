# 24장 - 컨텍스트가 꽉 찼습니다

`4부 - 에이전트 그래프 엔지니어링 (트랙 2)` | **한국어** | [English](../../../content_en/ch24/code/README.md) | [책 전체 목차](../../../README.md) | [출처 링크 모음](../../../SOURCES.md)

> 한 달 청구서가 예상의 6.4배로 나왔습니다.

왜 그렇게 됐는지는 로그를 열자마자 보였습니다. 대화가 길어질수록 매 턴 보내는 양이 늘어나고 있었거든요. 20턴짜리 대화는 8,000토큰이 맞았습니다. 그런데 실제 사용자들은 평균 47턴을 썼습니다. 저희가 20턴을 기준으로 잡은 이유는... 사실 없었습니다. 테스트할 때 그 정도만 해 봤을 뿐이에요. 이 장은 그 이야기입니다. 컨텍스트는 왜 차는지, 무엇을 버릴지 어떻게 정하는지, 그리고 버리는 순간 무엇을 잃는지요.

## 이 장의 절

| 절 | 제목 |
|---|---|
| 24.1 | 선형으로 자라는 것과 제곱으로 자라는 것 |
| 24.2 | 줄이는 네 가지 방법, 그리고 각각이 잃는 것 |
| 24.3 | 요약이 먼저 버리는 것 |
| 24.4 | 상태에는 참조만 싣는다 |
| 24.5 | 기억을 계층으로 나누기 |

## 한 장 요약

- 대화 길이는 선형으로 자라는데 누적 비용은 제곱으로 자랍니다. 매 턴 전체를 다시 보내기 때문이에요. 창이 차기 훨씬 전에 돈이 먼저 문제가 됩니다.
- 줄이는 방법을 고를 때 절감률만 보지 마세요. 「나중에 실제로 참조되는 사실이 몇 % 남는가」를 같이 재야 절반이 아니라 전체를 잰 겁니다.
- 무엇을 버릴지는 중요도가 아니라 「몇 번 쓰나」로 정합니다. 중요도는 취향이 들어가고, 중요한 것은 이미 최근 컨텍스트에 있습니다. 다만 사용자가 명시한 제약은 횟수와 무관하게 남기세요.
- 요약은 이유와 제약을 먼저 버립니다. 결정만 남고 이유가 없으면 에이전트가 그 결정을 뒤집고, 제약이 없으면 금지된 일을 다시 시도합니다. 프롬프트에 보존할 종류를 못 박고, 요약의 요약을 하지 마세요.
- 상태에는 참조만 싣습니다. 그러면 컨텍스트도 줄고 체크포인트도 싸집니다. 두 문제가 사실 같은 문제였어요.
- 기억은 계층으로 나누고 위에서부터 훑습니다. 비싼 조회를 안 하는 것이 빠른 조회를 만드는 것보다 크게 듭니다. 대신 위 계층이 낡으면 틀린 채로 빨라지니, 계층마다 유효 기간을 두세요.

## 키워드와 1차 출처

| 키워드 | 상태 | 출처 |
|---|---|---|
| 컨텍스트 창 | [사실상 표준] | [context window](https://docs.claude.com/en/docs/build-with-claude/context-windows) |
| 컨텍스트 엔지니어링 | [실험] | [context engineering](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents) |
| 압축 | [실험] | [compaction](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents) |
| 오프로딩 | [실험] | [offloading](https://docs.langchain.com/oss/python/langgraph/memory) |
| 프롬프트 캐싱 | [사실상 표준] | [prompt caching](https://docs.claude.com/en/docs/build-with-claude/prompt-caching) |
| 장기 기억 저장소 | [사실상 표준] | [long-term memory store](https://docs.langchain.com/oss/python/langgraph/memory) |
| 토큰 계산 | [사실상 표준] | [token counting](https://docs.claude.com/en/docs/build-with-claude/token-counting) |

상태 표시는 **[표준]** 공식 명세, **[사실상 표준]** 명세는 없지만 업계가 널리 쓰는 것, **[실험]** 아직 자리를 잡는 중이라는 뜻입니다.

## 예제 실행

<!-- 실행 가이드 시작 - 사람이 쓴 부분. gen-docs.py 가 건드리지 않는다. -->

확인 시점 2026년 8월. Python 3.9 이상. 외부 의존성 없음.

```bash
cd content/ch24/code
python3 ex1_growth.py          # 턴이 늘 때 누적 토큰이 제곱으로 자라는 것
python3 ex2_strategies.py      # 줄이기 네 방법의 토큰 절감과 사실 보존율
python3 ex3_summary_drift.py   # 요약을 반복하면 무엇이 먼저 사라지나
python3 ex4_offload.py         # 본문 대신 참조를 상태에 싣기
python3 ex5_memory_tiers.py    # 기억 계층별 조회 비용
```

`ex1` 의 단가는 확인 시점의 공개 가격표를 기준으로 한 예시입니다.
지금 값은 각 벤더의 가격 페이지에서 확인하세요.

<!-- 실행 가이드 끝 -->

---

**다음 장에서 뒤집히는 것:** 이 장은 에이전트 하나의 컨텍스트를 다뤘습니다. 그런데 에이전트를 여럿 두면 컨텍스트가 자동으로 나뉩니다. 문제가 사라지는 걸까요? 다음 장에서 보면, 사라지는 게 아니라 "에이전트 사이의 통신"으로 자리를 옮깁니다.

---

이전 [23장 사람이 끼어드는 지점](../../ch23/code/README.md) | [전체 목차](../../../README.md) | 다음 [25장 여섯 가지 위상, 그리고 도구를 꽂는 구멍](../../ch25/code/README.md)

이 장에서 틀린 곳을 찾으셨다면 [사실 오류로](https://github.com/leaf-kit/book-graph-engineering/issues/new?template=01-fact-error.yml), 상태 라벨이 어긋났다면 [라벨 이의로](https://github.com/leaf-kit/book-graph-engineering/issues/new?template=03-status-label.yml) 적어 주세요.
