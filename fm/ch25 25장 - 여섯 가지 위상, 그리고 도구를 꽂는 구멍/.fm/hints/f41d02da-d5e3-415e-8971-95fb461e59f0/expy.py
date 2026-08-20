# %% [markdown]
# # 멍청한 선택기가 모델을 대신할 수 있는 이유
#
# 25장 예제 5(`ex5_tool_selection.py`)는 모델을 전혀 쓰지 않는다.
# 질문과 도구 설명 사이의 **단어 겹침 개수**만 세서 도구를 고른다.
#
# $$\hat{t}(q) \;=\; \arg\max_{t \in T} \; s\bigl(q,\; d_t\bigr),
# \qquad s_{\text{overlap}}(q,d) = \bigl|\,\mathrm{tok}(q) \cap \mathrm{tok}(d)\,\bigr|$$
#
# 여기서 $d_t$ 는 도구 $t$ 의 **설명 문자열**이다. 이 식에서 중요한 것은
# 오른쪽 항에 $d_t$ 밖에 없다는 점이다. 도구의 실제 동작, 스키마, 런타임 결과는
# 어디에도 들어오지 않는다.
#
# 임베딩 검색기든 LLM이든 이 자리는 똑같다. 바뀌는 것은 $s$ 뿐이다.
#
# | 선택기 | $s$ 의 정체 | 입력 |
# |---|---|---|
# | 예제의 선택기 | 토큰 교집합 크기 | $q$, $d_t$ |
# | 임베딩 선택기 | $\cos(E(q), E(d_t))$ | $q$, $d_t$ |
# | LLM 선택기 | $\log P(t \mid q, d_1..d_n)$ | $q$, $d_t$ |
#
# **$d_t$ 가 유일한 신호라는 성질이 셋 다 같다.** 그래서 설명이 나쁘면
# 셋 다 못 고른다. 이 노트북은 그 공유 성질과, 겹침 점수만 갖는 고유한
# 약점(표면형·동의어·부정문)을 나눠서 확인한다.
#
# 필요 패키지: plotly, kaleido (정적 이미지 저장용)

# %%
import re
import random

import plotly.graph_objects as go
from plotly.subplots import make_subplots


def _show(fig):
    try:
        from IPython import get_ipython
        if get_ipython() is not None:  # VSCode 셀/Jupyter에서만 렌더링
            fig.show()
    except ImportError:
        pass


# 예제 5 원문의 질문 세트와 GOOD 설명 (그대로)
QUERIES = [
    ("김지훈이 누구야", "find_person"),
    ("김지훈 위로 누가 있어", "chain_of_command"),
    ("결제팀에 누구누구 있어", "team_members"),
    ("박민수 상급자 알려줘", "chain_of_command"),
    ("이서연 찾아줘", "find_person"),
    ("결제팀 명단", "team_members"),
    ("김지훈 보고 라인 전체", "chain_of_command"),
    ("이서연 정보", "find_person"),
]

GOOD = {
    "find_person":
        "사람 «한 명»을 이름으로 찾는다. 이름, 소속 팀, 상사 아이디를 준다. "
        "여러 명을 찾을 때는 쓰지 않는다.",
    "chain_of_command":
        "한 사람의 «위로 올라가는» 보고 체계를 뿌리까지 준다. "
        "상사, 상사의 상사, 보고 라인, 결재선을 물으면 이것이다. "
        "아래 부하 목록에는 쓰지 않는다.",
    "team_members":
        "팀 이름을 주면 그 팀 구성원 «전부»를 목록으로 준다. "
        "명단, 누구누구, 구성원, 몇 명을 물으면 이것이다.",
}

TOOLS = list(GOOD)


def tokenize(s):
    return set(re.findall(r"[가-힣A-Za-z]+", s))


print("도구 수:", len(TOOLS))
print("질문 수:", len(QUERIES))
print("질문 토큰 예:", sorted(tokenize("김지훈이 누구야")))
print("설명 토큰 예:", sorted(tokenize(GOOD["find_person"])))
# 출력: 도구 수: 3
# 출력: 질문 수: 8
# 출력: 질문 토큰 예: ['김지훈이', '누구야']
# 출력: 설명 토큰 예: ['때는', '명', '명을', '사람', '상사', '소속', '쓰지', '아이디를', '않는다', '여러', '을', '이름', '이름으로', '준다', '찾는다', '찾을', '팀', '한']
# 출력: (조사가 붙은 '명을'과 떨어진 '명'이 서로 다른 토큰이다. 이미 여기서 표면형 문제가 보인다.)

# %% [markdown]
# ## 1단계 — 점수판을 그대로 들여다본다
#
# 정확도만 보면 선택기가 «고른» 것처럼 보인다. 점수판을 보면 다르다.
# 8개 질문 × 3개 도구의 겹침 점수를 전부 찍어 본다.

# %%
def score_matrix(descriptions, score_fn):
    return [[score_fn(q, descriptions[t]) for t in TOOLS] for q, _ in QUERIES]


def s_overlap(q, d):
    return len(tokenize(q) & tokenize(d))


M = score_matrix(GOOD, s_overlap)

print(f"{'질문':<24}" + "".join(f"{t:<18}" for t in TOOLS) + "정답")
for (q, want), row in zip(QUERIES, M):
    print(f"{q:<24}" + "".join(f"{v:<18}" for v in row) + want)

zero_rows = sum(1 for row in M if max(row) == 0)
print(f"\n모든 도구가 0점인 질문: {zero_rows}/{len(QUERIES)}")
# 출력: 질문                      find_person       chain_of_command  team_members      정답
# 출력: 김지훈이 누구야                0                 0                 0                 find_person
# 출력: 김지훈 위로 누가 있어            0                 1                 0                 chain_of_command
# 출력: 결제팀에 누구누구 있어            0                 0                 1                 team_members
# 출력: 박민수 상급자 알려줘             0                 0                 0                 chain_of_command
# 출력: 이서연 찾아줘                 0                 0                 0                 find_person
# 출력: 결제팀 명단                  0                 0                 1                 team_members
# 출력: 김지훈 보고 라인 전체            0                 2                 0                 chain_of_command
# 출력: 이서연 정보                  0                 0                 0                 find_person
# 출력:
# 출력: 모든 도구가 0점인 질문: 4/8

# %% [markdown]
# ## 2단계 — 7/8 중 얼마가 «신호»였나
#
# 예제 원문의 `choose()` 는 `score` 를 `-1` 로 시작하고 `overlap > score` 로 비교한다.
# 그래서 **전부 0점이면 딕셔너리의 첫 키**(`find_person`)가 이긴다.
#
# 0점 질문 4개 중 3개는 정답이 우연히 `find_person` 이라 «맞은» 것이다.
# 동점을 기권(abstain)으로 바꾸면 겹침 점수가 실제로 잡은 양이 드러난다.

# %%
def choose_book(query, descriptions, score_fn=s_overlap):
    """예제 5 원문 방식: 동점이면 첫 키가 이긴다."""
    best, score = None, -1
    for name in TOOLS:
        v = score_fn(query, descriptions[name])
        if v > score:
            best, score = name, v
    return best


def choose_strict(query, descriptions, score_fn=s_overlap):
    """동점이거나 전부 0점이면 기권(None)."""
    scores = [score_fn(query, descriptions[t]) for t in TOOLS]
    top = max(scores)
    winners = [t for t, v in zip(TOOLS, scores) if v == top]
    if top <= 0 or len(winners) > 1:
        return None
    return winners[0]


book_hits = sum(choose_book(q, GOOD) == w for q, w in QUERIES)
strict_hits = sum(choose_strict(q, GOOD) == w for q, w in QUERIES)
lucky = [q for q, w in QUERIES
         if choose_book(q, GOOD) == w and choose_strict(q, GOOD) is None]

print(f"원문 규칙(동점 → 첫 키): {book_hits}/{len(QUERIES)}")
print(f"엄격 규칙(동점 → 기권) : {strict_hits}/{len(QUERIES)}")
print(f"우연히 맞은 질문: {lucky}")
# 출력: 원문 규칙(동점 → 첫 키): 7/8
# 출력: 엄격 규칙(동점 → 기권) : 4/8
# 출력: 우연히 맞은 질문: ['김지훈이 누구야', '이서연 찾아줘', '이서연 정보']

# %% [markdown]
# 겹침 점수가 실제로 «포착»한 것은 4/8이고, 그중에서도 점수 차이가 1~2점에 불과하다.
# 이 선택기는 판단력이 아니라 **설명 문장에 사용자 어휘가 들어 있는지**를 재는 리트머스다.
# 그게 이 선택기가 모델을 대신할 수 있는 이유이기도 하다. 설명의 품질만 재기 때문에.

# %%
def margin(query, descriptions, score_fn=s_overlap):
    """1등 점수 - 2등 점수. 0이면 사실상 못 고른 것."""
    scores = sorted((score_fn(query, descriptions[t]) for t in TOOLS), reverse=True)
    return scores[0] - scores[1]


margins = [margin(q, GOOD) for q, _ in QUERIES]
for (q, _), m in zip(QUERIES, margins):
    print(f"  {q:<24} 마진 {m}")
print(f"\n마진 0인 질문: {sum(1 for m in margins if m == 0)}/{len(QUERIES)}")
# 출력:   김지훈이 누구야                마진 0
# 출력:   김지훈 위로 누가 있어            마진 1
# 출력:   결제팀에 누구누구 있어            마진 1
# 출력:   박민수 상급자 알려줘             마진 0
# 출력:   이서연 찾아줘                 마진 0
# 출력:   결제팀 명단                  마진 1
# 출력:   김지훈 보고 라인 전체            마진 2
# 출력:   이서연 정보                  마진 0
# 출력:
# 출력: 마진 0인 질문: 4/8

# %% [markdown]
# ## 3단계 — 겹침 점수가 놓치는 세 가지
#
# 이 셋은 «겹침 점수 고유»의 약점이다. 임베딩·LLM 선택기는 앞의 둘을 대체로 넘고,
# 셋째는 LLM만 넘는다.
#
# 1. **표면형** — `김지훈이` ≠ `김지훈`, `사람의` ≠ `사람`. 조사·활용이 붙으면 교집합에서 빠진다.
#    문자 $n$-gram 자카드로 완화된다.
#    $$s_{\text{bigram}}(q,d) = \frac{|B(q) \cap B(d)|}{|B(q) \cup B(d)|}$$
# 2. **동의어** — `상급자` vs `상사`. 문자도 안 겹치니 $n$-gram도 못 잡는다.
#    임베딩이 «공짜로» 하는 일을 손으로 적으면 동의어 사전이다.
# 3. **부정문** — 설명의 «언제 안 쓰는지» 문장은 겹침 점수에 **가점**으로 들어간다.
#    금지 문구가 오히려 그 도구를 끌어당긴다. 부호를 뒤집을 수 있는 건 문맥을 읽는 선택기뿐이다.

# %%
def char_bigrams(s):
    out = set()
    for t in re.findall(r"[가-힣A-Za-z]+", s):
        t = "^" + t + "$"
        for i in range(len(t) - 1):
            out.add(t[i:i + 2])
    return out


def s_bigram(q, d):
    a, b = char_bigrams(q), char_bigrams(d)
    return len(a & b) / len(a | b) if (a | b) else 0.0


# 임베딩의 값싼 대리: 사용자 어휘 → 설명 어휘
SYNONYMS = {
    "상급자": ["상사"], "윗사람": ["상사"], "결재선": ["보고", "라인"],
    "인원": ["구성원"], "리스트": ["목록"], "명단": ["구성원"],
    "찾아줘": ["찾는다"], "누구야": ["사람"], "정보": ["이름"],
}


def s_synonym(q, d):
    qs = set(tokenize(q))
    for t in list(qs):
        qs |= set(SYNONYMS.get(t, []))
    return len(qs & tokenize(d))


SELECTORS = [("겹침(원문)", s_overlap), ("문자 bigram", s_bigram), ("겹침+동의어", s_synonym)]

PROBES = [
    ("표면형", "이서연 정보 찾아줘", "find_person"),
    ("동의어", "결제팀 인원 리스트", "team_members"),
    ("부정문", "부하 목록 알려줘", None),   # 어떤 도구도 하면 안 되는 질문
]

for kind, q, want in PROBES:
    print(f"\n[{kind}] {q}   (정답: {want})")
    for name, fn in SELECTORS:
        scores = {t: round(fn(q, GOOD[t]), 3) for t in TOOLS}
        got = choose_strict(q, GOOD, fn)
        verdict = "기권" if got is None else ("정답" if got == want else f"오답({got})")
        print(f"  {name:<12} {scores}  → {verdict}")
# 출력:
# 출력: [표면형] 이서연 정보 찾아줘   (정답: find_person)
# 출력:   겹침(원문)       {'find_person': 0, 'chain_of_command': 0, 'team_members': 0}  → 기권
# 출력:   문자 bigram    {'find_person': 0.036, 'chain_of_command': 0.014, 'team_members': 0.019}  → 정답
# 출력:   겹침+동의어       {'find_person': 2, 'chain_of_command': 0, 'team_members': 0}  → 정답
# 출력:
# 출력: [동의어] 결제팀 인원 리스트   (정답: team_members)
# 출력:   겹침(원문)       {'find_person': 0, 'chain_of_command': 0, 'team_members': 0}  → 기권
# 출력:   문자 bigram    {'find_person': 0.018, 'chain_of_command': 0.014, 'team_members': 0.038}  → 정답
# 출력:   겹침+동의어       {'find_person': 0, 'chain_of_command': 0, 'team_members': 1}  → 정답
# 출력:
# 출력: [부정문] 부하 목록 알려줘   (정답: None)
# 출력:   겹침(원문)       {'find_person': 0, 'chain_of_command': 1, 'team_members': 0}  → 오답(chain_of_command)
# 출력:   문자 bigram    {'find_person': 0.0, 'chain_of_command': 0.072, 'team_members': 0.038}  → 오답(chain_of_command)
# 출력:   겹침+동의어       {'find_person': 0, 'chain_of_command': 1, 'team_members': 0}  → 오답(chain_of_command)

# %% [markdown]
# 앞의 두 프로브(표면형·동의어)는 $s$ 를 바꾸면 넘어간다. 문자 bigram도, 동의어 사전도
# 정답을 찾았다. 즉 이 두 실패는 «선택기의 성능» 문제다.
#
# 부정문 프로브는 다르다. 세 선택기가 **전부 같은 오답**을 냈다.
# `chain_of_command` 설명의 마지막 문장이 «아래 부하 목록에는 쓰지 않는다»인데,
# 그 금지 문장의 단어(`부하`, `목록`) 때문에 하필 **금지된 도구**가 1위가 되었다.
#
# 표면 점수는 «쓰지 않는다»를 부호로 읽지 못한다. 단어가 있으면 가점이다.
# 그래서 «언제 안 쓰는지»를 쓰는 것은 표면 선택기에 대한 최적화가 아니라,
# **문맥을 읽는 선택기(모델)에 대한 최적화**다.
# 그런데도 예제의 선택기가 대리가 되는 이유는 다음 단계에 있다.

# %% [markdown]
# ## 4단계 — 공유 성질: 설명을 지우면 셋 다 같이 무너진다
#
# 설명 토큰을 확률 $p$ 로 지우고(=설명의 정보량을 깎고) 정확도를 잰다.
# 세 선택기 모두 같은 방향으로 붕괴한다. $s$ 가 무엇이든 입력이 $d_t$ 하나이기 때문이다.
#
# $$\text{acc}(p) \;\xrightarrow[\;p \to 1\;]{} \; \text{(신호 없음)}$$

# %%
def ablate(descriptions, p, rng):
    out = {}
    for name, desc in descriptions.items():
        toks = re.findall(r"[가-힣A-Za-z]+", desc)
        kept = [t for t in toks if rng.random() >= p]
        out[name] = " ".join(kept)
    return out


PS = [i / 8 for i in range(9)]
TRIALS = 60
curves = {}

for name, fn in SELECTORS:
    acc = []
    for p in PS:
        total = 0
        for seed in range(TRIALS):
            rng = random.Random(1000 * seed + int(p * 100))
            d = ablate(GOOD, p, rng)
            total += sum(choose_strict(q, d, fn) == w for q, w in QUERIES)
        acc.append(total / (TRIALS * len(QUERIES)))
    curves[name] = acc
    print(f"{name:<12} " + " ".join(f"{a:.2f}" for a in acc))
# 출력: (p = 0, 0.125, ..., 1.0 순서)
# 출력: 겹침(원문)       0.50 0.46 0.38 0.36 0.30 0.24 0.17 0.08 0.00
# 출력: 문자 bigram    0.62 0.64 0.61 0.59 0.55 0.48 0.38 0.24 0.00
# 출력: 겹침+동의어       0.88 0.81 0.72 0.68 0.58 0.49 0.35 0.19 0.00

# %% [markdown]
# 절대 높이는 셋이 다르다. $p=0$ 에서 0.50 / 0.62 / 0.88 이다.
# 동의어 사전을 붙인 쪽이 8개 중 7개를 맞힌다(남는 하나는 «박민수 상급자 알려줘»인데,
# `상급자 → 상사` 로 고쳐도 `상사` 가 `find_person` 설명에도 있어서 동점이 된다.
# 겹침 점수에는 «그 단어가 어느 도구에서 더 특징적인가»라는 개념, 즉 IDF가 없다).
#
# 그런데 곡선의 **모양**은 셋이 같다. 오른쪽으로 갈수록 같이 내려가고
# $p=1$ 에서 정확히 0으로 만난다. 선택기를 더 똑똑한 것으로 바꿔도 이 끝점은 옮길 수 없다.
# 설명이 없으면 고를 근거가 없다.
#
# 이것이 답의 핵심이다. 예제의 선택기는 절대 성능(높이)에서는 모델보다 훨씬 못하지만,
# **설명 품질에 대한 민감도(기울기)는 같은 방향**이다.
# 그래서 «설명을 고쳤더니 나아졌다»는 실험에 대해서는 대리(proxy)로 쓸 수 있다.

# %%
fig = make_subplots(
    rows=2, cols=2,
    subplot_titles=(
        "1. 겹침 점수판 (GOOD 설명) — 절반이 0점",
        "2. 설명 삭제율 vs 정확도 — 셋 다 0으로 수렴",
        "3. 질문별 마진(1등−2등) — 0이면 못 고른 것",
        "4. 프로브 3종 × 선택기 3종",
    ),
    specs=[[{"type": "heatmap"}, {"type": "scatter"}],
           [{"type": "bar"}, {"type": "heatmap"}]],
    vertical_spacing=0.16, horizontal_spacing=0.12,
)

# (1) 점수 히트맵
q_labels = [q for q, _ in QUERIES]
fig.add_trace(
    go.Heatmap(
        z=M, x=TOOLS, y=q_labels,
        text=[[str(v) for v in row] for row in M],
        texttemplate="%{text}", colorscale="Blues", zmin=0, zmax=2,
        showscale=False, hovertemplate="%{y} / %{x}: %{z}<extra></extra>",
    ),
    row=1, col=1,
)

# (2) ablation 곡선
for (name, _), dash in zip(SELECTORS, ["solid", "dash", "dot"]):
    fig.add_trace(
        go.Scatter(x=PS, y=curves[name], mode="lines+markers", name=name,
                   line=dict(dash=dash, width=2)),
        row=1, col=2,
    )

# (3) 마진 막대
fig.add_trace(
    go.Bar(x=q_labels, y=margins,
           marker_color=["#d62728" if m == 0 else "#1f77b4" for m in margins],
           showlegend=False, hovertemplate="%{x}: 마진 %{y}<extra></extra>"),
    row=2, col=1,
)

# (4) 프로브 결과 (1 정답 / 0 기권 / -1 오답)
probe_z, probe_txt = [], []
for kind, q, want in PROBES:
    zrow, trow = [], []
    for name, fn in SELECTORS:
        got = choose_strict(q, GOOD, fn)
        if got is None:
            zrow.append(0); trow.append("기권")
        elif got == want:
            zrow.append(1); trow.append("정답")
        else:
            zrow.append(-1); trow.append("오답")
    probe_z.append(zrow)
    probe_txt.append(trow)

fig.add_trace(
    go.Heatmap(
        z=probe_z, x=[n for n, _ in SELECTORS], y=[k for k, _, _ in PROBES],
        text=probe_txt, texttemplate="%{text}",
        colorscale=[[0.0, "#f4a3a3"], [0.5, "#eeeeee"], [1.0, "#a8d5a2"]],
        zmin=-1, zmax=1, showscale=False,
        hovertemplate="%{y} / %{x}: %{text}<extra></extra>",
    ),
    row=2, col=2,
)

fig.update_xaxes(title_text="설명 토큰 삭제율 p", row=1, col=2)
fig.update_yaxes(title_text="정확도(기권=오답)", range=[0, 1.0], row=1, col=2)
fig.update_xaxes(tickangle=-30, row=2, col=1)
fig.update_yaxes(title_text="마진", row=2, col=1)
fig.update_layout(
    height=880, width=1180,
    title_text="단순 겹침 선택기: 무엇을 포착하고 무엇을 놓치는가",
    template="plotly_white",
    legend=dict(orientation="h", y=1.02, x=0.55),
    font=dict(family="Apple SD Gothic Neo, AppleGothic, NanumGothic, sans-serif", size=12),
)

_show(fig)

import os
_out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "expy.png")
fig.write_image(_out, scale=2)
print("saved:", _out)
# 출력: saved: .../f41d02da-d5e3-415e-8971-95fb461e59f0/expy.png

# %% [markdown]
# ## 정리
#
# | 축 | 예제의 겹침 선택기 | 임베딩 선택기 | LLM 선택기 |
# |---|---|---|---|
# | 입력 | $q$, $d_t$ | $q$, $d_t$ | $q$, $d_t$ |
# | 단어 특이성(IDF) | 없음 | 벡터에 흡수 | 있음 |
# | 표면형(조사·활용) | 못 넘음 (문자 $n$-gram으로 완화) | 넘음 | 넘음 |
# | 동의어 | 못 넘음 (사전으로 땜질) | 넘음 | 넘음 |
# | 부정문 «안 쓴다» | 부호가 뒤집힘(가점) | 약함 | 읽음 |
# | 설명 없으면 | 못 고름 | 못 고름 | 못 고름 |
#
# 마지막 줄이 답이다.
# 단어 겹침만 세는 멍청한 선택기지만, **«설명이 나쁘면 못 고른다»는 성질은 모델도 같다.**
# 그래서 설명을 고치는 실험에서는 이 선택기가 모델의 대리로 쓸 수 있고,
# 의존성 없이 몇 줄로 돌아가니 예제로도 적합하다.
#
# 단, 대리의 한계도 같이 기억해야 한다.
# 겹침 점수에서 «올랐다»가 반드시 모델에서 «오른다»는 뜻은 아니다.
# 특히 «언제 안 쓰는지» 문장은 겹침 점수를 **떨어뜨리면서** 모델 정확도를 올린다.
# 대리는 방향을 보는 도구이고, 크기는 실제 모델로 재야 한다.
