"""
예제 4 — 폭발 반경. 하나가 뚫렸을 때 어디까지 번지나.

    python3 ex4_blast_radius.py

의존성 없음. 에이전트·자원 그래프를 놓고
「한 노드가 장악되면 도달 가능한 자원」을 센다.
"""

from collections import deque

# 에이전트 → 쓸 수 있는 도구
AGENTS = {
    "요약기":   ["read_docs"],
    "분석기":   ["read_docs", "db_read"],
    "보고서":   ["db_read", "send_mail"],
    "관리자":   ["read_docs", "db_read", "send_mail", "run_shell", "spawn"],
}

# 도구 → 닿는 자원
TOOLS = {
    "read_docs": ["문서저장소"],
    "db_read":   ["고객DB"],
    "send_mail": ["외부"],
    "run_shell": ["서버파일", "외부"],
    "spawn":     [],          # 다른 에이전트를 만들 수 있다
}

# spawn 이 있으면 «다른 에이전트로 갈아탈» 수 있다
SPAWNABLE = ["요약기", "분석기", "보고서", "관리자"]

VALUE = {"문서저장소": 1, "고객DB": 5, "외부": 4, "서버파일": 5}


def radius(start, allow_spawn=True):
    """이 에이전트가 장악됐을 때 닿는 자원 전부."""
    seen_agents, resources = set(), set()
    q = deque([start])
    while q:
        a = q.popleft()
        if a in seen_agents:
            continue
        seen_agents.add(a)
        for t in AGENTS[a]:
            resources |= set(TOOLS[t])
            if t == "spawn" and allow_spawn:
                q.extend(SPAWNABLE)
    return seen_agents, resources


def main():
    print("에이전트 하나가 장악됐다고 하자. 어디까지 닿나.\n")
    print(f"{'장악된 에이전트':<12}{'닿는 에이전트':>12}   {'닿는 자원':<30}{'피해 점수':>9}")
    print("-" * 72)
    for a in AGENTS:
        ags, res = radius(a)
        score = sum(VALUE[r] for r in res)
        print(f"{a:<12}{len(ags):>12}   {', '.join(sorted(res)):<30}{score:>9}")

    print("\nspawn 권한을 관리자에게서 뺀다.\n")
    AGENTS["관리자"].remove("spawn")
    print(f"{'장악된 에이전트':<12}{'닿는 에이전트':>12}   {'닿는 자원':<30}{'피해 점수':>9}")
    print("-" * 72)
    for a in AGENTS:
        ags, res = radius(a)
        score = sum(VALUE[r] for r in res)
        print(f"{a:<12}{len(ags):>12}   {', '.join(sorted(res)):<30}{score:>9}")

    print(
        "\n표가 안 바뀐 것처럼 보인다. 관리자만 spawn 을 갖고 있었으니\n"
        "관리자 자신의 반경은 그대로다. 다른 에이전트는 원래 spawn 이 없었다.\n"
        "\n그럼 spawn 을 빼는 게 소용없나. 아니다. «전파»가 사라졌다.\n"
        "첫 표에서 관리자가 닿는 에이전트가 4개였다. 둘째 표에서는 1개다.\n"
        "\n관리자가 여전히 제일 위험하다. 자원 점수가 같으니까.\n"
        "그래서 진짜 대응은 spawn 을 빼는 게 아니라 «관리자를 쪼개는» 것이다.\n"
        "\n한 에이전트가 read + db + shell + mail 을 다 갖고 있으면\n"
        "그 하나가 뚫렸을 때 전부 나간다. 최소 권한은 «각 에이전트가 자기 일에\n"
        "필요한 것만»이 아니라 «어떤 하나도 치명 조합을 갖지 않게»다.\n"
        "\n요약기를 보시라. 점수 1이다. 뚫려도 문서저장소까지다.\n"
        "이게 목표 모양이다. 에이전트를 나누는 이유가 성능만은 아니다."
    )


if __name__ == "__main__":
    main()
