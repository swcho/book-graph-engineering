"""
예제 4 — 지우면 무엇이 같이 무너지나. 미리 세어 본다.

    pip install kuzu
    python3 ex4_cascade.py

28장의 연쇄 철회와 같은 구조인데, 여기서는 «사람»이 뿌리다.
"""

import shutil
import tempfile

import kuzu

NODES = [
    ("p1", "Person", "김도현"), ("p2", "Person", "이서연"),
    ("t1", "Team", "결제팀"),
    ("d1", "Doc", "3분기 보고서"),
    ("s1", "Stat", "팀별 문서 수"),
    ("f1", "Fact", "결제팀은 문서 생산이 많다"),
    ("a1", "Answer", "결제팀에 리소스를 더 배정하자"),
    ("r1", "Run", "분기 분석 #901"),
]
EDGES = [
    ("p1", "t1", "속함"), ("p2", "t1", "속함"),
    ("p1", "d1", "작성"),
    ("s1", "d1", "집계함"),
    ("f1", "s1", "기댐"),
    ("a1", "f1", "기댐"),
    ("r1", "a1", "생성함"),
]


def build(path):
    db = kuzu.Database(path)
    c = kuzu.Connection(db)
    c.execute("CREATE NODE TABLE N(id STRING, kind STRING, label STRING, "
              "PRIMARY KEY(id))")
    c.execute("CREATE REL TABLE R(FROM N TO N, kind STRING)")
    for i, k, l in NODES:
        c.execute("CREATE (:N {id:$i, kind:$k, label:$l})",
                  {"i": i, "k": k, "l": l})
    for a, b, k in EDGES:
        c.execute("MATCH (x:N {id:$a}),(y:N {id:$b}) "
                  "CREATE (x)-[:R {kind:$k}]->(y)", {"a": a, "b": b, "k": k})
    return c


def rows(r):
    out = []
    while r.has_next():
        out.append(tuple(r.get_next()))
    return out


def main():
    tmp = tempfile.mkdtemp()
    c = build(tmp + "/db")

    print("「김도현(p1)을 지워 주세요」. 무엇이 영향을 받나.\n")

    direct = rows(c.execute(
        "MATCH (a:N {id:'p1'})-[e:R]->(b:N) RETURN b.id, b.kind, b.label"))
    print(f"직접 이어진 것 {len(direct)}개:")
    for i, k, l in direct:
        print(f"    [{k}] {l}")

    indirect = rows(c.execute(
        "MATCH (x:N)-[:R*1..5]->(d:N)<-[:R]-(p:N {id:'p1'}) "
        "WHERE x.id <> 'p1' RETURN DISTINCT x.id, x.kind, x.label "
        "ORDER BY x.id"))
    print(f"\n그것에 기대고 있는 것 {len(indirect)}개:")
    for i, k, l in indirect:
        print(f"    [{k}] {l}")

    print(
        "\n사람 하나를 지우려는데 일곱 개가 걸린다. 그중에 «이서연»도 있다.\n"
        "같은 팀이라는 이유로 걸렸다. 이건 명백히 지우면 안 되는 것이다.\n"
        "\n그러니까 «이어진 것을 전부 지운다»는 답이 아니다.\n"
        "이 쿼리는 «영향 범위»를 보여 줄 뿐이고, 그중 무엇을 지울지는 따로 정해야 한다.\n"
        "\n그리고 분석 결과까지 걸린다.\n"
        "\n경로를 따라가 보면 이렇다.\n"
        "  김도현 → 3분기 보고서 → 팀별 문서 수 → 결제팀은 문서 생산이 많다\n"
        "  → 결제팀에 리소스를 더 배정하자\n"
        "\n김도현이 쓴 문서를 지우면 집계가 바뀌고, 집계가 바뀌면 그 위의 판단이\n"
        "근거를 잃는다. 28장에서 본 연쇄 철회와 같은 구조다.\n"
        "\n그런데 여기서는 «지우면 안 되는» 것들이 섞여 있다.\n"
        "  집계(팀별 문서 수)는 개인정보가 아니다. 지울 이유가 없다\n"
        "  결정(리소스 배정)은 회사의 기록이다. 지우면 안 된다\n"
        "\n그래서 개인정보 삭제는 «연쇄로 지우기»가 아니다.\n"
        "  개인을 특정하는 것 → 지운다\n"
        "  그 사람이 만든 산출물 → 대개 남긴다 (작성자만 익명화)\n"
        "  집계와 결정        → 남긴다\n"
        "\n경계가 어디냐면 «그것이 개인을 가리키는가»다.\n"
        "「3분기 보고서」는 개인을 안 가리킨다. 「김도현이 작성」이 가리킨다.\n"
        "그러니 문서는 두고 엣지의 «작성자»만 익명 노드로 바꾼다.\n"
        "\n그리고 이 판정은 자동으로 못 한다. 노드 종류마다 사람이 정해 둬야 한다."
    )
    shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main()
