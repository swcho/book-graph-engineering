# 순서에 의존하지 않는 리듀서 만들기

## 질문

순서에 의존하지 않는 리듀서를 만드는 방법은 무엇인가?

## 답

**값 안에 판단 근거(시각, 출처, 신뢰도)를 넣고 리듀서가 그것을 보고 결정하게 한다.**

즉 "누가 나중에 도착했나"(실행 순서)가 아니라 "값 자체가 무엇을 주장하는가"(값 안의 메타데이터)로 승자를 정한다. 순서는 내가 못 정하지만, 값은 내가 정할 수 있기 때문이다.

---

## 왜 문제가 되는가 — 순서는 내가 정하는 게 아니다

19장의 전제는 두 가지다.

1. 노드는 상태 전체가 아니라 **바꾼 부분만** 돌려준다.
2. 같은 슈퍼스텝의 노드들은 **같은 상태 사본**을 받고, 서로가 쓴 걸 못 본다.

그래서 같은 필드를 여럿이 건드리면, 그 갱신들을 하나로 합치는 일은 전적으로 **리듀서**의 몫이 된다. 문제는 리듀서가 호출되는 **순서**다.

> 리듀서는 교환법칙을 지켜야 합니다. `f(a,b) == f(b,a)`가 아니면 실행 순서에 따라 답이 달라지고, **그 순서는 여러분이 못 정해요.** 값 안에 판단 근거(시각, 출처, 신뢰도)를 넣으세요.
> — 19장 「한 장 요약」

순서를 못 정한다는 말은 과장이 아니다. 병렬 브랜치의 완료 순서는 스케줄러 구현, 노드 등록 순서와 무관한 내부 큐, 스레드 풀 상황, 그리고 **실행기 버전**에 따라 달라진다. 오늘 통과한 테스트가 라이브러리 마이너 업그레이드 후에 다른 답을 내도 그건 버그 리포트를 쓸 근거가 못 된다 — 애초에 순서를 보장한 적이 없으니까.

## `ex3_custom_reducer.py`가 보여 주는 것 — 성공 두 개와 실패 두 개

예제 3은 필드 네 개에 리듀서 네 개를 붙이고, 같은 슈퍼스텝에서 두 출처(`ERP`, `CRM`)가 각자 값을 내게 한다.

```python
class S(TypedDict):
    담당:   Annotated[dict, keep_latest]      # 순서 무관 (거의)
    분류:   Annotated[dict, keep_best]        # 순서 무관 (거의)
    속성:   Annotated[dict, merge_dict]       # 순서 의존 ← 함정
    태그:   Annotated[list, collect_unique]   # 순서 의존 ← 함정
```

### 순서에 의존하지 **않는** 쪽 — 값 안의 근거를 본다

```python
def keep_latest(old, new):
    """타임스탬프가 더 최근인 쪽을 남긴다."""
    if not old:
        return new
    if not new:
        return old
    return new if new["at"] > old["at"] else old


def keep_best(old, new):
    """신뢰도가 높은 쪽. 같으면 먼저 온 쪽."""
    if not old:
        return new
    if not new:
        return old
    return new if new["conf"] > old["conf"] else old
```

이 둘이 보는 것은 `old`/`new`라는 **위치**가 아니라 `at`(시각)과 `conf`(신뢰도)라는 **값 안의 필드**다. 그래서 페이로드를 이렇게 실어 보낸다.

```python
def src_erp(s):
    return {"담당": {"who": "김하늘", "at": "2024-03-01"},   # 언제의 사실인가
            "분류": {"cat": "제조",   "conf": 0.7}, ...}     # 얼마나 믿을 만한가

def src_crm(s):
    return {"담당": {"who": "박서준", "at": "2026-01-15"},
            "분류": {"cat": "유통",   "conf": 0.9}, ...}
```

`담당`은 ERP가 먼저 오든 CRM이 먼저 오든 `2026-01-15 > 2024-03-01`이므로 **항상 박서준**이다. `분류`도 `0.9 > 0.7`이므로 **항상 유통**이다. 실행 순서가 뒤집혀도 같은 답이 나온다.

이게 이 카드의 답 그대로다. 값이 자기 자신에 대한 판단 근거를 들고 다니면, 리듀서는 도착 순서를 볼 이유가 없어진다.

### 순서에 의존하는 쪽 — 위치를 본다

```python
def merge_dict(old, new):
    """키 단위 병합. 겹치면 새 것이 이긴다."""
    out = dict(old or {})
    out.update(new or {})   # ← "새 것"의 정의가 «나중에 호출된 쪽»이다
    return out


def collect_unique(old, new):
    """이어 붙이되 중복은 뺀다. 순서는 유지."""
    ...  # ← 결과 «리스트 순서»가 호출 순서를 그대로 반영한다
```

`update()`의 "새 것"은 **의미상 최신**이 아니라 **함수 인자 위치**다. 저자가 실제로 겪은 결과가 예제 출력 설명에 그대로 남아 있다.

> `«속성»`을 보라. 등급이 A(ERP)와 B(CRM)로 갈렸는데 `«A»`가 남았다. `merge_dict`는 `«새 것이 이긴다»`로 짰는데, 실행기가 CRM을 먼저 돌려서 ERP가 `«새 것»`이 되어 버렸다. 코드를 짤 때 제가 기대한 것과 반대다.
>
> `«태그»` 순서도 보라. `['중견', '수도권', '제조']`다. CRM이 먼저 왔다는 뜻이다. 저는 ERP를 먼저 등록했는데도.

`b.add_node("ERP", ...)`를 먼저 썼다는 사실은 실행 순서와 아무 상관이 없다. **그래프 정의 순서 ≠ 실행 순서**다.

같은 함정이 `ex1_lost_update.py`의 `operator.add`에도 조용히 들어 있다. `count`(정수 덧셈)는 교환법칙이 성립해서 항상 3이지만, `logs`(리스트 이어 붙이기)는 **결합법칙만 성립하고 교환법칙은 성립하지 않는다**. 원소 집합은 같아도 `['재무','법무','영업']`인지 `['영업','재무','법무']`인지는 매 실행마다 달라질 수 있다. 로그라서 신경 안 쓸 뿐, 그 순서에 의미를 부여하는 순간 버그가 된다.

## 리듀서가 만족해야 할 성질

LangGraph의 리듀서는 `(현재값, 갱신값) -> 새값` 시그니처의 **폴드(fold)**로, 같은 슈퍼스텝에 쌓인 갱신들에 차례로 적용된다. 여기서 답이 순서와 무관하려면:

| 성질 | 식 | 왜 필요한가 |
|---|---|---|
| **교환법칙** (commutativity) | `f(a,b) == f(b,a)` | 두 노드의 완료 순서가 뒤집혀도 같은 답 |
| **결합법칙** (associativity) | `f(f(a,b),c) == f(a,f(b,c))` | 셋 이상일 때 묶는 방식이 달라져도 같은 답 |
| **멱등성** (idempotence) | `f(a,a) == a` | 재시도·중복 전달이 있어도 같은 답 |

셋을 다 만족하는 이항 연산을 수학에서는 **결합 반격자(join-semilattice)의 join**이라 부르고, 분산 시스템에서는 그런 자료형을 **CRDT**(Conflict-free Replicated Data Type), 특히 상태 기반 CRDT(CvRDT)라고 부른다. 리듀서를 짠다는 건 사실상 그 필드에 맞는 작은 CRDT를 하나 정의하는 일이다.

교환법칙만 놓고 보면 이렇게 갈린다.

- **성립** — `max`, `min`, 정수 덧셈, 집합 합집합, 논리 OR/AND, 그리고 `keep_latest`·`keep_best`처럼 **값 안의 전순서(total order)로 승자를 뽑는** 함수
- **불성립** — 리스트 이어 붙이기, 문자열 연결, `dict.update`, "마지막 걸 쓴다", "먼저 온 걸 쓴다"

## 동률(tie-break)이 진짜 함정이다

여기서 대부분 걸린다. `keep_best`의 독스트링을 다시 보자.

```python
def keep_best(old, new):
    """신뢰도가 높은 쪽. 같으면 먼저 온 쪽."""
    return new if new["conf"] > old["conf"] else old
```

`>`(초과)이므로 `conf`가 **같으면 `old`가 남는다**. 그런데 "`old`"는 곧 "먼저 호출된 쪽"이다. 즉 이 리듀서는 **동률일 때만 순서 의존으로 되돌아간다.** `keep_latest`도 `at`이 같으면 똑같다. 하루 단위 날짜 문자열(`"2024-03-01"`)을 쓰고 있으니 같은 날 갱신 두 건이면 바로 동률이다.

값 안의 근거로 결정한다는 원칙을 끝까지 밀려면, **동률을 남기지 않는 전순서**를 만들어야 한다. 표준적인 해법은 비교 키를 튜플로 확장하고, 마지막에 반드시 **유일하고 결정적인 값**(출처 ID, 노드 ID, 레코드 UUID)을 두는 것이다.

```python
SRC_RANK = {"ERP": 2, "CRM": 1}   # 동률이면 ERP가 이긴다 — 정책을 «명시»한다

def _key(v):
    # 우선순위: 신뢰도 → 시각 → 출처. 마지막 항이 동률을 없앤다.
    return (v["conf"], v["at"], SRC_RANK[v["src"]])

def keep_best(old, new):
    if not old:
        return new
    if not new:
        return old
    return new if _key(new) > _key(old) else old   # 이제 동률 자체가 없다
```

- `src`가 유일하므로 `_key(new) == _key(old)`인 경우는 두 값이 같은 출처의 같은 갱신일 때뿐이고, 그때는 어느 쪽을 남겨도 결과가 같다 → **멱등성**까지 덤으로 얻는다.
- 승자를 "ERP 우선"으로 할지 "CRM 우선"으로 할지는 도메인 결정이다. 중요한 건 **그 결정이 코드에 적혀 있다**는 것. 순서에 맡기면 아무도 그 결정을 한 적이 없는데 답은 나온다.

같은 방식으로 `merge_dict`와 `collect_unique`도 고칠 수 있다. 값을 벌거벗은 스칼라가 아니라 `{"v": ..., "at": ..., "src": ..., "conf": ...}` 봉투에 담고, **키마다 `_key` 비교로 승자를 뽑으면** 순서와 무관해진다.

```python
def merge_dict(old, new):
    out = dict(old or {})
    for k, v in (new or {}).items():
        if k not in out or _key(v) > _key(out[k]):   # 위치가 아니라 근거로 이긴다
            out[k] = v
    return out

def collect_unique(old, new):
    # 집합 합집합은 교환·결합·멱등을 모두 만족한다.
    # 사람이 볼 순서가 필요하면 «저장»이 아니라 «출력 직전»에 정렬한다.
    return sorted(set(old or []) | set(new or []))
```

핵심 요령 하나: **순서 있는 자료구조에 순서를 맡기지 말고, 정렬 가능한 키를 값에 심어라.** 그러면 저장은 순서 무관(집합/사전)으로 하고, 표시할 때 결정적으로 정렬할 수 있다.

## LWW와 CRDT — 이미 이름이 붙어 있는 패턴

`keep_latest`가 하는 일에는 정식 이름이 있다.

- **LWW (Last-Write-Wins)** — 값마다 타임스탬프를 붙여 두고, 병합할 때 타임스탬프가 큰 쪽을 남긴다. Cassandra, Riak, DynamoDB 계열의 충돌 해소 기본값으로 널리 쓰인다. `keep_latest`가 정확히 **LWW-Register**다.
- **LWW-Register / LWW-Element-Set** — CRDT 문헌의 표준 구성물. 등록기(register)는 `(값, 타임스탬프, 노드ID)` 삼중항을 들고 다니며, **타임스탬프 동률은 노드ID로 깬다.** 위에서 튜플 마지막에 출처를 넣은 것이 바로 이 관행이다.
- **G-Counter / PN-Counter** — 출처별로 칸을 나눠 세고 합칠 때 각 칸의 `max`를 취한다. `operator.add`로 단순 누적하는 카운터와 달리 재시도로 중복 전달돼도 값이 부풀지 않는다(멱등).
- **OR-Set (Observed-Remove Set)** — 원소마다 고유 태그를 붙여 추가/삭제 충돌을 순서 없이 해소한다. `collect_unique`를 진지하게 만들면 이 방향으로 간다.

**LWW의 알려진 약점**도 같이 알아 두는 게 좋다.

1. **벽시계는 못 믿는다.** 여러 프로세스·머신에서 찍은 타임스탬프는 시계 오차(clock skew) 때문에 인과관계와 어긋날 수 있다. 나중에 일어난 일이 더 작은 시각을 달고 오면 잘못된 쪽이 이긴다.
2. **이기지 못한 갱신은 조용히 사라진다.** LWW는 충돌을 "해소"하는 게 아니라 한쪽을 **버린다**. 둘 다 살려야 하는 도메인(장바구니, 협업 편집)에서는 오답이다.
3. 그래서 분산 시스템에서는 벽시계 대신 **논리 시계**(Lamport clock), **벡터 시계**(vector clock), 또는 **하이브리드 논리 시계**(HLC)를 타임스탬프로 쓴다. 인과 순서를 실제로 반영하면서도 전순서를 만들 수 있기 때문이다.

에이전트 그래프의 한 실행(single run) 안에서는 대개 한 프로세스라 1번이 덜 위험하지만, 노드가 외부 시스템에서 가져온 레코드의 `updated_at`을 그대로 쓴다면 그 순간 남의 시계를 신뢰하는 셈이 된다. `ex3`의 `at`이 "노드가 실행된 시각"이 아니라 "그 사실이 기록된 시각"이라는 점이 중요하다 — **판단 근거는 실행 시점이 아니라 데이터의 의미에서 나와야 한다.**

## 실무 체크리스트

리듀서를 하나 짤 때마다 아래를 통과시키면 된다.

1. **이 필드를 여럿이 쓰는가?** 쓴다면 타입에 `Annotated[..., reducer]`로 적는다. 타입만 읽고 동시 쓰기 여부를 알 수 있게 하는 것 자체가 목적이다(`ex1`의 결론).
2. **승부를 무엇으로 가르는가?** 답이 "나중에 온 쪽"이면 이미 틀렸다. `at`·`conf`·`src` 같은 근거를 값에 실어라.
3. **동률이면?** 전순서가 되도록 튜플 마지막에 유일 식별자를 넣어라.
4. **`f(a,b) == f(b,a)`인가?** 테스트로 못 박아라.

```python
from itertools import permutations

def assert_order_free(reducer, init, updates):
    """모든 도착 순열에 대해 같은 결과가 나오는지 확인한다."""
    results = []
    for perm in permutations(updates):
        acc = init
        for u in perm:
            acc = reducer(acc, u)
        results.append(acc)
    assert all(r == results[0] for r in results), f"순서 의존! {results}"
```

이 테스트가 `merge_dict`·`collect_unique`(원본)에서는 깨지고, `keep_latest`·`keep_best`(동률 없는 데이터)에서는 통과한다. 순열이 3~4개짜리라도 CI에 넣어 두면, 실행기 버전을 올리기 전에 잡아 준다.

5. **순서가 정말 필요하다면 리듀서로 풀지 마라.** 그건 리듀서 문제가 아니라 **슈퍼스텝 경계 문제**다. `ex2_superstep.py`가 보여 주듯, 사이에 노드를 하나 넣어 경계를 만들면 그 뒤 노드는 앞의 결과를 전부 본다. "합칠 수 없는 순서"는 병렬로 두면 안 되는 것이다.

## 기억할 문장

> 이게 함정이다. 순서에 기대는 리듀서는 `«내가 예상한 답»`을 안 낸다.
> 그리고 실행기 버전이 올라가면 순서가 또 바뀔 수 있다.
> 고치려면 **값에 출처와 시각을 같이 담고 리듀서가 그걸 보고 정해야 한다.**
> `«담당»`과 `«분류»`가 그렇게 돼 있다. 순서와 무관하게 같은 답이 나온다.
> — `ex3_custom_reducer.py`

한 줄로 줄이면: **리듀서가 "언제 왔는가"를 묻게 하지 말고 "무엇을 근거로 하는가"를 묻게 하라.**

## 관련 예제와 출처

- `content/ch19/code/ex3_custom_reducer.py` — `keep_latest`, `keep_best`, `merge_dict`, `collect_unique` 네 리듀서 비교. 순서 의존의 실패가 출력으로 드러난다.
- `content/ch19/code/ex1_lost_update.py` — 리듀서가 없을 때의 갱신 유실(lost update)과 `operator.add`의 교환법칙 유무.
- `content/ch19/code/ex2_superstep.py` — 같은 슈퍼스텝은 같은 상태 사본을 본다는 사실, 그리고 경계 노드로 순서를 만드는 법.
- [LangGraph Graph API — reducer / superstep](https://docs.langchain.com/oss/python/langgraph/graph-api) `[사실상 표준]`
- [Pregel: a system for large-scale graph processing](https://dl.acm.org/doi/10.1145/1807167.1807184) `[사실상 표준]` — 슈퍼스텝 계산 모형의 원전
- [A bridging model for parallel computation (BSP)](https://dl.acm.org/doi/10.1145/79173.79181) `[사실상 표준]`
- Shapiro et al., *A Comprehensive Study of Convergent and Commutative Replicated Data Types* (INRIA RR-7506, 2011) — LWW-Register, G-Counter, OR-Set 등 CRDT 계열의 표준 참고 문헌
- 14장(배치 병합의 생존 규칙) — 같은 "합치는 규칙이 도메인 지식이다"를 배치 관점에서 다룬다. 19.3절은 그것을 **실행 중**으로 옮긴 것이다.
