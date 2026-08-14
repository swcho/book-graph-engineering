# %% [markdown]
# # ex4_reuse_or_build.py — 적합도 임계값과 세 갈래 결론
#
# 12장 12.4절 「남의 어휘를 가져다 쓸까」의 판단 로직을 순수 파이썬으로 재현한다.
#
# 판단은 두 단계다.
#
# 1. **공개 어휘 후보가 있는가?** 없으면($v = \text{None}$) 무조건 **만든다(build)**.
# 2. 있다면 **적합도 $s$ 가 임계값 $\theta$ 이상인가?** 이상이면 **그대로 재사용(reuse)**,
#    미만이면 **우리 것을 만들고 «대략 같음»을 걸어 둔다(wrap)**.
#
# 수식으로 쓰면 이렇다.
#
# $$
# f(v, s;\ \theta) =
# \begin{cases}
# \text{build} & v = \varnothing \\[4pt]
# \text{reuse} & v \neq \varnothing \ \wedge\ s \ge \theta \\[4pt]
# \text{wrap}  & v \neq \varnothing \ \wedge\ s < \theta
# \end{cases}
# $$
#
# 책의 기본값은 $\theta = 0.7$ 이다. 저자 본인도 "0.7 은 제 감"이라고 못 박는다.
# 중요한 건 숫자의 정확성이 아니라 **숫자를 정해 두고 매번 같은 기준으로 판단하는 것**이다.
#
# 이 노트북은 $\theta$ 를 $0.5 \sim 0.9$ 로 바꿔 가며 각 어휘의 결론이 어떻게 흔들리는지 본다.

# %%
# 필요 패키지: plotly (시각화), kaleido (PNG 저장). 판단 로직 자체는 순수 파이썬 — 외부 DB/네트워크 불필요.
from __future__ import annotations


def _show(fig):
    try:
        from IPython import get_ipython
        if get_ipython() is not None:
            fig.show()
    except ImportError:
        pass


# 우리가 필요한 개념과, 공개 어휘에 이미 있는 것 (asset의 NEEDED 그대로)
NEEDED = {
    "제품":     {"공개어휘": "schema.org/Product",      "적합도": 0.9},
    "공급사":   {"공개어휘": "schema.org/Organization", "적합도": 0.8},
    "부품":     {"공개어휘": "schema.org/Product",      "적합도": 0.4},
    "리콜":     {"공개어휘": None,                      "적합도": 0.0},
    "대체가능": {"공개어휘": None,                      "적합도": 0.0},
    "납품":     {"공개어휘": "schema.org/seller",       "적합도": 0.5},
}

THRESHOLD = 0.7  # 책의 기본 임계값

print(f"어휘 {len(NEEDED)}개, 기본 임계값 {THRESHOLD}")
# 출력: 어휘 6개, 기본 임계값 0.7


# %% [markdown]
# ## 1. 판단 함수 — 세 갈래
#
# `classify` 는 어휘 하나에 대한 결론을 돌려주고, `partition` 은 원본 스크립트와 똑같이
# `reuse / wrap / build` 세 바구니로 나눈다.

# %%
def classify(info: dict, threshold: float = THRESHOLD) -> str:
    """공개 어휘 후보와 적합도로 세 갈래 결론을 낸다."""
    if info["공개어휘"] is None:
        return "build"          # 공개 어휘에 없다 — 만든다
    if info["적합도"] >= threshold:
        return "reuse"          # 그대로 가져다 쓴다
    return "wrap"               # 우리 것을 만들고 «대략 같음»을 걸어 둔다


def partition(needed: dict, threshold: float = THRESHOLD):
    reuse, build, wrap = [], [], []
    for term, info in needed.items():
        verdict = classify(info, threshold)
        if verdict == "build":
            build.append(term)
        elif verdict == "reuse":
            reuse.append((term, info["공개어휘"]))
        else:
            wrap.append((term, info["공개어휘"], info["적합도"]))
    return reuse, wrap, build


def report(needed: dict, threshold: float = THRESHOLD) -> None:
    reuse, wrap, build = partition(needed, threshold)
    print(f"[임계값 {threshold}]")
    print(f"그대로 가져다 쓴다 ({len(reuse)}개)")
    for t, v in reuse:
        print(f"  {t:<8} → {v}")
    print(f"\n비슷한데 안 맞는다 — 우리 것으로 만들고 «대략 같음»만 걸어 둔다 ({len(wrap)}개)")
    for t, v, s in wrap:
        print(f"  {t:<8} ~ {v}  (적합도 {s})")
    print(f"\n공개 어휘에 없다 — 만든다 ({len(build)}개)")
    for t in build:
        print(f"  {t}")


report(NEEDED, THRESHOLD)
# 출력:
# [임계값 0.7]
# 그대로 가져다 쓴다 (2개)
#   제품       → schema.org/Product
#   공급사      → schema.org/Organization
#
# 비슷한데 안 맞는다 — 우리 것으로 만들고 «대략 같음»만 걸어 둔다 (2개)
#   부품       ~ schema.org/Product  (적합도 0.4)
#   납품       ~ schema.org/seller  (적합도 0.5)
#
# 공개 어휘에 없다 — 만든다 (2개)
#   리콜
#   대체가능


# %% [markdown]
# ## 2. 임계값을 0.5 ~ 0.9 로 흔들어 본다
#
# `build` 는 $\theta$ 와 무관하다. 후보 자체가 없으니 임계값이 어떻든 결론이 안 바뀐다.
# 움직이는 건 후보가 있는 4개(제품 0.9, 공급사 0.8, 납품 0.5, 부품 0.4)뿐이고,
# 그중에서도 **경계가 어휘 점수 위를 지나갈 때만** 뒤집힌다.

# %%
THRESHOLDS = [0.5, 0.6, 0.7, 0.8, 0.9]
TERMS = list(NEEDED.keys())

MARK = {"reuse": "재사용", "wrap": "감싸기", "build": "신규"}

grid = {th: {t: classify(NEEDED[t], th) for t in TERMS} for th in THRESHOLDS}

header = "임계값 | " + " | ".join(f"{t:<6}" for t in TERMS)
print(header)
print("-" * len(header))
for th in THRESHOLDS:
    row = " | ".join(f"{MARK[grid[th][t]]:<6}" for t in TERMS)
    print(f" {th:<5} | {row}")
# 출력:
# 임계값 | 제품     | 공급사    | 부품     | 리콜     | 대체가능   | 납품
# ------------------------------------------------------------------
#  0.5   | 재사용    | 재사용    | 감싸기    | 신규     | 신규     | 재사용
#  0.6   | 재사용    | 재사용    | 감싸기    | 신규     | 신규     | 감싸기
#  0.7   | 재사용    | 재사용    | 감싸기    | 신규     | 신규     | 감싸기
#  0.8   | 재사용    | 재사용    | 감싸기    | 신규     | 신규     | 감싸기
#  0.9   | 재사용    | 감싸기    | 감싸기    | 신규     | 신규     | 감싸기


# %% [markdown]
# ### 뒤집히는 지점
#
# 어휘 $i$ 의 결론은 $\theta \le s_i$ 인 동안 `reuse`, $\theta > s_i$ 가 되는 순간 `wrap` 으로 넘어간다.
# 즉 뒤집힘 경계는 정확히 $\theta = s_i^{+}$ 다.
#
# - **납품** ($s = 0.5$): $\theta = 0.5$ 까지는 재사용, $0.6$ 부터 감싸기.
# - **공급사** ($s = 0.8$): $\theta = 0.8$ 까지는 재사용, $0.9$ 부터 감싸기.
# - **제품** ($s = 0.9$): 0.5~0.9 구간 내내 재사용 — 가장 안전한 재사용 후보.
# - **부품** ($s = 0.4$): 구간 내내 감싸기 — 이름은 같아도 뜻이 다른 대표 사례.
#
# 임계값을 0.7에서 0.5로 낮추면 «납품»이 `schema.org/seller` 로 바로 들어간다.
# 적합도 0.5짜리를 억지로 맞춰 쓰면 예외 조항이 쌓인다는 게 이 장의 경고다.

# %%
flips = []
for t in TERMS:
    prev = None
    for th in THRESHOLDS:
        cur = grid[th][t]
        if prev is not None and cur != prev:
            flips.append((t, prev, cur, th, NEEDED[t]["적합도"]))
        prev = cur

for t, a, b, th, s in flips:
    print(f"{t:<6} (적합도 {s}) : {MARK[a]} → {MARK[b]}  @ 임계값 {th}")
# 출력:
# 공급사    (적합도 0.8) : 재사용 → 감싸기  @ 임계값 0.9
# 납품     (적합도 0.5) : 재사용 → 감싸기  @ 임계값 0.6


# %% [markdown]
# ## 3. 임계값별 결론 분포
#
# 임계값이 올라가면 `reuse` 는 단조 감소하고 `wrap` 은 단조 증가한다. `build` 는 상수 2다.
#
# $$
# |\text{reuse}(\theta)| = \bigl|\{\, i : v_i \neq \varnothing \ \wedge\ s_i \ge \theta \,\}\bigr|
# $$

# %%
counts = {}
for th in THRESHOLDS:
    r, w, b = partition(NEEDED, th)
    counts[th] = {"reuse": len(r), "wrap": len(w), "build": len(b)}
    print(f"임계값 {th}: 재사용 {len(r)}, 감싸기 {len(w)}, 신규 {len(b)}")
# 출력:
# 임계값 0.5: 재사용 3, 감싸기 1, 신규 2
# 임계값 0.6: 재사용 2, 감싸기 2, 신규 2
# 임계값 0.7: 재사용 2, 감싸기 2, 신규 2
# 임계값 0.8: 재사용 2, 감싸기 2, 신규 2
# 임계값 0.9: 재사용 1, 감싸기 3, 신규 2


# %% [markdown]
# ## 4. 시각화
#
# 왼쪽: 어휘별 적합도 막대 + 기본 임계선 0.7 (후보 없는 어휘는 회색 0점).
# 오른쪽: 임계값 0.5~0.9 에 따른 세 갈래 개수 누적 막대.

# %%
import plotly.graph_objects as go
from plotly.subplots import make_subplots

COLOR = {"reuse": "#2E7D32", "wrap": "#EF6C00", "build": "#616161"}

fig = make_subplots(
    rows=1, cols=2,
    subplot_titles=("어휘별 적합도와 임계선 (θ=0.7)", "임계값별 결론 분포"),
    column_widths=[0.55, 0.45],
)

verdict_at_default = {t: classify(NEEDED[t], THRESHOLD) for t in TERMS}
fig.add_trace(
    go.Bar(
        x=TERMS,
        y=[NEEDED[t]["적합도"] for t in TERMS],
        marker_color=[COLOR[verdict_at_default[t]] for t in TERMS],
        text=[f"{NEEDED[t]['적합도']}<br>{MARK[verdict_at_default[t]]}" for t in TERMS],
        textposition="outside",
        showlegend=False,
        hovertemplate="%{x}: 적합도 %{y}<extra></extra>",
    ),
    row=1, col=1,
)
fig.add_hline(
    y=THRESHOLD, line_dash="dash", line_color="#C62828",
    annotation_text="THRESHOLD = 0.7", annotation_position="top right",
    row=1, col=1,
)

for key in ("reuse", "wrap", "build"):
    fig.add_trace(
        go.Bar(
            x=[str(th) for th in THRESHOLDS],
            y=[counts[th][key] for th in THRESHOLDS],
            name=MARK[key],
            marker_color=COLOR[key],
            hovertemplate="임계값 %{x}: " + MARK[key] + " %{y}개<extra></extra>",
        ),
        row=1, col=2,
    )

fig.update_yaxes(title_text="적합도", range=[0, 1.15], row=1, col=1)
fig.update_xaxes(title_text="임계값 θ", row=1, col=2)
fig.update_yaxes(title_text="어휘 수", row=1, col=2)
fig.update_layout(
    barmode="stack",
    title_text="적합도 0.7 기준 — 재사용 / 감싸기 / 신규",
    template="plotly_white",
    width=1000, height=460,
    legend=dict(orientation="h", y=-0.18),
)

_show(fig)

import os
_png = os.path.join(os.path.dirname(os.path.abspath(__file__)), "expy.png")
fig.write_image(_png, scale=2)
print(f"저장: {_png}")
# 출력: 저장: .../5b396e2e-c181-4459-84b9-528633b0633c/expy.png


# %% [markdown]
# ## 정리
#
# - 임계값은 **0.7**. 이 숫자 자체는 저자의 감이고, 요점은 기준을 문서로 못 박아 매번 같게 판단하는 것이다.
# - 세 갈래는 **(1) 0.7 이상 → 그대로 재사용**, **(2) 공개 어휘 없음 → 새로 만든다**,
#   **(3) 그 사이(후보는 있는데 0.7 미만) → 우리 것을 만들고 «대략 같음»을 걸어 둔다**.
# - «대략 같음»은 RDF 라면 `owl:sameAs` / `skos:closeMatch`, LPG 라면 속성에 매핑 표로 둔다.
# - 억지로 맞춰 쓰면(가) 예외 조항이 쌓이고, 다 새로 만들면(나) 밖과 주고받을 때마다 변환한다. 중간이 답이다.
