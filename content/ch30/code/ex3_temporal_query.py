"""
예제 3 — 「그때 그래프」를 되살린다. 두 가지 방법.

    pip install kuzu
    python3 ex3_temporal_query.py

방법 A — 이벤트를 재생해서 그때 상태를 만든다
방법 B — 엣지에 유효 구간을 박아 두고 쿼리로 자른다(27장)
둘은 답이 같고 값이 다르다.
"""

import shutil
import tempfile
import time

import kuzu

FACTS = [
    ("박민수", "이끔", "결제팀", "2024-01-01", "2026-03-31"),
    ("이서연", "이끔", "결제팀", "2026-04-01", "9999-12-31"),
    ("나",     "속함", "결제팀", "2023-06-01", "9999-12-31"),
    ("이서연", "속함", "결제팀", "2026-01-15", "2026-03-31"),
    ("김도현", "속함", "결제팀", "2025-02-01", "2026-06-30"),
]

# 같은 사실을 이벤트로 편 것
def to_events(facts):
    ev = []
    for s, k, o, vf, vt in facts:
        ev.append((vf, s, k, o, "추가"))
        if vt != "9999-12-31":
            ev.append((vt, s, k, o, "삭제"))
    return sorted(ev)


def build(path):
    db = kuzu.Database(path)
    c = kuzu.Connection(db)
    c.execute("CREATE NODE TABLE N(name STRING, PRIMARY KEY(name))")
    c.execute("CREATE REL TABLE R(FROM N TO N, kind STRING, "
              "vfrom STRING, vto STRING)")
    c.execute("CREATE NODE TABLE Ev(id INT64, at STRING, subj STRING, "
              "kind STRING, obj STRING, op STRING, PRIMARY KEY(id))")
    names = set()
    for s, _k, o, *_ in FACTS:
        names |= {s, o}
    for n in sorted(names):
        c.execute("CREATE (:N {name:$n})", {"n": n})
    for s, k, o, vf, vt in FACTS:
        c.execute("MATCH (a:N {name:$s}),(b:N {name:$o}) "
                  "CREATE (a)-[:R {kind:$k, vfrom:$f, vto:$t}]->(b)",
                  {"s": s, "o": o, "k": k, "f": vf, "t": vt})
    for i, (at, s, k, o, op) in enumerate(to_events(FACTS)):
        c.execute("CREATE (:Ev {id:$i, at:$at, subj:$s, kind:$k, obj:$o, "
                  "op:$op})",
                  {"i": i, "at": at, "s": s, "k": k, "o": o, "op": op})
    return c


def rows(r):
    out = []
    while r.has_next():
        out.append(tuple(r.get_next()))
    return out


def by_interval(c, t):
    return sorted(rows(c.execute(
        "MATCH (a:N)-[e:R]->(b:N) WHERE e.vfrom <= $t AND e.vto > $t "
        "RETURN a.name, e.kind, b.name", {"t": t})))


def by_replay(c, t):
    st = set()
    for at, s, k, o, op in rows(c.execute(
            "MATCH (e:Ev) WHERE e.at <= $t RETURN e.at, e.subj, e.kind, "
            "e.obj, e.op ORDER BY e.id", {"t": t})):
        if op == "추가":
            st.add((s, k, o))
        else:
            st.discard((s, k, o))
    return sorted(st)


def main():
    tmp = tempfile.mkdtemp()
    c = build(tmp + "/db")

    for t in ("2025-06-01", "2026-05-01"):
        a = by_interval(c, t)
        b = by_replay(c, t)
        print(f"[{t} 기준]")
        print(f"  구간 쿼리 {len(a)}건, 이벤트 재생 {len(b)}건, "
              f"{'같다' if a == b else '다르다'}")
        for s, k, o in a:
            print(f"      {s} -{k}-> {o}")
        print()

    # 값 비교
    N = 300
    t0 = time.perf_counter()
    for _ in range(N):
        by_interval(c, "2026-05-01")
    iv = (time.perf_counter() - t0) / N * 1000
    t0 = time.perf_counter()
    for _ in range(N):
        by_replay(c, "2026-05-01")
    rp = (time.perf_counter() - t0) / N * 1000
    print(f"조회 {N}회 평균: 구간 쿼리 {iv:.2f}ms, 이벤트 재생 {rp:.2f}ms")

    print(
        "\n답이 같다. 그리고 이 규모에서는 재생이 오히려 조금 빠르다.\n"
        "이벤트가 9개뿐이라 그렇다. 이벤트가 10만 개면 뒤집힌다.\n"
        "그러니 이 숫자로 «재생이 빠르다»고 결론 내면 안 된다.\n"
        "\n그러면 둘 중 하나만 있으면 되나. 아니다.\n"
        "\n구간 쿼리는 «상태»를 묻는 데 강하다. 그 시점에 무엇이 참이었나.\n"
        "이벤트 재생은 «변화»를 묻는 데 강하다. 무엇이 언제 왜 바뀌었나.\n"
        "\n구간 쿼리로는 «누가 바꿨나»를 못 묻는다. 엣지에 그 정보가 없으니까.\n"
        "이벤트로는 «지금 상태»를 물을 때마다 전부 재생해야 한다.\n"
        "\n그래서 실무에서는 둘 다 둔다.\n"
        "  이벤트 로그 — 진실의 원본(source of truth)\n"
        "  구간 엣지  — 이벤트에서 «만들어 낸» 조회용 뷰\n"
        "\n중요한 건 방향이다. 이벤트가 원본이고 엣지가 파생이다.\n"
        "거꾸로 하면(엣지를 고치고 이벤트를 나중에 적으면) 둘이 갈라진다.\n"
        "\n29장에서 본 «두 저장소가 갈라진다» 문제가 여기서 또 나온다.\n"
        "다만 여기서는 해법이 분명하다. 한쪽을 원본으로 정하고\n"
        "다른 쪽은 «항상 다시 만들 수 있게» 두면 된다."
    )
    shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main()
