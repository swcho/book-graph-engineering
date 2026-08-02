"""
예제 1 — 한 파일에 다 넣은 단일 에이전트. 30분 실습의 '전' 사진.

    python3 ex1_one_file.py

의존성 없음.
"""

from harness import REQUIREMENTS, build_prompt, check, fake_model


def main():
    prompt = build_prompt(REQUIREMENTS)
    spec = fake_model(prompt)

    print("=== 산출물 ===")
    print(spec)

    missing = check(spec)
    print("\n=== 채점 (이 채점은 에이전트가 하지 않았다. 내가 나중에 했다) ===")
    print(f"요구사항 {len(REQUIREMENTS)}개 중 빠진 것: {len(missing)}개")
    for m in missing:
        print(f"  - {m}")
    print(
        "\n문제는 빠졌다는 게 아니다. 빠진 걸 아무도 모른다는 것이다.\n"
        "이 프로그램에는 검사하는 단계가 없다. 그래서 결함이 그대로 나간다."
    )


if __name__ == "__main__":
    main()
