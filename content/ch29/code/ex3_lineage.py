"""
예제 3 — 답이 나왔는데, 무엇을 거쳐 나왔나.

    pip install kuzu
    python3 ex3_lineage.py

한 백본에서는 «답 → 실행 → 읽은 사실 → 출처»를 한 쿼리로 거슬러 올라간다.
"""

import shutil
import tempfile

import kuzu

SCHEMA = """
CREATE NODE TABLE Node(id STRING, kind STRING, label STRING, PRIMARY KEY(id));
CREATE REL TABLE Link(FROM Node TO Node, kind STRING, at STRING);
"""

NODES = [
    ("ans1",  "Answer",  "「3분기 환불률이 늘어난 이유는 배송 지연」"),
    ("run1",  "Run",     "분석 워크플로 #4821"),
    ("step1", "Step",    "1. 환불 사유 집계"),
    ("step2", "Step",    "2. 배송 지표 조회"),
    ("step3", "Step",    "3. 상관 판단"),
    ("f1",    "Fact",    "환불 사유 1위 = 배송 지연 (41%)"),
    ("f2",    "Fact",    "3분기 평균 배송일 4.2일 (전분기 2.8일)"),
    ("f3",    "Fact",    "배송 지연과 환불의 상관 0.71"),
    ("s1",    "Source",  "주문 DB 스냅숏 2026-10-01"),
    ("s2",    "Source",  "물류 대시보드 2026-10-01"),
    ("s3",    "Source",  "에이전트 추론 (규칙: 상관>0.6)"),
]

LINKS = [
    ("ans1", "run1", "생성됨", "2026-10-02T10:31"),
    ("run1", "step1", "포함", ""), ("run1", "step2", "포함", ""),
    ("run1", "step3", "포함", ""),
    ("step1", "f1", "읽음", "2026-10-02T10:22"),
    ("step2", "f2", "읽음", "2026-10-02T10:25"),
    ("step3", "f3", "만듦", "2026-10-02T10:29"),
    ("f3", "f1", "기댐", ""), ("f3", "f2", "기댐", ""),
    ("f1", "s1", "출처", ""), ("f2", "s2", "출처", ""),
    ("f3", "s3", "출처", ""),
]


def build(path):
    db = kuzu.Database(path)
    c = kuzu.Connection(db)
    for stmt in SCHEMA.strip().split(";"):
        if stmt.strip():
            c.execute(stmt)
    for i, k, l in NODES:
        c.execute("CREATE (:Node {id:$i, kind:$k, label:$l})",
                  {"i": i, "k": k, "l": l})
    for a, b, k, at in LINKS:
        c.execute("MATCH (x:Node {id:$a}),(y:Node {id:$b}) "
                  "CREATE (x)-[:Link {kind:$k, at:$at}]->(y)",
                  {"a": a, "b": b, "k": k, "at": at})
    return c


def rows(r):
    out = []
    while r.has_next():
        out.append(tuple(r.get_next()))
    return out


def main():
    tmp = tempfile.mkdtemp()
    c = build(tmp + "/db")

    print("답 하나를 거슬러 올라간다.\n")
    ans = rows(c.execute("MATCH (a:Node {id:'ans1'}) RETURN a.label"))[0][0]
    print(f"답: {ans}\n")

    print("한 쿼리로 근거 전체를 뽑는다:\n")
    print("  MATCH (a:Node {id:'ans1'})-[:Link*1..4]->(x:Node)")
    print("  RETURN DISTINCT x.kind, x.label\n")

    for kind in ("Run", "Step", "Fact", "Source"):
        out = rows(c.execute(
            "MATCH (a:Node {id:'ans1'})-[:Link*1..4]->(x:Node {kind:$k}) "
            "RETURN DISTINCT x.label ORDER BY x.label", {"k": kind}))
        print(f"  [{kind}]")
        for (l,) in out:
            print(f"      {l}")

    print("\n\n이제 반대로. 출처 하나가 틀렸다면 무엇이 흔들리나.\n")
    hit = rows(c.execute(
        "MATCH (a:Node)-[:Link*1..4]->(s:Node {id:'s2'}) "
        "RETURN DISTINCT a.kind, a.label ORDER BY a.kind"))
    print("  물류 대시보드(s2)가 틀렸다면 영향받는 것:")
    for k, l in hit:
        print(f"      [{k}] {l}")

    print(
        "\n두 방향이 «같은 엣지»를 반대로 따라간 것이다.\n"
        "정방향은 «왜 이 답이 나왔나», 역방향은 «이게 틀리면 뭐가 무너지나».\n"
        "\n이 두 질문이 운영에서 제일 자주 나온다.\n"
        "그런데 지식과 실행을 따로 두면 «답에서 출처까지»가 한 번에 안 이어진다.\n"
        "실행 로그는 로그대로, 지식 그래프는 그래프대로 있어서\n"
        "사람이 두 시스템을 오가며 손으로 이어야 한다.\n"
        "\n합쳐 두면 쿼리 한 줄이다. 그리고 이건 «있으면 좋은 것»이 아니다.\n"
        "28장에서 봤듯 에이전트가 쓰기 시작하면 «어디서 온 사실인가»가\n"
        "품질 관리의 핵심이 되고, 그때 이 경로가 없으면 손을 못 쓴다.\n"
        "\n한 가지 주의. 이 경로는 «저절로» 생기지 않는다.\n"
        "실행할 때마다 Reads·Writes·기댐 엣지를 만들어야 한다.\n"
        "그게 값이다. 실행마다 엣지 서너 개씩 늘어난다."
    )
    shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main()
