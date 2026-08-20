# %% [markdown]
# # 「최근 30일만」은 왜 필요한 것의 81%를 같이 버리는가
#
# 27.5절 `ex5_forgetting.py`와 같은 구조의 시뮬레이션을 다시 짓는다.
# 기억 400개를 만들고, 세 가지 잊기 정책을 적용해
# **남긴 비율(보존율)** 과 **필요했던 것 중 지켜낸 비율(recall)** 을 비교한다.
#
# 핵심 질문은 하나다. 왜 나이로 자르면 recall이 보존율을 따라 그대로 내려앉는가.

# %%
import random

import plotly.graph_objects as go


def _show(fig):
    try:
        from IPython import get_ipython
        if get_ipython() is not None:
            fig.show()
    except ImportError:
        pass


SEED = 17          # 난수는 반드시 고정
N = 400            # 기억 개수
DAYS = 180         # 나이는 0~180일 균등

# 종류별 «나중에 실제로 필요해질» 확률 (원본 ex5와 동일)
NEED_P = {"일회성": 0.03, "선호": 0.55, "관계": 0.62, "제약": 0.88}
# 종류별 등장 비중
KIND_W = {"일회성": 55, "선호": 20, "관계": 18, "제약": 7}

print("종류별 필요 확률:", NEED_P)
print("종류별 비중:", KIND_W)
# 출력: 종류별 필요 확률: {'일회성': 0.03, '선호': 0.55, '관계': 0.62, '제약': 0.88}
# 출력: 종류별 비중: {'일회성': 55, '선호': 20, '관계': 18, '제약': 7}

# %% [markdown]
# ## 1. 기억 만들기
#
# 기억 하나는 네 칸을 갖는다.
#
# - `age` — 며칠 된 기억인가. $\text{age} \sim \mathrm{Unif}\{0, 1, \dots, 180\}$
# - `used` — 지금까지 몇 번 참조됐나
# - `kind` — 일회성 / 선호 / 관계 / 제약
# - `needed` — 나중에 실제로 필요해지는가. $P(\text{needed} \mid \text{kind})$ 로만 결정된다
#
# 여기가 이 예제의 설계 전부다. **`needed`는 `kind`에만 의존하고 `age`와는 무관하게 뽑힌다.**
# 즉 나이와 중요도가 확률적으로 독립이다.
#
# $$P(\text{needed} \mid \text{age}=a) = P(\text{needed}) \quad \forall a$$
#
# 이게 인위적인 가정처럼 보이지만, 실제 대화 기억이 딱 이렇다.
# 「이 API는 부르면 안 된다」는 제약은 3개월 전에 말했다고 덜 중요해지지 않는다.

# %%
def make_memory(seed=SEED):
    rng = random.Random(seed)
    kinds = list(KIND_W)
    weights = [KIND_W[k] for k in kinds]
    out = []
    for i in range(N):
        age = rng.randint(0, DAYS)
        used = rng.choices([0, 1, 2, 5, 20], [50, 25, 15, 8, 2])[0]
        kind = rng.choices(kinds, weights)[0]
        # needed 는 kind 로만 결정된다. age 는 쳐다보지도 않는다.
        out.append({"id": i, "age": age, "used": used, "kind": kind,
                    "needed": rng.random() < NEED_P[kind]})
    return out


MEM = make_memory()
NEEDED = sum(1 for x in MEM if x["needed"])
print(f"기억 {N}개, 그중 나중에 필요해지는 것 {NEEDED}개 ({NEEDED / N:.1%})")
# 출력: 기억 400개, 그중 나중에 필요해지는 것 107개 (26.8%)

# 나이와 needed 가 정말 무관한지 확인한다.
# 400개 한 판은 표본 흔들림이 크므로 시드 200개를 모아서(=8만 개) 본다.
pool = []
for s in range(1000, 1200):
    pool.extend(make_memory(seed=s))
print(f"표본 {len(pool):,}개로 나이 구간별 필요 비율:")
for lo, hi in [(0, 30), (31, 75), (76, 120), (121, 180)]:
    band = [x for x in pool if lo <= x["age"] <= hi]
    nd = sum(1 for x in band if x["needed"])
    print(f"  나이 {lo:>3}~{hi:>3}일: {len(band):>6,}개 중 필요 {nd:>5,}개 ({nd / len(band):.1%})")
_base = sum(KIND_W[k] / sum(KIND_W.values()) * NEED_P[k] for k in KIND_W)
print(f"(이론값: 0.55*0.03 + 0.20*0.55 + 0.18*0.62 + 0.07*0.88 = {_base:.2%})")
# 출력: 표본 80,000개로 나이 구간별 필요 비율:
# 출력:   나이   0~ 30일: 13,674개 중 필요 4,180개 (30.6%)
# 출력:   나이  31~ 75일: 19,841개 중 필요 5,843개 (29.4%)
# 출력:   나이  76~120일: 19,952개 중 필요 6,044개 (30.3%)
# 출력:   나이 121~180일: 26,533개 중 필요 7,887개 (29.7%)
# 출력: (이론값: 0.55*0.03 + 0.20*0.55 + 0.18*0.62 + 0.07*0.88 = 29.97%)

# %% [markdown]
# 네 구간 모두 29.4~30.6%로, 이론값 29.97% 주변에 평평하게 누워 있다.
# **오래된 기억이라고 덜 필요해지지 않는다.**
# 이 한 줄이 「최근 30일만」의 사망 선고다.
# (400개 한 판만 보면 구간별로 17~30%까지 튀지만, 그건 표본 잡음이지 추세가 아니다.)

# %% [markdown]
# ## 2. 세 가지 정책

# %%
def keep_recent(m, days=30):
    """정책 A — 최근 30일만 남긴다. 나이 하나로 자른다."""
    return [x for x in m if x["age"] <= days]


def keep_used(m, k=1):
    """정책 B — 한 번이라도 쓴 것만 남긴다."""
    return [x for x in m if x["used"] >= k]


def keep_typed(m):
    """정책 C — 종류마다 다른 수명을 준다. 또는 두 번 이상 쓴 것."""
    keep_days = {"일회성": 7, "선호": 365, "관계": 365, "제약": 3650}
    return [x for x in m if x["age"] <= keep_days[x["kind"]] or x["used"] >= 2]


POLICIES = [
    ("전부 남긴다", lambda m: list(m)),
    ("최근 30일만", keep_recent),
    ("한 번이라도 쓴 것", keep_used),
    ("종류별로 다르게", keep_typed),
]

rows = []
for name, fn in POLICIES:
    kept = fn(MEM)
    got = sum(1 for x in kept if x["needed"])
    rows.append({
        "정책": name,
        "남긴 수": len(kept),
        "보존율": len(kept) / N,
        "지킨 필요": got,
        "recall": got / NEEDED,
        "lift": (got / NEEDED) / (len(kept) / N),
    })

print(f"{'정책':<20}{'남긴 수':>8}{'보존율':>9}{'지킨 필요':>10}{'recall':>9}{'lift':>8}")
print("-" * 66)
for r in rows:
    print(f"{r['정책']:<20}{r['남긴 수']:>8}{r['보존율']:>9.1%}"
          f"{r['지킨 필요']:>10}{r['recall']:>9.1%}{r['lift']:>8.2f}")
# 출력: 정책                     남긴 수      보존율     지킨 필요   recall    lift
# 출력: ------------------------------------------------------------------
# 출력: 전부 남긴다                  400   100.0%       107   100.0%    1.00
# 출력: 최근 30일만                   67    16.8%        20    18.7%    1.12
# 출력: 한 번이라도 쓴 것              192    48.0%        48    44.9%    0.93
# 출력: 종류별로 다르게                250    62.5%       104    97.2%    1.56

# %% [markdown]
# ## 3. 왜 이렇게 되는가 — 확률로
#
# 정책을 「기억을 남길지 말지 정하는 사건 $K$」로 보자. 우리가 재는 두 수는 이렇다.
#
# $$\text{보존율} = P(K), \qquad \text{recall} = P(K \mid \text{needed})$$
#
# 베이즈로 뒤집으면
#
# $$\frac{\text{recall}}{\text{보존율}} = \frac{P(K \mid \text{needed})}{P(K)} = \frac{P(\text{needed} \mid K)}{P(\text{needed})}$$
#
# 이 비율(위 표의 `lift`)이 정책이 가진 **정보량**이다.
# lift가 1이면 정책은 중요도에 대해 아무것도 모른 채 무작위로 뽑은 것과 같다.
#
# ### 정책 A: 최근 30일만
#
# 컷 조건은 $K = \{\text{age} \le 30\}$이고, 설계상 $\text{age} \perp \text{needed}$다. 따라서
#
# $$P(K \mid \text{needed}) = P(K) \;\Longrightarrow\; \text{lift} = 1$$
#
# 즉 **recall이 보존율과 똑같아진다.** 이론값은
#
# $$P(\text{age} \le 30) = \frac{31}{181} \approx 0.171$$
#
# 83%를 버리면 필요한 것도 정확히 83%를 버린다. 실측 16.8% / 18.7%는 이 17.1% 주변의 표본 흔들림이다.
#
# **나이 컷은 「고르는 일」을 전혀 하지 않는다. 그냥 균등 표본 추출이다.**

# %%
theory_keep = (30 + 1) / (DAYS + 1)
print(f"이론 보존율 P(age<=30) = 31/181 = {theory_keep:.3%}")
print(f"이론 recall  P(age<=30 | needed) = 같은 값 = {theory_keep:.3%}")
print(f"이론 lift = 1.000")
print()
print(f"실측 보존율 = {rows[1]['보존율']:.3%}")
print(f"실측 recall  = {rows[1]['recall']:.3%}")
print(f"실측 lift   = {rows[1]['lift']:.3f}")
# 출력: 이론 보존율 P(age<=30) = 31/181 = 17.127%
# 출력: 이론 recall  P(age<=30 | needed) = 같은 값 = 17.127%
# 출력: 이론 lift = 1.000
# 출력:
# 출력: 실측 보존율 = 16.750%
# 출력: 실측 recall  = 18.692%
# 출력: 실측 lift   = 1.121

# %% [markdown]
# ### 시드를 여러 개 돌려서 lift = 1 을 확인
#
# 한 번의 실행(400개)은 우연일 수 있다. 시드를 200개 돌려 평균을 본다.

# %%
lifts = {name: [] for name, _ in POLICIES[1:]}
for s in range(1000, 1200):
    mm = make_memory(seed=s)
    nd = sum(1 for x in mm if x["needed"])
    for name, fn in POLICIES[1:]:
        kept = fn(mm)
        got = sum(1 for x in kept if x["needed"])
        lifts[name].append((got / nd) / (len(kept) / N))

for name, vals in lifts.items():
    print(f"{name:<20} lift 평균 {sum(vals) / len(vals):.3f}  "
          f"(최소 {min(vals):.2f}, 최대 {max(vals):.2f})")
# 출력: 최근 30일만              lift 평균 1.020  (최소 0.54, 최대 1.58)
# 출력: 한 번이라도 쓴 것           lift 평균 0.998  (최소 0.75, 최대 1.19)
# 출력: 종류별로 다르게             lift 평균 1.586  (최소 1.43, 최대 1.76)

# %% [markdown]
# 「최근 30일만」의 lift 평균은 **1.020**. 정보량이 사실상 0이다.
# (편차가 큰 건 남긴 게 67개뿐이라 분모가 작아서다. 평균은 1로 수렴한다.)
#
# 여기서 덤으로 하나 더 보인다. 「한 번이라도 쓴 것」의 lift 평균도 **0.998**이다.
# 이 예제에서 `used`도 `needed`와 독립으로 뽑히기 때문이다.
# 즉 이 정책이 「최근 30일만」보다 나아 보였던 건 **고르기를 잘해서가 아니라 그냥 덜 버려서**다
# (48% 남김 vs 17% 남김). 책 본문의 「낫지만 여전히 55%를 잃는다」가 이 뜻이다.
#
# 「종류별로 다르게」만 lift가 **1.55**로 1을 크게 넘는다.
# `kind`가 `needed`를 실제로 결정하는 축이기 때문이다. 컷이 신호 위에 놓였다.

# %% [markdown]
# ## 4. 「최근 30일만」이 종류별로 무엇을 죽였나
#
# 나이 컷은 종류를 안 보므로, 제일 비싼 제약도 똑같이 83% 학살한다.

# %%
recent = keep_recent(MEM)
typed = keep_typed(MEM)
print(f"{'종류':<8}{'전체':>6}{'필요':>6}{'A남김':>7}{'A필요':>7}{'A recall':>10}"
      f"{'C남김':>7}{'C필요':>7}{'C recall':>10}")
print("-" * 68)
for k in ("일회성", "선호", "관계", "제약"):
    tot = [x for x in MEM if x["kind"] == k]
    nd = [x for x in tot if x["needed"]]
    ka = [x for x in recent if x["kind"] == k]
    ga = [x for x in ka if x["needed"]]
    kc = [x for x in typed if x["kind"] == k]
    gc = [x for x in kc if x["needed"]]
    print(f"{k:<8}{len(tot):>6}{len(nd):>6}{len(ka):>7}{len(ga):>7}"
          f"{len(ga) / len(nd):>10.0%}{len(kc):>7}{len(gc):>7}{len(gc) / len(nd):>10.0%}")
# 출력: 종류      전체    필요  A남김  A필요  A recall  C남김  C필요  C recall
# 출력: --------------------------------------------------------------------
# 출력: 일회성      226     5     38      2       40%     76      2       40%
# 출력: 선호         71    36      7      5       14%     71     36      100%
# 출력: 관계         71    39     16      8       21%     71     39      100%
# 출력: 제약         32    27      6      5       19%     32     27      100%

# %% [markdown]
# 제약 32개 중 26개가 나이 때문에 사라졌고, 필요했던 제약 27개 중 22개를 잃었다.
# 「이 API는 부르면 안 된다」가 딱 이 칸에 있다.
#
# 반면 종류별 정책은 **선호·관계·제약을 하나도 안 버린다** (recall 100%).
# 정작 버리는 건 일회성 226개 중 150개다. 그러면서 잃는 필요한 것은 3개뿐.
#
# > 덜 버려서 이긴 게 아니다. **버릴 것을 골라서** 이겼다.

# %% [markdown]
# ## 5. 시각화

# %%
names = [r["정책"] for r in rows]
keep_rates = [r["보존율"] * 100 for r in rows]
recalls = [r["recall"] * 100 for r in rows]

fig = go.Figure()
fig.add_trace(go.Bar(
    name="보존율 (남긴 비율)", x=names, y=keep_rates,
    marker_color="#9aa5b1",
    text=[f"{v:.1f}%" for v in keep_rates], textposition="outside",
))
fig.add_trace(go.Bar(
    name="recall (필요한 것 중 지켜낸 비율)", x=names, y=recalls,
    marker_color="#2f6f4f",
    text=[f"{v:.1f}%" for v in recalls], textposition="outside",
))
fig.add_trace(go.Scatter(
    name="lift = recall / 보존율", x=names, y=[r["lift"] for r in rows],
    mode="lines+markers+text", yaxis="y2",
    line=dict(color="#c0392b", dash="dot"), marker=dict(size=10),
    text=[f"{r['lift']:.2f}" for r in rows], textposition="top center",
))
fig.add_hline(y=1.0, yref="y2", line=dict(color="#c0392b", width=1, dash="dash"),
              opacity=0.35)
fig.update_layout(
    title="잊기 정책별 보존율 vs recall — 나이 컷은 lift=1 (정보량 0)",
    barmode="group",
    yaxis=dict(title="비율 (%)", range=[0, 118]),
    yaxis2=dict(title="lift", overlaying="y", side="right", range=[0, 2.0]),
    font=dict(family="Apple SD Gothic Neo, AppleGothic, NanumGothic, sans-serif",
              size=13),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0),
    template="plotly_white",
    width=980, height=560,
)
_show(fig)

fig.write_image("expy.png", scale=2)
print("expy.png 저장 완료")
# 출력: expy.png 저장 완료

# %% [markdown]
# ## 6. 한 줄 정리
#
# | 정책 | 보존율 | recall | lift | 뜻 |
# |---|---|---|---|---|
# | 전부 남긴다 | 100% | 100% | 1.00 | 안 버리니 안 잃는다. 대신 비싸다 |
# | 최근 30일만 | 16.8% | 18.7% | 1.12 (200시드 평균 1.02) | **무작위 표본 추출.** 83% 버리면 필요한 것도 81% 버린다 |
# | 한 번이라도 쓴 것 | 48.0% | 44.9% | 0.93 (200시드 평균 1.00) | 역시 정보량 0. 덜 버려서 덜 잃었을 뿐 |
# | 종류별로 다르게 | 62.5% | 97.2% | 1.56 (200시드 평균 1.59) | **더 많이 남기고 훨씬 더 잘 지킨다** |
#
# 나이는 중요도의 대리 변수가 아니다.
# 정렬 기준을 결과와 상관없는 축에 놓으면, 아무리 정교하게 잘라도 그건 그냥 랜덤 샘플링이다.
