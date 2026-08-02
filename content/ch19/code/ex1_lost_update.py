"""
예제 1 — 리듀서가 없으면 갱신이 사라진다.

    pip install "langgraph>=1.0,<2.0"
    python3 ex1_lost_update.py

확인 시점 LangGraph 1.0.1. API 키 필요 없음.
"""

import operator
from typing import Annotated, TypedDict

from langgraph.graph import END, START, StateGraph


# --- A안: 리듀서 없음 ---
class NoReducer(TypedDict):
    logs: list
    count: int


# --- B안: 리듀서 있음 ---
class WithReducer(TypedDict):
    logs: Annotated[list, operator.add]
    count: Annotated[int, operator.add]


def make(state_type):
    def worker(name):
        def fn(s):
            return {"logs": [f"{name} 실행"], "count": 1}
        return fn

    b = StateGraph(state_type)
    b.add_node("재무", worker("재무"))
    b.add_node("법무", worker("법무"))
    b.add_node("영업", worker("영업"))
    # 셋을 «동시에» 시작한다 — 같은 슈퍼스텝에 들어간다
    b.add_edge(START, "재무")
    b.add_edge(START, "법무")
    b.add_edge(START, "영업")
    b.add_edge("재무", END)
    b.add_edge("법무", END)
    b.add_edge("영업", END)
    return b.compile()


def main():
    print("노드 셋이 같은 슈퍼스텝에서 각각 logs 에 한 줄, count 에 1을 더한다.\n")

    for label, t in (("리듀서 없음", NoReducer), ("리듀서 있음", WithReducer)):
        try:
            app = make(t)
            out = app.invoke({"logs": [], "count": 0})
            print(f"[{label}]")
            print(f"    logs  {out['logs']}")
            print(f"    count {out['count']}")
        except Exception as e:
            print(f"[{label}] 예외 — {str(e).splitlines()[0][:70]}")
        print()

    print(
        "리듀서가 없으면 LangGraph 는 «같은 필드를 여럿이 쓰려 한다»고 막는다.\n"
        "막아 주는 게 다행이다. 조용히 하나만 남기는 프레임워크도 있다.\n"
        "\n리듀서가 있으면 셋이 다 합쳐진다. logs 는 이어 붙고 count 는 더해진다.\n"
        "\n여기서 중요한 건 «리듀서를 붙였다»가 아니라\n"
        "«이 필드를 여럿이 쓴다는 걸 타입에 적었다»는 것이다.\n"
        "타입을 읽으면 동시 쓰기 여부를 알 수 있다. 코드를 안 읽어도."
    )


if __name__ == "__main__":
    main()
