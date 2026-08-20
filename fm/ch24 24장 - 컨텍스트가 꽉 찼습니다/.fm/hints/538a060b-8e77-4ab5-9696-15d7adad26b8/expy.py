# %% [markdown]
# # 기억 계층의 해결 비율 — 55 / 20 / 15 / 8 / 2
#
# 24.5절 `ex5_memory_tiers.py`의 계층 표를 그대로 놓고,
# **캐스케이드 조회**(위 계층부터 내려가기)와 **전부 한 번에 넣기**의
# 기대 지연·기대 토큰을 계산한다.
#
# | 계층 | 지연(ms) | 건당 토큰 | 해결 비율 $p_i$ |
# |---|---|---|---|
# | 작업 기억 | 0.0 | 0 | 0.55 |
# | 최근 요약 | 1.5 | 350 | 0.20 |
# | 에피소드 기억 | 18.0 | 900 | 0.15 |
# | 지식 그래프 | 42.0 | 600 | 0.08 |
# | 없음(모름) | 0.0 | 0 | 0.02 |
#
# $\sum_i p_i = 1$ 이므로 이 다섯 값은 **확률 분포**다.
# "모름 2%"까지 포함해야 합이 1이 된다는 점이 핵심이다.
#
# 필요 패키지: plotly, kaleido (없으면 표 계산까지는 그대로 동작)

# %%
# 필요 패키지: plotly, kaleido


def _show(fig):
    try:
        from IPython import get_ipython

        if get_ipython() is not None:  # VSCode 셀/Jupyter에서만 렌더링
            fig.show()
    except ImportError:
        pass


# 이름, 지연(ms), 건당 토큰, 이 계층에서 답이 나올 확률
TIERS = [
    ("작업 기억", 0.0, 0, 0.55),
    ("최근 요약", 1.5, 350, 0.20),
    ("에피소드 기억", 18.0, 900, 0.15),
    ("지식 그래프", 42.0, 600, 0.08),
    ("없음(모름)", 0.0, 0, 0.02),
]

N_Q = 100
PRICE_IN = 3.0 / 1_000_000  # 입력 토큰 단가(USD)
KRW = 1_380

print("해결 비율 합계:", round(sum(t[3] for t in TIERS), 10))
# 출력: 해결 비율 합계: 1.0

# %% [markdown]
# ## 1. 도달 비율과 해결 비율은 다르다
#
# 카드가 묻는 55/20/15/8/2는 **해결 비율** $p_i$ 다.
# 여기서 파생되는 **도달 비율**(그 계층까지 내려온 질문 비율)은 살아남은 꼬리다.
#
# $$r_1 = 1,\qquad r_{i+1} = r_i - p_i$$
#
# 즉 $r_i = 1 - \sum_{j<i} p_j$ 이고, 값은
# $1.00 \to 0.45 \to 0.25 \to 0.10 \to 0.02$ 로 줄어든다.
#
# 비싼 계층일수록 도달 비율이 작다는 것이 계층 설계가 버는 지점이다.

# %%
rows = []
remaining = 1.0
for name, lat, tok, p in TIERS:
    rows.append((name, remaining, p, lat, tok))
    remaining -= p

print(f"{'계층':<14}{'도달 r_i':>10}{'해결 p_i':>10}{'지연ms':>8}{'토큰':>7}")
print("-" * 49)
for name, r, p, lat, tok in rows:
    print(f"{name:<14}{r:>10.2f}{p:>10.2f}{lat:>8.1f}{tok:>7}")
# 출력:
# 계층              도달 r_i    해결 p_i   지연ms     토큰
# -------------------------------------------------
# 작업 기억            1.00      0.55     0.0      0
# 최근 요약            0.45      0.20     1.5    350
# 에피소드 기억          0.25      0.15    18.0    900
# 지식 그래프           0.10      0.08    42.0    600
# 없음(모름)           0.02      0.02     0.0      0

# %% [markdown]
# ## 2. 캐스케이드의 기대 비용
#
# 질문 하나당 기대 지연과 기대 토큰은 **도달 비율로 가중한 합**이다.
#
# $$\mathbb{E}[\text{latency}] = \sum_i r_i \cdot \ell_i,
# \qquad \mathbb{E}[\text{tokens}] = \sum_i r_i \cdot t_i$$
#
# 반면 "전부 한 번에" 방식은 도달 비율이 없다. 모든 계층을 항상 친다.
#
# $$\mathbb{E}_{\text{all}}[\cdot] = \sum_i \ell_i \quad\text{(가중치 1)}$$

# %%
def cascade(n_q=N_Q):
    """위 계층부터 차례로 찾아 내려간다."""
    ms = tok = 0.0
    remaining = 1.0
    out = []
    for name, lat, t, p in TIERS:
        reached = remaining
        ms += reached * n_q * lat
        tok += reached * n_q * t
        out.append((name, reached * n_q, p * n_q, ms, tok))
        remaining -= p
    return out, ms, tok


def all_at_once(n_q=N_Q):
    """계층을 안 나누고 전부 한 번에 컨텍스트에 넣는다."""
    return n_q * sum(t[1] for t in TIERS), n_q * sum(t[2] for t in TIERS)


detail, ms, tok = cascade()
print(f"{'계층':<14}{'내려온 질문':>12}{'여기서 해결':>12}{'누적 ms':>10}{'누적 토큰':>11}")
print("-" * 61)
for name, reached, hit, cms, ctok in detail:
    print(f"{name:<14}{reached:>12.0f}{hit:>12.0f}{cms:>10,.1f}{ctok:>11,.0f}")
# 출력:
# 계층              내려온 질문      여기서 해결     누적 ms      누적 토큰
# -------------------------------------------------------------
# 작업 기억                100          55       0.0          0
# 최근 요약                 45          20      67.5     15,750
# 에피소드 기억               25          15     517.5     38,250
# 지식 그래프                10           8     937.5     44,250
# 없음(모름)                 2           2     937.5     44,250

# %%
ams, atok = all_at_once()
print(f"{'방식':<20}{'총 지연(ms)':>13}{'총 토큰':>11}{'토큰 비용':>12}")
print("-" * 56)
print(f"{'계층별로 내려가기':<20}{ms:>13,.0f}{tok:>11,.0f}{tok * PRICE_IN * KRW:>11,.0f}원")
print(f"{'전부 한 번에 넣기':<20}{ams:>13,.0f}{atok:>11,.0f}{atok * PRICE_IN * KRW:>11,.0f}원")
print(f"\n지연 비율 {ms / ams:.1%}, 토큰 비율 {tok / atok:.1%}")
# 출력:
# 방식                     총 지연(ms)        총 토큰       토큰 비용
# --------------------------------------------------------
# 계층별로 내려가기                937     44,250        183원   (실제 937.5ms)
# 전부 한 번에 넣기               6,150    185,000        766원
#
# 지연 비율 15.2%, 토큰 비율 23.9%

# %% [markdown]
# ## 3. 55%가 하는 일 — 상위 계층 비중의 민감도
#
# 작업 기억의 해결 비율 $p_1$ 을 흔들어 보면, 아래 계층의 도달 비율이
# 통째로 밀린다. $p_1$ 이 줄어든 만큼을 아래 계층에 비례 배분해서
# 기대 토큰이 어떻게 움직이는지 본다.
#
# 절감의 대부분은 **비싼 조회를 빠르게 만드는 것이 아니라 아예 안 하는 것**에서 나온다.

# %%
def cascade_tokens(p_top):
    """작업 기억 비중을 p_top으로 바꾸고 나머지를 비례 배분했을 때의 총 토큰."""
    rest = [t[3] for t in TIERS[1:]]
    scale = (1.0 - p_top) / sum(rest)
    probs = [p_top] + [p * scale for p in rest]
    tokens = 0.0
    remaining = 1.0
    for (_, _, t, _), p in zip(TIERS, probs):
        tokens += remaining * N_Q * t
        remaining -= p
    return tokens


grid = [0.0, 0.2, 0.4, 0.55, 0.7, 0.9]
for p in grid:
    v = cascade_tokens(p)
    print(f"p1={p:.2f} → 총 토큰 {v:>8,.0f}  (전부 한 번에 대비 {v / atok:5.1%})")
# 출력:
# p1=0.00 → 총 토큰   98,333  (전부 한 번에 대비 53.2%)
# p1=0.20 → 총 토큰   78,667  (전부 한 번에 대비 42.5%)
# p1=0.40 → 총 토큰   59,000  (전부 한 번에 대비 31.9%)
# p1=0.55 → 총 토큰   44,250  (전부 한 번에 대비 23.9%)
# p1=0.70 → 총 토큰   29,500  (전부 한 번에 대비 15.9%)
# p1=0.90 → 총 토큰    9,833  (전부 한 번에 대비  5.3%)

# %% [markdown]
# ## 4. 함정 — 위 계층이 낡으면 "틀린 채로 빠르다"
#
# 위 계산은 **위 계층이 맞을 때**를 전제한다.
# 작업 기억이 낡아 있을 확률을 $s$ 라 하면, 55% 중 $0.55 \cdot s$ 는
# 잘못된 답으로 조기 종료된다. 아래 계층은 영영 호출되지 않는다.
#
# $$\text{오답률} \approx p_1 \cdot s$$
#
# 상위 계층 비중이 클수록 빠르지만, 그만큼 **갱신 비용**이 커진다.

# %%
for s in (0.0, 0.05, 0.10, 0.20):
    print(f"작업 기억 낡음률 {s:>4.0%} → 조용한 오답 {0.55 * s * N_Q:>4.1f}건 / {N_Q}건")
# 출력:
# 작업 기억 낡음률   0% → 조용한 오답  0.0건 / 100건
# 작업 기억 낡음률   5% → 조용한 오답  2.8건 / 100건
# 작업 기억 낡음률  10% → 조용한 오답  5.5건 / 100건
# 작업 기억 낡음률  20% → 조용한 오답 11.0건 / 100건

# %% [markdown]
# ## 5. 시각화
#
# 왼쪽: 해결 비율 분포와 그 위에 겹친 도달 비율(살아남은 꼬리).
# 오른쪽: 캐스케이드 vs 전부 한 번에, 총 토큰 비교.

# %%
try:
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots

    names = [t[0] for t in TIERS]
    probs = [t[3] for t in TIERS]
    reach = []
    rem = 1.0
    for p in probs:
        reach.append(rem)
        rem -= p

    fig = make_subplots(
        rows=1,
        cols=2,
        subplot_titles=("계층별 해결 비율 vs 도달 비율", "총 토큰 (질문 100개)"),
        specs=[[{"secondary_y": False}, {"secondary_y": False}]],
    )
    fig.add_trace(
        go.Bar(x=names, y=[p * 100 for p in probs], name="해결 비율(%)",
               marker_color="#4C78A8", text=[f"{p:.0%}" for p in probs],
               textposition="outside"),
        row=1, col=1,
    )
    fig.add_trace(
        go.Scatter(x=names, y=[r * 100 for r in reach], name="도달 비율(%)",
                   mode="lines+markers", line=dict(color="#E45756", width=3)),
        row=1, col=1,
    )
    fig.add_trace(
        go.Bar(x=["계층별로 내려가기", "전부 한 번에 넣기"], y=[tok, atok],
               name="총 토큰", marker_color=["#54A24B", "#B279A2"],
               text=[f"{tok:,.0f}", f"{atok:,.0f}"], textposition="outside",
               showlegend=False),
        row=1, col=2,
    )
    fig.update_yaxes(title_text="비율(%)", range=[0, 110], row=1, col=1)
    fig.update_yaxes(title_text="토큰", row=1, col=2)
    fig.update_layout(
        title="기억 계층 55/20/15/8/2 — 해결 비율과 캐스케이드 효과",
        height=460, width=1100, bargap=0.35,
        legend=dict(orientation="h", y=1.12, x=0),
    )
    _show(fig)

    import os

    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "expy.png")
    fig.write_image(out, scale=2)
    print("saved:", out)
except ImportError as e:
    print("plotly/kaleido 없음 — 시각화 건너뜀:", e)
# 출력: saved: .../538a060b-8e77-4ab5-9696-15d7adad26b8/expy.png

# %% [markdown]
# ## 정리
#
# - 해결 비율은 **작업 기억 55%, 최근 요약 20%, 에피소드 기억 15%, 지식 그래프 8%, 모름 2%**.
#   합이 1이 되도록 "모름 2%"까지 명시한 것이 이 표의 설계다.
# - 도달 비율은 $1.00 \to 0.45 \to 0.25 \to 0.10 \to 0.02$ 로 줄어들고,
#   비싼 계층일수록 적게 호출된다.
# - 결과: 총 토큰 44,250 vs 185,000 (23.9%), 총 지연 937.5ms vs 6,150ms (15.2%).
# - 단, 상위 계층이 낡으면 55%를 **틀린 채로 빠르게** 처리한다.
#   계층 설계의 핵심 변수는 속도가 아니라 갱신(유효 기간)이다.
