# `ex1_crash_resume.py`에서 이어서 실행하는 방법

## 핵심 답

`app.get_state(cfg).next`가 **비어 있지 않으면** 이전 실행이 중간에 멈춰 있다는 뜻이므로,
`app.invoke(None, cfg)`처럼 **입력에 `None`을 주어** 호출한다.
LangGraph에서 입력 `None`은 "새 입력 없이, 체크포인트에 저장된 상태에서 **이어서** 실행하라"는 의미다.

## 예제 코드의 재개 분기

```python
conn = sqlite3.connect(DB, check_same_thread=False)
saver = SqliteSaver(conn)
app = b.compile(checkpointer=saver)
cfg = {"configurable": {"thread_id": "job-1"}}

snap = app.get_state(cfg)
if snap.next:
    print(f"이전 실행이 «{', '.join(snap.next)}» 앞에서 멈춰 있다. 이어서 간다.")
    out = app.invoke(None, cfg)          # None 을 주면 «이어서»
else:
    print("새로 시작한다.")
    out = app.invoke({"done": [], "step": 0}, cfg)
```

동작을 조각별로 나누면 이렇다.

| 조각 | 역할 |
|---|---|
| `SqliteSaver(conn)` + `compile(checkpointer=...)` | 슈퍼스텝 경계마다 상태를 SQLite 파일(`ckpt.sqlite`)에 저장 |
| `cfg = {"configurable": {"thread_id": "job-1"}}` | 체크포인트를 조회·저장하는 키. 같은 `thread_id`로 다시 부르면 같은 작업의 이력에 붙는다 |
| `app.get_state(cfg)` | 해당 스레드의 **최신 체크포인트**를 `StateSnapshot`으로 반환 |
| `snap.next` | 다음에 실행될 예정이었던 노드 이름들의 튜플. 끝까지 완주했거나 이력이 없으면 빈 튜플 |
| `app.invoke(None, cfg)` | 입력 없이 호출 → 저장된 상태를 그대로 복원해 `next` 노드부터 재개 |

## `snap.next`가 왜 판별 기준인가

`StateSnapshot.next`는 "체크포인트는 찍혔는데 아직 실행 안 된 다음 노드들"이다.

- **처음 실행**: 이 `thread_id`로 저장된 체크포인트가 없어 `next`가 비어 있음 → 초기 상태 `{"done": [], "step": 0}`을 넣고 새로 시작.
- **중간에 죽은 뒤 재실행**: 예를 들어 `CRASH_AT=3`으로 "결제" 노드 실행 중 `sys.exit(17)`로 죽으면, 마지막 체크포인트는 "계산"까지 끝난 시점이고 `snap.next == ("결제",)`가 된다 → `invoke(None, cfg)`로 "결제"부터 다시 실행.
- **완주한 뒤 재실행**: `END`까지 갔으면 `next`가 비어 있어 다시 새로 시작하는 분기를 탄다.

## `invoke(None, ...)`의 의미

- `None`이 아닌 값을 주면 그 값이 **새 입력으로 상태에 병합**된다. 이 예제 상태는 `Annotated[list, operator.add]` / `Annotated[int, operator.add]` 리듀서를 쓰므로, 재개 시 초기값을 또 넣으면 값이 누적·오염될 수 있다.
- `None`을 주면 입력 병합 없이 마지막 체크포인트의 상태로 복원해서, `next`에 기록된 노드부터 실행을 이어간다. 이는 `interrupt` 후 재개(human-in-the-loop)와 크래시 후 재개 모두에 쓰이는 LangGraph의 공통 재개 시맨틱이다.

## 전제 조건 두 가지

1. **내구성 있는 체크포인터**: `InMemorySaver`(메모리)는 프로세스가 죽으면 같이 사라지므로 이 재개가 성립하지 않는다. 예제 docstring이 강조하듯 "메모리 체크포인터는 체크포인터가 아니라 캐시"다. 그래서 SQLite 파일을 쓴다.
2. **같은 `thread_id`**: 체크포인트는 `thread_id` 단위로 저장·조회되므로, 재실행 때 반드시 같은 값("job-1")을 넘겨야 이전 이력에 이어 붙는다.

## 시연 흐름 (`run_crash_demo.sh`)

```bash
rm -f ckpt.sqlite
CRASH_AT=3 python3 ex1_crash_resume.py   # 1회차: "결제" 노드에서 exit 17로 죽는다
python3 ex1_crash_resume.py              # 2회차: next가 남아 있어 "결제"부터 이어서 완주
```

2회차는 코드 변경이나 특별한 플래그 없이 **그냥 같은 스크립트를 다시 실행**할 뿐이다.
재개 여부 판단(`get_state().next`)과 재개 호출(`invoke(None, cfg)`)이 `main()` 안에 이미 들어 있기 때문이다.

## 주의: 재개는 "체크포인트 경계부터 다시"다

체크포인트는 슈퍼스텝 **경계에만** 찍힌다. 죽은 노드가 이미 절반쯤 수행한 부작용(예: 결제 API 호출)은 되돌아오지 않고, 재개하면 그 노드를 **처음부터 다시** 실행한다. 그래서 이 장의 후속 예제들이 멱등 키(ex2)와 부작용 로그(ex3)를 다룬다 — 재개가 안전하려면 "다시 해도 되는" 노드여야 한다.
