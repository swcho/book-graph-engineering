"""
예제 2 — 벡터 검색과 그래프 순회는 «다른 질문»에 강하다.

    pip install kuzu
    python3 ex2_graph_vs_vector.py

질문을 세 종류로 나눠서 각각 어느 쪽이 이기는지 센다.
결론은 «하나를 고르라»가 아니다.
"""

import math
import shutil
import tempfile

import kuzu

# (사실, 아주 단순한 «임베딩» — 주제 축 세 개의 좌표)
#   축: [사람관계, 장소, 취향]
MEMO = [
    ("이서연 님이 결제팀에 새로 왔다",       [0.9, 0.1, 0.0]),
    ("이서연 님은 마포에 산다",             [0.6, 0.8, 0.0]),
    ("박민수 팀장은 매운 음식을 못 먹는다",   [0.5, 0.0, 0.9]),
    ("나는 채식을 한다",                   [0.2, 0.0, 0.9]),
    ("회식은 보통 강남에서 한다",           [0.1, 0.9, 0.3]),
    ("결제팀 팀장은 박민수다",              [0.9, 0.0, 0.1]),
    ("나는 강남에서 일한다",                [0.3, 0.9, 0.0]),
]

QUERIES = [
    ("비슷한 것 찾기",  "회식 장소 관련해서 뭐가 있었지",  [0.1, 0.9, 0.3]),
    ("여러 홉 잇기",    "우리 팀에서 마포에 사는 사람",    [0.7, 0.7, 0.0]),
    ("전부 세기",       "결제팀 사람이 몇 명이지",        [0.9, 0.1, 0.0]),
]


def cos(a, b):
    d = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    return d / (na * nb + 1e-9)


def vector_top(vec, k=3):
    return sorted(MEMO, key=lambda m: -cos(vec, m[1]))[:k]


def build(path):
    db = kuzu.Database(path)
    c = kuzu.Connection(db)
    c.execute("CREATE NODE TABLE N(name STRING, kind STRING, PRIMARY KEY(name))")
    c.execute("CREATE REL TABLE R(FROM N TO N, kind STRING)")
    for n, k in [("나", "P"), ("박민수", "P"), ("이서연", "P"),
                 ("결제팀", "T"), ("마포", "L"), ("강남", "L")]:
        c.execute("CREATE (:N {name:$n, kind:$k})", {"n": n, "k": k})
    for a, b, k in [("나", "결제팀", "속함"), ("박민수", "결제팀", "이끔"),
                    ("이서연", "결제팀", "속함"), ("이서연", "마포", "삶"),
                    ("나", "강남", "일함")]:
        c.execute("MATCH (x:N {name:$a}),(y:N {name:$b}) "
                  "CREATE (x)-[:R {kind:$k}]->(y)", {"a": a, "b": b, "k": k})
    return c


def rows(res):
    out = []
    while res.has_next():
        out.append(res.get_next())
    return out


def main():
    tmp = tempfile.mkdtemp()
    conn = build(tmp + "/db")

    print("같은 기억에 세 종류 질문을 던진다.\n")
    for kind, q, vec in QUERIES:
        print(f"[{kind}] {q}")
        top = vector_top(vec)
        print("  벡터 상위 3:")
        for text, v in top:
            print(f"      {cos(vec, v):.2f}  {text}")

        if kind == "여러 홉 잇기":
            r = rows(conn.execute(
                "MATCH (t:N {name:'결제팀'})<-[:R]-(p:N)-[e:R {kind:'삶'}]->"
                "(l:N {name:'마포'}) RETURN p.name"))
            print(f"  그래프: {[x[0] for x in r]}")
        elif kind == "전부 세기":
            r = rows(conn.execute(
                "MATCH (t:N {name:'결제팀'})<-[:R]-(p:N) RETURN count(p)"))
            print(f"  그래프: {r[0][0]}명")
        else:
            print("  그래프: (이 질문에는 순회할 경로가 없다)")
        print()

    print(
        "«비슷한 것 찾기»는 벡터가 이긴다. 정확히는, 그래프가 답할 수가 없다.\n"
        "«회식 장소 관련»에는 따라갈 엣지가 없다. 유사도 문제지 경로 문제가 아니다.\n"
        "\n«여러 홉 잇기»는 그래프가 이긴다. 그런데 이 예제에서는 벡터도 1등에\n"
        "«이서연 님은 마포에 산다»를 올렸다. 벡터가 이겼다고 볼 수도 있다.\n"
        "\n아니다. 벡터가 준 건 «마포에 사는 사람»이지 «우리 팀에서»가 아니다.\n"
        "2등이 «나는 강남에서 일한다»인 게 그 증거다. 조건 두 개 중 하나만 맞췄다.\n"
        "여기서는 마포에 사는 사람이 한 명뿐이라 우연히 답이 맞았다.\n"
        "마포 사는 사람이 열 명이고 그중 우리 팀이 한 명이면 벡터는 못 고른다.\n"
        "\n그래프는 «두 조건을 동시에 만족하는 것»을 구조로 찾는다.\n"
        "벡터는 «두 조건과 비슷한 것»을 찾는다. 그게 다른 일이다.\n"
        "\n«전부 세기»는 그래프만 할 수 있다. 벡터 상위 3에 팀원 셋이 다 안 나왔다.\n"
        "이서연과 박민수는 나왔는데 «나»가 안 나왔다. 3등이 엉뚱한 줄이다.\n"
        "k 를 늘리면 나오겠지만,\n"
        "«k 를 얼마로 해야 다 나오나»를 미리 알 방법이 없다.\n"
        "그게 벡터의 성질이다. 상위 k 개를 주는 물건에는 «전부»가 없다.\n"
        "\n그리고 «없음»도 못 한다. «마포에 사는 팀원이 없다»를 벡터로는 확인할 수 없다.\n"
        "유사도가 낮은 것도 어쨌든 무언가는 돌려주니까.\n"
        "\n그래서 결론은 «하나를 고르라»가 아니다.\n"
        "  비슷한 것 → 벡터\n"
        "  이어진 것 → 그래프\n"
        "  전부 / 세기 / 없음 확인 → 그래프\n"
        "\n실무에서는 대개 «벡터로 시작점을 찾고 그래프로 넓힌다».\n"
        "질문에서 사람 이름이나 개념을 벡터로 찾아 노드를 잡고,\n"
        "거기서 엣지를 따라간다. 두 단계다."
    )
    shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main()
