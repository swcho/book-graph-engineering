"""
예제 5 — 복구 훈련. «죽여 보지 않으면 복구되는지 모른다».

    python3 ex5_recovery_drill.py

의존성 없음. 죽을 수 있는 지점을 전부 열거하고 각각을 시험한다.
"""

from dataclasses import dataclass


@dataclass
class Step:
    name: str
    external_call: bool     # 밖에 영향을 주는가
    idempotent: bool        # 다시 해도 되는가


PIPELINE = [
    Step("입력 검증",   False, True),
    Step("재고 확인",   True,  True),      # 조회라 다시 해도 된다
    Step("재고 차감",   True,  False),     # 두 번 하면 재고가 두 번 준다
    Step("결제",        True,  False),     # 두 번 하면 두 번 결제
    Step("주문 생성",   True,  True),      # 멱등 키 있음
    Step("알림 발송",   True,  False),     # 두 번 하면 두 번 보낸다
]


def drill(steps):
    """각 지점에서 죽었다고 가정하고, 재개했을 때 무슨 일이 생기나."""
    rows = []
    for i, s in enumerate(steps):
        # 이 단계 «실행 중» 죽으면 이 단계부터 다시 한다
        if not s.external_call:
            verdict, note = "안전", "밖에 영향 없음"
        elif s.idempotent:
            verdict, note = "안전", "다시 해도 같음"
        else:
            verdict, note = "위험", "중복 실행됨"
        rows.append((i + 1, s.name, verdict, note))
    return rows


def main():
    rows = drill(PIPELINE)
    print(f"{'#':>2} {'단계':<10} {'재개 시':<6} 무슨 일이 생기나")
    print("-" * 48)
    risky = 0
    for i, name, verdict, note in rows:
        risky += verdict == "위험"
        mark = " ←" if verdict == "위험" else ""
        print(f"{i:>2} {name:<10} {verdict:<6} {note}{mark}")

    print(f"\n{len(PIPELINE)}단계 중 {risky}개가 위험하다.")

    print(
        "\n이 표를 만드는 데 20분이면 된다. 그리고 이게 복구 설계의 전부다.\n"
        "\n위험한 셋을 어떻게 할까. 순서대로 시도한다.\n"
        "  1. 멱등 키를 붙일 수 있나 — 상대 API 문서를 본다\n"
        "  2. 없으면 «했다는 기록»을 남긴다 (예제 3)\n"
        "  3. 그것도 안 되면 «사람 확인» 상태로 두고 멈춘다\n"
        "\n중요한 건 «어느 단계가 위험한지 목록으로 갖고 있는 것»이다.\n"
        "목록이 없으면 사고가 나고 나서야 그 단계가 위험했다는 걸 안다.\n"
        "\n그리고 이 표는 코드가 바뀌면 같이 바뀐다. 문서에 두지 말고 테스트로 두시라.\n"
        "«새 단계를 추가하면 이 표를 갱신하라»는 검사를 CI 에 넣으면 좋다."
    )


if __name__ == "__main__":
    main()
