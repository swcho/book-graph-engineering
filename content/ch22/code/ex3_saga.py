"""
예제 3 — 4단계 중 4번에서 실패했다. 앞의 셋을 어떻게 되돌리나.

    python3 ex3_saga.py

의존성 없음. 정방향 단계마다 «되갚는 동작»을 짝지어 두고
실패하면 역순으로 실행한다. 사가(saga) 패턴이다.
"""

from dataclasses import dataclass, field
from typing import Callable, List, Optional

world = {"재고": 10, "잔액": 100_000, "쿠폰": 1, "메일함": []}


@dataclass
class Step:
    name: str
    do: Callable[[], None]
    undo: Optional[Callable[[], None]]   # None 이면 되돌릴 수 없다는 뜻
    undo_name: str = ""


def build(fail_at: str, mail_first: bool = False) -> List[Step]:
    def maybe(name):
        if name == fail_at:
            raise RuntimeError(f"{name} 실패")

    stock = Step("재고 차감",
             lambda: (maybe("재고 차감"), world.__setitem__("재고", world["재고"] - 1)),
             lambda: world.__setitem__("재고", world["재고"] + 1), "재고 복구")
    coupon = Step("쿠폰 사용",
             lambda: (maybe("쿠폰 사용"), world.__setitem__("쿠폰", world["쿠폰"] - 1)),
             lambda: world.__setitem__("쿠폰", world["쿠폰"] + 1), "쿠폰 반환")
    pay = Step("결제",
             lambda: (maybe("결제"), world.__setitem__("잔액", world["잔액"] - 50_000)),
             lambda: world.__setitem__("잔액", world["잔액"] + 50_000), "환불")
    mail = Step("확정 메일",
             lambda: (maybe("확정 메일"), world["메일함"].append("주문 확정")),
             None, "")   # 보낸 메일은 회수할 수 없다

    # 메일을 «먼저» 보내는 순서와 «마지막»에 보내는 순서
    return [stock, mail, coupon, pay] if mail_first else [stock, coupon, pay, mail]


def run(fail_at: str, mail_first: bool = False):
    order = "메일이 두 번째" if mail_first else "메일이 마지막"
    print(f"\n=== {order} · {fail_at} 에서 실패 ===")
    before = dict(world)
    before["메일함"] = list(world["메일함"])
    done: List[Step] = []
    try:
        for s in build(fail_at, mail_first):
            s.do()
            done.append(s)
            print(f"  정방향  {s.name} ... 완료")
    except RuntimeError as e:
        print(f"  정방향  {e}")
        print(f"  ── 되갚기 시작 (역순 {len(done)}건)")
        for s in reversed(done):
            if s.undo is None:
                print(f"  역방향  {s.name} → 되돌릴 수 없음. 사람에게 넘긴다")
                continue
            s.undo()
            print(f"  역방향  {s.undo_name} ... 완료")

    print(f"  세상 상태  전 {before}")
    print(f"             후 {dict(world)}")
    same = dict(world) == before
    print(f"  원상 복구  {'예' if same else '아니오'}")


def main():
    print("정방향 4단계, 각 단계에 «되갚는 동작»을 짝지어 뒀다.")
    for f, mf in (("결제", False), ("확정 메일", False), ("결제", True)):
        run(f, mf)
        world.update({"재고": 10, "잔액": 100_000, "쿠폰": 1, "메일함": []})

    print(
        "\n앞의 둘은 깨끗하게 원상 복구된다. 세 번째만 메일함에 «주문 확정»이 남는다.\n"
        "취소된 주문인데 확정 메일을 받은 손님이 생긴 것이다.\n"
        "\n같은 코드, 같은 실패 지점이다. 다른 건 «단계 순서»뿐이다.\n"
        "\n그래서 규칙이 하나 나온다.\n"
        "«되돌릴 수 없는 단계는 최대한 뒤로 민다.»\n"
        "맨 뒤에 두면 그 앞이 전부 성공한 뒤에만 실행되니까,\n"
        "되갚을 일 자체가 안 생긴다.\n"
        "\n리팩터링이 아니라 순서 바꾸기다. 리스트 한 줄이면 된다."
    )


if __name__ == "__main__":
    main()
