# 체크포인트에서 「다르게 이어 가기」

> **Q.** 체크포인트에서 '다르게 이어 가기'는 어떻게 하는가?
>
> **A.** `app.update_state`로 값을 고치고 그 지점부터 다시 돌린다. "만약 예산이 150이었다면"을 실제로 실행해 볼 수 있다.

19.5절 「체크포인트는 복구용만이 아니다」와 `ex5_debug_state.py`의 마지막 문단이 이 카드의 출처입니다.

```
로그만 있으면 «100 을 넘었다»까지만 안다.
체크포인트가 있으면 «넘기 직전 상태»로 되감아서 그때 무엇을 하려 했는지 본다.

그리고 되감은 지점에서 «다르게» 이어 갈 수도 있다.
app.update_state 로 값을 고치고 그 지점부터 다시 돌리는 것이다.
«만약 예산이 150 이었다면»을 실제로 돌려 볼 수 있다.

이게 체크포인트의 두 번째 값어치다. 첫째는 복구, 둘째는 디버깅.
그리고 실무에서는 둘째를 훨씬 자주 쓴다.
```

LangGraph 문서는 이 기능을 **time travel**이라고 부르고, 두 가지로 나눕니다.

| 이름 | 하는 일 | 호출 |
|---|---|---|
| **리플레이(replay)** | 값은 그대로, 그 지점부터 다시 실행 | `invoke(None, snap.config)` |
| **포크(fork)** | 값을 고쳐 **새 가지**를 만들고 거기서부터 실행 | `update_state(...)` → `invoke(None, fork_config)` |

카드가 말하는 「다르게 이어 가기」가 바로 **포크**입니다.

---

## 1. 전체 흐름 — 네 단계

### 0단계: 체크포인터가 켜져 있어야 한다

되감기의 전제입니다. 체크포인터가 없으면 과거가 아예 남지 않습니다.

```python
app = b.compile(checkpointer=InMemorySaver())
cfg = {"configurable": {"thread_id": "dbg"}}
out = app.invoke({"쓴돈": 0, "기록": [], "회차": 0}, cfg)
```

### 1단계: `get_state_history(config)`로 슈퍼스텝별 스냅샷 목록을 얻는다

```python
def get_state_history(
    self,
    config: RunnableConfig,
    *,
    filter: dict[str, Any] | None = None,
    before: RunnableConfig | None = None,
    limit: int | None = None,
) -> Iterator[StateSnapshot]:
    """Get the history of the state of the graph."""
```

`ex5`가 이미 이 호출을 쓰고 있습니다.

```python
hist = list(app.get_state_history(cfg))
```

**최신이 먼저** 나오는 역순 이터레이터입니다(그래서 `ex5`가 시간순으로 보려고 `reversed(hist)`를 씁니다). 각 원소는 `StateSnapshot` 네임드튜플이고, 필드는 다음과 같습니다.

```
('values', 'next', 'config', 'metadata', 'created_at', 'parent_config', 'tasks', 'interrupts')
```

`ex5`의 그래프를 그대로 돌리면 이력이 이렇게 나옵니다.

```
쓴돈= 145 회차=2 next=()           tasks=[]
쓴돈=  95 회차=2 next=('정리',)      tasks=[('정리', {'쓴돈': 50})]
쓴돈=  65 회차=1 next=('검색',)      tasks=[('검색', {'쓴돈': 30, '회차': 1})]
쓴돈=  30 회차=1 next=('정리',)      tasks=[('정리', {'쓴돈': 35})]
쓴돈=   0 회차=0 next=('검색',)      tasks=[('검색', {'쓴돈': 30, '회차': 1})]
쓴돈=   0 회차=0 next=('__start__',) tasks=[('__start__', {'쓴돈': 0, '회차': 0})]
```

읽는 법이 중요합니다. **`values`는 「`next`를 실행하기 직전」의 상태**입니다. 4번째 줄(`쓴돈=95, next=('정리',)`)은 「예산 100을 아직 안 넘긴 마지막 순간, 그리고 다음에 정리를 부르려던 참」이라는 뜻이죠. `ex5`의 `culprit` 탐색이 찾는 게 정확히 이 지점입니다.

### 2단계: 되감을 지점의 `checkpoint_id`를 고른다

각 스냅샷의 `snap.config`가 그 시점을 가리키는 좌표입니다.

```python
for s in hist:
    print(s.next, s.config["configurable"]["checkpoint_id"])
```

```
before.config = {'configurable': {'thread_id': 't',
                                  'checkpoint_ns': '',
                                  'checkpoint_id': '1f1984a8-91d0-64c0-8003-3d58469c488d'}}
```

`thread_id`만 있는 config는 「그 스레드의 최신」을 뜻하고, `checkpoint_id`까지 붙으면 「그 스레드의 그 순간」을 뜻합니다. 되감기는 이 차이 하나로 굴러갑니다.

보통은 id를 손으로 복사하지 않고 조건으로 집습니다.

```python
before = next(s for s in hist if s.next == ("정리",) and s.values["쓴돈"] < 100)
```

### 3단계: `update_state`로 값을 고쳐 **새 체크포인트**를 만든다

```python
def update_state(
    self,
    config: RunnableConfig,
    values: dict[str, Any] | Any | None,
    as_node: str | None = None,
    task_id: str | None = None,
) -> RunnableConfig:
    """Update the state of the graph with the given values, as if they came from
    node `as_node`. If `as_node` is not provided, it will be set to the last node
    that updated the state, if not ambiguous.
    """
```

핵심은 **반환값이 새 config라는 것**입니다. 원본을 고치는 게 아니라 새 체크포인트를 낳고 그 좌표를 돌려줍니다.

```python
fork = app.update_state(before.config, {"예산": 150}, as_node="검색")
```

```
before.config  checkpoint_id = 1f1984a8-91d0-64c0-8003-3d58469c488d
fork.config    checkpoint_id = 1f1984a8-91d3-65da-8004-42155342e684   ← 새 id
fork 의 parent_config        = 1f1984a8-91d0-...  ← 되감은 지점을 부모로 가리킨다
```

### 4단계: 그 config로 `invoke(None, config)` — 그 지점부터 이어서 실행

첫 인자가 `None`인 게 포인트입니다. **새 입력을 주는 게 아니라 「저장된 상태에서 이어 가라」**는 신호입니다.

```python
res = app.invoke(None, fork)
```

`ex5`의 그래프에서 예산만 상태로 옮겨(아래 5절 참고) 실제로 돌린 결과입니다.

```
원본(예산 100):    쓴돈 145, 회차 2, 기록 ['검색 30','정리 35','검색 30','정리 50']
되감을 지점:       next=('정리',)  쓴돈 95  회차 2
fork 직후:         예산 150, 쓴돈 95(그대로), next=('정리',)
what-if(예산 150): 쓴돈 240, 회차 3, 기록 [...,'정리 50','검색 30','정리 65']
```

예산이 150이었다면 라우터가 한 바퀴를 더 돌렸을 것이고, 그래서 240까지 갔을 거라는 답이 **추측이 아니라 실행 결과로** 나옵니다.

---

## 2. 되감기는 원본을 부수지 않는다 — 분기(branch)다

`update_state`는 되감은 체크포인트를 **부모로 삼는 새 체크포인트**를 추가할 뿐입니다. 덮어쓰기가 아닙니다.

```
                                      ┌─ (원본) ─ 쓴돈 145  [그대로 남아 있다]
START ─ 검색 ─ 정리 ─ 검색 ─[쓴돈 95]─┤
                                      └─ (포크) ─ 예산 150 ─ 정리 ─ 검색 ─ 정리 ─ 쓴돈 240
```

실제로 확인해 보면 체크포인트 개수만 늘고 원본은 그대로 조회됩니다.

```
체크포인트 개수 before/after: 6 -> 9      (포크 세 번 = 새 체크포인트 세 개)
원본 최종 스냅샷 여전히 조회 가능: 145
```

그래서 「예산이 100이었을 때」와 「150이었다면」을 **나란히 놓고 비교**할 수 있습니다. 되감기 한 번 하면 원래 실행이 날아가는 방식이었다면 이 기능은 디버깅 도구로 쓸모가 없었을 겁니다.

한 가지 실용적인 주의: **스레드의 「최신」 포인터는 포크 쪽으로 옮겨 갑니다.**

```python
app.get_state(cfg)              # thread_id 만 → 최신 = 포크 쪽
app.get_state(hist[0].config)   # checkpoint_id 지정 → 원본 최종 스냅샷 (145)
```

원본 가지를 다시 보려면 그 시점의 `config`(= `checkpoint_id` 포함)를 들고 있어야 합니다. 원본과 what-if를 완전히 격리해 두고 싶다면 스레드를 나눠 쓰는 편이 안전합니다.

---

## 3. 함정 1 — `values`는 **리듀서를 거친다**

가장 많이 걸리는 곳입니다. `update_state`의 `values`는 「상태를 이 값으로 만들어라」가 아니라 **「어떤 노드가 이 값을 반환했다고 치자」**입니다. 노드 반환값과 똑같이 취급되니, 당연히 그 필드의 리듀서를 통과합니다. 문서도 같은 말을 합니다 — *state changes are applied using the specified node's writers, which includes any configured reducers*.

`ex5`의 상태는 세 필드가 전부 `operator.add`입니다.

```python
class S(TypedDict):
    쓴돈: Annotated[int, operator.add]
    기록: Annotated[list, operator.add]
    회차: Annotated[int, operator.add]
```

그래서 이렇게 됩니다.

```python
# 되감은 지점의 기록 = ['검색 30', '정리 35', '검색 30']
fork = app.update_state(before.config, {"기록": ["사람이 끼워 넣음"]}, as_node="검색")
```

```
기대(교체): ['사람이 끼워 넣음']
실제(append): ['검색 30', '정리 35', '검색 30', '사람이 끼워 넣음']
```

숫자도 마찬가지입니다. `쓴돈`이 95인 지점에서 `{"쓴돈": 5}`를 주면 5가 아니라 **100**이 됩니다.

```
쓴돈 95 지점에 {"쓴돈": 5}  →  95 + 5 = 100
```

**대응 요령**

- `operator.add` 필드를 **절댓값으로 바꾸고 싶다면 차이를 넣습니다.** 95를 20으로 만들려면 `{"쓴돈": -75}`.
- 애초에 what-if로 흔들 값(예산, 임계치, 모델 선택 같은 설정성 필드)은 **리듀서 없는 필드**로 두세요. 리듀서가 없으면 기본 동작이 교체라서 `{"예산": 150}`이 그대로 먹습니다. 위 4단계 실험에서 예산이 깔끔히 150이 된 이유입니다.
- 커스텀 리듀서(19.3절의 `keep_latest`, `keep_best` 같은 것)를 쓰는 필드라면 **그 리듀서를 통과시켜서도 내가 원하는 값이 이기는지** 확인해야 합니다. `keep_best`에 신뢰도 낮은 값을 넣으면 아무 일도 일어나지 않습니다.

---

## 4. 함정 2 — `as_node`가 「다음에 어디서 이어 갈지」를 정한다

`as_node`는 「이 갱신을 어느 노드가 낸 것으로 칠까」를 지정하는 인자입니다. 그리고 LangGraph는 **그 노드의 후속(successor)부터** 실행을 재개합니다. 즉 `as_node`는 사실상 **그래프 상의 재개 위치를 고르는 손잡이**입니다.

`ex5` 그래프(`START → 검색 → 정리 → (조건부) 검색 | END`)의 `쓴돈 95, next=('정리',)` 지점에서 세 가지를 비교해 보면.

| 호출 | 결과 `next` | 왜 |
|---|---|---|
| `update_state(cfg, {"쓴돈": 5})` (미지정) | `('정리',)` | 추론이 `검색`으로 붙어 후속인 `정리`부터 |
| `update_state(cfg, {"쓴돈": 5}, as_node="검색")` | `('정리',)` | `검색`의 후속 = `정리` |
| `update_state(cfg, {"쓴돈": -95}, as_node="정리")` | `('검색',)` | `정리`의 후속 = 조건부 엣지. `route`가 **새 값으로 다시 평가**되어 `검색` 선택 |

세 번째 줄이 재미있습니다. `as_node="정리"`로 두면 정리가 방금 끝난 셈이 되므로 `route(s)`가 다시 돌고, `쓴돈`이 0으로 내려간 덕에 END가 아니라 `검색`으로 갑니다. 즉 **`as_node` 하나 바꾸면 같은 값 갱신이라도 실행 경로가 달라집니다.**

주의할 점:

- **미지정은 추론입니다.** docstring이 명시하듯 *"the last node that updated the state, **if not ambiguous**"*. 같은 슈퍼스텝에서 여러 노드가 상태를 갱신한 병렬 분기(19.2절의 A·B·C 같은 상황)에서는 애매해집니다. **병렬이 섞인 그래프에서는 `as_node`를 명시하세요.**
- `as_node`에 준 이름은 **그래프에 실재하는 노드 이름**이어야 합니다. 재개 위치는 그 노드에서 나가는 엣지를 따라 결정되므로, 조건부 엣지가 걸린 노드를 지정하면 라우터 함수가 갱신된 상태로 다시 평가된다는 점도 같이 기억해 두면 좋습니다.

---

## 5. 함정 3 — 되감아지는 건 **상태뿐**이다

체크포인트는 그래프 상태의 스냅샷입니다. 그 밖의 것은 아무것도 되돌아가지 않습니다.

**되감기지 않는 것**

- **이미 나간 부작용.** 보낸 이메일, 호출한 결제 API, 커밋한 DB 트랜잭션, 슬랙에 붙인 메시지. 되감아 재실행하면 **한 번 더** 나갑니다. 18장의 재시도 논의와 같은 결론이고, 대응도 같습니다 — 외부 호출에 멱등키를 붙이거나, what-if 재실행에서는 부작용 노드를 스텁으로 갈아 끼우세요.
- **이미 청구된 비용.** `ex5`의 `쓴돈` 145는 상태 위의 숫자라 되감으면 95로 돌아가지만, 실제로 태운 토큰 요금은 안 돌아옵니다. **되감기는 공짜가 아니고, 재실행분은 새로 청구됩니다.** 1장의 41만 원 이야기가 여기서도 유효합니다.

**되감아도 같은 답이 안 나오는 것**

- **비결정적 노드.** LLM 호출, 검색 API, `time.time()`, 난수. 리플레이는 「값을 그대로 두고 다시 실행」이지 「그때 나온 응답을 재생」이 아닙니다. 문서도 리플레이 의미를 이렇게 적습니다 — 선택 지점 **이전** 노드의 결과는 체크포인트에서 불러오지만, **이후** 노드는 LLM 호출을 포함해 **다시 실행**되고 결과가 달라질 수 있다.
- 그래서 what-if 실험에서 결과가 달라졌을 때 **「예산을 바꿔서」인지 「모델이 이번엔 다른 말을 해서」인지 구분되지 않습니다.** `ex5`가 LLM 없이 순수 함수(`검색`, `정리`)로 짜인 건 우연이 아닙니다. 결정적이라 되감기의 효과만 깨끗하게 보이죠. 실제 그래프로 what-if를 할 거라면 온도를 0으로 낮추거나, 흔드는 변수 하나만 남기고 나머지를 고정해야 결론이 섭니다.

**한 가지 더 — `ex5`의 예산은 상태가 아니다**

```python
BUDGET = 100          # 모듈 상수

def route(s):
    if s["쓴돈"] >= BUDGET:
        return END
```

`BUDGET`이 **상태 밖의 파이썬 상수**라 `update_state`로는 건드릴 수 없습니다. 카드가 말하는 "만약 예산이 150이었다면"을 진짜로 되감아 돌리려면 예산을 상태 안으로 들여놓아야 합니다.

```python
class S(TypedDict):
    예산: int                                  # 리듀서 없음 → 교체
    쓴돈: Annotated[int, operator.add]
    기록: Annotated[list, operator.add]
    회차: Annotated[int, operator.add]

def route(s):
    if s["쓴돈"] >= s["예산"]:                  # 상수가 아니라 상태를 본다
        return END
    return END if s["회차"] >= 4 else "검색"
```

이렇게 두면 앞의 4단계가 그대로 통합니다. **「나중에 되감아 흔들어 보고 싶은 값은 상태에 있어야 한다」** — 19.4절의 "상태에 무엇을 넣을 것인가"에 이 기준을 하나 더 얹는 셈입니다. (다만 무제한은 아닙니다. 상태는 슈퍼스텝마다 통째로 저장되니 19.4절의 8KB 기준과 저울질하세요. 예산 같은 정수 몇 바이트는 당연히 남는 장사입니다.)

---

## 6. 실무에서 어디에 쓰나

### (1) 반사실(what-if) 실험

「임계치를 바꿨으면 결과가 달라졌을까」를 **처음부터 다시 돌리지 않고** 확인합니다. 앞 단계가 캐시에서 로드되니 분기점 이후만 비용이 듭니다.

- 예산/재시도 한도 바꿔 보기 (20장의 종료 조건 설계와 직결)
- 라우터가 다른 가지를 골랐다면 어땠을지
- 리트리버가 다른 문서를 물어 왔다면 답이 바뀌었을지

흔드는 값 하나만 남기고 나머지를 고정하는 게 요령입니다. 여러 개를 동시에 바꾸면 어느 게 효과였는지 못 가립니다.

### (2) 사람이 개입해 고치고 재개하기 (human-in-the-loop)

**같은 API를 쓰는 같은 메커니즘**입니다. 승인 대기든 값 교정이든 결국 「멈춘 지점의 상태를 고치고 이어 간다」니까요.

- 실행이 `interrupt()`에서 멈춘다 → 사람이 본다 → `update_state`로 도구 인자를 고친다 → 재개
- 잘못된 도구 호출 인자 교정: 모델이 만든 호출을 그대로 실행하지 않고 사람이 손본 뒤 통과
- 사람 승인 게이트: 잘못 갔으면 되감아 다른 가지로

LangGraph 문서가 time travel을 human-in-the-loop 항목 아래 두는 이유입니다. 다만 인터럽트가 걸린 그래프를 포크하면 **인터럽트도 다시 걸립니다.** 포크 뒤 재개는 `invoke(None, fork_config)`가 아니라 새 답을 실은 `Command(resume=...)`가 필요하고, 그때도 반드시 **포크의 config**에 실어 보내야 합니다.

```python
fork_config = graph.update_state(before_ask.config, {"value": ["forked"]})
graph.invoke(None, fork_config)                  # 다시 인터럽트에서 멈춤
graph.invoke(Command(resume="Bob"), fork_config) # 다른 답으로 재개
```

### (3) 사후 부검

19.5절이 「복구보다 디버깅에 여덟 배 자주 쓴다」고 한 그 용도입니다. 사고 스레드를 열어 상태를 훑고, 문제 지점을 짚고, 고쳐서 재현되는지 확인하는 것까지 한 자리에서 끝납니다.

---

## 확인 범위와 확인하지 못한 것

**확인한 것** — 아래는 LangChain 공식 time travel 문서(`docs.langchain.com/oss/python/langgraph/use-time-travel`)와 `langgraph` 소스의 시그니처로 확인했고, `ex5_debug_state.py`의 그래프를 **langgraph 1.2.11에서 직접 실행**해 재현했습니다.

- `get_state_history` / `update_state`의 정확한 시그니처와 docstring
- `update_state`가 새 `checkpoint_id`를 반환하고 `parent_config`가 되감은 지점을 가리키는 것, 원본 스냅샷이 그대로 조회되는 것
- `values`가 리듀서를 통과하는 것 (95 + 5 = 100, 리스트 append)
- `as_node`에 따라 재개 위치가 달라지는 것 (`검색` → `정리`, `정리` → 조건부 엣지 재평가)

**확인하지 못한 것 / 단정하지 않는 것**

- **버전 차이가 실재합니다.** 같은 실험을 `langgraph 0.6.11`에서 돌리면 갱신의 기준값이 달라져 95가 아니라 145 위에 얹혔습니다(빈 `update_state`가 145를 냈습니다). 위 설명은 **1.x 기준**입니다. 다른 버전을 쓴다면 빈 `update_state` 한 번으로 기준값을 직접 확인하고 시작하세요.
- 위 재현은 `InMemorySaver` 기준입니다. Postgres/SQLite 체크포인터의 이력 보존·정리(TTL) 정책까지는 확인하지 않았습니다.
- 서브그래프의 되감기는 서브그래프가 자기 체크포인터를 가졌는지에 따라 갈린다고 문서가 적고 있으나(없으면 서브그래프 전체가 통째로 재실행), 직접 재현하지는 않았습니다.
- `update_state`의 네 번째 인자 `task_id`는 시그니처로만 확인했고 동작은 검증하지 않았습니다.

---

## 한 줄 정리

**되감기는 좌표(`checkpoint_id`)를 골라 → 값을 얹고(`update_state`, 리듀서를 통과함) → 어디서 이어 갈지 정한 뒤(`as_node`) → `invoke(None, fork_config)`로 새 가지를 뻗는 일이다.** 원본은 남고, 상태 밖의 것은 따라오지 않는다.
