# 체크포인트를 도입할 때 함께 작성해야 하는 것은 무엇인가?

> **답**: **켜는 코드와 지우는 코드를 같은 커밋에 쓴다.**

---

## 1. 왜 「같은 커밋」인가

체크포인터를 켜는 코드는 한 줄이다.

```python
app = b.compile(checkpointer=InMemorySaver())
```

이 한 줄로 얻는 것은 크다 — 중단 지점 복구, 시간 여행 디버깅, human-in-the-loop. 그래서 아무 저항 없이 머지된다. 문제는 **이 한 줄이 만들어 내는 데이터의 수명이 아무 데도 안 적혀 있다**는 것이다.

지우는 코드는 성격이 다르다. 급하지 않고, 데모에 안 나오고, 켠 직후에는 아무 증상도 없다. **그래서 다음 스프린트로 미뤄지고, 그다음 스프린트로 미뤄진다.** 실제로 필요해지는 시점은 이미 수백만 행이 쌓인 뒤이고, 그때는 "지우는 기능을 추가하는 일"이 아니라 "장애 대응"이 되어 있다.

19장의 한 줄 요약이 이걸 말한다.

> 체크포인트는 복구보다 디버깅에 훨씬 자주 씁니다. 제 로그에서 여덟 배였어요. 그리고 **켜는 코드와 지우는 코드를 같은 커밋에 쓰세요.**

같은 커밋이라는 조건이 핵심이다. 별도 티켓으로 쪼개면 절대 안 온다. 같은 커밋에 묶으면 리뷰어가 "보존 기간이 얼마죠?"를 **켜기 전에** 묻게 된다. 이건 기술적 제약이 아니라 **의사결정을 강제하는 장치**다.

---

## 2. 체크포인트는 왜 무한히 쌓이는가 — 슈퍼스텝마다 스냅샷

체크포인트는 실행이 끝날 때 한 번 저장되는 게 아니다. **슈퍼스텝(superstep)이 끝날 때마다 그 시점의 상태를 통째로 저장한다.**

```
슈퍼스텝 0 끝  →  체크포인트 #0  (상태 전체 스냅샷)
슈퍼스텝 1 끝  →  체크포인트 #1  (상태 전체 스냅샷)
슈퍼스텝 2 끝  →  체크포인트 #2  (상태 전체 스냅샷)
       ...
```

예제 2(`ex2_superstep.py`)의 `get_state_history()`가 이걸 그대로 보여 준다. 실행 하나에 스냅샷이 여러 개 나온다.

```python
hist = list(app.get_state_history(cfg))
for i, snap in enumerate(reversed(hist)):
    nxt = ", ".join(snap.next) if snap.next else "(끝)"
    print(f"    {i}. 다음에 갈 노드: {nxt:<14} seen {len(snap.values.get('seen', []))}개")
```

중요한 점 둘.

1. **노드는 델타만 반환하지만, 저장되는 건 상태 전체다.** 노드가 `{"logs": ["..."]}` 만 돌려줘도, 리듀서가 합친 뒤의 **전체 상태**가 새 스냅샷으로 들어간다.
2. **안 바뀐 필드도 매번 다시 저장된다.** 검색 결과 원문 84KB가 상태에 있으면, 그건 슈퍼스텝마다 84KB씩 다시 쓰인다. 증분 저장은 체크포인터 구현이 지원해야만 되는 옵션이다.

즉 저장량은 대략 이렇게 곱해진다.

```
총 저장량 ≈ 상태 크기 × 슈퍼스텝 수 × 실행 횟수 × 보존 기간
                                              ↑
                                       지우는 코드가 없으면 = ∞
```

앞의 세 항은 유한하다. **마지막 항만 무한이 될 수 있고, 그걸 유한하게 만드는 게 지우는 코드다.**

### 예제 4의 산수

`ex4_state_size.py`가 잡은 가정: 슈퍼스텝 14회, 하루 1,200회 실행.

| | 상태 크기 | 실행당 | 하루 |
|---|---|---|---|
| 전부 담으면 | 약 135KB | 약 1.9MB | 약 2.3GB |
| 필요한 것만 담으면 | 약 2.3KB | 약 33KB | 약 0.04GB |

하루 2.3GB다. 지우지 않으면 한 달에 70GB, 1년이면 800GB가 넘는다. 상태를 줄이면 이 기울기가 수십 배 완만해지지만, **기울기가 완만해질 뿐 여전히 단조 증가다.** 상태 다이어트는 지우는 코드의 대체재가 아니다.

---

## 3. 지우지 않으면 무슨 일이 생기는가

### 3-1. 스토리지 비용 — 사실 가장 덜 중요하다

`ex4_state_size.py`의 결론이 솔직하다.

> 한 가지 덧붙이면, 저장비 자체는 큰 돈이 아니다. **월 1,600원**이다.
> 진짜 값은 «직렬화 시간»이다.

GB당 월 25원 기준이면 저장비만으로는 아무도 안 움직인다. 그러니 "비용 때문에 지워야 한다"는 논거로 팀을 설득하려 하면 실패한다. 진짜 이유는 아래 셋이다.

### 3-2. 개인정보 보존 기간 위반 — 되돌릴 수 없는 종류의 사고

이게 제일 무겁다. 상태에는 보통 이런 게 들어간다.

- 사용자가 입력한 질문 원문 (이름, 연락처, 계좌번호가 섞여 들어온다)
- 대화 이력 전체 (`messages`)
- 예제 3처럼 사업자번호·담당자명 같은 업무 데이터

그리고 이게 **슈퍼스텝마다 복제된다.** 즉 사용자가 이름 한 번 입력하면 그 이름은 체크포인트 14벌에 들어가 있다.

- **삭제 요청(GDPR 17조 / 개인정보보호법 파기 의무)이 오면 무엇을 지워야 하는지부터 모른다.** 애플리케이션 DB에서 사용자 행 하나 지우는 걸로 끝나지 않는다. 체크포인트 테이블 전체를 훑어야 한다.
- **보존 기간 초과 보관 자체가 위반이다.** "지울 방법이 없어서 남아 있었다"는 해명이 되지 않는다.
- **삭제 코드는 사고가 난 뒤에 급히 짜면 반드시 빠뜨린다.** 체크포인트 본체(`checkpoints`)는 지웠는데 중간 쓰기(`checkpoint_writes`, `checkpoint_blobs`)는 남는 식이다. 그래서 프레임워크가 제공하는 `delete_thread()`를 쓰는 게 안전하다 — 관련 테이블을 한꺼번에 정리한다.

### 3-3. 조회 성능 저하 — 디버깅 도구가 먼저 죽는다

여기에 역설이 있다. **체크포인트를 켠 주된 이유는 디버깅인데(저자 로그 기준 복구 대비 8배), 안 지우면 그 디버깅이 제일 먼저 망가진다.**

- `get_state_history()`와 `.list()`는 보통 `thread_id`로 인덱스를 타지만, 테이블이 수천만 행이 되면 인덱스 자체가 커지고 캐시 히트가 떨어진다.
- 스냅샷 하나가 1.9MB면 이력 20개를 훑는 것만으로 38MB를 역직렬화한다.
- Postgres 기준으로는 매 슈퍼스텝의 INSERT가 만드는 **테이블 팽창(bloat)과 VACUUM 부담**이 붙는다. 백업 시간, 복제 지연도 같이 늘어난다.

### 3-4. 실행 자체가 느려진다

18장에서 잰 체크포인트 오버헤드 40~120ms는 **실행 경로 위에 있는 지연**이다. 상태가 크고 테이블이 무거워지면 이게 몇 배가 되고, 그건 그대로 사용자가 기다리는 시간이 된다.

---

## 4. 무엇을 「지우는 코드」라고 부르는가

한 줄로는 안 된다. 최소한 이 넷이 같은 커밋에 있어야 한다.

| # | 항목 | 내용 |
|---|---|---|
| 1 | **보존 기간(TTL)을 숫자로 명시** | "30일" 처럼 코드나 설정에 적힌 값. 문서의 문장이 아니라 실행되는 값이어야 한다. |
| 2 | **주기적 정리(sweeper)** | 만료된 thread를 실제로 지우는 배치/크론/백그라운드 작업. |
| 3 | **단건 삭제 경로** | 사용자 삭제 요청이 왔을 때 특정 `thread_id`를 즉시 지우는 API. |
| 4 | **삭제가 도는지 확인할 수단** | 삭제 건수 메트릭이나 로그. 조용히 멈춘 정리 작업은 없는 것과 같다. |

### thread_id — 삭제의 단위

LangGraph에서 체크포인트를 묶는 단위는 **thread**이고, `config`의 `configurable.thread_id`로 식별한다.

```python
cfg = {"configurable": {"thread_id": "dbg"}}
out = app.invoke({"쓴돈": 0, "기록": [], "회차": 0}, cfg)
```

`thread_id` 없이는 체크포인터가 상태를 저장할 수도, 인터럽트 후 재개할 수도 없다. 그리고 **삭제도 이 단위로 이뤄진다.**

여기서 실무 함정 하나. `thread_id`를 랜덤 UUID로 던져 놓고 어디에도 기록하지 않으면, 나중에 "이 사용자의 thread가 무엇인가"를 되짚을 수 없다. **`thread_id ↔ 사용자/세션` 매핑을 애플리케이션 쪽에 남겨 두는 것도 「지우는 코드」의 일부다.** 이것도 켤 때 같이 넣어야 한다.

### 체크포인터 구현별 사정

| 구현 | 패키지 | 성격 | 지우는 얘기 |
|---|---|---|---|
| `InMemorySaver` (구 `MemorySaver`) | `langgraph-checkpoint` (내장) | 프로세스 메모리 | 프로세스가 죽으면 사라진다. 대신 **장수 프로세스에서는 메모리 누수**가 된다. |
| `SqliteSaver` / `AsyncSqliteSaver` | `langgraph-checkpoint-sqlite` | 로컬 파일 | 파일이 계속 커진다. 지워도 `VACUUM` 전에는 파일 크기가 안 줄어든다. |
| `PostgresSaver` / `AsyncPostgresSaver` | `langgraph-checkpoint-postgres` | 운영 권장 | 여기가 진짜 문제 지점. 여러 테이블에 나뉘어 쌓인다. |

예제들이 `InMemorySaver`를 쓰는 건 예제이기 때문이다. **`InMemorySaver`로 개발하다 `PostgresSaver`로 바꾸는 순간이 「지우는 코드」가 반드시 필요해지는 순간**인데, 그 교체는 보통 설정 한 줄짜리 PR로 지나간다. 이게 이 카드가 경고하는 바로 그 지점이다.

### `delete_thread()` — 표준 인터페이스에 들어 있다

모든 체크포인터는 `langgraph.checkpoint.base.BaseCheckpointSaver` 인터페이스를 따르고, 필수 메서드에 삭제가 포함돼 있다.

| 메서드 | 하는 일 |
|---|---|
| `.put` / `.aput` | 체크포인트 저장 |
| `.put_writes` / `.aput_writes` | 노드의 중간 출력 저장 |
| `.get_tuple` / `.aget_tuple` | 해당 config의 체크포인트 조회 |
| `.list` / `.alist` | 조건에 맞는 체크포인트 나열 |
| **`.delete_thread` / `.adelete_thread`** | **해당 thread의 모든 체크포인트와 writes 삭제** |

```python
# 단건 삭제 — 사용자 삭제 요청 대응
checkpointer.delete_thread(thread_id)

# 비동기 그래프(.ainvoke/.astream)를 쓴다면 async 쪽을 써야 한다
await checkpointer.adelete_thread(thread_id)
```

> **주의**: sync 그래프에서 async 체크포인터의 `delete_thread`를 실수로 호출하면 `RuntimeWarning: coroutine 'BaseCheckpointSaver.delete_thread' was never awaited` 가 뜨고 **아무것도 안 지워진 채 조용히 넘어간다.** 삭제 코드는 "돌았다"가 아니라 "몇 건 지웠다"를 확인해야 하는 이유다.

`delete_thread`가 인터페이스 필수 메서드라는 사실 자체가 힌트다. **프레임워크 설계자도 "삭제는 부가 기능이 아니라 체크포인터의 기본 책무"로 본 것이다.**

### 배치 정리 — TTL 설정

LangGraph Platform을 쓴다면 `langgraph.json`에 보존 정책을 선언할 수 있다.

```json
{
  "checkpointer": {
    "ttl": {
      "strategy": "delete",
      "default_ttl": 43200,
      "sweep_interval_minutes": 60
    }
  }
}
```

| 필드 | 의미 |
|---|---|
| `strategy` | `"delete"` 면 만료 시 실제로 지운다 |
| `default_ttl` | **분 단위** 유휴 시간. `1440` = 24시간, `43200` = 30일 |
| `sweep_interval_minutes` | 백그라운드 sweeper가 만료 thread를 훑는 주기 |

동작상 알아야 할 것들.

- **TTL이 지나는 즉시 지워지지 않는다.** sweeper가 타이머로 돌면서 만료된 thread를 찾는다. 즉 실제 삭제는 `default_ttl + 최대 sweep_interval` 뒤다. 보존 기간 규정을 빠듯하게 맞춰 놓으면 이 지연 때문에 넘길 수 있다.
- **만료 시계는 마지막 활동 기준으로 리셋된다.** thread 생성 시점이 아니라 **가장 최근 체크포인트 생성 시점**부터 센다. 계속 쓰는 대화는 계속 안 지워진다.
- **소급 적용되지 않는다.** 설정을 배포한 뒤에 만들어진 thread에만 붙는다. **이미 쌓인 것은 별도로 지워야 한다** — 이게 "나중에 하면 늦는다"의 구체적 형태다.
- **지워지는 것**: thread 레코드, 모든 체크포인트, 모든 writes, Platform run 레코드.
- **안 지워지는 것**: **LangSmith 트레이스.** 별개 백엔드이고 자체 보존 정책을 따른다. 개인정보를 지운다고 생각했는데 트레이스에 그대로 남아 있는 경우가 여기서 나온다.

Platform을 안 쓰고 `PostgresSaver`만 직접 쓴다면 이 sweeper가 **없다.** 그러면 직접 짜야 한다.

```python
# 개념 예시 — 만료된 thread를 골라 delete_thread 를 돌린다
for tid in find_expired_thread_ids(older_than_days=30):
    checkpointer.delete_thread(tid)
    metrics.incr("checkpoint.deleted")   # 4번 항목: 도는지 확인할 수단
```

핵심은 방식이 아니다. **"만료 판정 기준"과 "실제로 지우는 실행 경로"가 켜는 커밋 안에 같이 있느냐**다.

---

## 5. 곁가지 — 상태 다이어트는 지우는 코드와 짝이다

`ex4_state_size.py`의 판별 질문 하나가 저장량 전체를 좌우한다.

> **"다음 노드가 이걸 읽는가?"** — 아니면 상태에 두지 마라.

| 필드 | 크기 | 상태에 둘까 |
|---|---|---|
| 검색 결과 원문 | 84,000B | 아니오 (요약만 있으면 된다) |
| 중간 계산 캐시 | 31,000B | 아니오 (같은 노드 안에서만 쓴다) |
| 모델 원본 응답 | 12,000B | 아니오 (로그에만 쓴다) |
| 검색 결과 주소 | 180B | 예 |
| 재시도 횟수 | 8B | 예 (라우팅이 읽는다) |

저자 기준선은 **8KB** — 상태 하나가 이걸 넘으면 무엇을 뺄지 찾는다.

그런데 이 둘의 관계를 정확히 잡아야 한다.

- **상태 다이어트**는 기울기를 줄인다 (슈퍼스텝당 몇 KB인가).
- **지우는 코드**는 총량에 상한을 건다 (며칠치를 들고 있는가).

둘 다 필요하다. 상태를 아무리 줄여도 무한히 보관하면 언젠가 터지고, 아무리 잘 지워도 스냅샷이 1.9MB면 실행 지연은 그대로다. 그리고 **개인정보 보존 기간은 다이어트로는 절대 해결되지 않는다** — 8바이트짜리 필드에 든 개인정보도 개인정보다.

---

## 6. 한 줄 정리

| 질문 | 답 |
|---|---|
| 체크포인트는 언제 저장되나? | **슈퍼스텝마다.** 실행 끝에 한 번이 아니다 |
| 무엇이 저장되나? | 노드는 델타를 반환하지만 **상태 전체 스냅샷**이 저장된다 |
| 왜 무한히 쌓이나? | 슈퍼스텝 × 실행 횟수만큼 늘고, 지우지 않으면 보존 기간이 무한이라서 |
| 안 지우면 뭐가 문제인가? | ① 개인정보 보존 기간 위반 ② 조회 성능 저하(디버깅이 먼저 죽는다) ③ 직렬화 지연 ④ 스토리지 비용(가장 덜 중요) |
| 삭제 단위는? | **thread** — `configurable.thread_id` |
| 삭제 API는? | `delete_thread()` / `adelete_thread()` — `BaseCheckpointSaver` **필수** 메서드 |
| 보존 정책은? | TTL(분 단위) + sweeper. **소급 적용 안 됨** |
| 그래서 결론은? | **켜는 코드와 지우는 코드를 같은 커밋에 쓴다** |

## 참고

- [LangGraph Checkpointers — BaseCheckpointSaver 인터페이스와 구현체](https://docs.langchain.com/oss/python/langgraph/checkpointers)
- [LangGraph Persistence — 체크포인트, thread, 상태 이력](https://docs.langchain.com/oss/python/langgraph/persistence)
- [BaseCheckpointSaver.delete_thread — API 레퍼런스](https://reference.langchain.com/python/langgraph.checkpoint/base/BaseCheckpointSaver/delete_thread)
- [How Thread TTL Works with the "Delete" Strategy (LangChain Support)](https://support.langchain.com/articles/9574139807-how-thread-ttl-works-with-the-delete-strategy)
- [Understanding Checkpointers, Databases, API Memory and TTL (LangChain Support)](https://support.langchain.com/articles/6253531756-understanding-checkpointers-databases-api-memory-and-ttl)
- [`delete_thread` was never awaited — langgraph issue #4880](https://github.com/langchain-ai/langgraph/issues/4880)
- [LangGraph Graph API — StateGraph / reducer / superstep](https://docs.langchain.com/oss/python/langgraph/graph-api)
