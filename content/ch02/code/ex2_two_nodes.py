"""
예제 2 — 노드 두 개짜리 그래프. 30분 실습의 '후' 사진.

    pip install "langgraph>=1.0,<2.0"
    python3 ex2_two_nodes.py

확인 시점: LangGraph 1.0.1. API 키 필요 없음.
예제 1과 프롬프트가 글자 하나까지 같다. 달라진 건 구조뿐이다.
"""

import operator
from typing import Annotated, TypedDict

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph

from harness import REQUIREMENTS, build_prompt, check, fake_model

MAX_ROUNDS = 3


class State(TypedDict):
    spec: str
    missing: list
    rounds: Annotated[int, operator.add]
    log: Annotated[list, operator.add]


def write(state: State) -> dict:
    """생성 노드. 지적이 있으면 그걸 붙여서 다시 쓴다."""
    prompt = build_prompt(REQUIREMENTS,
                          previous=state["spec"] or None,
                          feedback=state["missing"] or None)
    spec = fake_model(prompt)
    return {
        "spec": spec,
        "rounds": 1,
        "log": [f"[생성] {state['rounds'] + 1}회차, 산출물 {len(spec)}자"],
    }


def review(state: State) -> dict:
    """검증 노드. 모델이 아니라 규칙이 본다. 그래서 결과가 흔들리지 않는다."""
    missing = check(state["spec"])
    return {
        "missing": missing,
        "log": [f"[검증] 빠진 항목 {len(missing)}개" + (f" {missing}" if missing else "")],
    }


def route(state: State) -> str:
    if not state["missing"]:
        return END
    if state["rounds"] >= MAX_ROUNDS:
        return END
    return "생성"


builder = StateGraph(State)
builder.add_node("생성", write)
builder.add_node("검증", review)
builder.add_edge(START, "생성")
builder.add_edge("생성", "검증")
builder.add_conditional_edges("검증", route, {"생성": "생성", END: END})

app = builder.compile(checkpointer=InMemorySaver())


def main():
    config = {"configurable": {"thread_id": "ch02-two-nodes"}}
    final = app.invoke({"spec": "", "missing": [], "rounds": 0, "log": []}, config)

    for line in final["log"]:
        print(" ", line)

    print("\n=== 산출물 ===")
    print(final["spec"])
    print(f"\n빠진 항목: {len(final['missing'])}개 (상한 {MAX_ROUNDS}회차)")
    print(f"체크포인트: {len(list(app.get_state_history(config)))}개")
    print(
        "\n프롬프트는 예제 1과 같다. 모델도 같다.\n"
        "노드를 둘로 쪼개고 그 사이에 조건이 붙은 화살표를 하나 놓았을 뿐이다."
    )


if __name__ == "__main__":
    main()
