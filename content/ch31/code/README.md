# 31장 — 두 에이전트가 같은 노드를 동시에 고쳤다

`6부 — 백본: 상태 관리 엔진` | [책 전체 목차](../../../README.md) | [출처 링크 모음](../../../SOURCES.md)

> 「분명히 고쳤는데요.」

[30장](../../ch30/code/README.md)은 변경이 *순서대로* 온다고 가정했습니다. 이벤트 1번 다음에 2번이 오고요. 이 장은 그 가정이 깨질 때 이야기입니다. 두 변경이 동시에 오면 순서가 없거든요. 그리고 그래프에서는 이게 관계형 DB보다 까다롭습니다. *무엇이 충돌 단위인지부터 애매하기* 때문이에요.

## 이 장의 절

| 절 | 제목 |
|---|---|
| 31.1 | 에러 없이 변경이 사라진다 |
| 31.2 | 쓰기 직전에 확인한다 |
| 31.3 | 그래프에서는 충돌 단위가 애매하다 |
| 31.4 | 감지한 다음이 진짜 문제다 |

## 한 장 요약

- 두 작업이 「읽고 → 판단하고 → 통째로 쓰기」를 하면 변경이 사라집니다. 에러 없이요. 로그에는 성공만 찍힙니다.
- 에이전트 시스템에서 이게 자주 나는 이유는 셋입니다. 판단 시간이 길고, 동시 실행이 기본이고, 전체를 다시 쓰는 코드를 만들기 쉬워서요.
- 트랜잭션으로는 안 풀립니다. 트랜잭션 안에 모델 호출이 들어가고, 워크플로는 프로세스 경계를 넘어 살아 있으니까요.
- 해법은 쓰기 직전에 「안 바뀌었나」를 확인하는 것입니다. 충돌은 에러가 아니라 *0행 갱신*으로 오니 `rowcount`를 봐야 해요.
- 낙관적과 비관적은 충돌률에서 갈립니다. 15~30% 근처가 갈림길이고, *판단을 잠금 밖으로 빼면 갈림길이 오른쪽으로 밀립니다*.
- 그래프에서는 충돌 단위부터 정해야 합니다. 노드 버전은 가짜 충돌을, 엣지 버전은 단일 값 누락을 만들어요. 「주어 + 관계 종류」를 논리 단위로 두고, 그 앞에 멱등 검사를 두세요.
- 충돌 감지는 기술 문제고 충돌 해결은 도메인 문제입니다. 필드 종류마다 합치는 방법이 다르고, 자유문은 애초에 자동으로 못 합칩니다.
- 그리고 자동 병합의 오류율을 재세요. 안 재면 「사람 일이 줄었다」만 보고 「조용히 틀린 것」을 못 봅니다.

## 키워드와 1차 출처

| 키워드 | 상태 | 출처 |
|---|---|---|
| 잃어버린 갱신 | [표준] | [lost update](https://www.postgresql.org/docs/current/transaction-iso.html) |
| 낙관적 잠금 | [사실상 표준] | [optimistic locking](https://martinfowler.com/eaaCatalog/optimisticOfflineLock.html) |
| 비관적 잠금 | [사실상 표준] | [pessimistic locking](https://martinfowler.com/eaaCatalog/pessimisticOfflineLock.html) |
| 비교 후 교체 | [표준] | [compare-and-swap](https://en.cppreference.com/w/cpp/atomic/atomic/compare_exchange) |
| 직렬화 가능 | [표준] | [serializable](https://www.postgresql.org/docs/current/transaction-iso.html#XACT-SERIALIZABLE) |
| 충돌 없는 자료형 | [실험] | [CRDT](https://inria.hal.science/inria-00555588) |
| 교착 | [표준] | [deadlock](https://www.postgresql.org/docs/current/explicit-locking.html#LOCKING-DEADLOCKS) |
| 쓰기 편중 | [표준] | [write skew](https://www.postgresql.org/docs/current/transaction-iso.html) |

상태 표시는 **[표준]** 공식 명세, **[사실상 표준]** 명세는 없지만 업계가 널리 쓰는 것, **[실험]** 아직 자리를 잡는 중이라는 뜻입니다.

## 예제 실행

<!-- 실행 가이드 시작 — 사람이 쓴 부분. gen-docs.py 가 건드리지 않는다. -->

확인 시점 2026년 8월. Python 3.9 이상.

```bash
cd content/ch31/code
pip install kuzu

python3 ex1_lost_update.py       # 진짜 스레드로 경쟁시킨다 (의존성 없음)
python3 ex2_optimistic.py        # 세 방식 비교 (의존성 없음)
python3 ex3_lock_contention.py   # 낙관적과 비관적이 뒤집히는 지점 (의존성 없음)
python3 ex4_conflict_shape.py    # 그래프에서 충돌 단위를 어디에 둘까
python3 ex5_merge_strategy.py    # 감지한 뒤에 무엇을 할까 (의존성 없음)
```

`ex1` 과 `ex2` 는 실제 스레드를 씁니다. 실행할 때마다 순서가 조금씩 달라질 수
있는데, 「하나가 사라진다」는 결과는 그대로입니다. 안 사라지면 `delay` 값을
키워서 다시 돌려 보세요.

`ex3` 의 값(판단 12ms, 잠금 획득 2.2ms)은 저희 환경에서 잰 것을 단순화한
것입니다. 뒤집히는 지점은 이 값에 따라 움직입니다. 직접 재서 넣으세요.

<!-- 실행 가이드 끝 -->

---

**다음 장에서 뒤집히는 것:** 이 장은 «스키마가 그대로»라고 가정했습니다. 같은 필드를 두고 다투는 얘기였죠. 그런데 필드 자체가 바뀌면요? 다음 장은 돌아가는 시스템의 구조를 바꾸는 이야기입니다.

---

이전 [30장 무엇이 언제 바뀌었는지 아무도 모른다](../../ch30/code/README.md) | [전체 목차](../../../README.md) | 다음 [32장 스키마를 바꾸는 날](../../ch32/code/README.md)

이 장에서 틀린 곳을 찾으셨다면 [사실 오류로](https://github.com/leaf-kit/book-graph-engineering/issues/new?template=01-fact-error.yml), 상태 라벨이 어긋났다면 [라벨 이의로](https://github.com/leaf-kit/book-graph-engineering/issues/new?template=03-status-label.yml) 적어 주세요.
