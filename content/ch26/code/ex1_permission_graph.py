"""
예제 1 — 권한을 목록이 아니라 «그래프»로 본다.

    python3 ex1_permission_graph.py

의존성 없음. 도구마다 권한을 적어 두고,
「이 에이전트가 결국 무엇까지 할 수 있나」를 따라가 본다.
목록으로는 안 보이는 «이어붙인 경로»가 나온다.
"""

# 도구      필요한 권한          이 도구가 «만들어 내는» 능력
TOOLS = {
    "read_file":     ({"fs.read"},        {"파일 내용"}),
    "write_file":    ({"fs.write"},       {"파일 변경"}),
    "run_shell":     ({"exec"},           {"임의 실행"}),
    "http_get":      ({"net.out"},        {"외부 데이터"}),
    "http_post":     ({"net.out"},        {"외부 전송"}),
    "db_query":      ({"db.read"},        {"고객 데이터"}),
    "send_mail":     ({"mail.send"},      {"외부 전송"}),
}

# 에이전트에게 준 권한
GRANTED = {"fs.read", "net.out", "db.read"}

# «이것과 이것이 같이 있으면 이 일이 가능해진다»
COMBOS = [
    ({"고객 데이터", "외부 전송"}, "고객 데이터 유출", "심각"),
    ({"파일 내용", "외부 전송"},   "소스 코드 유출", "심각"),
    ({"임의 실행", "외부 데이터"}, "원격 코드 실행", "치명"),
    ({"파일 변경", "임의 실행"},   "지속성 확보", "치명"),
]


def usable():
    return {t for t, (need, _) in TOOLS.items() if need <= GRANTED}


def capabilities(tools):
    out = set()
    for t in tools:
        out |= TOOLS[t][1]
    return out


def reachable_risks(caps):
    return [(name, level) for need, name, level in COMBOS if need <= caps]


def main():
    ok = usable()
    caps = capabilities(ok)

    print(f"에이전트에게 준 권한: {sorted(GRANTED)}\n")
    print(f"쓸 수 있는 도구 {len(ok)}개: {sorted(ok)}")
    print(f"그래서 생기는 능력: {sorted(caps)}\n")

    risks = reachable_risks(caps)
    print(f"{'조합으로 가능해지는 일':<24}{'등급':<6}")
    print("-" * 34)
    for name, level in risks:
        print(f"{name:<24}{level:<6}")
    if not risks:
        print("(없음)")

    print(
        "\n권한 목록만 보면 «읽기와 네트워크와 DB 조회»다. 무해해 보인다.\n"
        "그런데 db_query 로 고객 데이터를 읽고 http_post 로 밖에 보낼 수 있다.\n"
        "두 도구는 각각 안전한데 «이어붙이면» 유출 경로가 된다.\n"
        "\n권한을 목록으로 관리하면 이 이어붙임이 안 보인다.\n"
        "그래서 권한은 목록이 아니라 «도달 가능한 경로»로 봐야 한다.\n"
    )

    # net.out 을 빼면 어떻게 되나
    print("net.out 을 빼 본다.\n")
    GRANTED.discard("net.out")
    ok2 = usable()
    caps2 = capabilities(ok2)
    risks2 = reachable_risks(caps2)
    print(f"쓸 수 있는 도구 {len(ok2)}개: {sorted(ok2)}")
    print(f"가능해지는 위험: {[r[0] for r in risks2] or '없음'}")

    print(
        f"\n권한 하나를 빼서 도구가 {len(ok)}개에서 {len(ok2)}개로 줄었다.\n"
        f"그런데 위험 경로는 {len(risks)}개에서 {len(risks2)}개로 사라졌다.\n"
        "\n권한 하나가 «나가는 문»이었기 때문이다.\n"
        "가드레일을 설계할 때 도구를 하나씩 재는 것보다\n"
        "«어느 권한이 문인지»를 찾는 게 훨씬 크게 듣는다.\n"
        "\n대개 문은 셋이다. 나가는 네트워크, 임의 실행, 쓰기.\n"
        "이 셋을 막으면 나머지는 조합해도 밖으로 못 나간다."
    )


if __name__ == "__main__":
    main()
