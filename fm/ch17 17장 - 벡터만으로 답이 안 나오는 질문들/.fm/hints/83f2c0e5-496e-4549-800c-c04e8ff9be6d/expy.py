# %% [markdown]
# # 같은 성능표, 갈리는 결론 — 질문 분포가 결론을 뒤집는다
#
# 17장 ex5의 핵심을 재현한다. 유형별 정답률 표는 **하나**인데,
# 조직마다 질문 분포(mix)가 달라서 가중 평균이 달라진다.
#
# $$\text{score}(\text{mix}, \text{방식}) = \sum_{k \in \text{유형}} p_k \cdot \text{acc}_{k,\text{방식}}$$
#
# - A 조직(사실 조회 위주): 그래프를 붙여도 $+0.029$ — 오차 범위. 복잡도·지연·갱신 비용을 생각하면 붙이지 않는 게 맞다.
# - B 조직(분석 위주): $+0.240$ — 명확하게 이득.
#
# 즉 "GraphRAG가 좋은가?"가 아니라 "**우리 질문 분포에서** 좋은가?"가 맞는 질문이다.

# %%
# 필요 패키지: plotly, kaleido  (pip install plotly kaleido)
import os

import plotly.graph_objects as go
from plotly.subplots import make_subplots


def _show(fig):
    try:
        from IPython import get_ipython
        if get_ipython() is not None:  # VSCode 셀/Jupyter에서만 렌더링
            fig.show()
    except ImportError:
        pass


HERE = os.path.dirname(os.path.abspath(__file__)) if "__file__" in dir() else "."

# %% [markdown]
# ## 1. 유형별 점수표 (ex5의 RESULTS)
#
# 그래프를 붙이면 다중홉·비교·전역집계는 크게 좋아지지만,
# **사실조회·단일요약은 오히려 조금 나빠진다** (−0.02, −0.03).

# %%
KINDS = ["사실조회", "단일요약", "다중홉", "비교", "전역집계"]

ACC = {  # 유형별 정답률
    "벡터만":      {"사실조회": 0.91, "단일요약": 0.88, "다중홉": 0.47, "비교": 0.39, "전역집계": 0.18},
    "그래프 붙임": {"사실조회": 0.89, "단일요약": 0.85, "다중홉": 0.78, "비교": 0.74, "전역집계": 0.71},
}

print(f"{'유형':<8} {'벡터만':>8} {'그래프':>8} {'차이':>8}")
for k in KINDS:
    v, g = ACC["벡터만"][k], ACC["그래프 붙임"][k]
    print(f"{k:<8} {v:>8.2f} {g:>8.2f} {g - v:>+8.2f}{'  ← 나빠짐' if g < v else ''}")

# 출력:
# 유형       벡터만  그래프    차이
# 사실조회     0.91     0.89    -0.02  ← 나빠짐
# 단일요약     0.88     0.85    -0.03  ← 나빠짐
# 다중홉       0.47     0.78    +0.31
# 비교         0.39     0.74    +0.35
# 전역집계     0.18     0.71    +0.53

# %% [markdown]
# ## 2. 같은 표 × 다른 분포 = 다른 결론
#
# A 조직은 나빠지는 유형(사실조회+단일요약)에 질문의 86%가 몰려 있고,
# B 조직은 좋아지는 유형(다중홉+비교+전역집계)에 65%가 몰려 있다.

# %%
MIXES = {
    "A 조직 (사실 조회 위주)": {"사실조회": 0.62, "단일요약": 0.24, "다중홉": 0.09, "비교": 0.03, "전역집계": 0.02},
    "B 조직 (분석 위주)":      {"사실조회": 0.22, "단일요약": 0.13, "다중홉": 0.28, "비교": 0.19, "전역집계": 0.18},
}

THRESHOLD = 0.03  # 이보다 커야 "붙일 값 있음" (오차 범위 + 도입 비용 감안)


def weighted(mix, method):
    return sum(mix[k] * ACC[method][k] for k in mix)


for name, mix in MIXES.items():
    v, g = weighted(mix, "벡터만"), weighted(mix, "그래프 붙임")
    verdict = "붙일 값 있음" if g - v > THRESHOLD else "붙이지 마라"
    print(f"{name:<22} 벡터만 {v:.3f} → 그래프 {g:.3f}  (차이 {g - v:+.3f})  {verdict}")

# 출력:
# A 조직 (사실 조회 위주)      벡터만 0.833 → 그래프 0.862  (차이 +0.029)  붙이지 마라
# B 조직 (분석 위주)           벡터만 0.553 → 그래프 0.793  (차이 +0.240)  붙일 값 있음

# %% [markdown]
# 재현 완료: **A는 +0.029 (오차 범위), B는 +0.240 (명확)**.
# 장 도입부의 "0.833에서 0.862, 3% 올랐다"가 바로 A 조직 숫자다.
#
# ## 3. 분포를 연속적으로 바꾸면 결론이 어디서 뒤집히나
#
# A와 B 사이를 선형 보간한다:
#
# $$\text{mix}(t) = (1-t)\,\text{mix}_A + t\,\text{mix}_B, \qquad t \in [0, 1]$$
#
# 가중 평균이 분포에 대해 선형이므로 차이도 $t$에 대해 선형이다:
# $\Delta(t) = (1-t)(+0.029) + t(+0.240)$.

# %%
def lerp_mix(t):
    a, b = MIXES["A 조직 (사실 조회 위주)"], MIXES["B 조직 (분석 위주)"]
    return {k: (1 - t) * a[k] + t * b[k] for k in KINDS}


N = 200
ts = [i / N for i in range(N + 1)]
diffs = [weighted(lerp_mix(t), "그래프 붙임") - weighted(lerp_mix(t), "벡터만") for t in ts]

d_a, d_b = diffs[0], diffs[-1]
t_flip = (THRESHOLD - d_a) / (d_b - d_a)  # Δ(t) = 임계값이 되는 지점
mix_flip = lerp_mix(t_flip)
analytic_share = sum(mix_flip[k] for k in ("다중홉", "비교", "전역집계"))

print(f"Δ(0) = {d_a:+.3f} (A 조직),  Δ(1) = {d_b:+.3f} (B 조직)")
print(f"판정이 뒤집히는 지점: t* = {t_flip:.4f}")
print(f"그 지점의 분석형(다중홉+비교+전역집계) 비율: {analytic_share:.3f}")
print(f"A 조직의 분석형 비율: {sum(MIXES['A 조직 (사실 조회 위주)'][k] for k in ('다중홉', '비교', '전역집계')):.2f}")

# 출력:
# Δ(0) = +0.029 (A 조직),  Δ(1) = +0.240 (B 조직)
# 판정이 뒤집히는 지점: t* = 0.0028
# 그 지점의 분석형(다중홉+비교+전역집계) 비율: 0.141
# A 조직의 분석형 비율: 0.14

# %% [markdown]
# $t^* \approx 0.003$ — A 조직은 판정 경계 **바로 아래**에 서 있다.
# 분석형 질문 비율이 14%에서 조금만 늘어도 "붙일 값 있음"으로 넘어간다.
# 그래서 평균 하나(+0.029냐 +0.240이냐)만 볼 게 아니라,
# 질문 로그를 세서 자기 분포가 이 직선의 어디에 있는지를 확인해야 한다.

# %%
COL_V, COL_G = "#4269d0", "#efb118"

fig = make_subplots(
    rows=1, cols=2, column_widths=[0.42, 0.58],
    subplot_titles=("유형별 정답률 (같은 표)", "분포 보간 t에 따른 차이 Δ(t) = 그래프 − 벡터"),
)

fig.add_trace(go.Bar(name="벡터만", x=KINDS, y=[ACC["벡터만"][k] for k in KINDS],
                     marker_color=COL_V), row=1, col=1)
fig.add_trace(go.Bar(name="그래프 붙임", x=KINDS, y=[ACC["그래프 붙임"][k] for k in KINDS],
                     marker_color=COL_G), row=1, col=1)

fig.add_trace(go.Scatter(x=ts, y=diffs, mode="lines", name="Δ(t)",
                         line=dict(color="#3ca951", width=3), showlegend=False), row=1, col=2)
fig.add_hline(y=THRESHOLD, line_dash="dash", line_color="#9498a0", row=1, col=2,
              annotation_text="판정 임계 0.03", annotation_position="bottom right")
fig.add_trace(go.Scatter(x=[0, 1], y=[d_a, d_b], mode="markers+text",
                         text=[f"A 조직 {d_a:+.3f}", f"B 조직 {d_b:+.3f}"],
                         textposition=["top right", "bottom left"],
                         marker=dict(size=11, color=["#ff725c", "#3ca951"]),
                         showlegend=False), row=1, col=2)
fig.add_trace(go.Scatter(x=[t_flip], y=[THRESHOLD], mode="markers+text",
                         text=[f"뒤집힘 t*={t_flip:.3f} — A는 경계 바로 아래"],
                         textposition=["bottom right"],
                         marker=dict(size=10, symbol="x", color="#111111"),
                         showlegend=False), row=1, col=2)

fig.update_yaxes(title_text="정답률", range=[0, 1], row=1, col=1)
fig.update_xaxes(title_text="t (0=A 분포, 1=B 분포)", row=1, col=2)
fig.update_yaxes(title_text="가중 평균 차이 Δ", row=1, col=2)
fig.update_layout(
    title="같은 성능표에 다른 질문 분포를 곱하면 결론이 갈린다",
    barmode="group", width=1100, height=500, template="plotly_white",
    legend=dict(orientation="h", x=0.0, y=-0.22),
    margin=dict(b=90),
)

_show(fig)
fig.write_image(os.path.join(HERE, "expy.png"), scale=2)
print("expy.png 저장 완료")

# 출력:
# expy.png 저장 완료
