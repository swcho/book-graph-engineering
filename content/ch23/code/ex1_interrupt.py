"""
예제 1 — 그래프를 «사람 앞에서» 멈추고, 답을 받아 이어 간다.

    pip install "langgraph>=1.0,<2.0"
    python3 ex1_interrupt.py

체크포인터가 있어야 멈춘 자리를 기억한다. 21장에서 쓴 그것이다.
"""

from typing import TypedDict

from langgraph.graph import END, START, StateGraph
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Command, interrupt


class S(TypedDict):
    금액: int
    승인: str
    결과: str


def 초안(s: S) -> S:
    print(f"  [초안]  {s['금액']:,}원 환불 요청서를 만들었다")
    return {}


def 사람확인(s: S) -> S:
    if s["금액"] < 100_000:
        print("  [확인]  10만 원 미만이라 사람에게 안 묻는다")
        return {"승인": "자동"}

    # 여기서 그래프가 «멈춘다». 예외가 아니라 정상적인 중단이다.
    답 = interrupt({
        "물음": "이 환불을 승인하시겠습니까?",
        "금액": s["금액"],
        "근거": "고객 요청 · 상품 미개봉",
    })
    print(f"  [확인]  사람이 «{답}» 라고 했다")
    return {"승인": 답}


def 실행(s: S) -> S:
    if s["승인"] in ("자동", "승인"):
        return {"결과": f"{s['금액']:,}원 환불 완료"}
    return {"결과": "환불 거절 — 사유를 고객에게 안내"}


g = StateGraph(S)
for name, fn in (("초안", 초안), ("사람확인", 사람확인), ("실행", 실행)):
    g.add_node(name, fn)
g.add_edge(START, "초안")
g.add_edge("초안", "사람확인")
g.add_edge("사람확인", "실행")
g.add_edge("실행", END)

app = g.compile(checkpointer=InMemorySaver())


def run(금액, 사람답변=None):
    cfg = {"configurable": {"thread_id": f"환불-{금액}"}}
    print(f"\n=== {금액:,}원 ===")
    out = app.invoke({"금액": 금액, "승인": "", "결과": ""}, cfg)

    if "__interrupt__" in out:
        물음 = out["__interrupt__"][0].value
        print(f"  [멈춤]  {물음['물음']}  (근거: {물음['근거']})")
        상태 = app.get_state(cfg)
        print(f"          다음에 실행할 노드: {상태.next}")
        print(f"  ...사람이 답할 때까지 여기서 기다린다. 프로세스는 안 붙잡고 있어도 된다...")
        out = app.invoke(Command(resume=사람답변), cfg)

    print(f"  [끝]    {out['결과']}")


if __name__ == "__main__":
    run(50_000)
    run(300_000, 사람답변="승인")
    run(900_000, 사람답변="거절")

    print(
        "\n50,000원짜리는 사람을 안 부른다. 부르면 안 된다.\n"
        "«모든 것을 사람이 본다»는 정책은 아무것도 안 보는 정책과 같아진다.\n"
        "\n중요한 건 멈춘 뒤에 프로세스를 붙잡고 있지 않아도 된다는 점이다.\n"
        "상태가 체크포인터에 저장돼 있으니, 서버를 재시작해도 그 자리에 있다.\n"
        "사람이 사흘 뒤에 답해도 이어서 간다.\n"
        "\n이게 «사람을 기다리는 while 루프»와 결정적으로 다른 부분이다."
    )
