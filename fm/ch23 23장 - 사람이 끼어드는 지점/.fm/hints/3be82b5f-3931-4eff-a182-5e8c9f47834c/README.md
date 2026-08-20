# 중단이 발생했는지 어떻게 확인하는가?

> `invoke` 결과에 `__interrupt__` 키가 있는지 본다. 그 안의 `value`가 사람에게 물을 내용이다.

## 한 줄로

`interrupt()`는 **예외를 던져서 호출자에게 알리는 방식이 아니다.** 그래프가 정상적으로 「멈춘 상태」로 돌아오고, 그 사실은 `invoke()` 반환값에 붙은 `__interrupt__` 키로 표시된다. 그래서 확인은 `try/except`가 아니라 **딕셔너리 키 검사**다.

```python
out = app.invoke({"금액": 300_000, "승인": "", "결과": ""}, cfg)

if "__interrupt__" in out:
    물음 = out["__interrupt__"][0].value   # ← 사람에게 보여 줄 내용
    ...
```

## 왜 「키 검사」인가 — 반환값의 두 얼굴

`invoke()`의 반환값은 상황에 따라 의미가 다르다.

| 상황 | 반환값 | 확인 방법 |
|---|---|---|
| 끝까지 다 돌았다 | 최종 상태 딕셔너리 (`{"금액":…, "승인":…, "결과":…}`) | `__interrupt__` 없음 |
| 중간에 멈췄다 | 그 시점까지의 상태 **+** `__interrupt__` 키 | `__interrupt__` 있음 |

즉 `__interrupt__`는 **상태 스키마에 없는 예약 키**다. `TypedDict`로 선언한 `S`에는 `금액`·`승인`·`결과`만 있지만, 멈춘 경우 런타임이 `__interrupt__`를 하나 더 얹어서 돌려준다. 그래서 「끝났는지 / 물어야 하는지」를 구분하는 유일한 신호가 된다.

멈춘 상태에서 `out["결과"]`를 바로 읽으면 아직 `실행` 노드가 안 돌았으니 빈 문자열이다. 키 검사를 건너뛰면 여기서 조용히 틀린다.

## `__interrupt__` 안에 뭐가 들었나

값은 **`Interrupt` 객체의 시퀀스(튜플/리스트)** 다. 단수가 아니라 복수인 이유는 병렬 분기에서 여러 노드가 동시에 `interrupt()`를 부를 수 있기 때문이다.

```python
out["__interrupt__"]
# (Interrupt(value={'물음': '이 환불을 승인하시겠습니까?', '금액': 300000,
#                   '근거': '고객 요청 · 상품 미개봉'},
#            id='a1b2c3…'),)
```

`Interrupt` 객체의 주요 필드:

| 필드 | 뜻 |
|---|---|
| `value` | `interrupt(...)`에 넘긴 값 그대로. JSON 직렬화 가능한 아무 값(문자열, dict, list…). **사람에게 보여 줄 내용이 여기 있다.** |
| `id` | 이 중단의 고유 식별자. 체크포인트 네임스페이스 + 카운터로 만들어져서 재시도해도 같다. 병렬 중단이 여러 개일 때 「어느 물음에 대한 답인지」 짝지을 때 쓴다. |

ex1에서는 `interrupt()`에 dict를 넘겼으니 `value`도 dict다.

```python
답 = interrupt({
    "물음": "이 환불을 승인하시겠습니까?",
    "금액": s["금액"],
    "근거": "고객 요청 · 상품 미개봉",
})
```
↓ 호출자 쪽에서
```python
물음 = out["__interrupt__"][0].value
print(f"  [멈춤]  {물음['물음']}  (근거: {물음['근거']})")
```

여기서 `value`를 「물음 문자열」로만 생각하면 안 된다. **사람이 판단하는 데 필요한 근거를 통째로 담는 자리**다. 23.5절의 감사 기록에서 「보여 준 내용(`shown`)」으로 남길 것도 결국 이 `value`다.

## 확인한 다음 — 이어 붙는 흐름

```python
def run(금액, 사람답변=None):
    cfg = {"configurable": {"thread_id": f"환불-{금액}"}}
    out = app.invoke({"금액": 금액, "승인": "", "결과": ""}, cfg)

    if "__interrupt__" in out:                 # ① 멈췄나?
        물음 = out["__interrupt__"][0].value   # ② 뭘 물어야 하나?
        상태 = app.get_state(cfg)
        print(f"다음에 실행할 노드: {상태.next}")   # ('사람확인',)
        out = app.invoke(Command(resume=사람답변), cfg)  # ③ 답 넣고 재개

    print(out["결과"])
```

세 단계가 한 세트다.

1. **`__interrupt__` 키로 멈춤 감지**
2. **`.value`로 물을 내용 꺼내기**
3. **`Command(resume=답)`으로 재개** — 같은 `thread_id`(`cfg`)여야 한다. 체크포인터가 그 스레드의 멈춘 자리를 기억하고 있다.

`resume` 값은 멈춘 지점의 `interrupt()` 호출이 **반환하는 값**이 된다. 즉 `답 = interrupt({...})`의 `답`에 `"승인"`이 들어간다.

## 대안 — `get_state()`로 확인하기

`invoke()` 반환값을 손에 들고 있지 않은 경우(다른 프로세스, 웹 요청, 사흘 뒤 배치)에는 반환값을 볼 수 없다. 이때는 **스레드 상태를 조회**한다.

```python
snap = app.get_state(cfg)

snap.next          # ('사람확인',)  — 비어 있지 않으면 아직 안 끝났다
snap.interrupts    # (Interrupt(value={...}, id='…'),)  — 대기 중인 동적 중단
snap.tasks         # 대기 중인 태스크들; 각 태스크의 .interrupts 로도 접근
```

- `snap.next`가 **비어 있으면** 그래프가 끝난 것이다.
- `snap.next`가 있고 `snap.interrupts`(또는 `snap.tasks[i].interrupts`)에 항목이 있으면 **사람 답을 기다리는 중**이다.

이게 실무에서 더 자주 쓰는 경로다. 23장이 강조하는 「프로세스를 붙잡고 있지 않아도 된다」가 성립하려면, 멈춤 여부를 **반환값이 아니라 저장된 상태에서** 되읽을 수 있어야 하기 때문이다. 승인 대기 목록 화면은 스레드마다 `get_state()`를 돌려서 그린다.

| 확인 경로 | 언제 |
|---|---|
| `out["__interrupt__"]` | 방금 `invoke()`를 부른 그 자리에서 |
| `get_state(cfg).interrupts` / `.tasks[].interrupts` | 나중에, 다른 프로세스에서, 대기 목록을 훑을 때 |

## 자주 하는 실수

- **`try/except`로 잡으려 한다.** `interrupt()`는 내부적으로 특수 신호를 쓰지만 호출자에게는 예외로 올라오지 않는다. 예외 처리로 감싸면 아무것도 안 잡히고, 최악의 경우 내부 신호를 삼켜서 중단이 깨진다.
- **`out["__interrupt__"]`를 객체 하나로 본다.** 시퀀스다. `[0]`을 붙여야 `Interrupt` 하나가 나온다.
- **`.value`를 안 붙이고 그대로 출력한다.** `Interrupt(value=…, id=…)` 래퍼가 통째로 찍힌다.
- **재개할 때 `thread_id`를 바꾼다.** 다른 스레드에는 멈춘 자리가 없어서 처음부터 다시 돈다.
- **체크포인터 없이 `interrupt()`를 쓴다.** 멈춘 자리를 저장할 곳이 없다. ex1이 `InMemorySaver()`를 컴파일 시점에 넘기는 이유다. 운영에서는 21장에서 본 디스크 체크포인터를 써야 사흘 뒤 답변도 이어진다.

## 이어지는 함정 (23.2절)

`__interrupt__`를 확인하고 재개하면, 멈췄던 노드는 **처음부터 다시 돈다.** 체크포인트는 노드 경계에 찍히지 실행 중간에 찍히지 않기 때문이다. 그래서 `interrupt()` **앞**에 메일 발송 같은 부작용을 두면 두 번 나간다.

```python
def 나쁜노드(s):
    메일발송()                    # 재개 시 또 실행된다
    답 = interrupt("승인?")
    return {"승인": 답}

def 좋은노드(s):
    답 = interrupt("승인?")       # 부작용을 뒤로 민다
    기록()
    return {"승인": 답}
```

읽기만 하는 코드는 앞에 둬도 되고, 밖으로 나가는 것은 전부 뒤로 민다. 꼭 앞에 있어야 하면 노드를 「부작용 노드 → interrupt 노드」로 쪼개서 사이에 경계를 만든다.

## 출처

- [Interrupts — LangChain/LangGraph docs](https://docs.langchain.com/oss/python/langgraph/interrupts)
- [Human-in-the-Loop and Interrupts — langgraph DeepWiki](https://deepwiki.com/langchain-ai/langgraph/3.7-human-in-the-loop-and-interrupts)
- 본문 예제: `content/ch23/code/ex1_interrupt.py`, `ex2_node_reruns.py`
