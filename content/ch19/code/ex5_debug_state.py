"""
예제 5 — 상태 이력으로 «왜 이렇게 됐나»를 되짚는다.

    pip install "langgraph>=1.0,<2.0"
    python3 ex5_debug_state.py

확인 시점 LangGraph 1.0.1.
체크포인트가 있으면 디버깅이 «로그 읽기»가 아니라 «시간 여행»이 된다.
"""

import operator
from typing import Annotated, TypedDict

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph

BUDGET = 100


class S(TypedDict):
    쓴돈: Annotated[int, operator.add]
    기록: Annotated[list, operator.add]
    회차: Annotated[int, operator.add]


def 검색(s):
    return {"쓴돈": 30, "기록": ["검색 30"], "회차": 1}


def 정리(s):
    # 회차가 늘수록 비싸진다 — 실제로 흔한 패턴
    cost = 20 + s["회차"] * 15
    return {"쓴돈": cost, "기록": [f"정리 {cost}"]}


def route(s):
    if s["쓴돈"] >= BUDGET:
        return END
    return END if s["회차"] >= 4 else "검색"


b = StateGraph(S)
b.add_node("검색", 검색)
b.add_node("정리", 정리)
b.add_edge(START, "검색")
b.add_edge("검색", "정리")
b.add_conditional_edges("정리", route, {"검색": "검색", END: END})
app = b.compile(checkpointer=InMemorySaver())


def main():
    cfg = {"configurable": {"thread_id": "dbg"}}
    out = app.invoke({"쓴돈": 0, "기록": [], "회차": 0}, cfg)

    print(f"예산 {BUDGET}, 최종 사용 {out['쓴돈']}, 회차 {out['회차']}")
    print(f"기록 {out['기록']}\n")

    print("체크포인트를 거꾸로 훑어 «어디서 예산을 넘겼나» 찾기")
    hist = list(app.get_state_history(cfg))
    culprit = None
    for snap in hist:
        spent = snap.values.get("쓴돈", 0)
        if spent < BUDGET:
            culprit = snap
            break
    for snap in reversed(hist):
        spent = snap.values.get("쓴돈", 0)
        mark = "  ← 여기서 넘었다" if snap is not culprit and spent >= BUDGET else ""
        nxt = ", ".join(snap.next) if snap.next else "(끝)"
        print(f"    쓴돈 {spent:>4}  다음 {nxt:<10}{mark}")
        if mark:
            break

    print(
        "\n로그만 있으면 «100 을 넘었다»까지만 안다.\n"
        "체크포인트가 있으면 «넘기 직전 상태»로 되감아서 그때 무엇을 하려 했는지 본다.\n"
        "\n그리고 되감은 지점에서 «다르게» 이어 갈 수도 있다.\n"
        "app.update_state 로 값을 고치고 그 지점부터 다시 돌리는 것이다.\n"
        "«만약 예산이 150 이었다면»을 실제로 돌려 볼 수 있다.\n"
        "\n이게 체크포인트의 두 번째 값어치다. 첫째는 복구, 둘째는 디버깅.\n"
        "그리고 실무에서는 둘째를 훨씬 자주 쓴다."
    )


if __name__ == "__main__":
    main()
