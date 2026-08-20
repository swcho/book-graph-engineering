# %% [markdown]
# # 「종류를 보고」 병합 — 집합은 합집합, 수치는 변화량 합산
#
# 두 에이전트가 같은 노드를 동시에 고쳤을 때, 충돌 **감지**는 기술 문제라 일반 해법이
# 있지만 충돌 **해결**은 도메인 문제라 일반 해법이 없다.
# 그래서 필드의 **종류(kind)** 별로 병합 규칙을 따로 정한다.
#
# | 종류 | 병합 규칙 | 예 |
# |---|---|---|
# | 집합 | **합집합** | `결제,정산` + `결제,신규` → `결제,신규,정산` |
# | 수치 | **변화량 합산** | `3→5`(+2), `3→4`(+1) → `3+2+1 = 6` |
# | 자유문 | 사람에게 보류 | 설명 문구 |
# | 단일 참조 | 출처 등급 → 동률이면 사람 | 팀장 |
#
# 이 노트북이 보이려는 것은 세 가지다.
#
# 1. 합집합과 변화량 합산은 **교환법칙·결합법칙**을 만족해서 **적용 순서와 무관**하다.
# 2. last-write-wins(마지막이 이긴다)는 순서에 따라 결과가 갈라진다.
# 3. 「인원 = 6」 함정 — 변화량 합산은 **독립적인 증분**일 때만 맞다.
#
# 필요 패키지: plotly, kaleido (없으면 계산 셀은 그대로 동작하고 그림만 건너뛴다)

# %%
from itertools import permutations
from functools import reduce

PALETTE = {
    "type_aware": "#2a78d6",  # 종류를 보고
    "lww": "#eb6834",         # 마지막이 이긴다
    "truth": "#1baf7a",       # 실제 정답
}
KO_FONT = "Apple SD Gothic Neo, AppleGothic, Noto Sans KR, sans-serif"


def _show(fig):
    try:
        from IPython import get_ipython
        if get_ipython() is not None:
            fig.show()
    except ImportError:
        pass


# %% [markdown]
# ## 1. 카드의 그 예시부터 — 집합과 수치를 각각 합쳐 본다
#
# 원본 노드는 `태그 = {결제}`, `인원 = 3`.
# 에이전트 A는 `태그 = 결제,정산` / `인원 = 5`, 에이전트 B는 `태그 = 결제,신규` / `인원 = 4`를 쓰려고 한다.

# %%
def merge_set(base, a, b):
    """집합 필드: 양쪽이 «최종적으로 원하는 집합»의 합집합."""
    return sorted(set(a.split(",")) | set(b.split(",")))


def merge_number(base, a, b):
    """수치 필드: 양쪽이 만든 «변화량»을 더해 원본에 얹는다."""
    delta = (int(a) - int(base)) + (int(b) - int(base))
    return int(base) + delta


BASE_TAG, A_TAG, B_TAG = "결제", "결제,정산", "결제,신규"
BASE_NUM, A_NUM, B_NUM = "3", "5", "4"

tag_merged = merge_set(BASE_TAG, A_TAG, B_TAG)
num_merged = merge_number(BASE_NUM, A_NUM, B_NUM)

print(f"태그: {A_TAG} + {B_TAG} -> {','.join(tag_merged)}   (합집합)")
print(f"인원: {BASE_NUM}->{A_NUM} ({int(A_NUM)-int(BASE_NUM):+d}), "
      f"{BASE_NUM}->{B_NUM} ({int(B_NUM)-int(BASE_NUM):+d}) -> {num_merged}   (변화량 합산)")
print(f"\n누구도 {num_merged}을(를) 쓰려고 하지 않았는데 결과는 {num_merged}이다.")
# 출력:
# 태그: 결제,정산 + 결제,신규 -> 결제,신규,정산   (합집합)
# 인원: 3->5 (+2), 3->4 (+1) -> 6   (변화량 합산)
#
# 누구도 6을(를) 쓰려고 하지 않았는데 결과는 6이다.

# %% [markdown]
# ## 2. 수식으로 — 왜 순서가 상관없는가
#
# **집합 필드.** 각 편집자 $i$가 최종적으로 원하는 태그 집합을 $S_i$라 하면
#
# $$ S_{\text{merged}} \;=\; \bigcup_{i} S_i $$
#
# 합집합 $\cup$ 는 교환법칙 $A \cup B = B \cup A$, 결합법칙
# $(A \cup B) \cup C = A \cup (B \cup C)$, 멱등성 $A \cup A = A$ 를 모두 만족한다.
# 즉 $(\mathcal{P}(T),\ \cup)$ 는 **결합-반격자(join-semilattice)** 이고,
# 어떤 순서로 적용하든 상한(least upper bound)이라는 같은 값에 도달한다.
#
# **수치 필드.** 편집자 $i$의 변화량을 $d_i = v_i - v_{\text{base}}$ 라 하면
#
# $$ v_{\text{merged}} \;=\; v_{\text{base}} + \sum_{i} d_i $$
#
# 정수 덧셈도 교환·결합법칙을 만족한다. 단 **멱등성은 없다** —
# 같은 변화량을 두 번 적용하면 두 번 더해진다. 그래서 변화량에는 중복 적용 방지가 필요하다.
#
# **대조군: last-write-wins.** $\text{lww}(a, b) = b$ 는 결합법칙은 만족하지만
# ($\text{lww}(\text{lww}(a,b),c) = c = \text{lww}(a,\text{lww}(b,c))$)
# 교환법칙은 만족하지 않는다 ($\text{lww}(a,b)=b \ne a=\text{lww}(b,a)$).
# **교환법칙이 깨진다는 것이 곧 「순서에 따라 결과가 갈린다」는 뜻**이다.

# %% [markdown]
# ## 3. 편집을 «패치»로 표현하고, 패치끼리 합친다
#
# 순서 무관을 제대로 검증하려면 편집 하나하나를 「최종 값」이 아니라
# **합칠 수 있는 패치**로 들고 있어야 한다.
# 집합은 태그 집합, 수치는 변화량(delta), 자유문/단일 참조는 후보 집합으로 표현한다.

# %%
HOLD = "＜사람 확인 보류＞"

BASE = {"태그": frozenset({"결제"}), "인원": 3, "설명": "이전 설명", "팀장": "박민수"}

# 편집자 이름 -> 그가 만든 «패치»
EDITS = {
    "A(user)":       {"태그": frozenset({"결제", "정산"}), "delta_인원": +2, "설명": "새 설명 A"},
    "B(agent-4821)": {"태그": frozenset({"결제", "신규"}), "delta_인원": +1, "설명": "새 설명 B"},
    "C(batch)":      {"태그": frozenset({"정산", "대사"}), "delta_인원": -1, "설명": "이전 설명"},
}


def merge_patch(p, q):
    """패치 ⊔ 패치. 종류별 규칙을 그대로 적용한다."""
    return {
        # 집합: 합집합 (교환·결합·멱등)
        "태그": p["태그"] | q["태그"],
        # 수치: 변화량 합산 (교환·결합)
        "delta_인원": p["delta_인원"] + q["delta_인원"],
        # 자유문: 다르면 사람에게 (집합으로 모아 두면 순서 무관해진다)
        "설명": p["설명"] if p["설명"] == q["설명"] else HOLD,
    }


def apply_to_base(patch, base=BASE):
    return {
        "태그": ",".join(sorted(patch["태그"])),
        "인원": base["인원"] + patch["delta_인원"],
        "설명": patch["설명"],
    }


def merge_lww(p, q):
    """대조군: 나중 것이 이긴다. 앞의 편집을 통째로 버린다."""
    return q


print("BASE  :", {k: (sorted(v) if isinstance(v, frozenset) else v) for k, v in BASE.items()})
for name, e in EDITS.items():
    print(f"  {name:<15} 태그={sorted(e['태그'])}  인원변화={e['delta_인원']:+d}  설명={e['설명']!r}")
# 출력:
# BASE  : {'태그': ['결제'], '인원': 3, '설명': '이전 설명', '팀장': '박민수'}
#   A(user)         태그=['결제', '정산']  인원변화=+2  설명='새 설명 A'
#   B(agent-4821)   태그=['결제', '신규']  인원변화=+1  설명='새 설명 B'
#   C(batch)        태그=['대사', '정산']  인원변화=-1  설명='이전 설명'

# %% [markdown]
# ## 4. 모든 순열을 돌려 본다 — 종류를 보고 vs 마지막이 이긴다

# %%
names = list(EDITS)
perms = list(permutations(names))

rows_type, rows_lww = [], []
for order in perms:
    patches = [EDITS[n] for n in order]
    rows_type.append((order, apply_to_base(reduce(merge_patch, patches))))
    rows_lww.append((order, apply_to_base(reduce(merge_lww, patches))))

print("순열                                   [종류를 보고]            [마지막이 이긴다]")
print("-" * 92)
for (order, t), (_, l) in zip(rows_type, rows_lww):
    label = " → ".join(n.split("(")[0] for n in order)
    print(f"{label:<14} 태그={t['태그']:<20} 인원={t['인원']}   |   "
          f"태그={l['태그']:<16} 인원={l['인원']}")
# 출력:
# 순열                                   [종류를 보고]            [마지막이 이긴다]
# --------------------------------------------------------------------------------------------
# A → B → C      태그=결제,대사,신규,정산  인원=5   |   태그=대사,정산    인원=2
# A → C → B      태그=결제,대사,신규,정산  인원=5   |   태그=결제,신규    인원=4
# B → A → C      태그=결제,대사,신규,정산  인원=5   |   태그=대사,정산    인원=2
# B → C → A      태그=결제,대사,신규,정산  인원=5   |   태그=결제,정산    인원=5
# C → A → B      태그=결제,대사,신규,정산  인원=5   |   태그=결제,신규    인원=4
# C → B → A      태그=결제,대사,신규,정산  인원=5   |   태그=결제,정산    인원=5
# → 왼쪽은 6개 순열 전부 같다. 오른쪽은 3가지로 갈린다.

# %%
uniq_type_tag = {t["태그"] for _, t in rows_type}
uniq_type_num = {t["인원"] for _, t in rows_type}
uniq_lww_tag = {l["태그"] for _, l in rows_lww}
uniq_lww_num = {l["인원"] for _, l in rows_lww}

print(f"순열 개수: {len(perms)}")
print(f"[종류를 보고]   태그 고유 결과 {len(uniq_type_tag)}개 {uniq_type_tag}, "
      f"인원 고유 결과 {len(uniq_type_num)}개 {uniq_type_num}")
print(f"[마지막이 이긴다] 태그 고유 결과 {len(uniq_lww_tag)}개, "
      f"인원 고유 결과 {len(uniq_lww_num)}개 {sorted(uniq_lww_num)}")

assert len(uniq_type_tag) == 1 and len(uniq_type_num) == 1, "종류를 보고 는 순서 무관이어야 한다"
assert len(uniq_lww_num) > 1, "LWW 는 순서에 따라 갈라져야 한다"
print("\n→ 종류를 보고: 모든 순열이 같은 값으로 수렴(convergent).")
print("→ 마지막이 이긴다: 누가 마지막이냐에 따라 결과가 갈린다.")
# 출력:
# 순열 개수: 6
# [종류를 보고]   태그 고유 결과 1개 {'결제,대사,신규,정산'}, 인원 고유 결과 1개 {5}
# [마지막이 이긴다] 태그 고유 결과 3개, 인원 고유 결과 3개 [2, 4, 5]
#
# → 종류를 보고: 모든 순열이 같은 값으로 수렴(convergent).
# → 마지막이 이긴다: 누가 마지막이냐에 따라 결과가 갈린다.

# %% [markdown]
# ## 5. 법칙을 직접 검증한다 — 교환·결합·멱등

# %%
def _key(p):
    return (tuple(sorted(p["태그"])), p["delta_인원"], p["설명"])


A, B, C = (EDITS[n] for n in names)

comm = _key(merge_patch(A, B)) == _key(merge_patch(B, A))
assoc = _key(merge_patch(merge_patch(A, B), C)) == _key(merge_patch(A, merge_patch(B, C)))
idem_set = merge_patch(A, A)["태그"] == A["태그"]
idem_num = merge_patch(A, A)["delta_인원"] == A["delta_인원"]

print(f"교환법칙  A⊔B == B⊔A            : {comm}")
print(f"결합법칙  (A⊔B)⊔C == A⊔(B⊔C)   : {assoc}")
print(f"멱등성    집합 A⊔A == A         : {idem_set}")
print(f"멱등성    수치 A⊔A == A         : {idem_num}  ← 변화량은 멱등이 아니다!")
print(f"          (A⊔A 의 인원변화 = {merge_patch(A, A)['delta_인원']:+d}, 원래 {A['delta_인원']:+d})")

# 대조군 LWW
print()
print(f"[LWW] 교환법칙 lww(A,B)==lww(B,A): {_key(merge_lww(A, B)) == _key(merge_lww(B, A))}")
print(f"[LWW] 결합법칙                    : "
      f"{_key(merge_lww(merge_lww(A, B), C)) == _key(merge_lww(A, merge_lww(B, C)))}")
print("→ LWW 는 결합법칙만 만족한다. 교환법칙이 없으니 순서가 결과를 바꾼다.")
# 출력:
# 교환법칙  A⊔B == B⊔A            : True
# 결합법칙  (A⊔B)⊔C == A⊔(B⊔C)   : True
# 멱등성    집합 A⊔A == A         : True
# 멱등성    수치 A⊔A == A         : False  ← 변화량은 멱등이 아니다!
#           (A⊔A 의 인원변화 = +4, 원래 +2)
#
# [LWW] 교환법칙 lww(A,B)==lww(B,A): False
# [LWW] 결합법칙                    : True
# → LWW 는 결합법칙만 만족한다. 교환법칙이 없으니 순서가 결과를 바꾼다.

# %% [markdown]
# ## 6. 「인원 = 6」 함정 — 변화량 합산이 틀리는 경우
#
# 변화량 합산은 두 편집이 **서로 독립적인 증분**일 때만 맞다.
# 두 에이전트가 **같은 사실을 각자 다시 센 결과**를 썼다면, 그건 증분이 아니라 관측값이다.
# 관측값끼리는 더하면 안 된다.

# %%
def merge_delta(base, a, b):
    return base + (a - base) + (b - base)


scenarios = [
    # (이름, base, A가 쓴 값, B가 쓴 값, 편집의 의미, 실제 정답)
    ("독립 증분", 3, 5, 4, "A가 2명 채용, B가 1명 채용", 6),
    ("재계수",   3, 5, 4, "둘 다 «현재 인원»을 다시 셈", 5),
]

print(f"{'시나리오':<10}{'편집 의미':<28}{'변화량 합산':>10}{'실제 정답':>10}   판정")
print("-" * 74)
trap_rows = []
for name, base, a, b, meaning, truth in scenarios:
    got = merge_delta(base, a, b)
    verdict = "맞음" if got == truth else "틀림 ←  함정"
    trap_rows.append((name, got, truth))
    print(f"{name:<10}{meaning:<28}{got:>10}{truth:>10}   {verdict}")

print("\n두 시나리오의 «데이터»는 완전히 같다: base=3, A=5, B=4.")
print("다른 것은 «편집이 무엇을 뜻하는가» 뿐이다. 이건 스키마가 아니라 도메인 지식이다.")
print("장바구니 담기·재고 차감·좋아요 수 = 독립 증분 → 합산 OK.")
print("현재 값을 다시 센 결과(재계수·상태 스냅샷) → 합산 금지, 사람 또는 최신 관측 채택.")
# 출력:
# 시나리오      편집 의미                       변화량 합산     실제 정답   판정
# --------------------------------------------------------------------------
# 독립 증분     A가 2명 채용, B가 1명 채용                 6         6   맞음
# 재계수       둘 다 «현재 인원»을 다시 셈                 6         5   틀림 ←  함정
#
# 두 시나리오의 «데이터»는 완전히 같다: base=3, A=5, B=4.
# 다른 것은 «편집이 무엇을 뜻하는가» 뿐이다. 이건 스키마가 아니라 도메인 지식이다.
# 장바구니 담기·재고 차감·좋아요 수 = 독립 증분 → 합산 OK.
# 현재 값을 다시 센 결과(재계수·상태 스냅샷) → 합산 금지, 사람 또는 최신 관측 채택.

# %% [markdown]
# ## 7. CRDT와의 연결
#
# 「종류를 보고」 전략이 하는 일은 사실 **CRDT를 필드 단위로 손으로 고른 것**이다.
#
# | 이 노트북의 규칙 | 대응하는 CRDT | 성질 |
# |---|---|---|
# | 태그 합집합 | **G-Set** (grow-only set) | 교환·결합·멱등 → 순서 무관, 재적용 안전 |
# | 인원 변화량 합산 | **PN-Counter** (증가/감소 카운터) | 교환·결합, **멱등 아님** → 중복 적용 방지 필요 |
# | 설명(자유문) | 대응 CRDT 없음(또는 RGA/텍스트 CRDT) | 병합 불가 → 사람에게 |
# | 팀장(단일 참조) | LWW-Register | 결정적이지만 «옳음»은 보장 안 됨 |
#
# CRDT의 핵심 정리는 이것이다. 병합 연산이 **결합-반격자**(교환·결합·멱등)를 이루면
# 어떤 순서로 어떤 replica가 합치든 같은 값에 수렴한다(**strong eventual consistency**).
#
# $$ (S,\ \sqcup) \text{ 가 반격자} \iff a \sqcup b = b \sqcup a,\;
# (a \sqcup b) \sqcup c = a \sqcup (b \sqcup c),\; a \sqcup a = a $$
#
# 여기서 얻는 실무적 결론:
#
# - **집합/카운터는 병합 가능한 자료형으로 «미리» 모델링**해 두면 충돌 해결이 공짜가 된다.
# - 카운터는 멱등이 아니므로 **각 증분에 고유 ID**를 붙여 중복 적용을 막아야 한다.
# - 자유문·단일 참조처럼 **병합 규칙을 정할 수 없는 필드는 사람에게 보내는 것이 정답**이다.
#   충돌 **감지**는 기술이지만 충돌 **해결**은 도메인이다.

# %% [markdown]
# ## 8. 시각화

# %%
import os

try:
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
    _HAS_PLOTLY = True
except ImportError:
    _HAS_PLOTLY = False
    print("plotly 미설치 — 시각화를 건너뜁니다. (pip install plotly kaleido)")

if _HAS_PLOTLY:
    x_labels = [" → ".join(n.split("(")[0] for n in order) for order in perms]

    fig = make_subplots(
        rows=1, cols=3,
        subplot_titles=(
            "순열별 「인원」 병합 결과",
            "6개 순열이 만든 고유 결과 개수",
            "변화량 합산의 함정 (base=3, A=5, B=4)",
        ),
        horizontal_spacing=0.09,
    )

    # (1) 순열별 인원 결과
    fig.add_trace(go.Scatter(
        x=x_labels, y=[t["인원"] for _, t in rows_type],
        name="종류를 보고", legendgroup="ta", mode="lines+markers",
        line=dict(color=PALETTE["type_aware"], width=2), marker=dict(size=10),
        text=[str(t["인원"]) for _, t in rows_type], textposition="top center",
    ), row=1, col=1)
    fig.add_trace(go.Scatter(
        x=x_labels, y=[l["인원"] for _, l in rows_lww],
        name="마지막이 이긴다", legendgroup="lww", mode="lines+markers",
        line=dict(color=PALETTE["lww"], width=2, dash="dot"), marker=dict(size=10, symbol="square"),
    ), row=1, col=1)

    # (2) 고유 결과 개수
    fig.add_trace(go.Bar(
        x=["태그(집합)", "인원(수치)"], y=[len(uniq_type_tag), len(uniq_type_num)],
        name="종류를 보고", legendgroup="ta", showlegend=False,
        marker=dict(color=PALETTE["type_aware"], line=dict(color="white", width=2)),
        text=[len(uniq_type_tag), len(uniq_type_num)], textposition="outside",
    ), row=1, col=2)
    fig.add_trace(go.Bar(
        x=["태그(집합)", "인원(수치)"], y=[len(uniq_lww_tag), len(uniq_lww_num)],
        name="마지막이 이긴다", legendgroup="lww", showlegend=False,
        marker=dict(color=PALETTE["lww"], line=dict(color="white", width=2)),
        text=[len(uniq_lww_tag), len(uniq_lww_num)], textposition="outside",
    ), row=1, col=2)

    # (3) 함정
    fig.add_trace(go.Bar(
        x=[r[0] for r in trap_rows], y=[r[1] for r in trap_rows],
        name="변화량 합산 결과", legendgroup="ta2", showlegend=True,
        marker=dict(color=PALETTE["type_aware"], line=dict(color="white", width=2)),
        text=[r[1] for r in trap_rows], textposition="outside",
    ), row=1, col=3)
    fig.add_trace(go.Bar(
        x=[r[0] for r in trap_rows], y=[r[2] for r in trap_rows],
        name="실제 정답", legendgroup="truth", showlegend=True,
        marker=dict(color=PALETTE["truth"], line=dict(color="white", width=2)),
        text=[r[2] for r in trap_rows], textposition="outside",
    ), row=1, col=3)

    fig.add_annotation(
        x="재계수", y=6.9, xref="x3", yref="y3", text="합산 6 ≠ 정답 5",
        showarrow=True, arrowhead=2, ax=0, ay=-28,
        font=dict(size=12, color="#5c5c5c"),
    )

    fig.update_yaxes(title_text="인원 값", row=1, col=1, dtick=1, range=[1, 6])
    fig.update_yaxes(title_text="고유 결과 개수", row=1, col=2, dtick=1, range=[0, 4])
    fig.update_yaxes(title_text="인원 값", row=1, col=3, range=[0, 8])
    fig.update_xaxes(tickangle=-30, row=1, col=1)

    fig.update_layout(
        title=dict(
            text="「종류를 보고」 병합: 집합=합집합 · 수치=변화량 합산 → 순서 무관",
            font=dict(size=18),
        ),
        template="plotly_white",
        font=dict(family=KO_FONT, size=12, color="#3d3d3d"),
        barmode="group", bargap=0.35,
        legend=dict(orientation="h", yanchor="bottom", y=1.12, xanchor="left", x=0),
        width=1400, height=520,
        margin=dict(t=130, b=90, l=70, r=40),
    )

    _show(fig)

    try:
        _here = os.path.dirname(os.path.abspath(__file__))
    except NameError:  # 노트북 실행 시
        _here = os.getcwd()
    out = os.path.join(_here, "expy.png")
    try:
        fig.write_image(out, scale=2)
        print(f"저장: {out}")
    except Exception as exc:  # kaleido 미설치 등
        print(f"이미지 저장 실패(kaleido 필요): {exc}")
# 출력:
# 저장: .../expy.png

# %% [markdown]
# ## 정리
#
# - **집합 → 합집합**: `결제,정산` + `결제,신규` = `결제,신규,정산`. 교환·결합·멱등 → 순서 무관(G-Set).
# - **수치 → 변화량 합산**: `3→5`(+2)와 `3→4`(+1)를 더해 `3+3 = 6`. 교환·결합 → 순서 무관, 그러나 멱등은 아님(PN-Counter).
# - **6은 누구도 쓰지 않은 값**이다. 「두 명 늘고 한 명 늘었다」면 맞고,
#   「같은 사실을 다르게 셌다」면 틀린다. 변화량 합산은 **독립적인 증분**에만 쓴다.
# - **자유문·단일 참조**는 병합 규칙이 없다 → 출처 등급, 그것도 동률이면 사람에게.
