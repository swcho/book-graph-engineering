# 상태 크기를 줄이는 두 가지 방법

> **Q.** 상태 크기를 줄이는 두 가지 방법은 무엇인가?
>
> **A.** 원문을 밖에 두고 상태에는 주소만 넣기(24장 오프로딩), 또는 체크포인터가 바뀐 것만 저장하게 하기(구현이 지원해야 함)다.

---

## 0. 왜 이 질문이 나오는가

19장 `ex4_state_size.py`가 재는 것은 「필드 하나의 크기」가 아니라 **「그 크기 × 슈퍼스텝 수」**다.

```python
FIELDS = [
    ("질문",            220,   "다음 노드가 읽는다",     True),
    ("검색 결과 원문",   84_000, "요약만 있으면 된다",     False),
    ("검색 결과 주소",     180,  "필요하면 다시 읽는다",   True),
    ("검색 결과 요약",   1_800,  "다음 노드가 읽는다",     True),
    ...
]
SUPERSTEPS = 14
RUNS_PER_DAY = 1_200
```

핵심은 예제의 이 문장이다.

> 「검색 결과 원문」이 84KB 다. 이게 슈퍼스텝마다 다시 저장된다. **안 바뀌는데도 매번 통째로.**

체크포인트는 슈퍼스텝 경계마다 남는다. 그러니 상태에 84KB짜리 값이 하나 들어가 있으면, 그 값이 첫 슈퍼스텝 이후로 한 글자도 안 바뀌어도 14번 다시 직렬화되고 14번 다시 기록된다. 그리고 예제가 마지막에 못을 박는 대로, **진짜 비용은 저장비가 아니라 직렬화 시간**이다.

> 저장비 자체는 큰 돈이 아니다. 월 1,600원이다. 진짜 값은 「직렬화 시간」이다. 1.9MB 를 슈퍼스텝마다 쓰고 읽으면 지연이 붙고, 그게 사용자가 기다리는 시간이 된다. 18장에서 잰 체크포인트 40~120ms 가 여기서 몇 배가 된다.

이 문제에 대한 대처가 예제에 정확히 두 줄로 적혀 있다.

```
1. 상태에 안 넣는다 — 원문은 밖에 두고 상태에는 「주소」만 (24장 오프로딩)
2. 체크포인터가 「바뀐 것만」 저장하게 한다 — 구현이 지원해야 한다
```

---

## 1. 방법 1 — 오프로딩: 값 대신 주소를 넣는다

### 패턴

큰 원문(검색 결과 전문, 업로드된 문서, 모델 원본 응답, 이미지 바이트)을 외부 저장소(S3/GCS, DB, Redis 같은 캐시, 로컬 파일시스템)에 두고, 상태에는 **그걸 다시 찾아올 수 있는 최소 정보**만 남긴다.

- **키 또는 URI** — `s3://bucket/run/abc/doc-1.txt`
- **해시** — 내용이 바뀌지 않았음을 확인하는 용도
- **요약/메타** — 다음 노드가 「판단」에 실제로 쓰는 압축본, 길이·출처 같은 라벨

### 상태 타입 예시

```python
from typing import Annotated, TypedDict
import operator


class DocRef(TypedDict):
    uri: str        # s3://raw/run-2026-08-15/doc-3.txt
    sha256: str     # 내용 동일성 확인
    n_bytes: int    # 페치 전에 비용을 가늠하는 용도
    source: str     # 출처 (리듀서가 판단 근거로 쓸 수도 있다)


class S(TypedDict):
    질문: str
    # 84KB 원문이 아니라 180B 참조만 쌓는다
    문서들: Annotated[list[DocRef], operator.add]
    # 다음 노드가 실제로 읽는 것은 요약뿐
    요약: Annotated[list[str], operator.add]
```

노드는 이렇게 나뉜다.

```python
def 검색(s):
    text = search_api(s["질문"])                 # 84KB
    uri = blob_store.put(text)                   # 밖에 둔다
    return {
        "문서들": [{"uri": uri,
                    "sha256": sha256(text),
                    "n_bytes": len(text),
                    "source": "web"}],
        "요약": [summarize(text)],               # 1.8KB
    }


def 분석(s):
    # 원문이 정말 필요한 노드만 그때 가서 읽는다
    text = blob_store.get(s["문서들"][-1]["uri"])
    ...
```

19장 예제 기준으로 84,000B가 180B로 줄어든다. **약 466배**다. 예제 전체로는 전부 담을 때 135,748B, 필요한 것만 담을 때 2,348B — 약 58배 차이다.

### 얻는 것

| 얻는 것 | 왜 |
|---|---|
| 체크포인트 크기 급감 | 슈퍼스텝마다 반복 저장되던 덩어리가 사라진다 |
| 직렬화/역직렬화 시간 급감 | 실제로 사용자가 기다리는 지연이 줄어든다 (18장의 40~120ms가 몇 배로 불어나던 걸 막는다) |
| 의존성이 타입에 드러난다 | 예제 표현대로 「상태가 작아지면 이 노드가 무엇에 의존하는가가 타입만 봐도 보인다」 |
| 스트리밍/전송 비용 감소 | 상태를 클라이언트로 흘려보내는 경우 전송량도 같이 준다 |
| 리듀서 병합 비용 감소 | 병렬 노드가 합칠 때도 작은 값만 합친다 |

### 잃는 것 (공짜가 아니다)

| 잃는 것 | 구체적으로 |
|---|---|
| **외부 저장소 의존** | 장애 지점이 하나 늘어난다. 체크포인트는 멀쩡한데 blob 스토어가 죽으면 재개해도 원문을 못 읽는다 |
| **참조 무결성** | URI는 살아 있는데 객체가 지워진 「끊어진 참조」가 생길 수 있다. 상태만 보고는 알 수 없다 |
| **수명 관리** | 외부 저장소의 TTL/라이프사이클 정책이 체크포인트 보존 기간보다 짧으면, 3일 전 체크포인트로 시간 여행했을 때 원문이 이미 없다 |
| **fetch 비용/지연** | 원문을 읽는 노드마다 네트워크 왕복이 붙는다. 여러 노드가 같은 원문을 읽으면 중복 페치가 된다 (노드 내 캐시나 「읽는 노드를 하나로 모으기」로 완화) |
| **재현성이 외부에 종속** | 19장 `ex5`의 시간 여행(`get_state_history` + `update_state` 후 재실행)은 그 시점의 **원문이 그대로 남아 있어야** 재현된다. 원문이 변경되거나 삭제되면 「같은 상태에서 다시 돌렸는데 답이 다르다」가 된다. → `sha256`을 같이 저장해 두면 최소한 「달라졌다」는 걸 감지는 할 수 있다 |
| 보안 경계가 늘어난다 | 민감 원문이 그래프 밖에 나가므로 접근 제어·암호화를 별도로 챙겨야 한다 |

정리하면 오프로딩은 **「크기 문제」를 「수명·무결성 문제」로 바꾸는 거래**다. 예제가 "1번이 확실하다"고 한 건 효과가 확실하다는 뜻이지 공짜라는 뜻이 아니다.

---

## 2. 방법 2 — 증분 저장: 체크포인터가 「바뀐 것만」 저장하게 한다

### 아이디어

상태는 채널(필드) 단위로 버전이 매겨진다. 어떤 슈퍼스텝에서 실제로 갱신된 채널은 보통 한둘뿐이다. 그렇다면 체크포인트를 통짜로 다시 쓰지 말고, **이번에 버전이 올라간 채널의 값만 새로 직렬화해서 저장**하고, 안 바뀐 채널은 이전에 저장해 둔 값을 그대로 가리키게 하면 된다.

즉 체크포인트 레코드는 **「채널 이름 → 버전」 맵**만 갖고, 실제 값은 `(채널, 버전)`으로 찾아가는 별도 저장소에 두는 구조다. 같은 84KB 원문이 14 슈퍼스텝 내내 안 바뀌면 **한 번만** 기록되고, 이후 13번의 체크포인트는 같은 `(channel, version)`을 가리키기만 한다.

핵심 단서가 답에 붙어 있다: **「구현이 지원해야 한다」.** 이건 사용자가 코드로 켜는 옵션이 아니라, 고른 체크포인터가 그렇게 짜여 있느냐의 문제다.

### LangGraph 구현별 확인 결과

아래는 `langchain-ai/langgraph` 저장소 `main` 브랜치 소스를 직접 읽고 확인한 것이다.

| 체크포인터 | 채널 단위 분리 저장? | 근거 |
|---|---|---|
| `PostgresSaver` / `AsyncPostgresSaver` | **예** | `checkpoint_blobs` 테이블, PK `(thread_id, checkpoint_ns, channel, version)` |
| `InMemorySaver` | **예** | `blobs` dict, 키 `(thread_id, checkpoint_ns, channel, version)` |
| `SqliteSaver` | **아니오** | `checkpoints.checkpoint`에 통짜 BLOB 하나, `new_versions` 인자를 아예 안 씀 |
| 그 외 (Redis 등) | *확인 안 함* | 소스를 확인하지 않았으므로 단정하지 않는다 |

#### (a) PostgresSaver — 채널별 blob 테이블

`libs/checkpoint-postgres/.../postgres/base.py`의 마이그레이션 SQL:

```sql
CREATE TABLE IF NOT EXISTS checkpoint_blobs (
    thread_id TEXT NOT NULL,
    checkpoint_ns TEXT NOT NULL DEFAULT '',
    channel TEXT NOT NULL,
    version TEXT NOT NULL,
    type TEXT NOT NULL,
    blob BYTEA,
    PRIMARY KEY (thread_id, checkpoint_ns, channel, version)
);
```

기본키가 `(thread_id, checkpoint_ns, channel, version)`이다. **채널 하나의 특정 버전 값이 딱 한 행**이다. 그리고 upsert는 이렇다.

```sql
INSERT INTO checkpoint_blobs (thread_id, checkpoint_ns, channel, version, type, blob)
VALUES (%s, %s, %s, %s, %s, %s)
ON CONFLICT (thread_id, checkpoint_ns, channel, version) DO NOTHING
```

`DO NOTHING` — 같은 버전이 이미 있으면 **다시 쓰지 않는다**. 그리고 `put()`에서 쓰기 대상을 고르는 부분:

```python
# inline primitive values in checkpoint table
# others are stored in blobs table
blob_values = {}
for k, v in checkpoint["channel_values"].items():
    if isinstance(v, _DeltaSnapshot):
        blob_values[k] = copy["channel_values"].pop(k)
        copy["channel_values"][k] = True
    elif v is None or isinstance(v, (str, int, float, bool)):
        pass                       # 작은 원시값은 checkpoints JSONB 안에 그대로
    else:
        blob_values[k] = copy["channel_values"].pop(k)   # 큰 값은 빼서 blobs로

with self._cursor(pipeline=True) as cur:
    if blob_versions := {
        k: v for k, v in new_versions.items() if k in blob_values
    }:
        cur.executemany(self.UPSERT_CHECKPOINT_BLOBS_SQL, self._dump_blobs(...))
```

읽어야 할 두 가지:

1. `new_versions` — **이번 슈퍼스텝에서 새로 버전이 올라간 채널만** 담긴 맵. 이걸로 필터링하므로 안 바뀐 채널은 직렬화조차 안 한다 (`_dump_blobs`는 `versions.items()`만 순회한다).
2. 원시값(str/int/float/bool/None)은 `blob_values`로 빠지지 않고 `checkpoints` 테이블의 JSONB에 인라인으로 남는다. 작은 값은 조인 비용이 더 비싸기 때문이다.

결과적으로 Postgres에서는 **안 바뀐 84KB 원문이 슈퍼스텝마다 재직렬화되지 않는다**. 채널 하나가 한 번 쓰이고, 이후 체크포인트들은 같은 버전 문자열을 가리킬 뿐이다.

#### (b) InMemorySaver — 같은 구조를 메모리에서

`libs/checkpoint/.../memory/__init__.py`:

```python
blobs: dict[
    tuple[
        str, str, str, str | int | float
    ],  # thread id, checkpoint ns, channel, version
    tuple[str, bytes],
]
```

```python
def put(self, config, checkpoint, metadata, new_versions):
    c = checkpoint.copy()
    ...
    values: dict[str, Any] = c.pop("channel_values")
    for k, v in new_versions.items():                 # ← 새 버전만
        self.blobs[(thread_id, checkpoint_ns, k, v)] = (
            self.serde.dumps_typed(values[k]) if k in values else ("empty", b"")
        )
    self.storage[thread_id][checkpoint_ns].update({...})
```

`channel_values`를 체크포인트 본체에서 **떼어 내고**(`c.pop`), `new_versions`에 든 채널만 직렬화한다. 나머지 체크포인트 메타(`c`)만 storage에 넣는다. 즉 InMemorySaver도 채널별 증분 방식이다. 19장 `ex2`, `ex5`가 쓰는 게 바로 이 세이버다.

#### (c) SqliteSaver — 통짜 저장

`libs/checkpoint-sqlite/.../sqlite/__init__.py`의 테이블은 둘뿐이고, 채널 blob 테이블이 없다.

```sql
CREATE TABLE IF NOT EXISTS checkpoints (
    thread_id TEXT NOT NULL,
    checkpoint_ns TEXT NOT NULL DEFAULT '',
    checkpoint_id TEXT NOT NULL,
    parent_checkpoint_id TEXT,
    type TEXT,
    checkpoint BLOB,
    metadata BLOB,
    PRIMARY KEY (thread_id, checkpoint_ns, checkpoint_id)
);
```

그리고 `put()`:

```python
def put(self, config, checkpoint, metadata, new_versions) -> RunnableConfig:
    thread_id = config["configurable"]["thread_id"]
    checkpoint_ns = config["configurable"]["checkpoint_ns"]
    type_, serialized_checkpoint = self.serde.dumps_typed(checkpoint)   # ← 통째로
    ...
    cur.execute(
        "INSERT OR REPLACE INTO checkpoints (thread_id, checkpoint_ns, checkpoint_id, "
        "parent_checkpoint_id, type, checkpoint, metadata) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (..., serialized_checkpoint, serialized_metadata),
    )
```

**`new_versions` 파라미터를 받기만 하고 본문에서 한 번도 쓰지 않는다.** `checkpoint`(= `channel_values` 포함) 전체를 `dumps_typed`로 통째 직렬화해 한 행에 넣는다. 시그니처는 같아도 저장 방식은 다르다.

→ **같은 그래프, 같은 상태 타입이라도 체크포인터를 SqliteSaver에서 PostgresSaver로 바꾸면 「매 슈퍼스텝 84KB 재기록」이 「전체 실행 중 84KB 한 번」으로 바뀐다.** 답에 붙은 「구현이 지원해야 한다」가 바로 이 얘기다.

#### (d) 덧붙임 — DeltaChannel (아직 안정화 전)

Postgres `put()` 코드에 나온 `_DeltaSnapshot`은 최근 LangGraph에 들어온 한 단계 더 나아간 장치다. 위 (a)~(c)가 **「채널 단위」 증분**이라면, `DeltaChannel`은 **채널 값 「내부」의 증분**이다. 대략 이렇게 동작한다.

- 갱신마다 체크포인트에는 **센티널만** 남기고 실제 변화분은 `checkpoint_writes` 행으로 쌓는다.
- `snapshot_frequency`마다 한 번씩 전체 값을 `_DeltaSnapshot` blob으로 적는다.
- 값을 복원할 때는 `get_delta_channel_history`가 부모 체인을 거슬러 올라가며 `_DeltaSnapshot` 조상을 만날 때까지 write를 누적한다.

대신 대가가 명확하다. 소스 주석이 직접 경고하는 대로, 조상 체크포인트나 그 write를 지우면(`prune`의 `keep_latest`, `delete_for_runs`) **체인이 끊겨 델타 채널이 조용히 빈 값으로 복원된다 — 예외조차 안 난다.** `copy_thread`도 부모 체인 전체를 복사해야 한다. 그리고 소스 자체가 "delta-channel design이 안정화되는 동안 내용이 바뀔 수 있다"고 밝히고 있으므로, 지금 프로덕션 기준으로 삼기엔 이르다.

### 증분 저장의 얻는 것 / 잃는 것

| | |
|---|---|
| 얻는 것 | 코드 변경 없이(체크포인터만 바꿔서) 반복 직렬화가 사라진다. 상태 타입·노드 로직을 안 건드려도 된다 |
| 잃는 것 | (1) 「최신 상태 읽기」가 조인/다중 조회가 된다 — 쓰기를 줄이고 읽기를 늘린 거래. (2) 채널 하나가 **여전히 84KB**라서, 그 채널이 실제로 바뀌는 슈퍼스텝에는 그대로 84KB를 쓴다. (3) 가비지 컬렉션/보존 정책이 복잡해진다 — 오래된 `(channel, version)` 행을 언제 지울지 판단해야 한다. DeltaChannel까지 가면 체인 절단 위험이 붙는다 |

**중요:** 증분 저장은 「안 바뀌는 큰 값」에만 듣는다. 매 슈퍼스텝 바뀌는 큰 값(예: 계속 누적되는 메시지 리스트)에는 효과가 거의 없다.

---

## 3. 선택 기준 — 순서가 중요하다

이 두 가지는 **1순위가 아니다.** 예제가 표로 먼저 보여 준 것은 필터다.

```
1순위. 애초에 상태에 넣지 않는다  ← 「다음 노드가 읽는가?」
   ↓ 그래도 다음 노드가 읽어야 하는데 크다면
2순위. 오프로딩 — 값 대신 주소를 넣는다
   ↓ 그래도 상태 안에 있어야 하고, 자주 안 바뀐다면
3순위. 증분 저장 — 체크포인터를 채널 단위로 저장하는 구현으로
```

### 1순위: 「다음 노드가 읽는가」 필터

`ex4`의 표에서 `False`로 걸러진 것들을 보라.

| 필드 | 크기 | 상태에 둘까 | 왜 아닌가 |
|---|---|---|---|
| 검색 결과 원문 | 84,000B | 아니오 | 요약만 있으면 된다 |
| 모델 원본 응답 | 12,000B | 아니오 | **로그에만 쓴다** |
| 중간 계산 캐시 | 31,000B | 아니오 | **같은 노드 안에서만 쓴다** |
| 실행 로그 | 6,400B | 아니오 | **사람이 나중에 본다** |

「모델 원본 응답」, 「중간 계산 캐시」, 「실행 로그」는 오프로딩할 필요도 없다. **다음 노드가 아예 안 읽으니까 상태에 넣을 이유가 없다.** 로그로 보내고, 로컬 변수로 두고, 관측 시스템(트레이싱)으로 보내면 된다. 이 셋만 빼도 49,400B가 사라진다.

오프로딩과 증분 저장은 **이 필터를 통과했는데도 여전히 큰 값**에 대한 대책이다. 필터를 안 돌리고 오프로딩부터 하면, 애초에 없어도 될 값을 굳이 S3에 넣고 URI를 관리하는 헛수고를 하게 된다.

### 2 vs 3 — 어느 쪽?

| 상황 | 고를 것 |
|---|---|
| 값이 크고, 소수의 노드만 읽는다 | **오프로딩**. 읽는 노드에서만 fetch |
| 값이 크고, 거의 안 바뀐다 | 오프로딩이 여전히 낫지만, 저장소를 못 늘리면 **증분 저장**으로 완화 |
| 값이 크고, 매 슈퍼스텝 바뀐다 | 둘 다 별 효과 없음. **값 자체를 줄여야 한다** (요약, 윈도잉, 트리밍) |
| 코드를 못 건드린다 (운영 중) | **증분 저장**. 체크포인터 교체만으로 효과가 난다 |
| 외부 저장소를 못 쓴다 | **증분 저장** |

두 방법은 배타적이지 않다. 원문은 오프로딩하고, 남은 요약/메시지들은 채널 단위 증분 저장 체크포인터에 맡기는 조합이 실무에서 가장 흔하다.

### 저자의 임계선

> 제 기준: 상태 하나가 8KB 를 넘으면 무엇을 뺄지 찾는다.

8KB는 규격이 아니라 **점검 트리거**다. 넘으면 무조건 고치라는 게 아니라, 넘었으니 표를 한 번 그려 보라는 신호다.

---

## 4. 흔히 하는 착각

| 착각 | 실제 |
|---|---|
| 「저장비가 아까워서 줄인다」 | 아니다. `ex4` 계산으로 월 1,600원이다. **줄이는 이유는 직렬화 지연**이고, 그게 사용자 대기 시간이 된다 |
| 「체크포인터는 다 똑같이 저장한다」 | 아니다. 같은 `put(config, checkpoint, metadata, new_versions)` 시그니처를 쓰면서 SqliteSaver는 `new_versions`를 무시하고 통째 저장, PostgresSaver/InMemorySaver는 채널별로 나눠 저장한다 |
| 「오프로딩하면 상태 관리가 단순해진다」 | 반대다. 크기 문제가 **수명·무결성 문제**로 바뀐다. 시간 여행 재현성이 외부 데이터 보존에 종속된다 |
| 「증분 저장을 켜면 큰 값이 작아진다」 | 아니다. 바뀌는 슈퍼스텝에는 그대로 다 쓴다. **반복 쓰기**만 없앤다 |
| 「상태를 줄이는 건 성능 최적화일 뿐」 | 부수 효과가 더 크다. 「상태가 작아지면 이 노드가 무엇에 의존하는가가 타입만 봐도 보인다」 — 설계 가독성이 같이 올라간다 |

---

## 5. 한 줄 정리

**먼저 「다음 노드가 읽는가」로 걸러 내고, 그래도 커야 하는 값은 밖에 두고 주소만 넣거나(오프로딩 — 크기 문제를 수명·무결성 문제로 바꾼다), 채널별 증분 저장을 지원하는 체크포인터를 쓴다(LangGraph 기준 PostgresSaver·InMemorySaver는 지원, SqliteSaver는 통짜 저장).**

---

## 참고

- [LangGraph — Persistence](https://docs.langchain.com/oss/python/langgraph/persistence)
- [LangGraph — Graph API (state / reducer / superstep)](https://docs.langchain.com/oss/python/langgraph/graph-api)
- [`checkpoint-postgres/langgraph/checkpoint/postgres/base.py`](https://github.com/langchain-ai/langgraph/blob/main/libs/checkpoint-postgres/langgraph/checkpoint/postgres/base.py) — `checkpoint_blobs` 스키마, `UPSERT_CHECKPOINT_BLOBS_SQL`, `_dump_blobs`
- [`checkpoint-postgres/langgraph/checkpoint/postgres/__init__.py`](https://github.com/langchain-ai/langgraph/blob/main/libs/checkpoint-postgres/langgraph/checkpoint/postgres/__init__.py) — `put()`의 `new_versions` 필터, 원시값 인라인
- [`checkpoint/langgraph/checkpoint/memory/__init__.py`](https://github.com/langchain-ai/langgraph/blob/main/libs/checkpoint/langgraph/checkpoint/memory/__init__.py) — `blobs` 딕셔너리 키 구조
- [`checkpoint-sqlite/langgraph/checkpoint/sqlite/__init__.py`](https://github.com/langchain-ai/langgraph/blob/main/libs/checkpoint-sqlite/langgraph/checkpoint/sqlite/__init__.py) — 통짜 `checkpoint BLOB`, `new_versions` 미사용
- [`checkpoint/langgraph/checkpoint/base/__init__.py`](https://github.com/langchain-ai/langgraph/blob/main/libs/checkpoint/langgraph/checkpoint/base/__init__.py) — `DeltaChannelHistory`, `_DeltaSnapshot` 관련 경고 (안정화 전)
