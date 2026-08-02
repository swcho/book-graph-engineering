"""
예제 4 — 체크포인터를 무엇으로 쓰느냐가 지연을 정한다. 직접 잰다.

    pip install "langgraph>=1.0,<2.0" "langgraph-checkpoint-sqlite<3"
    python3 ex4_checkpointer_cost.py

확인 시점 LangGraph 1.0.1.
"""

import operator
import os
import sqlite3
import tempfile
import time
from typing import Annotated, TypedDict

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import END, START, StateGraph

N_STEPS = 12
PAYLOAD_SIZES = (0, 2_000, 32_000, 256_000)   # 상태에 실어 나르는 더미 데이터 크기


class S(TypedDict):
    n:    Annotated[int, operator.add]
    blob: str


def build(payload):
    def fn(s: S) -> dict:
        return {"n": 1, "blob": payload}
    b = StateGraph(S)
    prev = START
    for i in range(N_STEPS):
        name = f"s{i}"
        b.add_node(name, fn)
        b.add_edge(prev, name)
        prev = name
    b.add_edge(prev, END)
    return b


def timeit(app, cfg, payload, repeat=5):
    best = float("inf")
    for i in range(repeat):
        c = dict(cfg)
        c["configurable"] = dict(cfg["configurable"], thread_id=f"t{i}-{len(payload)}")
        t0 = time.perf_counter()
        app.invoke({"n": 0, "blob": ""}, c)
        best = min(best, time.perf_counter() - t0)
    return best * 1000


def main():
    tmpdir = tempfile.mkdtemp()
    print(f"노드 {N_STEPS}개짜리 그래프를 끝까지 돌린 시간 (ms)\n")
    print(f"{'상태 크기':>10} {'메모리':>10} {'SQLite 파일':>13} {'배수':>7}")
    print("-" * 46)

    for size in PAYLOAD_SIZES:
        payload = "x" * size
        b = build(payload)
        cfg = {"configurable": {"thread_id": "t"}}

        mem = timeit(b.compile(checkpointer=InMemorySaver()), cfg, payload)

        path = os.path.join(tmpdir, f"c{size}.sqlite")
        conn = sqlite3.connect(path, check_same_thread=False)
        disk = timeit(b.compile(checkpointer=SqliteSaver(conn)), cfg, payload)
        conn.close()

        print(f"{size:>9,}B {mem:>10.1f} {disk:>13.1f} {disk/mem:>6.1f}x")

    print(
        "\n32KB 까지는 배수가 2.0~2.8 로 거의 평평하다. 그 뒤에 꺾인다.\n"
        "작은 구간에서는 «쓰기 호출 자체»가 지배하기 때문이다.\n"
        "슈퍼스텝마다 트랜잭션을 여는 값이 상태 크기와 무관하게 붙는다.\n"
        "\n그래서 대처가 구간마다 다르다.\n"
        "  32KB 미만 — 상태를 줄여도 소용없다. «슈퍼스텝 수»를 줄여야 한다\n"
        "  32KB 이상 — 상태를 줄이는 게 바로 듣는다 (19장)\n"
        "\n제가 처음에 «상태를 줄이면 항상 빨라진다»고 생각한 게 틀렸다.\n"
        "재 보기 전에는 어느 구간에 있는지 모른다.\n"
        f"이 예제는 {N_STEPS}단계인데, 30단계짜리면 그만큼 더 든다.\n"
        "\n그런데 이걸 이유로 메모리 체크포인터를 쓰면 안 된다.\n"
        "프로세스가 죽으면 다 사라지니까. 그건 체크포인터가 아니라 캐시다.\n"
        "\n지연이 문제면 줄일 곳은 «상태 크기»지 «체크포인터 종류»가 아니다. 19장 참조."
    )


if __name__ == "__main__":
    main()
