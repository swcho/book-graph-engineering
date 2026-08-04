# 21장 — 프로세스가 죽어도 작업은 살아 있어야 한다

`4부 — 에이전트 그래프 엔지니어링 (트랙 2)` | **한국어** | [English](../../../content_en/ch21/code/README.md) | [책 전체 목차](../../../README.md) | [출처 링크 모음](../../../SOURCES.md)

> 4시간짜리 배치가 3시간 51분에서 죽었습니다.

[20장](../../ch20/code/README.md)에서 「재개하면 예산이 이어진다」를 전제로 얘기했는데, 그러려면 죽었다 살아나도 상태가 남아 있어야 합니다. 이 장이 그 이야기입니다. 그런데 상태를 저장하는 것만으로는 안 끝나요. 저장한 지점과 죽은 지점 사이에 *이미 벌어진 일*이 있거든요.

## 이 장의 절

| 절 | 제목 |
|---|---|
| 21.1 | 체크포인트는 경계에만 찍힌다 |
| 21.2 | 그래서 멱등성이 필요하다 |
| 21.3 | 상대가 멱등 키를 안 받아 주면 |
| 21.4 | 내구성은 공짜가 아니다 |
| 21.5 | 무엇에 저장할 것인가 |
| 21.6 | 죽여 보지 않으면 복구되는지 모른다 |

## 한 장 요약

- 체크포인트는 슈퍼스텝 경계에만 찍힙니다. 경계와 죽은 시점 사이의 일은 재개할 때 다시 합니다.
- 노드를 잘게 쪼개면 그 창이 좁아지지만 0이 되진 않습니다. 그리고 체크포인트 횟수가 늘어서 느려져요. 실측으로 SQLite는 메모리의 2.0~2.8배고, 32KB를 넘으면 4.8배까지 갑니다.
- 창을 없애는 대신 *다시 해도 되게* 만듭니다. 그게 멱등성입니다. 멱등 키는 요청이 아니라 *작업*에서 나와야 하고, 상대 API가 실제로 지원하는지 문서로 확인해야 합니다.
- 상대가 지원 안 하면 부작용 로그를 씁니다. 그래도 창은 남아요. 남은 건 「모름」으로 분류해서 사람이 마감합니다. 없애려 하지 말고 좁히고 넘기세요.
- 메모리 체크포인터는 체크포인터가 아니라 캐시입니다. 개발 중에는 완벽하게 동작하고 배포하는 날 죽습니다.
- 그리고 죽여 보지 않으면 복구되는지 모릅니다. `kill -9` 한 번이 5분이에요.

## 키워드와 1차 출처

| 키워드 | 상태 | 출처 |
|---|---|---|
| 체크포인터 | [사실상 표준] | [checkpointer](https://docs.langchain.com/oss/python/langgraph/persistence) |
| 내구성 있는 실행 | [사실상 표준] | [durable execution](https://docs.temporal.io/evaluate/understanding-temporal) |
| 멱등성 | [표준] | [idempotency](https://datatracker.ietf.org/doc/html/rfc9110#section-9.2.2) |
| 멱등 키 | [사실상 표준] | [idempotency key](https://datatracker.ietf.org/doc/html/draft-ietf-httpapi-idempotency-key-header) |
| 정확히 한 번 | [사실상 표준] | [exactly-once](https://kafka.apache.org/documentation/#semantics) |
| 스레드 아이디 | [사실상 표준] | [thread id](https://docs.langchain.com/oss/python/langgraph/persistence) |
| 쓰기 전 로그 | [사실상 표준] | [write-ahead log](https://www.sqlite.org/wal.html) |

상태 표시는 **[표준]** 공식 명세, **[사실상 표준]** 명세는 없지만 업계가 널리 쓰는 것, **[실험]** 아직 자리를 잡는 중이라는 뜻입니다.

## 예제 실행

<!-- 실행 가이드 시작 — 사람이 쓴 부분. gen-docs.py 가 건드리지 않는다. -->

확인 시점 2026년 8월. Python 3.9 이상.

```bash
cd content/ch21/code
pip install "langgraph>=1.0,<2.0" "langgraph-checkpoint-sqlite<3"

bash run_crash_demo.sh          # 프로세스를 실제로 죽였다가 이어서 실행
python3 ex2_idempotency.py      # 의존성 없음
python3 ex3_side_effect_log.py  # 의존성 없음
python3 ex4_checkpointer_cost.py # 체크포인터별 지연 실측
python3 ex5_recovery_drill.py   # 의존성 없음
```

`langgraph-checkpoint-sqlite` 는 **3 미만**을 쓰세요.
3.x 는 `langgraph-checkpoint` 4.x 를 끌어오는데, 확인 시점의 langgraph 1.0.1 과
직렬화 계층이 맞지 않아 임포트에서 실패합니다.

<!-- 실행 가이드 끝 -->

---

**다음 장에서 뒤집히는 것:** 이 장은 「다시 하면 된다」를 전제로 했습니다. 그런데 다시 할 수 없는 것도 있어요. 이미 보낸 메일, 이미 삭제한 파일. 그럴 때는 되돌리는 대신 *되갚아야* 합니다. 다음 장은 보상 트랜잭션 이야기입니다.

---

이전 [20장 끝나지 않는 루프를 끝내는 법](../../ch20/code/README.md) | [전체 목차](../../../README.md) | 다음 [22장 되돌릴 수 없는 일을 되갚는 법](../../ch22/code/README.md)

이 장에서 틀린 곳을 찾으셨다면 [사실 오류로](https://github.com/leaf-kit/book-graph-engineering/issues/new?template=01-fact-error.yml), 상태 라벨이 어긋났다면 [라벨 이의로](https://github.com/leaf-kit/book-graph-engineering/issues/new?template=03-status-label.yml) 적어 주세요.
