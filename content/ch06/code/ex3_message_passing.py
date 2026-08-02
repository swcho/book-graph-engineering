"""
예제 3 — 그래프 신경망의 한 층. 이웃 정보를 모아 자기 벡터를 갱신한다.

    python3 ex3_message_passing.py

의존성 없음. 학습은 안 한다. «메시지 패싱»이 무엇인지 눈으로 보는 게 목적이다.
층을 한 번 돌면 1홉, 두 번 돌면 2홉 정보가 섞인다. 그게 전부다.
"""

from collections import defaultdict

EDGES = [("A", "B"), ("B", "C"), ("C", "D"), ("A", "E"), ("E", "F"), ("B", "E")]
# 시작 특징. 여기서는 «장애를 몇 번 겪었나, 팀 규모» 두 칸이라고 치자.
FEAT = {"A": [4.0, 2.0], "B": [1.0, 5.0], "C": [0.0, 3.0],
        "D": [2.0, 1.0], "E": [3.0, 4.0], "F": [0.0, 2.0]}


def adjacency(edges):
    adj = defaultdict(set)
    for a, b in edges:
        adj[a].add(b)
        adj[b].add(a)
    return adj


def layer(feat, adj, w_self=0.5, w_nbr=0.5):
    """한 층: 자기 벡터와 이웃 평균을 섞는다. 진짜 GNN 은 여기에 학습 가중치가 붙는다."""
    out = {}
    for n, v in feat.items():
        nbrs = adj[n]
        if nbrs:
            avg = [sum(feat[m][i] for m in nbrs) / len(nbrs) for i in range(len(v))]
        else:
            avg = [0.0] * len(v)
        out[n] = [round(w_self * v[i] + w_nbr * avg[i], 3) for i in range(len(v))]
    return out


def show(title, feat):
    print(f"\n{title}")
    for n in sorted(feat):
        print(f"  {n}: {feat[n]}")


def main():
    adj = adjacency(EDGES)
    print("이웃 목록:", {k: sorted(v) for k, v in sorted(adj.items())})
    show("0층 — 자기 특징만", FEAT)

    f1 = layer(FEAT, adj)
    show("1층 — 이웃(1홉)이 섞였다", f1)

    f2 = layer(f1, adj)
    show("2층 — 이웃의 이웃(2홉)까지 섞였다", f2)

    print(
        "\nD 를 보라. 0층에서는 [2.0, 1.0] 이었다.\n"
        "1층에서 C 의 값이 섞이고, 2층에서 B 의 값까지 흘러 들어온다.\n"
        "«구조»가 값에 녹아드는 과정이다.\n"
        "\n얻는 것: 이웃이 비슷하면 벡터도 비슷해진다. 그래서 링크 예측이 된다.\n"
        "잃는 것: 2층을 지나면 어느 이웃이 얼마나 기여했는지 되짚기 어렵다.\n"
        "층을 깊게 쌓으면 모든 노드가 비슷해지기까지 한다(과평활, over-smoothing).\n"
        "\n2~3층에서 멈추는 게 관행인데, 그 관행의 이유가 여기 있다."
    )


if __name__ == "__main__":
    main()
