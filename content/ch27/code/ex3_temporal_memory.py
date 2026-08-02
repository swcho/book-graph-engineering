"""
예제 3 — 기억은 «언제부터 언제까지» 참이었나.

    pip install kuzu
    python3 ex3_temporal_memory.py

「박민수가 팀장이다」는 영원한 사실이 아니다.
15장에서 본 이시간(bitemporal) 모델을 기억에 적용한다.
"""

import shutil
import tempfile

import kuzu

# (주어, 관계, 목적어, 유효 시작, 유효 끝(None=지금도), 기록 시각)
FACTS = [
    ("박민수", "이끔",  "결제팀", "2024-01-01", "2026-03-31", "2024-01-05"),
    ("이서연", "이끔",  "결제팀", "2026-04-01", None,         "2026-04-02"),
    ("나",     "속함",  "결제팀", "2023-06-01", None,         "2023-06-01"),
    ("나",     "선호",  "채식",   "2025-09-01", None,         "2025-09-10"),
    ("나",     "선호",  "육식",   "2023-01-01", "2025-08-31", "2023-01-15"),
]

ASKED = ["2025-01-15", "2026-05-20"]


def build(path):
    db = kuzu.Database(path)
    c = kuzu.Connection(db)
    c.execute("CREATE NODE TABLE N(name STRING, PRIMARY KEY(name))")
    c.execute("CREATE REL TABLE R(FROM N TO N, kind STRING, "
              "vfrom STRING, vto STRING, recorded STRING)")
    names = set()
    for s, _k, o, *_ in FACTS:
        names |= {s, o}
    for n in sorted(names):
        c.execute("CREATE (:N {name:$n})", {"n": n})
    for s, k, o, vf, vt, rec in FACTS:
        c.execute("MATCH (a:N {name:$s}),(b:N {name:$o}) "
                  "CREATE (a)-[:R {kind:$k, vfrom:$vf, vto:$vt, recorded:$r}]->(b)",
                  {"s": s, "o": o, "k": k, "vf": vf,
                   "vt": vt or "9999-12-31", "r": rec})
    return c


def ask(c, when):
    r = c.execute(
        "MATCH (a:N)-[e:R]->(b:N) WHERE e.vfrom <= $t AND e.vto >= $t "
        "RETURN a.name, e.kind, b.name ORDER BY a.name", {"t": when})
    out = []
    while r.has_next():
        out.append(tuple(r.get_next()))
    return out


def ask_no_time(c):
    r = c.execute("MATCH (a:N)-[e:R]->(b:N) RETURN a.name, e.kind, b.name "
                  "ORDER BY a.name")
    out = []
    while r.has_next():
        out.append(tuple(r.get_next()))
    return out


def main():
    tmp = tempfile.mkdtemp()
    c = build(tmp + "/db")

    print("시간을 안 보면 이렇게 나온다.\n")
    for s, k, o in ask_no_time(c):
        print(f"  {s} -{k}-> {o}")
    print("\n박민수와 이서연이 둘 다 팀장이고, 채식과 육식을 둘 다 선호한다.")
    print("서로 모순되는 사실이 같이 산다. 시간 칸을 안 봤기 때문이다.\n")

    for when in ASKED:
        print(f"[{when} 시점에 물으면]")
        for s, k, o in ask(c, when):
            print(f"  {s} -{k}-> {o}")
        print()

    print(
        "같은 그래프인데 답이 다르다. 그게 맞는 것이다.\n"
        "\n에이전트 기억에서 이게 왜 중요한가.\n"
        "\n사용자가 «팀장님께 보고서 보내 줘»라고 하면 지금 팀장에게 보내야 한다.\n"
        "그런데 2024년 대화 기록을 요약해 넣으면 박민수가 팀장으로 남아 있다.\n"
        "요약은 시간 칸을 안 갖고 다니기 때문이다(24장).\n"
        "\n그래서 «오래된 것을 지운다»가 답이 아니다. 지우면 과거를 못 묻는다.\n"
        "«2025년 3월에 팀장이 누구였지»는 정당한 질문이다.\n"
        "\n답은 지우는 게 아니라 «끝나는 시각을 적는» 것이다.\n"
        "새 사실이 들어오면 옛 사실의 vto 를 채운다. 옛 사실은 그대로 남는다.\n"
        "\n이걸 안 하면 기억이 쌓일수록 모순이 늘어난다.\n"
        "그리고 모순된 기억을 받은 모델은 «최근 것»이 아니라 «자주 나온 것»을 고른다.\n"
        "박민수가 2년간 팀장이었고 이서연이 두 달이면, 박민수가 이긴다."
    )
    shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main()
