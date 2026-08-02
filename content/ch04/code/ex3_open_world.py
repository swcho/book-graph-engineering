"""
예제 3 — 열린 세계 가정. 시맨틱 웹이 사람들을 제일 많이 배신한 지점.

    python3 ex3_open_world.py

의존성 없음.
관계형 데이터베이스는 «적혀 있지 않으면 거짓»으로 봅니다(닫힌 세계).
RDF/OWL 은 «적혀 있지 않으면 모른다»로 봅니다(열린 세계).
이 차이가 실무에서 어떻게 사고로 이어지는지 봅시다.
"""

FACTS = {
    ("가온테크", "담당", "김하늘"),
    ("나루소프트", "담당", "박서준"),
    # 다올물산에 대해서는 아무것도 적혀 있지 않다.
}
COMPANIES = ["가온테크", "나루소프트", "다올물산"]


def closed_world(company):
    """SQL 이라면: WHERE NOT EXISTS (...) → 담당자 없음"""
    return any(f[0] == company and f[1] == "담당" for f in FACTS)


def open_world(company):
    """OWL 이라면: 적혀 있지 않을 뿐, 없다고 말하지 않았다"""
    if any(f[0] == company and f[1] == "담당" for f in FACTS):
        return "있음"
    return "모름"


def main():
    print(f"{'회사':<10} {'닫힌 세계(SQL)':<18} {'열린 세계(OWL)'}")
    print("-" * 46)
    for c in COMPANIES:
        print(f"{c:<10} {'담당 있음' if closed_world(c) else '담당 없음':<18} {open_world(c)}")

    print(
        "\n다올물산 줄이 문제다.\n"
        "«담당자 없는 회사에 알림을 보내라»는 배치를 SQL 로 짜면 다올물산이 걸린다.\n"
        "같은 걸 OWL 추론기로 짜면 아무도 안 걸린다. «없다»고 결론 내리지 않으니까.\n"
        "\n제가 이걸 몰라서 3주를 헤맸습니다. 추론기가 고장 난 줄 알았어요.\n"
        "고장이 아니라 설계였습니다."
    )

    # 닫힌 세계를 원한다면 명시적으로 «없다»를 적어야 한다.
    print("\n열린 세계에서 «없다»를 말하려면 이렇게 적어야 한다:")
    print('  ex:다올물산 owl:complementOf [ a owl:Restriction ;')
    print('      owl:onProperty ex:담당 ; owl:someValuesFrom owl:Thing ] .')
    print("  ...읽기 싫죠. 이게 OWL 이 외면당한 이유 중 하나입니다.")
    print("\n실무 해법: 검증은 SHACL 로 합니다. SHACL 은 닫힌 세계로 봅니다. 13장에서.")


if __name__ == "__main__":
    main()
