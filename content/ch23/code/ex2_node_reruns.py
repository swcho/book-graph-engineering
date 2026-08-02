"""
예제 2 — interrupt 로 멈춘 노드는 재개할 때 «처음부터» 다시 돈다.

    python3 ex2_node_reruns.py

21장의 «슈퍼스텝 경계» 얘기가 여기서 그대로 되돌아온다.
"""

from typing import TypedDict

from langgraph.graph import END, START, StateGraph
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Command, interrupt

호출수 = {"메일": 0, "조회": 0}


class S(TypedDict):
    주문: str
    승인: str


def 나쁜노드(s: S) -> S:
    호출수["메일"] += 1
    print(f"    → 담당자에게 «검토 요청» 메일 발송 (누적 {호출수['메일']}회)")
    답 = interrupt("승인하시겠습니까?")
    return {"승인": 답}


def 좋은노드(s: S) -> S:
    답 = interrupt("승인하시겠습니까?")      # 부작용 «앞»에 둔다
    호출수["조회"] += 1
    print(f"    → 결과 기록 (누적 {호출수['조회']}회)")
    return {"승인": 답}


def build(node):
    g = StateGraph(S)
    g.add_node("검토", node)
    g.add_edge(START, "검토")
    g.add_edge("검토", END)
    return g.compile(checkpointer=InMemorySaver())


def run(label, node, tid):
    print(f"\n[{label}]")
    app = build(node)
    cfg = {"configurable": {"thread_id": tid}}
    app.invoke({"주문": "A-1024", "승인": ""}, cfg)
    print("    ...사람이 답한다...")
    app.invoke(Command(resume="승인"), cfg)


def main():
    print("interrupt() 앞에 부작용이 있으면 어떻게 되는지 본다.")
    run("부작용이 interrupt «앞»에 있다", 나쁜노드, "t1")
    run("부작용이 interrupt «뒤»에 있다", 좋은노드, "t2")

    print(
        f"\n메일 발송 {호출수['메일']}회, 결과 기록 {호출수['조회']}회.\n"
        "\n담당자가 검토 요청 메일을 두 번 받았다. 승인을 «하고 나서» 한 번 더.\n"
        "\n이유는 21장에서 본 것과 같다. 체크포인트는 노드 «경계»에 찍힌다.\n"
        "interrupt 는 노드 중간에서 멈추지만, 재개할 때는 그 노드의 처음으로 돌아간다.\n"
        "노드 안에서 interrupt 앞에 있던 코드는 두 번 실행된다.\n"
        "\n규칙은 하나다. «interrupt 앞에는 부작용을 두지 않는다.»\n"
        "읽기만 하는 코드는 괜찮다. 밖으로 나가는 것은 전부 뒤로 민다.\n"
        "\n부작용이 꼭 앞에 있어야 하면? 노드를 둘로 쪼개서\n"
        "«부작용 노드» → «interrupt 노드» 로 만든다. 그러면 경계가 사이에 생긴다."
    )


if __name__ == "__main__":
    main()
