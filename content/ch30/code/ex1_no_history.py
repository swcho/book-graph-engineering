"""
예제 1 — 현재 상태만 저장하면 무엇을 못 하나.

    pip install kuzu
    python3 ex1_no_history.py

같은 변경을 «덮어쓰기»와 «이벤트 쌓기» 두 방식으로 기록하고
답할 수 있는 질문을 비교한다.
"""

import shutil
import tempfile

import kuzu

CHANGES = [
    ("2026-03-02", "박민수", "이끔", "결제팀", "추가", "hr-sync"),
    ("2026-04-01", "박민수", "이끔", "결제팀", "삭제", "hr-sync"),
    ("2026-04-01", "이서연", "이끔", "결제팀", "추가", "hr-sync"),
    ("2026-04-14", "이서연", "이끔", "정산팀", "추가", "agent-4821"),
    ("2026-04-15", "이서연", "이끔", "정산팀", "삭제", "admin:kim"),
    ("2026-05-20", "이서연", "삶",   "마포",   "추가", "user-utterance"),
]


def build(path):
    db = kuzu.Database(path)
    c = kuzu.Connection(db)
    # 현재 상태만
    c.execute("CREATE NODE TABLE N(name STRING, PRIMARY KEY(name))")
    c.execute("CREATE REL TABLE Cur(FROM N TO N, kind STRING)")
    # 이벤트 로그
    c.execute("CREATE NODE TABLE Ev(id INT64, at STRING, subj STRING, "
              "kind STRING, obj STRING, op STRING, actor STRING, "
              "PRIMARY KEY(id))")
    for n in ("박민수", "이서연", "결제팀", "정산팀", "마포"):
        c.execute("CREATE (:N {name:$n})", {"n": n})
    for i, (at, s, k, o, op, who) in enumerate(CHANGES):
        c.execute("CREATE (:Ev {id:$i, at:$at, subj:$s, kind:$k, obj:$o, "
                  "op:$op, actor:$w})",
                  {"i": i, "at": at, "s": s, "k": k, "o": o, "op": op, "w": who})
        if op == "추가":
            c.execute("MATCH (a:N {name:$s}),(b:N {name:$o}) "
                      "CREATE (a)-[:Cur {kind:$k}]->(b)",
                      {"s": s, "o": o, "k": k})
        else:
            c.execute("MATCH (a:N {name:$s})-[e:Cur {kind:$k}]->"
                      "(b:N {name:$o}) DELETE e",
                      {"s": s, "o": o, "k": k})
    return c


def rows(r):
    out = []
    while r.has_next():
        out.append(tuple(r.get_next()))
    return out


def main():
    tmp = tempfile.mkdtemp()
    c = build(tmp + "/db")

    print("변경 6건을 넣었다. 현재 상태는 이렇다.\n")
    for a, k, b in rows(c.execute(
            "MATCH (a:N)-[e:Cur]->(b:N) RETURN a.name, e.kind, b.name "
            "ORDER BY a.name")):
        print(f"  {a} -{k}-> {b}")

    print("\n\n이제 네 가지를 물어본다.\n")

    qs = [
        ("Q1", "지금 결제팀 팀장은?"),
        ("Q2", "3월 15일에는 팀장이 누구였나?"),
        ("Q3", "「이서연 -이끔-> 정산팀」은 누가 넣고 누가 지웠나?"),
        ("Q4", "에이전트가 넣은 것 중 사람이 되돌린 게 몇 건인가?"),
    ]
    print(f"{'':<4}{'질문':<36}{'현재 상태만':<14}{'이벤트 로그'}")
    print("-" * 82)

    a1 = rows(c.execute("MATCH (p:N)-[:Cur {kind:'이끔'}]->"
                        "(:N {name:'결제팀'}) RETURN p.name"))
    print(f"{qs[0][0]:<4}{qs[0][1]:<36}{a1[0][0]:<14}{a1[0][0]}")

    # Q2 — 이벤트를 3/15 까지 재생한다
    st = set()
    for at, s, k, o, op in rows(c.execute(
            "MATCH (e:Ev) WHERE e.at <= '2026-03-15' "
            "RETURN e.at, e.subj, e.kind, e.obj, e.op ORDER BY e.id")):
        if op == "추가":
            st.add((s, k, o))
        else:
            st.discard((s, k, o))
    lead = [s for s, k, o in st if k == "이끔" and o == "결제팀"]
    print(f"{qs[1][0]:<4}{qs[1][1]:<36}{'답 못 함':<14}{lead[0]}")

    who = rows(c.execute(
        "MATCH (e:Ev {subj:'이서연', kind:'이끔', obj:'정산팀'}) "
        "RETURN e.op, e.actor, e.at ORDER BY e.id"))
    trail = " / ".join(f"{op} {a} ({at})" for op, a, at in who)
    print(f"{qs[2][0]:<4}{qs[2][1]:<36}{'답 못 함':<14}{trail}")

    # Q4 — 에이전트가 추가한 뒤 사람이 삭제한 짝
    added = {(s, k, o): (at, w) for at, s, k, o, op, w in
             [(r[0], r[1], r[2], r[3], r[4], r[5]) for r in rows(c.execute(
                 "MATCH (e:Ev) WHERE e.op='추가' AND e.actor STARTS WITH 'agent' "
                 "RETURN e.at, e.subj, e.kind, e.obj, e.op, e.actor"))]}
    reverted = 0
    for at, s, k, o, w in rows(c.execute(
            "MATCH (e:Ev) WHERE e.op='삭제' AND e.actor STARTS WITH 'admin' "
            "RETURN e.at, e.subj, e.kind, e.obj, e.actor")):
        if (s, k, o) in added:
            reverted += 1
    print(f"{qs[3][0]:<4}{qs[3][1]:<36}{'답 못 함':<14}{reverted}건")

    print(
        "\nQ2 를 보시라. 지금 팀장은 이서연인데 3월에는 박민수였다.\n"
        "이벤트를 그 시점까지 «재생»하면 그때 상태가 그대로 나온다.\n"
        "\n현재 상태만 두면 Q1 밖에 못 한다.\n"
        "그런데 운영에서 자주 나오는 건 Q2~Q4 다.\n"
        "\n«3월에는 어땠나»는 감사와 분쟁에서 반드시 나온다.\n"
        "«누가 넣었나»는 사고 조사의 첫 질문이다.\n"
        "«에이전트가 넣은 것 중 되돌려진 비율»은 28장의 품질 지표 그 자체다.\n"
        "\n덮어쓰기는 답을 «지운다». 그래서 나중에 복원이 안 된다.\n"
        "이벤트를 쌓으면 현재 상태는 «재생해서» 만들 수 있고, 과거도 남는다.\n"
        "\n대신 값을 치른다. 저장 공간과 재생 시간이다. 다음 예제에서 잰다."
    )
    shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main()
