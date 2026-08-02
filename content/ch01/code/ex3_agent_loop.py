"""
예제 3 — 같은 질문을 에이전트 루프로. 단 '그래프로 그린' 루프로.

    pip install "langgraph>=1.0,<2.0"
    python3 ex3_agent_loop.py

확인 시점: LangGraph 1.0.1 기준. API 키가 필요 없다.
모델 자리에는 정해진 답을 내놓는 가짜 함수를 끼워 두었다.
이 예제가 보여 주려는 건 모델의 똑똑함이 아니라 루프의 모양이니까.

첫 시도에서 일부러 틀린 술어를 고르게 해 두었다. 재시도 한 번에 스스로 고친다.
그리고 무한히 고치지 못하도록 종료 조건이 상태 안에 들어 있다.
"""

import operator
from typing import Annotated, TypedDict

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph

from ex2_graph_grounded import build_graph
from notes import GROUND_TRUTH, QUESTION, TRIPLES

MAX_TRIES = 3
GRAPH = build_graph(TRIPLES)


class State(TypedDict):
    question: str
    predicate: str
    findings: list
    tries: Annotated[int, operator.add]   # 리듀서: 반환값을 더한다
    log: Annotated[list, operator.add]    # 리듀서: 반환 리스트를 이어 붙인다


# ---------------------------------------------------------------- 노드 3개
def plan(state: State) -> dict:
    """모델 자리. 어떤 술어를 따라갈지 고른다."""
    guess = "해지의사" if state["tries"] == 0 else "해지"
    return {
        "predicate": guess,
        "tries": 1,
        "log": [f"[계획] {state['tries'] + 1}번째 시도, 술어를 '{guess}'로 잡음"],
    }


def act(state: State) -> dict:
    """도구 자리. 그래프를 실제로 읽는다."""
    hits = []
    for node, edges in GRAPH.items():
        ends = [e for e in edges
                if e[0] == state["predicate"] and e[2]["연월"].startswith("2024")]
        for _, _, end_props in ends:
            if any(e[0] == "체결" and e[2]["연월"] > end_props["연월"] for e in edges):
                hits.append(node)
    return {
        "findings": sorted(set(hits)),
        "log": [f"[실행] '{state['predicate']}' 경로로 {len(set(hits))}건"],
    }


def verify(state: State) -> dict:
    ok = len(state["findings"]) > 0
    return {"log": [f"[검증] {'근거 있음' if ok else '근거 없음'}"]}


def route(state: State) -> str:
    """종료 조건. 이 함수가 없으면 그림 5의 루프가 된다."""
    if state["findings"]:
        return END
    if state["tries"] >= MAX_TRIES:
        return END
    return "계획"


# ---------------------------------------------------------------- 그래프 조립
builder = StateGraph(State)
builder.add_node("계획", plan)
builder.add_node("실행", act)
builder.add_node("검증", verify)
builder.add_edge(START, "계획")
builder.add_edge("계획", "실행")
builder.add_edge("실행", "검증")
builder.add_conditional_edges("검증", route, {"계획": "계획", END: END})

app = builder.compile(checkpointer=InMemorySaver())


def main():
    config = {"configurable": {"thread_id": "ch01-demo"}}
    seed = {"question": QUESTION, "predicate": "", "findings": [], "tries": 0, "log": []}
    final = app.invoke(seed, config)

    print(f"질문: {QUESTION}\n")
    for line in final["log"]:
        print(" ", line)

    found = set(final["findings"])
    print(f"\n답: {sorted(found)}")
    print(f"정답: {sorted(GROUND_TRUTH)}")
    print(f"맞았나: {'예' if found == GROUND_TRUTH else '아니오'}")
    print(f"총 시도 횟수: {final['tries']} (상한 {MAX_TRIES})")

    # 체크포인트가 남아 있다. 이 줄이 4부 전체의 예고편이다.
    history = list(app.get_state_history(config))
    print(f"\n저장된 체크포인트: {len(history)}개")
    print("가장 최근 체크포인트에서 다음에 갈 노드:", app.get_state(config).next or "(없음, 종료)")


if __name__ == "__main__":
    main()
