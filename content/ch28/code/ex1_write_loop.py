"""
예제 1 — 에이전트가 그래프에 «쓰기» 시작하면 무슨 일이 생기나.

    pip install kuzu
    python3 ex1_write_loop.py

추출한 것을 검증 없이 그대로 넣는 루프를 10회 돌린다.
"""

import shutil
import tempfile

import kuzu

# 매 턴 «추출기»가 뽑아 낸 트리플. 일부러 지저분하게 섞어 뒀다.
# (주어, 관계, 목적어, 이게 맞는 사실인가)
EXTRACTED = [
    [("박민수", "이끔", "결제팀", True)],
    [("이서연", "속함", "결제팀", True)],
    [("민수", "이끔", "결제팀", True)],            # 같은 사람, 다른 이름
    [("이서연", "속함", "정산팀", False)],          # 잘못 뽑음
    [("박민수", "이끔", "정산팀", False)],          # 잘못 뽑음
    [("결제팀", "속함", "이서연", False)],          # 방향 뒤집힘
    [("박민수", "관리", "결제팀", True)],            # 같은 뜻, 다른 관계 이름
    [("이서연", "속함", "결제팀", True)],           # 중복
    [("PM", "이끔", "결제팀", True)],               # 또 다른 이름
    [("박민수", "이끔", "결제팀", True)],           # 중복
]


def build(path):
    db = kuzu.Database(path)
    c = kuzu.Connection(db)
    c.execute("CREATE NODE TABLE N(name STRING, PRIMARY KEY(name))")
    c.execute("CREATE REL TABLE R(FROM N TO N, kind STRING)")
    return c


def ensure(c, name):
    r = c.execute("MATCH (n:N {name:$n}) RETURN n.name", {"n": name})
    if not r.has_next():
        c.execute("CREATE (:N {name:$n})", {"n": name})


def write(c, s, k, o):
    ensure(c, s)
    ensure(c, o)
    c.execute("MATCH (a:N {name:$s}),(b:N {name:$o}) "
              "CREATE (a)-[:R {kind:$k}]->(b)", {"s": s, "o": o, "k": k})


def stats(c):
    n = c.execute("MATCH (n:N) RETURN count(n)").get_next()[0]
    e = c.execute("MATCH ()-[r:R]->() RETURN count(r)").get_next()[0]
    return n, e


def leaders(c):
    r = c.execute("MATCH (p:N)-[e:R]->(t:N {name:'결제팀'}) "
                  "WHERE e.kind IN ['이끔','관리'] RETURN DISTINCT p.name")
    out = []
    while r.has_next():
        out.append(r.get_next()[0])
    return out


def main():
    tmp = tempfile.mkdtemp()
    c = build(tmp + "/db")

    print(f"{'턴':>3}{'노드':>6}{'엣지':>6}  이번에 넣은 것")
    print("-" * 56)
    wrong = 0
    for i, batch in enumerate(EXTRACTED, 1):
        for s, k, o, ok in batch:
            write(c, s, k, o)
            wrong += not ok
        n, e = stats(c)
        mark = "" if all(x[3] for x in batch) else "  ← 틀린 사실"
        print(f"{i:>3}{n:>6}{e:>6}  {batch[0][0]} -{batch[0][1]}-> "
              f"{batch[0][2]}{mark}")

    n, e = stats(c)
    print(f"\n10턴 뒤: 노드 {n}개, 엣지 {e}개. 그중 틀린 사실 {wrong}개.")
    print(f"\n«결제팀을 이끄는 사람»을 물으면: {leaders(c)}")
    r = c.execute("MATCH (p:N)-[e:R]->(t:N {name:'정산팀'}) RETURN p.name, e.kind")
    j = []
    while r.has_next():
        a, k = r.get_next()
        j.append(f"{a} -{k}->")
    print(f"«정산팀» 을 물으면: {j}   (전부 틀린 사실이다)")

    print(
        "\n세 명이 나온다. 실제로는 한 명이다.\n"
        "\n박민수·민수·PM 은 같은 사람인데 노드가 셋이다(27장의 개체 해상도).\n"
        "이 셋은 «맞는 사실»만 넣었는데도 이렇게 된다. 이름이 달랐을 뿐이다.\n"
        "\n엣지 10개 중 3개가 틀렸다. 30% 다.\n"
        "그런데 조회 결과는 셋 다 «같은 사람의 다른 이름»이라 셋 다 맞기도 하고\n"
        "«한 명이냐 세 명이냐»를 물으면 셋 다 틀리기도 하다.\n"
        "\n이게 더 고약하다. 명백히 틀린 게 아니라 «반쯤 맞는» 상태라서\n"
        "조회 결과만 보고는 문제가 있는지 알 수가 없다.\n"
        "\n«정산팀»으로 물으면 어떻게 되는지도 보시라. 틀린 엣지 두 개가 통째로 답이 된다.\n"
        "조회는 «있는 것을 전부» 주기 때문이다. 넣을 때 안 거른 것은 꺼낼 때도 안 걸러진다.\n"
        "\n읽기 전용 그래프에서는 이런 일이 안 생긴다. 사람이 넣은 것만 있으니까.\n"
        "쓰기를 열면 «품질 관리»가 곧 시스템의 일부가 된다.\n"
        "그게 이 장의 주제다."
    )
    shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main()
