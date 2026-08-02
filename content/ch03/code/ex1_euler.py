"""
예제 1 — 오일러가 1736년에 한 계산을 그대로.

    python3 ex1_euler.py

의존성 없음. 코드 20줄이면 끝난다. 그게 이 문제의 요점이다.
"""

# 쾨니히스베르크: 땅 4곳, 다리 7개. (다중 엣지가 있으므로 리스트로 센다)
KONIGSBERG = [
    ("북", "섬A"), ("북", "섬A"),      # 다리 2개
    ("남", "섬A"), ("남", "섬A"),      # 다리 2개
    ("북", "섬B"),
    ("남", "섬B"),
    ("섬A", "섬B"),
]


def degrees(edges):
    d = {}
    for a, b in edges:
        d[a] = d.get(a, 0) + 1
        d[b] = d.get(b, 0) + 1
    return d


def euler_verdict(edges):
    d = degrees(edges)
    odd = [v for v, n in d.items() if n % 2 == 1]
    if len(odd) == 0:
        return d, odd, "모든 다리를 한 번씩 건너 제자리로 돌아올 수 있다 (오일러 회로)"
    if len(odd) == 2:
        return d, odd, f"{odd[0]}에서 출발해 {odd[1]}에서 끝나면 가능하다 (오일러 경로)"
    return d, odd, f"불가능하다. 홀수 차수가 {len(odd)}개다 (0개나 2개여야 한다)"


def report(name, edges):
    d, odd, verdict = euler_verdict(edges)
    print(f"[{name}] 다리 {len(edges)}개")
    print("  차수:", ", ".join(f"{k}={v}" for k, v in sorted(d.items())))
    print(f"  홀수 차수: {odd or '없음'}")
    print(f"  판정: {verdict}\n")


if __name__ == "__main__":
    report("쾨니히스베르크 1736", KONIGSBERG)

    # 다리를 하나만 더 놓으면? 북과 남을 잇는 다리를 추가해 본다.
    report("다리 하나 추가 (북-남)", KONIGSBERG + [("북", "남")])

    print("오일러가 한 일은 다리를 세는 게 아니라 «땅의 모양을 버린 것»이다.")
    print("강폭도 다리 길이도 답에 영향을 주지 않는다. 남는 건 연결의 개수뿐.")
    print("이 버림이 그래프 이론의 시작이다.")
