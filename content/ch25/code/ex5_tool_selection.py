"""
예제 5 — 도구 설명이 호출을 정한다. 설명을 바꿔 정확도를 잰다.

    python3 ex5_tool_selection.py

의존성 없음. 모델 없이 «설명과 질문의 겹침»으로 고르는 아주 단순한
선택기를 쓴다. 진짜 모델은 이보다 낫지만, 설명이 나쁘면
같은 방식으로 틀린다는 것을 보여 주는 게 목적이다.
"""

import re

QUERIES = [
    ("김지훈이 누구야",                 "find_person"),
    ("김지훈 위로 누가 있어",           "chain_of_command"),
    ("결제팀에 누구누구 있어",          "team_members"),
    ("박민수 상급자 알려줘",            "chain_of_command"),
    ("이서연 찾아줘",                   "find_person"),
    ("결제팀 명단",                     "team_members"),
    ("김지훈 보고 라인 전체",           "chain_of_command"),
    ("이서연 정보",                     "find_person"),
]

BAD = {
    "find_person":      "사람 조회",
    "chain_of_command": "체인 조회",
    "team_members":     "팀 조회",
}

GOOD = {
    "find_person":
        "사람 «한 명»을 이름으로 찾는다. 이름, 소속 팀, 상사 아이디를 준다. "
        "여러 명을 찾을 때는 쓰지 않는다.",
    "chain_of_command":
        "한 사람의 «위로 올라가는» 보고 체계를 뿌리까지 준다. "
        "상사, 상사의 상사, 보고 라인, 결재선을 물으면 이것이다. "
        "아래 부하 목록에는 쓰지 않는다.",
    "team_members":
        "팀 이름을 주면 그 팀 구성원 «전부»를 목록으로 준다. "
        "명단, 누구누구, 구성원, 몇 명을 물으면 이것이다.",
}


def tokenize(s):
    return set(re.findall(r"[가-힣A-Za-z]+", s))


def choose(query, descriptions):
    q = tokenize(query)
    best, score = None, -1
    for name, desc in descriptions.items():
        overlap = len(q & tokenize(desc))
        if overlap > score:
            best, score = name, overlap
    return best


def run(label, descriptions):
    hit = 0
    print(f"\n[{label}]")
    for q, want in QUERIES:
        got = choose(q, descriptions)
        ok = got == want
        hit += ok
        mark = "  " if ok else " ←틀림"
        print(f"  {q:<22}{got:<20}{mark}")
    print(f"  정확도 {hit}/{len(QUERIES)} = {hit / len(QUERIES):.0%}")
    return hit


def main():
    print("도구는 그대로다. 설명만 바꾼다.")
    a = run("설명이 짧다", BAD)
    b = run("설명에 «언제 쓰나»와 «언제 안 쓰나»가 있다", GOOD)

    print(
        f"\n{a}/{len(QUERIES)} 에서 {b}/{len(QUERIES)} 로 올랐다. "
        "코드는 한 줄도 안 고쳤다.\n"
        "\n남은 하나 «박민수 상급자 알려줘»가 재미있다.\n"
        "설명에는 «상사»가 있는데 사용자는 «상급자»라고 했다. 단어가 안 겹친다.\n"
        "이게 도구 설명을 쓸 때 제일 자주 놓치는 지점이다.\n"
        "우리는 사내 용어로 쓰고, 사용자는 자기 말로 묻는다.\n"
        "\n대응은 «동의어를 설명에 넣는 것»이다. 상사·상급자·윗사람·결재선.\n"
        "촌스러워 보여도 이게 듣는다. 실제 질문 로그에서 뽑아 넣으면 더 좋다.\n"
        "\n여기 쓴 선택기는 단어가 겹치는 걸 세는 게 전부다. 모델보다 훨씬 멍청하다.\n"
        "그런데 «설명이 나쁘면 못 고른다»는 성질은 모델도 같다.\n"
        "\n좋은 설명에 들어간 것은 셋이다.\n"
        "  1. 무엇을 «주는지» (반환값을 말한다)\n"
        "  2. 어떤 «말»로 물었을 때 이것인지 (사용자 어휘를 넣는다)\n"
        "  3. 언제 «안» 쓰는지 (경계를 긋는다)\n"
        "\n3번이 제일 자주 빠지고 제일 크게 듣는다.\n"
        "도구가 늘어날수록 «비슷한 도구»가 생기고, 그때 경계를 그어 둔 쪽이 이긴다.\n"
        "\n2장의 말로 하면 «Description 이 호출을 결정»하고,\n"
        "그래프의 말로 하면 도구 설명이 곧 «엣지 선택 함수»다.\n"
        "엣지를 고르는 규칙을 자연어로 적어 두는 셈이라, 그 글이 곧 코드다."
    )


if __name__ == "__main__":
    main()
