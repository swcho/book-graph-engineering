"""
예제 2 — 슈퍼스텝 경계를 눈으로 본다.

    pip install "langgraph>=1.0,<2.0"
    python3 ex2_superstep.py

확인 시점 LangGraph 1.0.1.
"""

import operator
from typing import Annotated, TypedDict

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph


class S(TypedDict):
    seen: Annotated[list, operator.add]
    step: int


def mk(name):
    def fn(s):
        # 이 노드가 «본» 상태를 기록한다. 같은 슈퍼스텝이면 같은 걸 본다.
        return {"seen": [f"{name}: step={s['step']}, seen={len(s['seen'])}개"]}
    return fn


def bump(s):
    return {"step": s["step"] + 1, "seen": ["--- 경계 ---"]}


b = StateGraph(S)
for n in ("A", "B", "C"):
    b.add_node(n, mk(n))
b.add_node("경계", bump)
b.add_node("D", mk("D"))
b.add_node("E", mk("E"))

b.add_edge(START, "A")
b.add_edge(START, "B")
b.add_edge(START, "C")
b.add_edge("A", "경계")
b.add_edge("B", "경계")
b.add_edge("C", "경계")
b.add_edge("경계", "D")
b.add_edge("경계", "E")
b.add_edge("D", END)
b.add_edge("E", END)

app = b.compile(checkpointer=InMemorySaver())


def main():
    cfg = {"configurable": {"thread_id": "ss"}}
    out = app.invoke({"seen": [], "step": 0}, cfg)

    print("실행 순서와 각 노드가 «본» 상태\n")
    for line in out["seen"]:
        print("   ", line)

    print("\n슈퍼스텝별 체크포인트")
    hist = list(app.get_state_history(cfg))
    for i, snap in enumerate(reversed(hist)):
        nxt = ", ".join(snap.next) if snap.next else "(끝)"
        print(f"    {i}. 다음에 갈 노드: {nxt:<14} "
              f"seen {len(snap.values.get('seen', []))}개")

    print(
        "\nA·B·C 가 전부 «seen=0개»를 봤다. 같은 슈퍼스텝이라 같은 상태 사본을 받았기 때문이다.\n"
        "서로가 쓴 걸 못 본다. 이게 슈퍼스텝의 성질이다.\n"
        "\nD·E 는 «경계» 노드가 끝난 뒤라 앞의 결과를 다 본다.\n"
        "\n그래서 «같은 슈퍼스텝 안에서 서로 결과를 참조»하는 설계는 안 된다.\n"
        "필요하면 사이에 노드를 하나 넣어 경계를 만들어야 한다.\n"
        "제가 이걸 몰라서 «왜 B 가 A 의 결과를 못 보지»로 반나절을 썼다."
    )


if __name__ == "__main__":
    main()
