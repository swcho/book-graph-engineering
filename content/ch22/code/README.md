# 22장 — 되돌릴 수 없는 일을 되갚는 법

`4부 · 에이전트 그래프 엔지니어링 (트랙 2)` · [책 전체 목차](../../../README.md) · [출처 링크 모음](../../../SOURCES.md)

> 장애는 3분이었습니다. 복구에는 40분이 걸렸어요.

[21장](../../ch21/code/README.md)에서 「다시 하면 된다」를 전제로 얘기했습니다. 이 장은 그 전제가 배신하는 두 지점을 봅니다. 다시 하는 게 문제를 키우는 경우, 그리고 애초에 다시 할 수 없는 경우요.

## 이 장의 절

| 절 | 제목 |
|---|---|
| 22.1 | 다 같이 실패하면 다 같이 재시도한다 |
| 22.2 | 타임아웃은 층이 아니라 예산이다 |
| 22.3 | 되돌릴 수 없으면 되갚는다 |
| 22.4 | 되갚기가 실패하면 |
| 22.5 | 쌓아 두는 곳이 있어야 한다 |

## 한 장 요약

- 재시도는 좋은데 여럿이 동시에 하면 장애를 키웁니다. 지수 백오프만으로는 봉우리가 안 낮아져요. 「다 같이」를 흩는 건 흔들기(jitter)입니다.
- 장애가 끝나는 순간이 제일 위험합니다. 회로 차단기의 「반쯤 열림」에서 정찰병을 *한 명만* 보내세요.
- 각 층 타임아웃의 합이 바깥 타임아웃보다 크면 그 설정은 거짓말입니다. 층이 아니라 예산으로 다루고, 뒤 단계의 최소 필요분을 먼저 떼어 두세요.
- 밖으로 나간 일은 롤백이 안 됩니다. 되갚는 동작을 짝지어 두고 역순으로 실행합니다. 되돌릴 수 없는 단계는 최대한 뒤로 미세요. 코드 안 고치고 순서만 바꿔도 위험이 사라집니다.
- 되갚기가 실패하면 대기열에 적습니다. 그건 우리 DB 안의 일이라 거기서 멈춰요. 무한히 안 내려갑니다.
- 데드레터 큐는 항목만 보고 재실행할 수 있어야 합니다. 멱등 키를 반드시 넣으세요. 그리고 알림은 늘리지 말고 줄이세요. 아무도 안 보는 알림은 없는 것과 같습니다.

## 키워드와 1차 출처

| 키워드 | 상태 | 출처 |
|---|---|---|
| 지수 백오프 | [사실상 표준] | [exponential backoff](https://aws.amazon.com/builders-library/timeouts-retries-and-backoff-with-jitter/) |
| 흔들기 | [사실상 표준] | [jitter](https://aws.amazon.com/builders-library/timeouts-retries-and-backoff-with-jitter/) |
| 재시도 폭풍 | [사실상 표준] | [retry storm](https://sre.google/sre-book/handling-overload/) |
| 회로 차단기 | [사실상 표준] | [circuit breaker](https://martinfowler.com/bliki/CircuitBreaker.html) |
| 사가 패턴 | [사실상 표준] | [saga](https://www.cs.cornell.edu/andru/cs711/2002fa/reading/sagas.pdf) |
| 보상 트랜잭션 | [사실상 표준] | [compensating transaction](https://learn.microsoft.com/en-us/azure/architecture/patterns/compensating-transaction) |
| 데드레터 큐 | [사실상 표준] | [dead letter queue](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-dead-letter-queues.html) |
| 재시도 후 대기 | [표준] | [Retry-After](https://datatracker.ietf.org/doc/html/rfc9110#field.retry-after) |

상태 표시는 **[표준]** 공식 명세, **[사실상 표준]** 명세는 없지만 업계가 널리 쓰는 것, **[실험]** 아직 자리를 잡는 중이라는 뜻입니다.

## 예제 실행

<!-- 실행 가이드 시작 — 사람이 쓴 부분. gen-docs.py 가 건드리지 않는다. -->

확인 시점 2026년 8월. Python 3.9 이상. 외부 의존성 없음.

```bash
cd content/ch22/code
python3 ex1_backoff.py          # 재시도 전략별 부하 봉우리
python3 ex2_timeout_budget.py   # 층별 타임아웃과 예산 배분
python3 ex3_saga.py             # 보상 트랜잭션과 단계 순서
python3 ex4_undo_fails.py       # 되갚기가 실패할 때
python3 ex5_dlq.py              # 데드레터 큐와 원인 분류
```

`ex1` 은 난수를 쓰지만 시드를 42로 고정했습니다. 시드를 바꾸면 숫자가
조금 달라지는데, 세 전략의 순서는 바뀌지 않습니다.

<!-- 실행 가이드 끝 -->

---

**다음 장에서 뒤집히는 것:** 이 장에서 「사람에게 넘긴다」를 여러 번 썼습니다. 그런데 넘기는 방법을 안 정했어요. 슬랙 알림 말고요. 다음 장은 사람을 그래프 안의 *노드*로 넣는 이야기입니다.

---

← [21장 프로세스가 죽어도 작업은 살아 있어야 한다](../../ch21/code/README.md) · [전체 목차](../../../README.md) · [23장 사람이 끼어드는 지점](../../ch23/code/README.md) →

이 장에서 틀린 곳을 찾으셨다면 [사실 오류로](https://github.com/leaf-kit/book-graph-engineering/issues/new?template=01-fact-error.yml), 상태 라벨이 어긋났다면 [라벨 이의로](https://github.com/leaf-kit/book-graph-engineering/issues/new?template=03-status-label.yml) 적어 주세요.
