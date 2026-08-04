# 30장 - 무엇이 언제 바뀌었는지 아무도 모른다

`6부 - 백본: 상태 관리 엔진` | **한국어** | [English](../../../content_en/ch30/code/README.md) | [책 전체 목차](../../../README.md) | [출처 링크 모음](../../../SOURCES.md)

> 「이거 원래 이랬나요?」

6부가 시작됩니다. 5부에서 두 그래프를 하나의 백본으로 합쳤는데, 합쳐 놓고 보니 운영 문제들이 남아 있어요. 그리고 그 문제들이 전부 같은 얼굴을 하고 있습니다. *「지금 상태」만 갖고는 답할 수 없는 질문들*이요.

## 이 장의 절

| 절 | 제목 |
|---|---|
| 30.1 | 현재 상태만 두면 못 하는 질문들 |
| 30.2 | 이벤트가 원본이고 상태는 파생이다 |
| 30.3 | 그때 그래프를 되살리는 두 가지 길 |
| 30.4 | 어떻게 접느냐가 답을 정한다 |
| 30.5 | 로그가 감사 로그가 되려면 |

## 한 장 요약

- 현재 상태만 두면 「지금 뭐죠?」밖에 못 답합니다. 감사, 사고 조사, 품질 지표는 전부 이력이 있어야 답할 수 있어요.
- 「로그를 잘 남기자」로는 안 됩니다. 로그는 빠뜨려도 아무 일이 안 생기거든요. *「기록도 남긴다」가 아니라 「기록이 곧 쓰기다」*로 뒤집어야 합니다.
- 이벤트가 원본이고 상태는 파생입니다. 조회용 뷰는 언제든 다시 만들 수 있어야 하고, 되는지는 실제로 지우고 재생해 봐야 압니다.
- 이벤트에는 「바뀐 것」을 넣으세요. 「바뀐 뒤 전체 상태」를 넣으면 무엇이 바뀌었는지 모르고 동시 변경도 못 합칩니다.
- 재생 시간은 데이터 양이 아니라 스냅숏 주기로 정해집니다. 주기는 복구 목표 시간에서 거꾸로 계산하세요.
- 이벤트를 쌓는 것만으로는 아무것도 안 정해집니다. *어떻게 접을 것인가*가 실제 동작을 정하고, 그건 도메인 결정입니다. 「마지막이 이긴다」를 기본으로 두면 에이전트가 사람을 덮어요.
- 감사 로그가 되려면 「안 고쳤다」를 보일 수 있어야 합니다. 해시 고리는 막지 않고 표가 나게 합니다. 그것만으로 충분한지는 무엇을 지키는지에 달렸습니다.
- 그리고 이벤트에 개인정보를 직접 넣지 마세요. 지울 수 없는 곳에 지워야 하는 것을 넣게 됩니다.

## 키워드와 1차 출처

| 키워드 | 상태 | 출처 |
|---|---|---|
| 이벤트 소싱 | [사실상 표준] | [event sourcing](https://martinfowler.com/eaaDev/EventSourcing.html) |
| 추가 전용 로그 | [사실상 표준] | [append-only log](https://kafka.apache.org/documentation/#design) |
| 재생 | [사실상 표준] | [replay](https://martinfowler.com/eaaDev/EventSourcing.html) |
| 스냅숏 | [사실상 표준] | [snapshot](https://www.sqlite.org/wal.html) |
| 쓰기 전 로그 | [사실상 표준] | [write-ahead log](https://www.postgresql.org/docs/current/wal-intro.html) |
| 명령-조회 분리 | [사실상 표준] | [CQRS](https://martinfowler.com/bliki/CQRS.html) |
| 해시 고리 | [표준] | [hash chain](https://datatracker.ietf.org/doc/html/rfc6962) |
| 감사 추적 | [표준] | [audit trail](https://csrc.nist.gov/pubs/sp/800/53/r5/upd1/final) |

상태 표시는 **[표준]** 공식 명세, **[사실상 표준]** 명세는 없지만 업계가 널리 쓰는 것, **[실험]** 아직 자리를 잡는 중이라는 뜻입니다.

## 예제 실행

<!-- 실행 가이드 시작 - 사람이 쓴 부분. gen-docs.py 가 건드리지 않는다. -->

확인 시점 2026년 8월. Python 3.9 이상.

```bash
cd content/ch30/code
pip install kuzu

python3 ex1_no_history.py        # 현재 상태만 두면 못 하는 질문들
python3 ex2_replay_cost.py       # 재생 값과 스냅숏 (의존성 없음)
python3 ex3_temporal_query.py    # 「그때 그래프」를 되살리는 두 방법
python3 ex4_reducer_conflict.py  # 리듀서가 답을 정한다 (의존성 없음)
python3 ex5_audit_trail.py       # 해시 고리로 위변조를 드러내기 (의존성 없음)
```

`ex2` 는 실행할 때마다 시간이 조금씩 달라집니다. 첫 줄(1만 개)에서 배수가
1 근처거나 그보다 작게 나오는 것도 정상입니다. 스냅숏이 아직 안 찍혔거든요.

`ex3` 의 조회 시간 비교는 이벤트 9개짜리 장난감 규모입니다.
이 숫자로 「재생이 빠르다」고 결론 내지 마세요.

<!-- 실행 가이드 끝 -->

---

**다음 장에서 뒤집히는 것:** 이 장은 변경이 "순서대로" 온다고 가정했습니다. 이벤트 1번 다음에 2번이 오고요. 그런데 두 에이전트가 "동시에" 같은 노드를 고치면 순서가 없습니다. 다음 장은 그 얘기입니다.

---

이전 [29장 하나의 백본](../../ch29/code/README.md) | [전체 목차](../../../README.md) | 다음 [31장 두 에이전트가 같은 노드를 동시에 고쳤다](../../ch31/code/README.md)

이 장에서 틀린 곳을 찾으셨다면 [사실 오류로](https://github.com/leaf-kit/book-graph-engineering/issues/new?template=01-fact-error.yml), 상태 라벨이 어긋났다면 [라벨 이의로](https://github.com/leaf-kit/book-graph-engineering/issues/new?template=03-status-label.yml) 적어 주세요.
