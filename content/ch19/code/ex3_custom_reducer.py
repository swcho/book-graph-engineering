"""
예제 3 — 리듀서를 직접 쓴다. «어떻게 합칠까»가 도메인 지식이다.

    pip install "langgraph>=1.0,<2.0"
    python3 ex3_custom_reducer.py

확인 시점 LangGraph 1.0.1.
"""

from typing import Annotated, TypedDict

from langgraph.graph import END, START, StateGraph


# ---------- 리듀서 넷 ----------
def keep_latest(old, new):
    """타임스탬프가 더 최근인 쪽을 남긴다."""
    if not old:
        return new
    if not new:
        return old
    return new if new["at"] > old["at"] else old


def keep_best(old, new):
    """신뢰도가 높은 쪽. 같으면 먼저 온 쪽."""
    if not old:
        return new
    if not new:
        return old
    return new if new["conf"] > old["conf"] else old


def merge_dict(old, new):
    """키 단위 병합. 겹치면 새 것이 이긴다."""
    out = dict(old or {})
    out.update(new or {})
    return out


def collect_unique(old, new):
    """이어 붙이되 중복은 뺀다. 순서는 유지."""
    seen, out = set(), []
    for x in list(old or []) + list(new or []):
        k = x if isinstance(x, str) else str(x)
        if k not in seen:
            seen.add(k); out.append(x)
    return out


class S(TypedDict):
    담당:   Annotated[dict, keep_latest]
    분류:   Annotated[dict, keep_best]
    속성:   Annotated[dict, merge_dict]
    태그:   Annotated[list, collect_unique]


def src_erp(s):
    return {"담당": {"who": "김하늘", "at": "2024-03-01"},
            "분류": {"cat": "제조", "conf": 0.7},
            "속성": {"사업자번호": "123-45-67890", "등급": "A"},
            "태그": ["제조", "중견"]}


def src_crm(s):
    return {"담당": {"who": "박서준", "at": "2026-01-15"},
            "분류": {"cat": "유통", "conf": 0.9},
            "속성": {"등급": "B", "지역": "수도권"},
            "태그": ["중견", "수도권"]}


b = StateGraph(S)
b.add_node("ERP", src_erp)
b.add_node("CRM", src_crm)
b.add_edge(START, "ERP")
b.add_edge(START, "CRM")
b.add_edge("ERP", END)
b.add_edge("CRM", END)
app = b.compile()


def main():
    out = app.invoke({"담당": {}, "분류": {}, "속성": {}, "태그": []})

    print("두 출처가 같은 슈퍼스텝에서 각자 값을 낸다.\n")
    print(f"{'필드':<6} {'리듀서':<16} 결과")
    print("-" * 66)
    rows = [("담당", "가장 최근", out["담당"]),
            ("분류", "신뢰도 높은 쪽", out["분류"]),
            ("속성", "키 단위 병합", out["속성"]),
            ("태그", "중복 뺀 이어 붙이기", out["태그"])]
    for name, rule, val in rows:
        print(f"{name:<6} {rule:<16} {val}")

    print(
        "\n필드마다 «합치는 규칙»이 다르다. 14장의 생존 규칙과 같은 얘기다.\n"
        "다만 거기서는 배치로 병합했고 여기서는 실행 중에 합친다.\n"
        "\n«속성»을 보라. 등급이 A(ERP)와 B(CRM) 로 갈렸는데 «A»가 남았다.\n"
        "merge_dict 는 «새 것이 이긴다»로 짰는데, 실행기가 CRM 을 먼저 돌려서\n"
        "ERP 가 «새 것»이 되어 버렸다. 코드를 짤 때 제가 기대한 것과 반대다.\n"
        "\n«태그» 순서도 보라. ['중견', '수도권', '제조'] 다. CRM 이 먼저 왔다는 뜻이다.\n"
        "저는 ERP 를 먼저 등록했는데도.\n"
        "\n이게 함정이다. 순서에 기대는 리듀서는 «내가 예상한 답»을 안 낸다.\n"
        "그리고 실행기 버전이 올라가면 순서가 또 바뀔 수 있다.\n"
        "고치려면 값에 출처와 시각을 같이 담고 리듀서가 그걸 보고 정해야 한다.\n"
        "«담당»과 «분류»가 그렇게 돼 있다. 순서와 무관하게 같은 답이 나온다."
    )


if __name__ == "__main__":
    main()
