"""
예제 4 — 생성-검증 루프에 네 가지 종료 조건을 다 붙인다.

    pip install "langgraph>=1.0,<2.0"
    python3 ex4_generator_critic.py

확인 시점 LangGraph 1.0.1. API 키 필요 없음.
"""

import operator
from typing import Annotated, TypedDict

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph

REQUIRED = ["## 개요", "## 원인", "## 조치", "## 재발 방지"]
MAX_ROUNDS, MAX_COST, STALL_LIMIT = 6, 90.0, 2


class S(TypedDict):
    text:    str
    missing: list
    rounds:  Annotated[int, operator.add]
    cost:    Annotated[float, operator.add]
    scores:  Annotated[list, operator.add]
    ending:  str          # 어떤 이유로 끝났는지. 이게 중요하다.


def generate(s: S) -> dict:
    """모델 자리. 3회차부터는 더 못 고친다 — 실제로 흔한 일이다."""
    have = [x for x in REQUIRED if x in s["text"]]
    if s["rounds"] < 2:
        have = REQUIRED[: len(have) + 1]
    text = "\n\n".join(f"{x}\n내용" for x in have)
    return {"text": text, "rounds": 1, "cost": 22.0}


def critic(s: S) -> dict:
    miss = [x for x in REQUIRED if x not in s["text"]]
    return {"missing": miss, "scores": [len(miss)]}


def stalled(scores):
    n = STALL_LIMIT + 1
    if len(scores) < n:
        return False
    w = scores[-n:]
    return w[-1] >= min(w[:-1])


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


def mark(reason):
    def fn(s: S) -> dict:
        return {"ending": reason}
    return fn


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


def main():
    cfg = {"configurable": {"thread_id": "gc"}}
    out = app.invoke({"text": "", "missing": [], "rounds": 0,
                      "cost": 0.0, "scores": [], "ending": ""}, cfg)

    print(f"끝난 이유  {out['ending']}")
    print(f"회차       {out['rounds']} / {MAX_ROUNDS}")
    print(f"쓴 비용     {out['cost']:.0f} / {MAX_COST:.0f}")
    print(f"점수 이력   {out['scores']}")
    print(f"남은 항목   {out['missing']}")

    print(
        "\n«정체»로 끝났다. 위반이 3→2→2 로 가면서 마지막에 안 줄었기 때문이다.\n"
        "\n횟수 상한만 있었다면 6회차까지 돌아 132를 썼을 것이다.\n"
        "정체 감지가 세 회차를 아꼈다.\n"
        "\n그리고 끝난 이유가 상태에 남는다는 게 중요하다.\n"
        "호출한 쪽이 이걸 보고 다르게 대응할 수 있다.\n"
        "  성공 — 그대로 쓴다\n"
        "  상한 — 사람에게 넘긴다 (더 돌리면 될 수도 있다)\n"
        "  예산 — 예산을 올릴지 물어본다\n"
        "  정체 — 사람에게 넘긴다 (더 돌려도 안 된다)\n"
        "\n«상한»과 «정체»의 대응이 다르다. 불리언 하나로는 이 구분이 안 된다."
    )


if __name__ == "__main__":
    main()
