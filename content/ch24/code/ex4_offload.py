"""
예제 4 — 상태에 본문을 넣지 말고 «참조»를 넣는다.

    python3 ex4_offload.py

의존성 없음(표준 sqlite3). 21장에서 잰 체크포인터 비용이
상태 크기에 어떻게 달렸는지 여기서 되갚아진다.
"""

import json
import os
import sqlite3
import tempfile
import time

DOC = "가" * 40_000          # 문서 한 편 (본문 4만 자)
N_DOCS = 6
N_STEPS = 12


def setup(path):
    db = sqlite3.connect(path)
    db.execute("CREATE TABLE doc (id TEXT PRIMARY KEY, body TEXT)")
    db.executemany("INSERT INTO doc VALUES (?,?)",
                   [(f"doc-{i}", DOC) for i in range(N_DOCS)])
    db.commit()
    return db


def run_inline(db):
    """본문을 상태에 통째로 싣고 다닌다."""
    state = {"docs": [], "note": ""}
    t0 = time.perf_counter()
    for step in range(N_STEPS):
        if step < N_DOCS:
            body = db.execute("SELECT body FROM doc WHERE id=?",
                              (f"doc-{step}",)).fetchone()[0]
            state["docs"].append({"id": f"doc-{step}", "body": body})
        blob = json.dumps(state, ensure_ascii=False)   # 슈퍼스텝마다 직렬화
        state["note"] = f"step {step}"
    return time.perf_counter() - t0, len(blob.encode())


def run_ref(db):
    """참조만 싣고, 필요할 때 꺼내 쓴다."""
    state = {"docs": [], "note": ""}
    reads = 0
    t0 = time.perf_counter()
    for step in range(N_STEPS):
        if step < N_DOCS:
            state["docs"].append({"id": f"doc-{step}", "len": len(DOC),
                                  "head": DOC[:40]})
        if step == N_STEPS - 1:          # 마지막에 실제로 한 편만 읽는다
            db.execute("SELECT body FROM doc WHERE id=?", ("doc-2",)).fetchone()
            reads += 1
        blob = json.dumps(state, ensure_ascii=False)
        state["note"] = f"step {step}"
    return time.perf_counter() - t0, len(blob.encode()), reads


def main():
    path = os.path.join(tempfile.mkdtemp(), "docs.db")
    db = setup(path)

    t1, size1 = run_inline(db)
    t2, size2, reads = run_ref(db)

    print(f"문서 {N_DOCS}편(각 {len(DOC):,}자)을 {N_STEPS}단계 그래프에서 다룬다.\n")
    print(f"{'방식':<22}{'상태 크기':>14}{'직렬화 시간':>14}{'문서 조회':>10}")
    print("-" * 62)
    print(f"{'본문을 상태에':<22}{size1:>13,}B{t1 * 1000:>12.1f}ms{0:>10}")
    print(f"{'참조만 상태에':<22}{size2:>13,}B{t2 * 1000:>12.1f}ms{reads:>10}")
    print(f"\n상태 크기 {size1 / size2:,.0f}배 차이, 직렬화 시간 {t1 / t2:,.0f}배 차이")

    print(
        "\n21장에서 «32KB를 넘으면 체크포인터 비용이 꺾인다»고 쟀다.\n"
        f"본문을 실으면 {size1:,}B 다. 한참 넘는다.\n"
        f"참조만 실으면 {size2:,}B 다. 꺾이는 지점 아래다.\n"
        "\n두 장의 얘기가 여기서 만난다.\n"
        "«컨텍스트를 줄이는 일»과 «체크포인트를 싸게 만드는 일»이 같은 일이었다.\n"
        "\n대신 값을 치른다. 마지막에 문서 한 편을 꺼내 오는 조회가 한 번 든다.\n"
        "6편을 다 실어 놓고 1편만 쓸 거면, 5편은 그냥 짐이었다.\n"
        "\n판단 기준은 «몇 번 쓰나»다.\n"
        "  거의 매 단계 쓴다   → 상태에 싣는다\n"
        "  가끔 한 번 쓴다    → 참조만 싣고 그때 꺼낸다\n"
        "  안 쓸 수도 있다    → 참조도 싣지 말고 색인만 남긴다"
    )


if __name__ == "__main__":
    main()
