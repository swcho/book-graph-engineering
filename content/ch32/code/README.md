# 32장 - 스키마를 바꾸는 날

`6부 - 백본: 상태 관리 엔진` | **한국어** | [English](../../../content_en/ch32/code/README.md) | [책 전체 목차](../../../README.md) | [출처 링크 모음](../../../SOURCES.md)

> 관계 이름 하나를 바꾸는 데 6주가 걸렸습니다.

[31장](../../ch31/code/README.md)은 스키마가 그대로라고 가정했습니다. 같은 필드를 두고 다투는 얘기였죠. 이 장은 필드 자체가 바뀔 때 이야기입니다. 그리고 미리 말씀드리면, 이 장의 절반은 「어떻게 바꾸나」가 아니라 *「언제 옛것을 지워도 되나」*입니다. 그게 훨씬 어려워요.

## 이 장의 절

| 절 | 제목 |
|---|---|
| 32.1 | 무엇이 깨지고 무엇이 안 깨지나 |
| 32.2 | 둘 다 되는 구간을 만든다 |
| 32.3 | 「아무도 안 쓴다」를 어떻게 아나 |
| 32.4 | 이행 중에 데이터가 어긋난다 |
| 32.5 | 계획을 코드로 적는다 |

## 한 장 요약

- 더하는 변경은 안 깨지고 바꾸거나 빼는 변경은 깨집니다. 그리고 위험은 스키마가 아니라 「그 스키마를 어떻게 읽고 있느냐」에 있어요.
- 바꾸기 전에 「누가 읽나」를 세세요. 코드 검색으로는 동적 쿼리를 못 찾습니다. [29장](../../ch29/code/README.md)의 `Reads` 엣지가 여기서 값을 합니다.
- 한 번에 바꾸면 배포 순간에 뭔가 죽습니다. 옛것과 새것이 둘 다 되는 구간을 만드세요. 읽기를 먼저 옮기고 쓰기를 나중에 옮깁니다.
- 백필은 쪼개서 돌리고, 어디까지 했는지 남기고, 멱등하게 만드세요. 그리고 끝난 뒤 한 번 더 돌립니다.
- 이행 중에는 데이터가 어긋납니다. 안 어긋나는 이행은 없어요. 막으려 하지 말고 *세세요*. 불일치가 0이 될 때까지 수축하지 않습니다.
- 수축 기준은 「최근 30일」이 아니라 *「가장 긴 배치 주기」*입니다. 분기 배치면 92일, 연말 정산이면 365일이에요. 크론 표현식을 파싱해서 계산하세요.
- 그리고 드물게 도는 잡일수록 실패 알림을 세게 거세요. 매일 도는 건 내일 알지만 2년에 한 번 도는 건 2년 뒤에 압니다.
- 마이그레이션 계획은 문서가 아니라 코드로 적으세요. 조건을 못 채우면 넘어갈 수 없게요.

## 키워드와 1차 출처

| 키워드 | 상태 | 출처 |
|---|---|---|
| 확장-수축 | [사실상 표준] | [expand and contract](https://martinfowler.com/bliki/ParallelChange.html) |
| 무중단 배포 | [사실상 표준] | [zero-downtime deployment](https://martinfowler.com/bliki/BlueGreenDeployment.html) |
| 양쪽 쓰기 | [사실상 표준] | [dual write](https://martinfowler.com/bliki/ParallelChange.html) |
| 백필 | [사실상 표준] | [backfill](https://cloud.google.com/architecture/database-migration-concepts-principles-part-1) |
| 스키마 진화 | [사실상 표준] | [schema evolution](https://avro.apache.org/docs/current/specification/#schema-resolution) |
| 제약 검증 | [표준] | [SHACL](https://www.w3.org/TR/shacl/) |
| 하위 호환 | [사실상 표준] | [backward compatibility](https://protobuf.dev/programming-guides/proto3/#updating) |

상태 표시는 **[표준]** 공식 명세, **[사실상 표준]** 명세는 없지만 업계가 널리 쓰는 것, **[실험]** 아직 자리를 잡는 중이라는 뜻입니다.

## 예제 실행

<!-- 실행 가이드 시작 - 사람이 쓴 부분. gen-docs.py 가 건드리지 않는다. -->

확인 시점 2026년 8월. Python 3.9 이상.

```bash
cd content/ch32/code
pip install kuzu

python3 ex1_breaking_change.py    # 무엇이 깨지고, 누가 읽고 있나
python3 ex2_expand_contract.py    # 확장-수축 여섯 단계
python3 ex3_when_to_contract.py   # 「아무도 안 쓴다」를 확인하는 법 (의존성 없음)
python3 ex4_dual_read.py          # 이행 중 읽기 전략 넷 (의존성 없음)
python3 ex5_migration_plan.py     # 마이그레이션을 검사 가능한 형태로 (의존성 없음)
```

`ex1` 은 29장에서 만든 `Reads` 엣지를 그대로 씁니다. 그 장을 안 보셨으면
「실행이 무엇을 읽었는지 기록해 둔다」 정도로 이해하시면 됩니다.

`ex5` 는 일부러 `dual-read` 단계에서 막히게 해 두었습니다.
`STATE["불일치_건수"]` 를 0으로 바꾸면 다음 단계로 넘어갑니다.

<!-- 실행 가이드 끝 -->

---

**다음 부에서 만나는 것:** 6부가 백본을 "만드는" 얘기였다면 7부는 "운영하는" 얘기입니다. 느려질 때 어디를 보는지, 비용이 어디서 나는지, 그리고 사람이 「지워 주세요」라고 했을 때 그래프에서 무엇을 지워야 하는지.

---

이전 [31장 두 에이전트가 같은 노드를 동시에 고쳤다](../../ch31/code/README.md) | [전체 목차](../../../README.md) | 다음 [33장 쿼리 플랜을 읽으면 비용이 보인다](../../ch33/code/README.md)

이 장에서 틀린 곳을 찾으셨다면 [사실 오류로](https://github.com/leaf-kit/book-graph-engineering/issues/new?template=01-fact-error.yml), 상태 라벨이 어긋났다면 [라벨 이의로](https://github.com/leaf-kit/book-graph-engineering/issues/new?template=03-status-label.yml) 적어 주세요.
