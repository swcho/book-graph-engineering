# %% [markdown]
# # TransE 를 직접 학습시켜 보기
#
# **카드 질문**: 지식 그래프 임베딩의 대표 1차 출처는 무엇인가?
# **답**: TransE 논문 — *Translating Embeddings for Modeling Multi-relational Data*, NIPS 2013.
#
# 이 스크립트는 출처를 외우는 대신 **그 논문이 실제로 무엇을 하는 모델인지**를 코드로 만든다.
#
# TransE 의 주장은 한 줄이다.
#
# $$\mathbf{h} + \mathbf{r} \approx \mathbf{t}$$
#
# 관계를 «행렬»이나 «신경망»이 아니라 **좌표계 위의 평행이동 벡터**로 본다.
# 그래서 `(한국, 수도, 서울)` 이 참이면 `서울 - 한국` 이 곧 관계 `수도` 의 벡터가 된다.
#
# 필요 패키지: numpy, plotly, kaleido  (`pip install numpy plotly kaleido`)

# %%
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

SEED = 42


def _show(fig):
    try:
        from IPython import get_ipython
        if get_ipython() is not None:  # VSCode 셀/Jupyter에서만 렌더링
            fig.show()
    except ImportError:
        pass


# dataviz 검증 통과 팔레트 (light surface #fcfcfb, all-pairs)
C_BLUE, C_ORANGE, C_AQUA = "#2a78d6", "#eb6834", "#1baf7a"
C_VIOLET, C_RED = "#4a3aa7", "#e34948"
INK, INK2, SURFACE = "#0b0b0b", "#52514e", "#fcfcfb"

print("numpy", np.__version__)
# 출력: numpy 2.0.2

# %% [markdown]
# ## 1. 아주 작은 지식 그래프
#
# 트리플 8개, 엔티티 12개, 관계 2개. 손으로 따라갈 수 있는 크기다.
#
# 이 그래프는 일부러 **1대1 관계만** 넣었다. TransE 가 가장 잘 도는 조건이다.
# 3절에서 이 조건을 깨면 무슨 일이 나는지 본다.

# %%
KG = [
    ("한국", "수도", "서울"),
    ("일본", "수도", "도쿄"),
    ("프랑스", "수도", "파리"),
    ("이탈리아", "수도", "로마"),
    ("한국", "공용어", "한국어"),
    ("일본", "공용어", "일본어"),
    ("프랑스", "공용어", "프랑스어"),
    ("이탈리아", "공용어", "이탈리아어"),
]

TYPE_OF = {
    "한국": "국가", "일본": "국가", "프랑스": "국가", "이탈리아": "국가",
    "서울": "도시", "도쿄": "도시", "파리": "도시", "로마": "도시",
    "한국어": "언어", "일본어": "언어", "프랑스어": "언어", "이탈리아어": "언어",
}

ENTS = sorted({h for h, _, _ in KG} | {t for _, _, t in KG})
RELS = sorted({r for _, r, _ in KG})
print(f"엔티티 {len(ENTS)}개: {ENTS}")
print(f"관계 {len(RELS)}개: {RELS}")
print(f"트리플 {len(KG)}개")
# 출력: 엔티티 12개: ['도쿄', '로마', '서울', '이탈리아', '이탈리아어', '일본', '일본어', '파리', '프랑스', '프랑스어', '한국', '한국어']
# 출력: 관계 2개: ['공용어', '수도']
# 출력: 트리플 8개

# %% [markdown]
# ## 2. 점수 함수 · 손실 · 네거티브 샘플링
#
# ### 점수(비유사도) 함수
#
# $$d(h, r, t) = \lVert \mathbf{h} + \mathbf{r} - \mathbf{t} \rVert_{1\;\text{or}\;2}$$
#
# 값이 **작을수록** 참에 가깝다. 논문은 $L_1$ 과 $L_2$ 중 검증셋으로 고른다.
#
# ### 마진 랭킹 손실 (margin ranking loss)
#
# $$\mathcal{L} = \sum_{(h,r,t)\in S}\ \sum_{(h',r,t')\in S'_{(h,r,t)}}
# \big[\, \gamma + d(h,r,t) - d(h',r,t') \,\big]_+$$
#
# $[x]_+ = \max(0, x)$. 참 트리플이 거짓 트리플보다 **적어도 마진 $\gamma$ 만큼**
# 가까우면 그 항은 0이 된다. 절대적인 거리를 맞추는 게 아니라 **순위**만 맞춘다.
# 링크 예측이 랭킹 문제라서 그렇다.
#
# ### 네거티브 샘플링
#
# 지식 그래프에는 «참» 트리플만 있다. 거짓 예시가 없으면 모든 벡터를 0으로 만드는 게 최적이다.
# 그래서 참 트리플의 머리 **또는** 꼬리 하나를 무작위 엔티티로 갈아끼워 거짓을 만든다.
#
# $$S'_{(h,r,t)} = \{(h',r,t)\ |\ h' \in E\} \cup \{(h,r,t')\ |\ t' \in E\}$$
#
# 관계는 갈아끼우지 않는다.
#
# ### 노름 제약
#
# 손실은 «참을 가깝게» 하는 대신 «거짓을 멀게» 해서도 줄어든다.
# 제약이 없으면 모델이 엔티티 벡터의 크기만 무한히 키워서 손실을 줄인다(꼼수).
# 그래서 논문은 매 배치마다 엔티티 임베딩을 $\lVert \mathbf{e} \rVert_2 = 1$ 로 되돌린다.
# 관계 벡터에는 제약을 걸지 않는다.

# %%
def train_transe(triples, dim=2, margin=1.0, lr=0.05, epochs=3000,
                 seed=SEED, p=2, track=None):
    """TransE. 논문 Algorithm 1 을 전배치 경사하강으로 줄인 것."""
    rng = np.random.default_rng(seed)
    ents = sorted({h for h, _, _ in triples} | {t for _, _, t in triples})
    rels = sorted({r for _, r, _ in triples})
    ei = {e: i for i, e in enumerate(ents)}
    ri = {r: i for i, r in enumerate(rels)}

    # 초기화: Uniform(-6/sqrt(k), 6/sqrt(k)) 뒤 정규화 (논문 Algorithm 1)
    b = 6.0 / np.sqrt(dim)
    E = rng.uniform(-b, b, (len(ents), dim))
    R = rng.uniform(-b, b, (len(rels), dim))
    R /= np.linalg.norm(R, axis=1, keepdims=True)

    idx = np.array([[ei[h], ri[r], ei[t]] for h, r, t in triples])
    known = {tuple(row) for row in idx.tolist()}
    E0 = None
    hist = {"loss": [], "d_pos": [], "d_neg": [], "extra": []}

    def dist(a):
        return np.linalg.norm(a, ord=p)

    for ep in range(epochs + 1):
        # 노름 제약: 엔티티만 단위 구 «안»으로 되돌린다.
        # 논문은 ‖e‖=1 로 붙이지만, k=2 에서 그러면 모든 점이 원 위에 갇혀
        # 평행이동 구조를 그릴 자리가 없다. 여기서는 흔히 쓰는 ‖e‖<=1 변형을 쓴다.
        E /= np.maximum(np.linalg.norm(E, axis=1, keepdims=True), 1.0)
        if ep == 0:
            E0 = E.copy()

        # 네거티브 샘플링: 머리 또는 꼬리 하나를 바꾼다
        neg = idx.copy()
        for k in range(len(neg)):
            for _ in range(20):
                cand = neg[k].copy()
                side = 0 if rng.random() < 0.5 else 2
                cand[side] = rng.integers(len(ents))
                if tuple(cand.tolist()) not in known:
                    neg[k] = cand
                    break

        gE, gR = np.zeros_like(E), np.zeros_like(R)
        loss, dp_sum, dn_sum = 0.0, 0.0, 0.0
        for (h, r, t), (hn, rn, tn) in zip(idx, neg):
            vp = E[h] + R[r] - E[t]
            vn = E[hn] + R[rn] - E[tn]
            dp, dn = dist(vp), dist(vn)
            dp_sum, dn_sum = dp_sum + dp, dn_sum + dn
            m = margin + dp - dn
            if m > 0:
                loss += m
                # d/dx ||x||_2 = x/||x|| ,  d/dx ||x||_1 = sign(x)
                up = vp / max(dp, 1e-12) if p == 2 else np.sign(vp)
                un = vn / max(dn, 1e-12) if p == 2 else np.sign(vn)
                gE[h] += up; gR[r] += up; gE[t] -= up
                gE[hn] -= un; gR[rn] -= un; gE[tn] += un

        n = len(idx)
        hist["loss"].append(loss / n)
        hist["d_pos"].append(dp_sum / n)
        hist["d_neg"].append(dn_sum / n)
        if track is not None:
            hist["extra"].append(track(E, R, ei, ri))

        if ep < epochs:
            E -= lr * gE
            R -= lr * gR

    return {"E": E, "R": R, "E0": E0, "ents": ents, "rels": rels,
            "ei": ei, "ri": ri, "hist": hist}


# %% [markdown]
# ## 3. 학습시켜 보기
#
# 시각화를 위해 차원 $k=2$ 로 둔다. $L_2$ 거리, 학습률 0.05, 4000 에폭.
#
# 마진은 $\gamma=0.5$ 로 둔다. 반지름 1인 원 안에 엔티티 12개를 넣어야 해서
# 좌표가 비좁기 때문이다. 고차원에서는 $\gamma=1$ 도 문제없다(6절에서 확인).

# %%
m = train_transe(KG, dim=2, margin=0.5, lr=0.05, epochs=4000)
h = m["hist"]

print(f"손실     {h['loss'][0]:.4f} → {h['loss'][-1]:.4f}")
print(f"참 거리   {h['d_pos'][0]:.4f} → {h['d_pos'][-1]:.4f}   (‖h+r-t‖, 작을수록 좋다)")
print(f"거짓 거리 {h['d_neg'][0]:.4f} → {h['d_neg'][-1]:.4f}   (클수록 좋다)")
print(f"간격     {h['d_neg'][-1] - h['d_pos'][-1]:.4f}   (마진 0.5 이상이면 손실 0)")
# 출력: 손실     0.3948 → 0.0000
# 출력: 참 거리   1.6287 → 0.1544   (‖h+r-t‖, 작을수록 좋다)
# 출력: 거짓 거리 1.8561 → 1.5794   (클수록 좋다)
# 출력: 간격     1.4249   (마진 0.5 이상이면 손실 0)

# %% [markdown]
# ### h + r ≈ t 가 정말 생겼나
#
# 트리플마다 $\lVert \mathbf{h}+\mathbf{r}-\mathbf{t} \rVert$ 를 학습 전후로 찍어 본다.

# %%
E, R, ei, ri = m["E"], m["R"], m["ei"], m["ri"]
E0 = m["E0"]


def resid(Emat, hh, rr, tt):
    return float(np.linalg.norm(Emat[ei[hh]] + R[ri[rr]] - Emat[ei[tt]]))


print(f"{'트리플':<34}{'학습 전':>9}{'학습 후':>9}")
for hh, rr, tt in KG:
    print(f"({hh}, {rr}, {tt})".ljust(34)
          + f"{resid(E0, hh, rr, tt):>9.3f}{resid(E, hh, rr, tt):>9.3f}")
# 출력: 트리플                                    학습 전     학습 후
# 출력: (한국, 수도, 서울)                          2.745    0.221
# 출력: (일본, 수도, 도쿄)                          0.967    0.194
# 출력: (프랑스, 수도, 파리)                         1.072    0.116
# 출력: (이탈리아, 수도, 로마)                        0.479    0.180
# 출력: (한국, 공용어, 한국어)                        2.229    0.051
# 출력: (일본, 공용어, 일본어)                        0.809    0.150
# 출력: (프랑스, 공용어, 프랑스어)                      2.073    0.161
# 출력: (이탈리아, 공용어, 이탈리아어)                    2.885    0.164

# %% [markdown]
# ### 관계 벡터는 하나뿐이다
#
# 학습된 `수도` 벡터 하나가 4개 나라 모두를 자기 수도로 옮긴다.
# 나라마다 다른 규칙을 배운 게 아니다. **평행이동 한 번**이다.

# %%
r_cap = R[ri["수도"]]
print(f"학습된 r_수도 = {np.round(r_cap, 3)}   ‖r‖={np.linalg.norm(r_cap):.3f}\n")
for c, city in [("한국", "서울"), ("일본", "도쿄"), ("프랑스", "파리"), ("이탈리아", "로마")]:
    diff = E[ei[city]] - E[ei[c]]
    print(f"  {city} - {c} = {np.round(diff, 3)}   r_수도와의 차 {np.linalg.norm(diff - r_cap):.3f}")
# 출력: 학습된 r_수도 = [ 0.648 -0.431]   ‖r‖=0.779
# 출력:
# 출력:   서울 - 한국 = [ 0.565 -0.227]   r_수도와의 차 0.221
# 출력:   도쿄 - 일본 = [ 0.621 -0.239]   r_수도와의 차 0.194
# 출력:   파리 - 프랑스 = [ 0.569 -0.347]   r_수도와의 차 0.116
# 출력:   로마 - 이탈리아 = [ 0.626 -0.253]   r_수도와의 차 0.180

# %% [markdown]
# ## 4. 링크 예측 — 논문이 실제로 재는 것
#
# $(h, r, ?)$ 의 물음표 자리에 모든 엔티티를 넣어 보고 $d(h,r,t')$ 로 **정렬**한다.
# 정답의 순위가 곧 지표다. TransE 논문이 쓰는 지표:
#
# - **Mean rank**: 정답 순위의 평균 (낮을수록 좋다)
# - **Hits@10**: 정답이 상위 10위 안에 든 비율
# - **filtered 설정**: 후보 중 «학습셋에 이미 있는 다른 참 트리플»은 빼고 센다.
#   이 filtered 개념을 처음 제안한 것도 이 논문이다.

# %%
def rank_tails(hh, rr, topk=5):
    d = np.linalg.norm(E[ei[hh]] + R[ri[rr]] - E, ord=2, axis=1)
    order = np.argsort(d)
    return [(m["ents"][i], float(d[i])) for i in order[:topk]]


for q in [("프랑스", "수도"), ("일본", "공용어")]:
    print(f"({q[0]}, {q[1]}, ?)")
    for name, d in rank_tails(*q):
        print(f"    {d:.3f}  {name}")
# 출력: (프랑스, 수도, ?)
# 출력:     0.116  파리
# 출력:     0.469  프랑스어
# 출력:     0.707  일본어
# 출력:     0.747  도쿄
# 출력:     0.779  프랑스
# 출력: (일본, 공용어, ?)
# 출력:     0.150  일본어
# 출력:     0.439  프랑스어
# 출력:     0.647  파리
# 출력:     0.713  서울
# 출력:     0.730  도쿄

# %%
ranks = []
for hh, rr, tt in KG:
    d = np.linalg.norm(E[ei[hh]] + R[ri[rr]] - E, ord=2, axis=1)
    ranks.append(int((d < d[ei[tt]]).sum()) + 1)
ranks = np.array(ranks)
print(f"순위: {ranks.tolist()}")
print(f"Mean rank {ranks.mean():.2f} / Hits@1 {(ranks == 1).mean():.0%} / Hits@3 {(ranks <= 3).mean():.0%}")
# 출력: 순위: [1, 1, 1, 1, 1, 1, 1, 1]
# 출력: Mean rank 1.00 / Hits@1 100% / Hits@3 100%

# %% [markdown]
# ### 차원과 마진의 관계
#
# $k=2$ 는 그림을 그리려고 고른 값이다. 좌표가 비좁아 마진을 못 키운다.
# 차원을 올리면 같은 $\gamma=1$ 에서도 여유 있게 수렴한다.
# 실제 TransE 논문은 $k=20$ 또는 $50$ 을 쓴다.

# %%
print(f"{'k':>4}{'γ':>6}{'최종 손실':>12}{'최대 잔차':>12}{'Hits@1':>9}")
for dim, mg in [(2, 1.0), (2, 0.5), (10, 1.0), (20, 1.0), (50, 1.0)]:
    mm = train_transe(KG, dim=dim, margin=mg, lr=0.05, epochs=4000)
    Em, Rm, eim, rim = mm["E"], mm["R"], mm["ei"], mm["ri"]
    res = [np.linalg.norm(Em[eim[a]] + Rm[rim[b_]] - Em[eim[c]]) for a, b_, c in KG]
    rk = []
    for a, b_, c in KG:
        dd = np.linalg.norm(Em[eim[a]] + Rm[rim[b_]] - Em, axis=1)
        rk.append((dd < dd[eim[c]]).sum() + 1)
    print(f"{dim:>4}{mg:>6.1f}{mm['hist']['loss'][-1]:>12.4f}"
          f"{max(res):>12.3f}{np.mean(np.array(rk) == 1):>9.0%}")
# 출력:    k     γ       최종 손실       최대 잔차   Hits@1
# 출력:    2   1.0      0.1441       0.373      50%
# 출력:    2   0.5      0.0000       0.221     100%
# 출력:   10   1.0      0.0000       0.132     100%
# 출력:   20   1.0      0.0000       0.109     100%
# 출력:   50   1.0      0.0000       0.121     100%

# %% [markdown]
# ## 5. 시각화 — 좌표 위에서 관계가 «화살표»가 되는 과정
#
# 왼쪽 위는 무작위 초기값, 오른쪽 위는 3000 에폭 뒤.
# 학습이 끝나면 `수도` 화살표 4개가 서로 **평행하고 길이도 같아진다**.
# 그게 곧 «관계 하나 = 평행이동 벡터 하나» 라는 뜻이다.

# %%
TYPE_COLOR = {"국가": C_BLUE, "도시": C_ORANGE, "언어": C_AQUA}

fig = make_subplots(
    rows=2, cols=2,
    subplot_titles=("학습 전 — 무작위 배치", "학습 후 — h + r ≈ t",
                    "마진 랭킹 손실 (이동평균 41에폭)",
                    "참/거짓 트리플의 거리 (이동평균 41에폭)"),
    vertical_spacing=0.14, horizontal_spacing=0.10,
)


def draw_space(Emat, row, col, axref, ayref, legend):
    for typ, color in TYPE_COLOR.items():
        pts = [e for e in m["ents"] if TYPE_OF[e] == typ]
        fig.add_trace(go.Scatter(
            x=[Emat[ei[e]][0] for e in pts], y=[Emat[ei[e]][1] for e in pts],
            mode="markers+text", text=pts, textposition="top center",
            textfont=dict(size=9, color=INK),
            marker=dict(size=9, color=color, line=dict(width=2, color=SURFACE)),
            name=typ, legendgroup=typ, showlegend=legend, hoverinfo="text",
        ), row=row, col=col)
    for hh, rr, tt in KG:
        a, b_ = Emat[ei[hh]], Emat[ei[tt]]
        # 화살표는 중립 회색. 색은 «엔티티 종류»에만 쓴다.
        # 어느 관계인지는 화살표가 가리키는 점의 색(도시=수도, 언어=공용어)이 말해 준다.
        fig.add_annotation(
            x=b_[0], y=b_[1], ax=a[0], ay=a[1], xref=axref, yref=ayref,
            axref=axref, ayref=ayref, showarrow=True, arrowhead=2,
            arrowsize=1.1, arrowwidth=1.4, opacity=0.6, arrowcolor="#9a9a94",
        )


draw_space(E0, 1, 1, "x", "y", True)
draw_space(E, 1, 2, "x2", "y2", False)

def smooth(v, w=41):
    """네거티브를 매 에폭 새로 뽑아 곡선이 튄다. 이동평균으로 추세만 남긴다."""
    return np.convolve(np.asarray(v), np.ones(w) / w, mode="valid")


ep = np.arange(len(smooth(h["loss"])))
fig.add_trace(go.Scatter(x=ep, y=smooth(h["loss"]), mode="lines", name="손실",
                         line=dict(color=C_VIOLET, width=2), showlegend=False),
              row=2, col=1)
fig.add_trace(go.Scatter(x=ep, y=smooth(h["d_pos"]), mode="lines", name="참 ‖h+r-t‖",
                         line=dict(color=C_VIOLET, width=2)), row=2, col=2)
fig.add_trace(go.Scatter(x=ep, y=smooth(h["d_neg"]), mode="lines", name="거짓 ‖h'+r-t'‖",
                         line=dict(color=C_RED, width=2, dash="dash")),
              row=2, col=2)
fig.add_trace(go.Scatter(x=ep, y=smooth(np.array(h["d_neg"]) - np.array(h["d_pos"])),
                         mode="lines", name="간격 (거짓-참)",
                         line=dict(color=INK2, width=1.6, dash="dot")),
              row=2, col=2)
fig.add_hline(y=0.5, line=dict(color="#9a9a94", width=1),
              annotation_text="마진 γ=0.5 — 간격이 이 선을 넘으면 손실 0",
              annotation_position="bottom right",
              annotation_font=dict(size=10, color=INK2), row=2, col=2)

fig.update_layout(
    title=dict(text="TransE — 관계를 평행이동 벡터로 배우는 과정 (k=2, γ=0.5, L2)",
               font=dict(size=17, color=INK)),
    template="plotly_white", paper_bgcolor=SURFACE, plot_bgcolor=SURFACE,
    font=dict(color=INK2, size=11), width=1080, height=800,
    legend=dict(orientation="h", y=1.10, x=0.5, xanchor="center",
                bgcolor="rgba(0,0,0,0)"),
    margin=dict(l=60, r=30, t=140, b=55),
)
for r_, c_ in [(1, 1), (1, 2)]:
    fig.update_xaxes(range=[-1.45, 1.45], zeroline=False, showgrid=True,
                     gridcolor="#eeeeec", row=r_, col=c_)
    fig.update_yaxes(range=[-1.45, 1.45], zeroline=False, showgrid=True,
                     gridcolor="#eeeeec", scaleanchor=f"x{'' if c_ == 1 else '2'}",
                     row=r_, col=c_)
fig.update_xaxes(title_text="에폭", row=2, col=1)
fig.update_xaxes(title_text="에폭", row=2, col=2)
fig.update_yaxes(title_text="트리플당 평균 손실", row=2, col=1)
fig.update_yaxes(title_text="평균 거리", row=2, col=2)

fig.write_image("expy.png", scale=2)
_show(fig)
print("expy.png 저장 완료")
# 출력: expy.png 저장 완료

# %% [markdown]
# ## 6. 한계 (1) — 1대다 · 다대1 · 다대다 관계
#
# TransE 의 가정이 곧 한계다. $\mathbf{h}+\mathbf{r} \approx \mathbf{t}$ 는
# 머리와 관계가 정해지면 꼬리가 **한 점으로 정해진다**는 뜻이다.
#
# 1대다 관계 `(한국, 도시, 서울)`, `(한국, 도시, 부산)`, `(한국, 도시, 인천)` 이 함께 참이면
#
# $$\mathbf{서울} \approx \mathbf{한국}+\mathbf{r} \approx \mathbf{부산} \approx \mathbf{인천}$$
#
# 서울·부산·인천이 **같은 자리로 뭉개진다**. 다대1은 머리 쪽이, 다대다는 양쪽이 뭉개진다.
# 실제 지식 그래프에서 1대1 관계는 소수라서, 이게 TransE 성능 상한의 주된 원인이 된다.
#
# 차원을 늘리면 해결될까? 아래는 $k=20$ 으로 돌린다.

# %%
ONE_TO_N = [
    ("한국", "도시", "서울"), ("한국", "도시", "부산"), ("한국", "도시", "인천"),
    ("일본", "도시", "도쿄"), ("일본", "도시", "오사카"), ("일본", "도시", "교토"),
    ("한국", "수도", "서울"), ("일본", "수도", "도쿄"),
]
m2 = train_transe(ONE_TO_N, dim=20, margin=1.0, lr=0.05, epochs=3000)
E2, ei2 = m2["E"], m2["ei"]


def dist2(a, b_):
    return float(np.linalg.norm(E2[ei2[a]] - E2[ei2[b_]]))


print("같은 1대다 묶음 안의 꼬리끼리 (붕괴하면 0에 가까워진다)")
for a, b_ in [("부산", "인천"), ("서울", "부산"), ("서울", "인천"),
              ("오사카", "교토"), ("도쿄", "오사카"), ("도쿄", "교토")]:
    print(f"  ‖{a} - {b_}‖ = {dist2(a, b_):.3f}")
print("\n다른 묶음 사이 (붕괴 안 함 — 비교 기준)")
for a, b_ in [("서울", "도쿄"), ("부산", "오사카"), ("한국", "일본")]:
    print(f"  ‖{a} - {b_}‖ = {dist2(a, b_):.3f}")
print("\n부산·인천은 «한국의 도시»라는 신호밖에 없어 사실상 같은 점이 되었다.")
print("서울만 덜 무너진 건 (한국, 수도, 서울) 이라는 다른 관계가 하나 더 붙어 있어서다.")
print("실제 지식 그래프에서 1대1 관계는 소수다. 그래서 이 붕괴가 성능 상한이 된다.")
# 출력: 같은 1대다 묶음 안의 꼬리끼리 (붕괴하면 0에 가까워진다)
# 출력:   ‖부산 - 인천‖ = 0.038
# 출력:   ‖서울 - 부산‖ = 0.707
# 출력:   ‖서울 - 인천‖ = 0.733
# 출력:   ‖오사카 - 교토‖ = 0.057
# 출력:   ‖도쿄 - 오사카‖ = 0.757
# 출력:   ‖도쿄 - 교토‖ = 0.711
# 출력:
# 출력: 다른 묶음 사이 (붕괴 안 함 — 비교 기준)
# 출력:   ‖서울 - 도쿄‖ = 1.471
# 출력:   ‖부산 - 오사카‖ = 1.477
# 출력:   ‖한국 - 일본‖ = 1.523
# 출력:
# 출력: 부산·인천은 «한국의 도시»라는 신호밖에 없어 사실상 같은 점이 되었다.
# 출력: 서울만 덜 무너진 건 (한국, 수도, 서울) 이라는 다른 관계가 하나 더 붙어 있어서다.
# 출력: 실제 지식 그래프에서 1대1 관계는 소수다. 그래서 이 붕괴가 성능 상한이 된다.

# %% [markdown]
# ## 7. 한계 (2) — 대칭 관계를 표현할 수 없다
#
# `협력` 처럼 대칭인 관계는 $(a, r, b)$ 와 $(b, r, a)$ 가 **둘 다 참**이다. 그러면
#
# $$\mathbf{a}+\mathbf{r}=\mathbf{b}, \quad \mathbf{b}+\mathbf{r}=\mathbf{a}
# \;\Longrightarrow\; 2\mathbf{r} = \mathbf{0} \;\Longrightarrow\;
# \mathbf{r}=\mathbf{0},\ \mathbf{a}=\mathbf{b}$$
#
# 관계 벡터가 0으로 무너지고, 짝이 된 두 엔티티가 같은 점이 된다.
# 재귀 관계 $(a, r, a)$ 도 같은 이유로 $\mathbf{r}=\mathbf{0}$ 을 강요한다.
#
# 반대로 TransE 가 **잘하는** 것도 있다. 역관계($\mathbf{r}_{inv}=-\mathbf{r}$)와
# 합성($\mathbf{r}_1+\mathbf{r}_2=\mathbf{r}_3$)은 평행이동으로 자연스럽게 표현된다.
#
# (아래에서 $\lVert r_{협력}\rVert$ 가 정확히 0까지는 안 간다. 매 에폭 새로 뽑는
# 네거티브가 계속 잡아당기기 때문이다. 비대칭 관계와 비교하면 차이가 분명하다.)

# %%
SYM = [
    ("가온테크", "협력", "나루소프트"), ("나루소프트", "협력", "가온테크"),
    ("다올물산", "협력", "라온에너지"), ("라온에너지", "협력", "다올물산"),
    ("가온테크", "자회사", "가온랩"), ("다올물산", "자회사", "다올랩"),
]


def watch(Emat, Rmat, ei_, ri_):
    return (float(np.linalg.norm(Rmat[ri_["협력"]])),
            float(np.linalg.norm(Rmat[ri_["자회사"]])),
            float(np.linalg.norm(Emat[ei_["가온테크"]] - Emat[ei_["나루소프트"]])))


m3 = train_transe(SYM, dim=20, margin=1.0, lr=0.05, epochs=3000, track=watch)
tr = m3["hist"]["extra"]
print(f"{'에폭':>6}{'‖r_협력‖':>12}{'‖r_자회사‖':>13}{'‖가온-나루‖':>13}")
for e in [0, 100, 500, 1500, 3000]:
    a, b_, c = tr[e]
    print(f"{e:>6}{a:>12.4f}{b_:>13.4f}{c:>13.4f}")
# 출력:     에폭      ‖r_협력‖      ‖r_자회사‖      ‖가온-나루‖
# 출력:      0      1.0000       1.0000       1.6236
# 출력:    100      0.2159       1.3979       0.0989
# 출력:    500      0.2939       1.4448       0.2551
# 출력:   1500      0.2661       1.4411       0.1785
# 출력:   3000      0.2887       1.4529       0.1211

E3, ei3 = m3["E"], m3["ei"]
pairs = [(a, b_) for i, a in enumerate(m3["ents"]) for b_ in m3["ents"][i + 1:]]
base = np.mean([np.linalg.norm(E3[ei3[a]] - E3[ei3[b_]]) for a, b_ in pairs])
print(f"\n(비교 기준) 전체 엔티티 쌍의 평균 거리 = {base:.3f}")
print("대칭 관계 r_협력 은 거의 0 벡터로 무너졌고, 짝지어진 두 회사도 사실상 같은 점이 되었다.")
print("비대칭 관계 r_자회사 는 멀쩡히 살아 있다. 문제는 «대칭»이라는 성질 자체다.")
# 출력:
# 출력: (비교 기준) 전체 엔티티 쌍의 평균 거리 = 1.435
# 출력: 대칭 관계 r_협력 은 거의 0 벡터로 무너졌고, 짝지어진 두 회사도 사실상 같은 점이 되었다.
# 출력: 비대칭 관계 r_자회사 는 멀쩡히 살아 있다. 문제는 «대칭»이라는 성질 자체다.

# %% [markdown]
# ## 8. 정리
#
# | 항목 | TransE |
# |---|---|
# | 출처 | Bordes et al., *Translating Embeddings for Modeling Multi-relational Data*, **NIPS 2013** |
# | 점수 함수 | $d(h,r,t)=\lVert \mathbf{h}+\mathbf{r}-\mathbf{t}\rVert_{1/2}$ |
# | 손실 | 마진 랭킹 손실 $[\gamma + d_{pos} - d_{neg}]_+$ |
# | 학습 신호 | 머리/꼬리 치환 네거티브 샘플링 + 엔티티 노름 제약 $\lVert e\rVert_2=1$ |
# | 파라미터 수 | $O((|E|+|R|)\cdot k)$ — 관계당 벡터 하나뿐이라 아주 가볍다 |
# | 잘하는 것 | 반대칭, 역관계, 합성 |
# | 못하는 것 | 1대다·다대1·다대다, 대칭, 재귀 |
# | 구조적 한계 | 전이적(transductive) — 학습에 없던 엔티티는 좌표가 없다 |
#
# 6장 본문의 「구조를 값에 녹인다」가 여기서 그대로 보인다.
# 좌표 12개와 벡터 2개로 트리플 8개를 전부 복원할 수 있게 되었지만,
# 그 좌표만 봐서는 «왜» 그 자리인지 되짚을 수 없다. 그게 이 장이 말하는 거래다.
