"""
예제 4 — 같은 작업을 체인과 상태 그래프로. 코드 길이와 «할 수 있는 것»을 비교한다.

    pip install "langgraph>=1.0,<2.0"
    python3 ex4_same_task_two_ways.py

확인 시점 LangGraph 1.0.1. API 키 필요 없음.
"""

import operator
from typing import Annotated, TypedDict

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph

REQUIRED = ["## 개요", "## 원인", "## 조치"]


def draft(text, hint=None):
    """모델 자리. 지적이 있으면 그 절을 채운다."""
    have = [s for s in REQUIRED if s in (text or "")]
    if hint:
        have = list(dict.fromkeys(have + hint))
    else:
        have = REQUIRED[:1]          # 처음엔 한 절만 쓴다
    return "\n\n".join(f"{s}\n내용" for s in have)


def check(text):
    return [s for s in REQUIRED if s not in text]


# ---------------------------------------------------------------- 체인
def run_chain():
    text = draft("")
    missing = check(text)
    return text, missing, ["작성", "검사"]


# ---------------------------------------------------------------- 상태 그래프
class S(TypedDict):
    text: str
    missing: list
    rounds: Annotated[int, operator.add]
    trace: Annotated[list, operator.add]


def n_draft(s: S) -> dict:
    t = draft(s["text"], hint=s["missing"] or None)
    return {"text": t, "rounds": 1, "trace": [f"작성{s['rounds']+1}"]}


def n_check(s: S) -> dict:
    return {"missing": check(s["text"]), "trace": ["검사"]}


def route(s: S) -> str:
    if not s["missing"]:
        return END
    return END if s["rounds"] >= 4 else "작성"


b = StateGraph(S)
b.add_node("작성", n_draft)
b.add_node("검사", n_check)
b.add_edge(START, "작성")
b.add_edge("작성", "검사")
b.add_conditional_edges("검사", route, {"작성": "작성", END: END})
app = b.compile(checkpointer=InMemorySaver())


def main():
    t1, m1, tr1 = run_chain()
    print("[체인]")
    print(f"    거친 단계 {tr1}")
    print(f"    빠진 절 {m1}")

    cfg = {"configurable": {"thread_id": "ch18"}}
    f = app.invoke({"text": "", "missing": [], "rounds": 0, "trace": []}, cfg)
    print("\n[상태 그래프]")
    print(f"    거친 단계 {f['trace']}")
    print(f"    빠진 절 {f['missing']}")
    print(f"    체크포인트 {len(list(app.get_state_history(cfg)))}개")

    print(
        "\n체인은 «검사»까지 하고 끝난다. 빠진 걸 알아도 고칠 자리가 없다.\n"
        "상태 그래프는 검사 결과를 보고 작성으로 돌아간다.\n"
        "\n늘어난 코드는 조건 함수 하나와 엣지 한 줄이다.\n"
        "그 대신 얻은 것 셋.\n"
        "  1. 되돌아갈 수 있다\n"
        "  2. 몇 번 돌았는지 상태에 있다 (프롬프트가 아니라)\n"
        "  3. 매 단계 체크포인트가 남는다 — 죽어도 이어서 할 수 있다\n"
        "\n2번이 특히 중요하다. «3번까지만 시도해»를 프롬프트에 적으면 그건 부탁이고,\n"
        "상태에 적으면 그건 보장이다."
    )


if __name__ == "__main__":
    main()
