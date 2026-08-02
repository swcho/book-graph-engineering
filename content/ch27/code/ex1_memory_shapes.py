"""
예제 1 — 같은 대화 기억을 세 가지 모양으로 저장하고, 세 종류 질문을 던진다.

    pip install kuzu
    python3 ex1_memory_shapes.py

모양이 답할 수 있는 질문을 정한다. 그게 이 예제의 전부다.
"""

import re
import shutil
import tempfile

import kuzu

# 사용자가 지난 두 달 동안 흘린 말들
FACTS = [
    "저는 서울 강남에서 일합니다",
    "회사는 결제팀이고 팀장은 박민수입니다",
    "박민수 팀장은 매운 음식을 못 먹습니다",
    "지난주에 팀 회식을 마포에서 했습니다",
    "저는 회식 때 채식만 합니다",
    "이서연 님이 새로 팀에 왔습니다",
    "이서연 님은 마포에 삽니다",
]

# 그래프로 옮긴 같은 사실들
NODES = [("나", "Person"), ("박민수", "Person"), ("이서연", "Person"),
         ("결제팀", "Team"), ("강남", "Place"), ("마포", "Place"),
         ("매운맛", "Pref"), ("채식", "Pref")]
EDGES = [("나", "결제팀", "속함"), ("박민수", "결제팀", "이끔"),
         ("이서연", "결제팀", "속함"), ("나", "강남", "일함"),
         ("이서연", "마포", "삶"), ("박민수", "매운맛", "못먹음"),
         ("나", "채식", "선호")]

QUESTIONS = [
    ("내가 어디서 일하지?", ["강남"]),
    ("회식 장소를 정할 때 피해야 할 것은?", ["매운맛", "채식"]),
    ("우리 팀에서 마포에 사는 사람은?", ["이서연"]),
]


# 질문에서 뽑아 낼 «찾을 말». 실제 시스템은 임베딩을 쓰지만
# 여기서는 무엇이 걸리고 무엇이 안 걸리는지 눈으로 보려고 낱말로 한다.
TERMS = {
    "내가 어디서 일하지?": ["일합니다", "일"],
    "회식 장소를 정할 때 피해야 할 것은?": ["회식"],
    "우리 팀에서 마포에 사는 사람은?": ["마포", "팀"],
}


def flat_search(q):
    """모양 1 — 그냥 다 이어 붙인 텍스트에서 말로 찾기."""
    return [f for f in FACTS if any(t in f for t in TERMS.get(q, []))]


def keyed_search(q):
    """모양 2 — 키-값. 미리 정한 칸만 답할 수 있다."""
    # 미리 정해 둔 칸만 있다. 칸에 없는 질문은 답을 못 한다.
    kv = {"일하": ("근무지", "강남"), "식성": ("식성", "채식")}
    for key, (name, val) in kv.items():
        if key in q:
            return [f"{name}={val}"]
    return []


def graph_search(conn, q):
    """모양 3 — 그래프. 이어진 것을 따라간다."""
    if "일하" in q:
        rows = conn.execute(
            "MATCH (p:N {name:'나'})-[e:R]->(x:N) WHERE e.kind='일함' "
            "RETURN x.name")
    elif "피해야" in q:
        # 팀에 속한 사람들의 선호를 전부 모은다 (2홉)
        rows = conn.execute(
            "MATCH (t:N {name:'결제팀'})<-[:R]-(p:N)-[e:R]->(pref:N) "
            "WHERE pref.kind='Pref' RETURN DISTINCT pref.name")
    elif "마포에 사는" in q:
        rows = conn.execute(
            "MATCH (t:N {name:'결제팀'})<-[:R]-(p:N)-[e:R]->(pl:N {name:'마포'}) "
            "WHERE e.kind='삶' RETURN p.name")
    else:
        return []
    out = []
    while rows.has_next():
        out.append(rows.get_next()[0])
    return out


def build(path):
    db = kuzu.Database(path)
    c = kuzu.Connection(db)
    c.execute("CREATE NODE TABLE N(name STRING, kind STRING, PRIMARY KEY(name))")
    c.execute("CREATE REL TABLE R(FROM N TO N, kind STRING)")
    for n, k in NODES:
        c.execute("CREATE (:N {name:$n, kind:$k})", {"n": n, "k": k})
    for a, b, k in EDGES:
        c.execute("MATCH (x:N {name:$a}), (y:N {name:$b}) "
                  "CREATE (x)-[:R {kind:$k}]->(y)", {"a": a, "b": b, "k": k})
    return c


def main():
    tmp = tempfile.mkdtemp()
    conn = build(tmp + "/db")

    print(f"사실 {len(FACTS)}개를 세 가지 모양으로 저장했다.\n")
    print(f"{'질문':<28}{'평평한 텍스트':<16}{'키-값':<12}{'그래프'}")
    print("-" * 78)
    score = {"flat": 0, "kv": 0, "graph": 0}
    for q, want in QUESTIONS:
        f = flat_search(q)
        k = keyed_search(q)
        g = graph_search(conn, q)
        ok_f = "△ 원문 %d줄" % len(f) if f else "✗ 못 찾음"
        ok_k = "○ " + k[0] if k else "✗ 칸 없음"
        ok_g = ("○ " + ",".join(g)) if set(want) <= set(g) else \
               (("△ " + ",".join(g)) if g else "✗")
        score["flat"] += bool(f)
        score["kv"] += bool(k)
        score["graph"] += set(want) <= set(g)
        print(f"{q:<28}{ok_f:<16}{ok_k:<12}{ok_g}")

    print(
        "\n세 번째 질문이 갈림길이다. «우리 팀에서 마포에 사는 사람».\n"
        "\n평평한 텍스트는 원문 다섯 줄을 준다. 일곱 줄 중 다섯이다.\n"
        "«팀»과 «마포»가 둘 다 흔한 말이라 거의 다 걸렸다.\n"
        "답이 그 안에 있긴 한데, 어느 줄을 어떻게 이을지는 모델이 해야 한다.\n"
        "«팀에 속한 사람»과 «마포에 산다»를 이으려면 두 줄을 동시에 봐야 하고,\n"
        "일곱 줄일 때는 다섯을 다 줘도 되지만 7,000줄이면 못 준다.\n"
        "그때 상위 다섯 줄에 그 둘이 같이 들어올 보장이 없다.\n"
        "\n키-값은 아예 답을 못 한다. «마포에 사는 팀원»이라는 칸을 안 만들어 뒀으니까.\n"
        "그리고 그런 칸을 미리 다 만들어 둘 수는 없다. 질문은 무한하다.\n"
        "\n그래프는 답한다. 팀 → 팀원 → 사는 곳을 «따라가면» 되기 때문이다.\n"
        "이 경로는 저장할 때 몰랐던 것이다. 질문이 들어온 뒤에 만들어진다.\n"
        "\n이게 그래프를 기억으로 쓰는 이유다. 저장할 때 «질문을 몰라도 된다»."
    )
    shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main()
