"""
예제 2 — 재개하면 «이미 한 일»을 다시 한다. 그게 결제라면.

    python3 ex2_idempotency.py

의존성 없음.
"""

from collections import Counter


class PaymentAPI:
    """외부 결제 API 흉내. 멱등 키를 지원하는 판과 아닌 판."""

    def __init__(self, idempotent):
        self.idempotent = idempotent
        self.charges = []
        self.seen_keys = {}

    def charge(self, order_id, amount, key=None):
        if self.idempotent and key is not None:
            if key in self.seen_keys:
                return self.seen_keys[key], "캐시된 결과"
            receipt = f"R-{len(self.charges) + 1:03d}"
            self.charges.append((order_id, amount, receipt))
            self.seen_keys[key] = receipt
            return receipt, "새 결제"
        receipt = f"R-{len(self.charges) + 1:03d}"
        self.charges.append((order_id, amount, receipt))
        return receipt, "새 결제"


def run(api, attempts, use_key):
    """attempts 번 재시도한다. 실제로는 «죽었다 재개»가 반복되는 것."""
    log = []
    for i in range(attempts):
        key = "order-8842" if use_key else None
        receipt, how = api.charge("order-8842", 50_000, key)
        log.append(f"시도 {i+1}: {receipt} ({how})")
    return log


def main():
    cases = [
        ("멱등 키 없음",           PaymentAPI(idempotent=True),  False),
        ("멱등 키 있음",           PaymentAPI(idempotent=True),  True),
        ("API 가 멱등을 지원 안 함", PaymentAPI(idempotent=False), True),
    ]

    for name, api, use_key in cases:
        log = run(api, 3, use_key)
        total = sum(a for _, a, _ in api.charges)
        print(f"[{name}]")
        for line in log:
            print(f"    {line}")
        print(f"    실제 결제 {len(api.charges)}건, 합계 {total:,}원\n")

    print(
        "가운데만 맞다. 나머지 둘은 15만 원을 결제한다.\n"
        "\n세 번째가 흥미롭다. 우리가 멱등 키를 «보냈는데도» 중복이 났다.\n"
        "받는 쪽이 지원해야 소용이 있는 것이다.\n"
        "\n그래서 확인할 게 둘이다.\n"
        "  1. 우리가 키를 보내는가\n"
        "  2. 상대가 그 키를 보는가\n"
        "\n2번을 확인 안 하고 1번만 해 두면, 코드는 안전해 보이는데 실제로는 안 안전하다.\n"
        "상대 문서를 읽고, 그리고 «실제로 두 번 보내서» 확인해야 한다.\n"
        "\n상대가 지원 안 하면 우리가 기록을 남겨야 한다. 다음 예제가 그거다."
    )


if __name__ == "__main__":
    main()
