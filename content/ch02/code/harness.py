"""
2장 공통 부품. 의존성 없음. Python 3.9 이상.

여기 들어 있는 `fake_model` 은 진짜 언어 모델이 아니다.
API 키 없이도 예제가 돌아가야 해서 넣은 가짜다.
대신 진짜 모델이 흔히 보이는 성질 두 가지를 흉내 낸다.

  1) 지시가 길어지면 뒤쪽 요구사항을 빠뜨린다.
  2) 빠뜨린 걸 지적해 주면 그때 채운다.

이 두 성질이 2장 전체의 논거다. 모델을 바꿔도 이 성질은 정도만 달라진다.
"""

REQUIREMENTS = [
    "함수 이름과 인자를 적는다",
    "반환값의 형식을 적는다",
    "실패했을 때 무엇을 던지는지 적는다",
    "같은 요청을 두 번 보내면 어떻게 되는지 적는다",
]

# 각 요구사항이 지켜졌는지 검사하는 표식
MARKERS = {
    "함수 이름과 인자를 적는다": "## 시그니처",
    "반환값의 형식을 적는다": "## 반환",
    "실패했을 때 무엇을 던지는지 적는다": "## 예외",
    "같은 요청을 두 번 보내면 어떻게 되는지 적는다": "## 멱등성",
}

_BLOCKS = {
    "## 시그니처": "## 시그니처\ncharge(order_id: str, amount: int) -> Receipt",
    "## 반환": "## 반환\nReceipt(id, status, charged_at). status 는 paid 또는 pending.",
    "## 예외": "## 예외\nInsufficientFunds, GatewayTimeout(재시도 가능), InvalidOrder.",
    "## 멱등성": "## 멱등성\norder_id 를 멱등 키로 쓴다. 같은 키의 두 번째 요청은 첫 결과를 그대로 돌려준다.",
}


def fake_model(prompt: str) -> str:
    """지시 길이에 따라 뒤쪽 요구사항을 빠뜨리는 모델 흉내."""
    # 지적을 받았으면 이전 산출물에 빠진 항목만 덧붙여 다시 낸다.
    if "빠진 항목:" in prompt:
        wanted = [m.strip() for m in
                  prompt.split("빠진 항목:")[1].strip().splitlines()[0].split(",")
                  if m.strip()]
        previous = ""
        if "이전 산출물:" in prompt:
            previous = prompt.split("이전 산출물:")[1].split("빠진 항목:")[0].strip()
        blocks = [previous] if previous else []
        blocks += [_BLOCKS[w] for w in wanted if w in _BLOCKS]
        return "\n\n".join(b for b in blocks if b)

    # 첫 요청. 지시가 길수록 뒤쪽을 잘라 먹는다.
    n_req = prompt.count("- ")
    kept = max(1, n_req - 2)          # 4개를 요구하면 2개만 쓴다
    return "\n\n".join(list(_BLOCKS.values())[:kept])


def check(spec: str):
    """규칙 기반 검증. 모델이 아니라 코드가 한다. 그래서 결과가 매번 같다."""
    missing = [marker for marker in MARKERS.values() if marker not in spec]
    return missing


def build_prompt(reqs, previous=None, feedback=None) -> str:
    lines = ["결제 함수의 명세를 마크다운으로 써라.", ""]
    lines += [f"- {r}" for r in reqs]
    if feedback:
        lines += ["", "이전 산출물:", previous or "", "", f"빠진 항목: {', '.join(feedback)}"]
    return "\n".join(lines)
