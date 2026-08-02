"""
예제 1 — 같은 그래프, 세 가지 표현. 메모리를 재 본다.

    python3 ex1_three_forms.py

의존성 없음. sys.getsizeof 로 대략 잰다. 정확한 값은 아니고 «자릿수»를 보는 용도다.
"""

import sys
from array import array
from collections import defaultdict

from graphgen import make

N = 20_000


def deep_size(obj, seen=None):
    """중첩 컨테이너까지 대략 더한다."""
    seen = seen if seen is not None else set()
    if id(obj) in seen:
        return 0
    seen.add(id(obj))
    size = sys.getsizeof(obj)
    if isinstance(obj, dict):
        size += sum(deep_size(k, seen) + deep_size(v, seen) for k, v in obj.items())
    elif isinstance(obj, (list, tuple, set)):
        size += sum(deep_size(x, seen) for x in obj)
    return size


def build_matrix(edges, n):
    """인접 행렬. n×n 비트. 여기서는 bytearray 한 줄에 n비트씩."""
    row_bytes = (n + 7) // 8
    m = bytearray(row_bytes * n)
    for a, b in edges:
        m[a * row_bytes + (b >> 3)] |= 1 << (b & 7)
        m[b * row_bytes + (a >> 3)] |= 1 << (a & 7)
    return m


def build_adjlist(edges):
    adj = defaultdict(list)
    for a, b in edges:
        adj[a].append(b)
        adj[b].append(a)
    return dict(adj)


def build_csr(edges, n):
    """오프셋 배열 + 이웃 배열. 정수 배열 두 개가 전부다."""
    deg = [0] * n
    for a, b in edges:
        deg[a] += 1
        deg[b] += 1
    offset = array("i", [0] * (n + 1))
    for i in range(n):
        offset[i + 1] = offset[i] + deg[i]
    cursor = list(offset[:n])
    nbr = array("i", [0] * offset[n])
    for a, b in edges:
        nbr[cursor[a]] = b; cursor[a] += 1
        nbr[cursor[b]] = a; cursor[b] += 1
    return offset, nbr


def main():
    edges = make(n=N, avg_deg=12)
    print(f"노드 {N:,}개, 엣지 {len(edges):,}개\n")

    m = build_matrix(edges, N)
    adj = build_adjlist(edges)
    off, nbr = build_csr(edges, N)

    rows = [
        ("인접 행렬 (비트)", sys.getsizeof(m)),
        ("인접 리스트 (dict of list)", deep_size(adj)),
        ("CSR (배열 2개)", sys.getsizeof(off) + sys.getsizeof(nbr)),
    ]
    base = min(r[1] for r in rows)
    print(f"{'표현':<28} {'바이트':>14} {'배수':>8}")
    for name, size in rows:
        print(f"{name:<28} {size:>14,} {size/base:>7.1f}x")

    print(
        f"\n인접 행렬은 노드 수의 제곱이다. {N:,}노드면 "
        f"{N*N//8/1024/1024:.0f}MB 가 필요하고, 엣지가 몇 개든 상관없다.\n"
        "노드가 수천 이하일 때만 쓸 만하다.\n"
        "\ndict of list 는 편한데 무겁다. 파이썬 객체가 원소마다 붙기 때문이다.\n"
        "CSR 은 정수 배열 두 개다. 제일 조밀하고, 이웃이 연속으로 놓인다."
    )


if __name__ == "__main__":
    main()
