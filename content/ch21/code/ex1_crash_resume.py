"""
예제 1 — 프로세스를 진짜로 죽여 보고 이어서 돌린다.

    pip install "langgraph>=1.0,<2.0"
    python3 ex1_crash_resume.py

확인 시점 LangGraph 1.0.1. SQLite 체크포인터를 쓴다.
«메모리 체크포인터로는 이 예제가 성립하지 않는다»는 게 요점이다.
"""

import operator
import os
import sqlite3
import sys
from typing import Annotated, TypedDict

from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import END, START, StateGraph

DB = "ckpt.sqlite"
CRASH_AT = int(os.environ.get("CRASH_AT", "0"))   # 0 이면 안 죽는다


class S(TypedDict):
    done: Annotated[list, operator.add]
    step: Annotated[int, operator.add]


def make(name, idx):
    def fn(s: S) -> dict:
        if CRASH_AT == idx:
            print(f"    [{name}] 실행 중 프로세스가 죽는다")
            sys.exit(17)
        print(f"    [{name}] 완료")
        return {"done": [name], "step": 1}
    return fn


NODES = ["조회", "계산", "결제", "통보"]

b = StateGraph(S)
prev = START
for i, n in enumerate(NODES, 1):
    b.add_node(n, make(n, i))
    b.add_edge(prev, n)
    prev = n
b.add_edge(prev, END)


def main():
    conn = sqlite3.connect(DB, check_same_thread=False)
    saver = SqliteSaver(conn)
    app = b.compile(checkpointer=saver)
    cfg = {"configurable": {"thread_id": "job-1"}}

    snap = app.get_state(cfg)
    if snap.next:
        print(f"이전 실행이 «{', '.join(snap.next)}» 앞에서 멈춰 있다. 이어서 간다.")
        out = app.invoke(None, cfg)          # None 을 주면 «이어서»
    else:
        print("새로 시작한다.")
        out = app.invoke({"done": [], "step": 0}, cfg)

    print(f"\n끝난 단계 {out['done']}  (총 {out['step']}개)")
    conn.close()


if __name__ == "__main__":
    main()
