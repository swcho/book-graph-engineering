# `ex4`에서 종료 이유를 노드로 만든 방식

> **Q.** `ex4`에서 종료 이유를 노드로 만든 방식은 무엇인가?
>
> **A.** 성공·상한·예산·정체 각각을 `mark(reason)` 노드로 두고 END로 연결한다. 조건 분기가 그 노드 중 하나로 보낸다.

---

## 1. 한 줄로 말하면

「끝났다/안 끝났다」를 불리언 하나로 남기지 않고, **끝난 이유 네 가지를 각각 그래프의 노드로 승격**시킨 것입니다. 조건 분기(`route`)는 어느 노드로 갈지만 정하고, 실제로 상태에 이유를 써넣는 일은 그 노드가 합니다. 이유 노드는 전부 `END`로 이어지므로 어디로 가든 그래프는 끝납니다.

```
                      ┌──→ 성공 ──┐
                      │           │
START → 생성 → 검증 ──┼──→ 상한 ──┼──→ END
          ↑           │           │
          │           ├──→ 예산 ──┤
          └───────────┤           │
           "생성"     └──→ 정체 ──┘
```

---

## 2. 원문 코드

### 2.1 `mark(reason)` — 클로저 공장

`ex4_generator_critic.py`에서 네 개의 종료 노드를 만들어 내는 부분입니다.

```python
def mark(reason):
    def fn(s: S) -> dict:
        return {"ending": reason}
    return fn
```

`mark`는 노드 자체가 아니라 **노드 함수를 찍어 내는 공장(factory)** 입니다. `reason`을 클로저로 붙잡아 두고, 호출되면 `{"ending": reason}` 이라는 상태 갱신 딕셔너리를 돌려주는 함수 `fn`을 만들어 냅니다. `mark("성공")`, `mark("상한")`, `mark("예산")`, `mark("정체")` 는 각각 다른 `reason`을 품은 서로 다른 함수 객체입니다.

왜 클로저를 쓰나요? 이유가 네 개인데 몸통은 똑같기 때문입니다. `def mark_success(s): ...`, `def mark_limit(s): ...` 를 네 번 쓰는 대신 한 줄짜리 루프로 등록할 수 있습니다.

> ⚠️ 흔한 함정 — 여기서 `for r in (...)`: `lambda s: {"ending": r}` 로 쓰면 안 됩니다. 파이썬의 late binding 때문에 네 람다가 모두 루프 마지막 값(`"정체"`)을 참조하게 됩니다. `mark(r)`처럼 **함수 호출로 감싸서** `reason`을 그 호출의 지역 변수로 고정시키는 것이 정석입니다.

### 2.2 노드 등록과 `add_conditional_edges` 매핑

```python
b = StateGraph(S)
b.add_node("생성", generate)
b.add_node("검증", critic)
for r in ("성공", "상한", "예산", "정체"):
    b.add_node(r, mark(r))
    b.add_edge(r, END)
b.add_edge(START, "생성")
b.add_edge("생성", "검증")
b.add_conditional_edges("검증", route,
                        {"생성": "생성", "성공": "성공", "상한": "상한",
                         "예산": "예산", "정체": "정체"})
app = b.compile(checkpointer=InMemorySaver())
```

읽는 순서:

1. `for r in ("성공", "상한", "예산", "정체")` — 이유 이름 네 개를 돌면서
2. `b.add_node(r, mark(r))` — **이유 이름을 그대로 노드 이름으로** 쓰고, 그 노드의 몸통은 `mark(r)`로 찍어 낸 함수
3. `b.add_edge(r, END)` — 그 노드는 무조건 `END`로 간다. 되돌아갈 길이 없다
4. `add_conditional_edges("검증", route, {...})` — 검증 노드 다음에 `route`를 실행하고, 그 반환 문자열을 매핑표(`path_map`)로 노드 이름에 대응시킨다

이름을 이유와 같게 맞춰 뒀기 때문에 매핑표가 `{"성공": "성공", ...}` 처럼 항등 사상(identity)이 됩니다. 사실 이 경우 세 번째 인자를 생략해도 동작합니다 — LangGraph 문서: *"the return value `routing_function` is used as the name of the node (or list of nodes) to send the state to next."* 그래도 명시하는 편이 낫습니다. 매핑표를 적어 두면 **그래프를 컴파일할 때 도달 가능한 목적지가 확정**되어, 시각화(`get_graph().draw_*`)에 엣지가 제대로 그려지고 오타를 실행 전에 잡을 수 있습니다.

### 2.3 이유를 고르는 쪽 — `route`

```python
def route(s: S) -> str:
    if not s["missing"]:
        return "성공"
    if s["rounds"] >= MAX_ROUNDS:
        return "상한"
    if s["cost"] >= MAX_COST:
        return "예산"
    if stalled(s["scores"]):
        return "정체"
    return "생성"
```

`route`가 하는 일은 오직 **문자열 하나를 고르는 것**입니다. 상태를 건드리지 않습니다. 판단은 여기서 하고, 기록은 `mark`가 만든 노드에서 합니다. 이 분업이 이 설계의 핵심입니다.

---

## 3. 왜 이렇게 하나 — 조건부 엣지는 상태를 쓸 수 없다

가장 자연스러워 보이는 코드는 이것입니다.

```python
# 이렇게는 안 된다
def route(s: S) -> str:
    if not s["missing"]:
        s["ending"] = "성공"      # ← 반영되지 않는다
        return END
    ...
```

LangGraph에서 **라우팅 함수의 반환값은 「다음에 갈 노드 이름」으로만 해석**됩니다. 상태 갱신으로 해석되지 않습니다. 공식 문서 설명대로 라우팅 함수는 현재 상태를 **읽고** 값을 반환할 뿐, 상태를 수정하는 경로가 없습니다. 실제로 위처럼 `s["ending"] = ...` 로 딕셔너리를 직접 건드려도, 그 변경은 채널/리듀서를 거치지 않은 로컬 변형이라 다음 슈퍼스텝의 상태에 안전하게 반영된다고 보장되지 않습니다.

LangGraph 구조상 이유는 이렇습니다.

- **노드**는 「상태의 부분 갱신 딕셔너리」를 반환하고, 프레임워크가 그것을 채널별 리듀서에 통과시켜 상태에 합칩니다. `ex4`의 `S`에서 `rounds`, `cost`, `scores`가 `Annotated[..., operator.add]`로 선언된 것이 그 리듀서입니다. `ending`은 리듀서가 없어 마지막에 쓴 값으로 덮어써집니다.
- **조건부 엣지**는 그 갱신 파이프라인 바깥에 있는 순수한 배선(routing) 계층입니다. 상태를 읽어 목적지를 고르는 것이 전부이고, 반환값이 갱신 딕셔너리로 취급되는 통로 자체가 없습니다.

그래서 「이유를 상태에 남기고 싶다」와 「그 이유에 따라 끝내고 싶다」를 동시에 하려면 **쓰기를 담당할 노드가 하나 더 필요**합니다. 그것이 `mark(reason)`으로 만든 네 개의 노드입니다. 조건부 엣지가 못 하는 일(쓰기)을 노드로 떠넘기고, 조건부 엣지는 자기가 할 수 있는 일(고르기)만 합니다.

### 3.1 대안 — `Command`

LangGraph에는 갱신과 라우팅을 한 함수에서 처리하는 길도 있습니다. 문서에도 명시되어 있습니다 — *"Use `Command` instead of conditional edges if you want to combine state updates and routing in a single function."*

```python
from langgraph.types import Command

def check(s: S) -> Command:
    if not s["missing"]:
        return Command(update={"ending": "성공"}, goto=END)
    ...
```

`ex4`가 `Command` 대신 노드 분리를 택한 이유는 **가독성과 시각화**입니다. 이유가 노드로 존재하면 그래프 그림에 「성공/상한/예산/정체」 네 개의 종착점이 그대로 보입니다. 종료 경로가 몇 개이고 각각 어디로 가는지가 코드가 아니라 **그래프 구조 자체로 드러납니다.** 이 장의 주제가 「종료를 설계로 만들라」이므로, 종료 이유를 구조에 새기는 쪽이 메시지에 맞습니다.

---

## 4. 왜 「이유」가 불리언보다 중요한가

`ex4`의 상태 정의에 붙은 주석이 이 장의 논지입니다.

```python
class S(TypedDict):
    text:    str
    missing: list
    rounds:  Annotated[int, operator.add]
    cost:    Annotated[float, operator.add]
    scores:  Annotated[list, operator.add]
    ending:  str          # 어떤 이유로 끝났는지. 이게 중요하다.
```

그리고 실행 결과 설명:

> 그리고 끝난 이유가 상태에 남는다는 게 중요하다.
> 호출한 쪽이 이걸 보고 다르게 대응할 수 있다.
> - 성공 — 그대로 쓴다
> - 상한 — 사람에게 넘긴다 (더 돌리면 될 수도 있다)
> - 예산 — 예산을 올릴지 물어본다
> - 정체 — 사람에게 넘긴다 (더 돌려도 안 된다)
>
> «상한»과 «정체»의 대응이 다르다. 불리언 하나로는 이 구분이 안 된다.

「상한」은 *더 돌리면 될 수도 있는* 종료이고, 「정체」는 *더 돌려도 안 되는* 종료입니다. 겉보기엔 둘 다 「실패로 끝남」이지만 후속 조치가 정반대입니다. `done: bool` 하나만 남기면 이 구분이 사라집니다.

같은 원칙이 `guards.py`에도 나옵니다.

```python
"""
20장 공통 — 종료 조건 네 가지를 한곳에. 의존성 없음.

핵심은 «어떤 이유로 끝났는지»를 돌려주는 것이다.
불리언 하나만 돌려주면 호출한 쪽이 다르게 대응할 수 없다.
"""
```

`Guards.check()`도 `bool`이 아니라 `Optional[str]`을 돌려줍니다. `ex4`는 그 아이디어를 그래프 위로 옮긴 것입니다 — 「이유 문자열 반환」이 「이유 노드로의 라우팅」이 됩니다.

---

## 5. 실행하면 무슨 일이 일어나나

`generate`가 3회차부터 더 못 고치도록 되어 있어(`if s["rounds"] < 2:` 조건) 위반 건수가 3→2→2 로 흐르고, `stalled()`가 이를 잡습니다.

```python
def stalled(scores):
    n = STALL_LIMIT + 1
    if len(scores) < n:
        return False
    w = scores[-n:]
    return w[-1] >= min(w[:-1])
```

`STALL_LIMIT = 2`이므로 최근 3개를 보고, 마지막 값이 앞 두 값의 최솟값보다 **작지 않으면**(같아도) 정체로 판정합니다. 그래서 `route`가 `"정체"`를 반환 → `add_conditional_edges` 매핑이 `"정체"` 노드로 보냄 → `mark("정체")`가 `{"ending": "정체"}` 를 씀 → `b.add_edge("정체", END)` 로 종료. 최종 출력의 `out['ending']`이 `"정체"`가 되는 경로입니다.

> «정체»로 끝났다. 위반이 3→2→2 로 가면서 마지막에 안 줄었기 때문이다.
> 횟수 상한만 있었다면 6회차까지 돌아 132를 썼을 것이다. 정체 감지가 세 회차를 아꼈다.

또 하나 눈여겨볼 점 — `route`의 검사 순서가 **성공 → 상한 → 예산 → 정체** 라는 것입니다. 여러 조건이 동시에 참이어도 `ending`에는 하나만 남습니다. 순서가 곧 우선순위이므로, 「성공했는데 마침 예산도 다 썼다」는 경우 `"성공"`이 이깁니다. 노드가 네 개여도 상태에 기록되는 이유는 언제나 하나입니다.

---

## 6. 외워야 할 것

| 요소 | 역할 |
|---|---|
| `mark(reason)` | 클로저 공장. `{"ending": reason}` 을 반환하는 노드 함수를 찍어 낸다 |
| `b.add_node(r, mark(r))` | 이유 이름 = 노드 이름. 네 개를 루프로 등록 |
| `b.add_edge(r, END)` | 이유 노드는 전부 `END`로. 되돌아갈 길 없음 |
| `route` | 상태를 읽고 문자열만 고른다. 쓰기는 안 한다 (못 한다) |
| `add_conditional_edges("검증", route, {...})` | 문자열 → 노드 이름 매핑(`path_map`). 컴파일 시 목적지 확정 + 시각화 |
| `ending: str` | 후속 조치를 나누는 근거. 불리언으로는 상한/정체 구분 불가 |

**한 문장:** 조건부 엣지는 상태를 못 쓰니까, 이유를 쓰는 일을 `mark(reason)`으로 찍어 낸 노드 네 개에 맡기고 그것들을 전부 `END`로 붙였다.

---

## 참고

- [Graph API overview — LangChain Docs](https://docs.langchain.com/oss/python/langgraph/graph-api)
- [`StateGraph.add_conditional_edges` — LangChain Reference](https://reference.langchain.com/python/langgraph/graph/state/StateGraph/add_conditional_edges)
- [is it possible to update state in condition function? — langgraph Discussion #2113](https://github.com/langchain-ai/langgraph/discussions/2113)
- [Building effective agents — Anthropic (evaluator-optimizer 패턴)](https://www.anthropic.com/engineering/building-effective-agents)
