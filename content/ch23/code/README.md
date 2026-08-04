# 23장 — 사람이 끼어드는 지점

`4부 — 에이전트 그래프 엔지니어링 (트랙 2)` | **한국어** | [English](../../../content_en/ch23/code/README.md) | [책 전체 목차](../../../README.md) | [출처 링크 모음](../../../SOURCES.md)

> 승인 대기 건이 2주 동안 묶여 있었습니다.

[22장](../../ch22/code/README.md)에서 「사람에게 넘긴다」를 여러 번 썼는데, 넘기는 방법을 안 정했습니다. 이 장이 그 이야기입니다. 사람을 그래프 밖의 예외가 아니라 *안의 노드*로 넣는 방법이요.

## 이 장의 절

| 절 | 제목 |
|---|---|
| 23.1 | 멈추는 것은 예외가 아니다 |
| 23.2 | 중단점 앞에 부작용을 두지 마라 |
| 23.3 | 어디에 문을 달 것인가 |
| 23.4 | 사람이 답을 안 하면 |
| 23.5 | 무엇을 보여 줬는지 남긴다 |

## 한 장 요약

- 사람을 그래프 밖의 예외가 아니라 안의 노드로 넣습니다. 중단점은 예외가 아니라 정상적인 중단이고, 멈춘 자리는 체크포인터에 남습니다. 프로세스를 붙잡고 있지 않아도 돼요.
- 중단점 앞에는 부작용을 두지 마세요. 재개하면 그 노드를 처음부터 다시 돕니다. 부작용이 앞에 있어야 하면 노드를 둘로 쪼개서 경계를 만드세요.
- 문턱은 취향이 아니라 용량으로 정합니다. 검토 시간이 용량의 70%를 넘지 않는 문턱 중 제일 낮은 것. 전부 사람이 보는 정책은 결국 아무도 안 보는 정책이 됩니다.
- 무응답 정책이 없으면 기본값은 「영원히 기다림」입니다. 시간이 지날수록 다르게 처리하세요. 등급 올리기는 판단을 올리는 장치가 아니라 주의를 끄는 장치입니다.
- 승인 기록에는 「보여 준 내용」과 「상태 지문」이 들어가야 합니다. 지문이 다르면 다시 물으세요. 다만 결정에 영향을 주는 필드만 해시하세요. 매번 다시 물으면 사람이 확인 없이 누르기 시작합니다.

## 키워드와 1차 출처

| 키워드 | 상태 | 출처 |
|---|---|---|
| 사람 개입 | [사실상 표준] | [human in the loop](https://docs.langchain.com/oss/python/langgraph/interrupts) |
| 중단점 | [사실상 표준] | [interrupt](https://docs.langchain.com/oss/python/langgraph/interrupts) |
| 재개 명령 | [사실상 표준] | [Command(resume)](https://docs.langchain.com/oss/python/langgraph/interrupts) |
| 승인 관문 | [사실상 표준] | [approval gate](https://learn.microsoft.com/en-us/azure/architecture/patterns/gatekeeper) |
| 등급 올리기 | [사실상 표준] | [escalation](https://sre.google/workbook/incident-response/) |
| 감사 추적 | [표준] | [audit trail](https://www.w3.org/TR/prov-o/) |
| 네 눈 원칙 | [사실상 표준] | [four-eyes principle](https://www.bis.org/publ/bcbs230.pdf) |

상태 표시는 **[표준]** 공식 명세, **[사실상 표준]** 명세는 없지만 업계가 널리 쓰는 것, **[실험]** 아직 자리를 잡는 중이라는 뜻입니다.

## 예제 실행

<!-- 실행 가이드 시작 — 사람이 쓴 부분. gen-docs.py 가 건드리지 않는다. -->

확인 시점 2026년 8월. Python 3.9 이상.

```bash
cd content/ch23/code
pip install "langgraph>=1.0,<2.0"

python3 ex1_interrupt.py     # 멈추고, 답 받고, 이어 가기
python3 ex2_node_reruns.py   # interrupt 앞의 부작용이 두 번 실행된다
python3 ex3_gate_policy.py   # 승인 문턱을 용량으로 정하기 (의존성 없음)
python3 ex4_no_answer.py     # 사람이 답을 안 할 때 (의존성 없음)
python3 ex5_audit.py         # 승인 감사 기록 (의존성 없음)
```

`ex1`, `ex2` 는 메모리 체크포인터를 씁니다. 운영에서는 21장에서 본 대로
디스크에 저장하는 체크포인터를 써야 사람이 사흘 뒤에 답해도 이어집니다.

<!-- 실행 가이드 끝 -->

---

**다음 장에서 뒤집히는 것:** 이 장에서 「묻는 순간의 내용을 상태에 통째로 저장하라」고 썼습니다. 그런데 그렇게 쌓다 보면 상태가 터져요. 다음 장은 컨텍스트가 꽉 찼을 때 무엇을 버릴 것인가입니다.

---

이전 [22장 되돌릴 수 없는 일을 되갚는 법](../../ch22/code/README.md) | [전체 목차](../../../README.md) | 다음 [24장 컨텍스트가 꽉 찼습니다](../../ch24/code/README.md)

이 장에서 틀린 곳을 찾으셨다면 [사실 오류로](https://github.com/leaf-kit/book-graph-engineering/issues/new?template=01-fact-error.yml), 상태 라벨이 어긋났다면 [라벨 이의로](https://github.com/leaf-kit/book-graph-engineering/issues/new?template=03-status-label.yml) 적어 주세요.
