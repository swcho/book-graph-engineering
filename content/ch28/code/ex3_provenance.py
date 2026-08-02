"""
예제 3 — 어디서 온 사실인가. 그리고 근거가 무너지면 사실도 무너진다.

    pip install kuzu
    python3 ex3_provenance.py

모든 엣지에 출처를 달고, 출처를 철회했을 때 무엇이 같이 사라지는지 본다.
"""

import shutil
import tempfile

import kuzu

SOURCES = {
    "src1": ("사용자 발화", "2026-05-01", 1.00),
    "src2": ("사내 위키 v3", "2026-04-20", 0.90),
    "src3": ("에이전트 추론", "2026-05-02", 0.55),
    "src4": ("외부 기사", "2026-03-11", 0.40),
}

FACTS = [
    ("박민수", "이끔", "결제팀", "src1"),
    ("이서연", "속함", "결제팀", "src2"),
    ("이서연", "삶",   "마포",   "src1"),
    ("박민수", "삶",   "마포",   "src4"),      # 외부 기사에서 왔다
    ("이서연", "동료", "박민수", "src3"),      # 위 둘에서 «추론»된 것
    ("이서연", "이웃", "박민수", "src3"),      # 이것도 추론
]

# 추론된 사실이 어떤 사실에 기대고 있는지
DERIVED_FROM = {
    ("이서연", "동료", "박민수"): [("이서연", "속함", "결제팀"),
                                   ("박민수", "이끔", "결제팀")],
    ("이서연", "이웃", "박민수"): [("이서연", "삶", "마포"),
                                   ("박민수", "삶", "마포")],
}


def build(path):
    db = kuzu.Database(path)
    c = kuzu.Connection(db)
    c.execute("CREATE NODE TABLE N(name STRING, PRIMARY KEY(name))")
    c.execute("CREATE REL TABLE R(FROM N TO N, kind STRING, src STRING, "
              "conf DOUBLE, alive BOOLEAN)")
    names = set()
    for s, _k, o, _ in FACTS:
        names |= {s, o}
    for n in sorted(names):
        c.execute("CREATE (:N {name:$n})", {"n": n})
    for s, k, o, src in FACTS:
        c.execute("MATCH (a:N {name:$s}),(b:N {name:$o}) "
                  "CREATE (a)-[:R {kind:$k, src:$src, conf:$cf, alive:true}]->(b)",
                  {"s": s, "o": o, "k": k, "src": src, "cf": SOURCES[src][2]})
    return c


def show(c, title):
    print(f"\n{title}")
    r = c.execute("MATCH (a:N)-[e:R]->(b:N) WHERE e.alive "
                  "RETURN a.name, e.kind, b.name, e.src, e.conf ORDER BY e.src")
    while r.has_next():
        a, k, b, src, cf = r.get_next()
        print(f"  {a} -{k}-> {b:<8} 출처 {SOURCES[src][0]:<12} 신뢰 {cf:.2f}")


def retract(c, src):
    """출처 하나를 철회한다. 거기 기댄 추론도 같이 죽인다."""
    killed = []
    r = c.execute("MATCH (a:N)-[e:R {src:$s}]->(b:N) WHERE e.alive "
                  "RETURN a.name, e.kind, b.name", {"s": src})
    direct = []
    while r.has_next():
        direct.append(tuple(r.get_next()))
    c.execute("MATCH ()-[e:R {src:$s}]->() SET e.alive = false", {"s": src})
    killed += [(*t, "직접") for t in direct]

    # 죽은 사실에 기대고 있던 추론을 찾아 같이 죽인다
    changed = True
    while changed:
        changed = False
        for derived, bases in DERIVED_FROM.items():
            r = c.execute("MATCH (a:N {name:$s})-[e:R {kind:$k}]->(b:N {name:$o}) "
                          "WHERE e.alive RETURN 1",
                          {"s": derived[0], "k": derived[1], "o": derived[2]})
            if not r.has_next():
                continue
            for b in bases:
                r2 = c.execute("MATCH (x:N {name:$s})-[e:R {kind:$k}]->"
                               "(y:N {name:$o}) WHERE e.alive RETURN 1",
                               {"s": b[0], "k": b[1], "o": b[2]})
                if not r2.has_next():
                    c.execute("MATCH (x:N {name:$s})-[e:R {kind:$k}]->"
                              "(y:N {name:$o}) SET e.alive = false",
                              {"s": derived[0], "k": derived[1], "o": derived[2]})
                    killed.append((*derived, "연쇄"))
                    changed = True
                    break
    return killed


def main():
    tmp = tempfile.mkdtemp()
    c = build(tmp + "/db")
    show(c, "처음 상태 (사실 6개)")

    print("\n\n외부 기사(src4)가 오보로 밝혀져 철회한다.")
    killed = retract(c, "src4")
    for a, k, b, how in killed:
        print(f"  죽임: {a} -{k}-> {b}   ({how})")
    show(c, "철회 뒤")

    print(
        "\n엣지 하나를 지웠는데 둘이 사라졌다.\n"
        "«박민수가 마포에 산다»가 오보였고, 거기 기대던 «이웃이다»도 같이 무너진다.\n"
        "\n이게 출처를 다는 이유다. 사실 하나가 틀렸을 때\n"
        "«그것 때문에 믿게 된 것»을 찾아 같이 걷어 낼 수 있다.\n"
        "\n출처가 없으면 어떻게 되나. 오보인 걸 알아도 «이웃이다»는 남는다.\n"
        "그리고 그건 어디서 왔는지 아무도 모르는 사실이 된다.\n"
        "이런 것들이 쌓이면 그래프를 통째로 못 믿게 된다.\n"
        "\n에이전트가 쓰기 시작하면 «추론된 사실»의 비율이 빠르게 오른다.\n"
        "그래서 이 연쇄 철회가 읽기 전용 그래프보다 훨씬 중요해진다.\n"
        "\n한 가지 주의. 이 예제는 «기댄 관계»를 손으로 적어 뒀다.\n"
        "실무에서는 추론할 때 그때그때 기록해야 한다. 나중에는 복원 못 한다."
    )
    shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main()
