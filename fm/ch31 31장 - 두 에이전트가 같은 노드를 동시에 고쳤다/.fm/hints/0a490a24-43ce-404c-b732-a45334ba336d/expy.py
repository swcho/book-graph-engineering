# %% [markdown]
# # `ex4_conflict_shape.py` — 여섯 경우 중 '충돌 아님'은 어느 것인가
#
# 질문: 여섯 시나리오 중 **'충돌 아님'**으로 판정되는 것은?
#
# 답: **한 노드의 다른 엣지**(겹치는 것이 없음)와 **양쪽에서 같은 엣지 추가**(결과가 같아 멱등)다.
#
# 이 노트북은 에셋의 `ex4_conflict_shape.py`를 kuzu 없이 재구현한다.
# 여섯 시나리오를 세 가지 **버전 배치**(노드 버전 / 엣지 버전 / 논리 단위)로
# 실제로 판정해 $6 \times 3$ 판정 행렬을 만들고,
# 노드 3/6 · 엣지 3/6 · 논리 단위 5/6, 멱등 검사를 붙이면 6/6 이 되는 것을 확인한다.
#
# 핵심 아이디어는 하나다. 각 방식은 연산에서 **잠금 키 집합** $K(op)$ 를 뽑고
#
# $$\text{충돌} \iff K(op_A) \cap K(op_B) \neq \varnothing$$
#
# 로 판정한다. 방식이 다르다는 건 $K$ 가 다르다는 뜻일 뿐이다.

# %%
# 필요 패키지: plotly, kaleido  (kuzu 불필요 — 그래프는 파이썬 자료구조로 흉내낸다)
from dataclasses import dataclass


def _show(fig):
    try:
        from IPython import get_ipython
        if get_ipython() is not None:
            fig.show()
    except ImportError:
        pass


@dataclass(frozen=True)
class Op:
    """에이전트 한 명이 하려는 쓰기 한 건."""
    kind: str          # "add" | "setprop" | "delnode"
    src: str = ""      # 주어 노드
    rel: str = ""      # 관계 종류
    dst: str = ""      # 목적어 노드
    value: str = ""    # setprop 일 때 쓰려는 값

    def nodes(self):
        """이 연산이 건드리는 노드들."""
        if self.kind == "delnode":
            return {self.src}
        return {self.src, self.dst}

    def result(self):
        """쓰기가 끝난 뒤의 상태를 나타내는 지문. 같으면 결과가 같다."""
        return (self.kind, self.src, self.rel, self.dst, self.value)


print(Op("add", "이서연", "이끔", "결제팀").nodes())
print(Op("delnode", "결제팀").nodes())
# 출력: {'결제팀', '이서연'}
# 출력: {'결제팀'}

# %% [markdown]
# ## 1. 여섯 경우 — 책의 `SCENARIOS`
#
# `ex4` 의 표를 그대로 옮긴다. 마지막 두 칸이 **원하는 판정**과 그 이유다.

# %%
SCENARIOS = [
    ("같은 엣지의 속성",
     Op("setprop", "이서연", "이끔", "결제팀", value="2026-01-01"),
     Op("setprop", "이서연", "이끔", "결제팀", value="2026-03-01"),
     "충돌", "둘 다 같은 것을 고친다"),
    ("한 노드의 다른 엣지",
     Op("add", "이서연", "이끔", "결제팀"),
     Op("add", "이서연", "삶", "마포"),
     "충돌 아님", "겹치는 것이 없다"),
    ("단일 값 관계",
     Op("add", "이서연", "이끔", "결제팀"),
     Op("add", "김도현", "이끔", "결제팀"),
     "충돌", "팀장은 한 명 (28장)"),
    ("노드 삭제 대 엣지 추가",
     Op("delnode", "결제팀"),
     Op("add", "이서연", "속함", "결제팀"),
     "충돌", "없는 노드에 엣지를 못 단다"),
    ("양쪽에서 같은 엣지 추가",
     Op("add", "이서연", "속함", "결제팀"),
     Op("add", "이서연", "속함", "결제팀"),
     "충돌 아님", "결과가 같다 (멱등, 21장)"),
    ("서로 다른 방향",
     Op("add", "이서연", "멘토", "김도현"),
     Op("add", "김도현", "멘토", "이서연"),
     "도메인이 정함", "대칭 관계면 충돌"),
]

print("두 에이전트가 그래프를 동시에 고치는 여섯 경우.\n")
print(f"{'경우':<14}{'판정':<10}이유")
print("-" * 52)
for name, a, b, verdict, why in SCENARIOS:
    print(f"{name:<14}{verdict:<10}{why}")

NOT_CONFLICT = [n for n, _a, _b, v, _w in SCENARIOS if v == "충돌 아님"]
print(f"\n'충돌 아님' 은 {len(NOT_CONFLICT)}개: {NOT_CONFLICT}")
# 출력: 두 에이전트가 그래프를 동시에 고치는 여섯 경우.
# 출력: (표 6줄)
# 출력: '충돌 아님' 은 2개: ['한 노드의 다른 엣지', '양쪽에서 같은 엣지 추가']

# %% [markdown]
# ## 2. 단일 값 관계 목록 (28장의 `SINGLE_VALUED`)
#
# 「한 명만」인 관계에는 **어느 쪽이 하나인가**라는 방향이 있다.
#
# - `이끔`: 팀 하나에 팀장 하나 → 제약이 걸린 쪽은 **목적어**(팀)
# - `속함`, `삶`: 사람 하나에 소속/거주지 하나 → 제약이 걸린 쪽은 **주어**(사람)
# - `멘토`: 여러 명 가능 → 단일 값 아님
#
# 논리 단위는 이 «제약이 걸린 쪽 + 관계 종류»를 한 덩어리로 본다.

# %%
SINGLE_VALUED = {
    "이끔": "in",    # 목적어(팀) 기준으로 하나
    "속함": "out",   # 주어(사람) 기준으로 하나
    "삶": "out",
}   # "멘토" 는 여기 없다 = 다중 값

def anchor(op):
    """단일 값 관계에서 제약이 걸린 쪽 노드."""
    return op.dst if SINGLE_VALUED[op.rel] == "in" else op.src

for rel in ("이끔", "속함", "멘토"):
    o = Op("add", "이서연", rel, "결제팀")
    print(rel, "→", anchor(o) if rel in SINGLE_VALUED else "다중 값")
# 출력: 이끔 → 결제팀
# 출력: 속함 → 이서연
# 출력: 멘토 → 다중 값

# %% [markdown]
# ## 3. 세 가지 버전 배치 = 세 가지 잠금 키 $K(op)$
#
# | 배치 | $K(op)$ |
# |---|---|
# | 노드 버전 | 건드리는 **모든 노드** |
# | 엣지 버전 | 엣지 하나 `(주어, 관계, 목적어)` (노드 삭제는 그 노드) |
# | 논리 단위 | 단일 값이면 `(제약 쪽, 관계)`, 다중 값이면 엣지 하나 |
#
# 노드 삭제만 예외 규칙이 하나 붙는다. 논리 단위에서는
# **삭제된 노드에 걸리는 모든 엣지와 충돌**로 본다.

# %%
def keys_node(op):
    return {("N", n) for n in op.nodes()}


def keys_edge(op):
    if op.kind == "delnode":
        return {("N", op.src)}
    return {("E", op.src, op.rel, op.dst)}


def keys_logical(op):
    if op.kind == "delnode":
        return {("N", op.src)}
    if op.rel in SINGLE_VALUED:
        return {("L", anchor(op), op.rel)}
    return {("E", op.src, op.rel, op.dst)}


def judge(a, b, keyfn, logical=False, idempotent=False):
    """'막음' 또는 '통과'."""
    if idempotent and a.result() == b.result():
        return "통과"                       # 쓰려는 것이 이미 있는 것과 같다
    if logical:                             # 노드 삭제는 그 노드에 걸린 전부와 충돌
        for x, y in ((a, b), (b, a)):
            if x.kind == "delnode" and x.src in y.nodes():
                return "막음"
    return "막음" if keyfn(a) & keyfn(b) else "통과"


STRATEGIES = [
    ("노드 버전", keys_node, False),
    ("엣지 버전", keys_edge, False),
    ("논리 단위", keys_logical, True),
]

a, b = SCENARIOS[2][1], SCENARIOS[2][2]     # 단일 값 관계
print("단일 값 관계 —", "이서연-이끔->결제팀  vs  김도현-이끔->결제팀")
for name, fn, lg in STRATEGIES:
    print(f"  {name}: {judge(a, b, fn, lg):<4} keys(A)={sorted(fn(a))}")
# 출력: 단일 값 관계 — 이서연-이끔->결제팀  vs  김도현-이끔->결제팀
# 출력:   노드 버전: 막음  keys(A)=[('N', '결제팀'), ('N', '이서연')]
# 출력:   엣지 버전: 통과  keys(A)=[('E', '이서연', '이끔', '결제팀')]
# 출력:   논리 단위: 막음  keys(A)=[('L', '결제팀', '이끔')]

# %% [markdown]
# ## 4. 6 × 3 판정 행렬
#
# 원하는 것(`WANT`)은 '충돌'이면 `막음`, '충돌 아님'이면 `통과`다.
# '도메인이 정함'인 여섯째는 비대칭 멘토 관계로 두어 `통과`가 정답이다.

# %%
WANT = {
    "같은 엣지의 속성": "막음",
    "한 노드의 다른 엣지": "통과",
    "단일 값 관계": "막음",
    "노드 삭제 대 엣지 추가": "막음",
    "양쪽에서 같은 엣지 추가": "통과",
    "서로 다른 방향": "통과",
}


def matrix(idem=False):
    rows = []
    for name, a, b, _v, _w in SCENARIOS:
        rows.append((name, [judge(a, b, fn, lg, idem) for _n, fn, lg in STRATEGIES]))
    return rows


def report(rows, title):
    print(title)
    print(f"{'경우':<14}{'노드 버전':<9}{'엣지 버전':<9}{'논리 단위':<9}원하는 것")
    print("-" * 56)
    score = [0, 0, 0]
    for name, verds in rows:
        w = WANT[name]
        cells = []
        for i, v in enumerate(verds):
            score[i] += v == w
            cells.append(v + ("" if v == w else "*"))
        print(f"{name:<14}{cells[0]:<9}{cells[1]:<9}{cells[2]:<9}{w}")
    print(f"{'맞은 개수':<14}{score[0]:<9}{score[1]:<9}{score[2]:<9}(* 는 틀린 판정)\n")
    return score


base = matrix(idem=False)
score_base = report(base, "버전을 어디에 둘 것인가 — 기본\n")
# 출력: 같은 엣지의 속성   막음 막음 막음 / 막음
# 출력: 한 노드의 다른 엣지 막음* 통과 통과 / 통과
# 출력: 단일 값 관계     막음 통과* 막음 / 막음
# 출력: 노드 삭제 대 엣지 추가 막음 통과* 막음 / 막음
# 출력: 양쪽에서 같은 엣지 추가 막음* 막음* 막음* / 통과
# 출력: 서로 다른 방향    막음* 통과 통과 / 통과
# 출력: 맞은 개수 3 3 5

# %% [markdown]
# 어느 것도 6/6 이 아니다. 그게 이 표의 요점이다.
#
# - **노드 버전 3/6** — 「한 노드의 다른 엣지」가 헛충돌한다. **가짜 충돌**.
# - **엣지 버전 3/6** — 「단일 값 관계」를 못 잡는다. 팀장이 둘이 된다. **누락**.
# - **논리 단위 5/6** — 남은 하나가 「양쪽에서 같은 엣지 추가」다.
#
# 마지막 하나는 결과가 같으니 통과시켜도 되는데 세 방식 모두 막는다.
# 버전 비교 **전에** 멱등 검사를 먼저 하면 된다 (21장).

# %%
idem = matrix(idem=True)
score_idem = report(idem, "버전 비교 «전에» 멱등 검사를 먼저 — 「결과가 같으면 성공」\n")
print(f"논리 단위: {score_base[2]}/6 → {score_idem[2]}/6")
# 출력: 양쪽에서 같은 엣지 추가 행이 세 방식 모두 통과로 바뀐다
# 출력: 맞은 개수 4 4 6
# 출력: 논리 단위: 5/6 → 6/6

# %% [markdown]
# ## 5. 다시 질문으로
#
# '충돌 아님'인 둘은 **이유가 서로 다르다**.
#
# - 「한 노드의 다른 엣지」 — 애초에 **겹치는 것이 없다**. 논리 단위 키가 다르다.
# - 「양쪽에서 같은 엣지 추가」 — 키는 **완전히 같다**. 그런데 **결과가 같아서**(멱등) 통과다.
#
# 앞의 것은 잠금 단위를 잘 고르면 풀리고, 뒤의 것은 잠금 단위로는 절대 못 푼다.

# %%
for name, a, b, verdict, why in SCENARIOS:
    if verdict != "충돌 아님":
        continue
    same_key = bool(keys_logical(a) & keys_logical(b))
    same_result = a.result() == b.result()
    print(f"{name}: 키 겹침={same_key}, 결과 같음={same_result}  ({why})")
# 출력: 한 노드의 다른 엣지: 키 겹침=False, 결과 같음=False  (겹치는 것이 없다)
# 출력: 양쪽에서 같은 엣지 추가: 키 겹침=True, 결과 같음=True  (결과가 같다 (멱등, 21장))

# %% [markdown]
# ## 6. 판정 행렬 히트맵
#
# - 초록 = 정답
# - 노랑 = 가짜 충돌 (안 겹치는데 막음)
# - 빨강 = 누락 (막아야 하는데 통과)

# %%
import plotly.graph_objects as go
from plotly.subplots import make_subplots

STRAT_NAMES = [n for n, _f, _l in STRATEGIES]
COLORS = [(0.0, "#7fbf7b"), (0.33, "#7fbf7b"),
          (0.34, "#f6d55c"), (0.66, "#f6d55c"),
          (0.67, "#e06666"), (1.0, "#e06666")]
LABEL = {0: "정답", 1: "가짜 충돌", 2: "누락"}


def grade(verdict, want):
    if verdict == want:
        return 0
    return 1 if verdict == "막음" else 2      # 막음인데 통과여야 함 = 가짜 충돌


def panel(rows):
    names = [n for n, _v in rows]
    z, text, hover = [], [], []
    for name, verds in rows:
        w = WANT[name]
        g = [grade(v, w) for v in verds]
        z.append(g)
        text.append([f"{v}<br>{LABEL[c]}" for v, c in zip(verds, g)])
        hover.append([f"{name}<br>{s}: {v} (원하는 것 {w}) — {LABEL[c]}"
                      for s, v, c in zip(STRAT_NAMES, verds, g)])
    return names, z, text, hover


fig = make_subplots(
    rows=1, cols=2, horizontal_spacing=0.16,
    subplot_titles=(f"기본 — {score_base[0]}/6 · {score_base[1]}/6 · {score_base[2]}/6",
                    f"멱등 검사 추가 — {score_idem[0]}/6 · {score_idem[1]}/6 · {score_idem[2]}/6"))

for col, rows in ((1, base), (2, idem)):
    names, z, text, hover = panel(rows)
    fig.add_trace(go.Heatmap(
        z=z, x=STRAT_NAMES, y=names, text=text, texttemplate="%{text}",
        customdata=hover, hovertemplate="%{customdata}<extra></extra>",
        textfont=dict(size=11, color="#1b1b1b"),
        colorscale=COLORS, zmin=0, zmax=2, showscale=False,
        xgap=3, ygap=3), row=1, col=col)

for c in (1, 2):
    fig.update_xaxes(side="top", row=1, col=c)
    fig.update_yaxes(autorange="reversed", row=1, col=c)   # 첫 시나리오가 맨 위

for ann in fig.layout.annotations[:2]:                     # 서브플롯 제목을 위로 밀기
    ann.update(y=1.10, yanchor="bottom", font=dict(size=13))

for i, (color, name) in enumerate((("#7fbf7b", "정답"),
                                   ("#f6d55c", "가짜 충돌"),
                                   ("#e06666", "누락"))):
    fig.add_trace(go.Scatter(x=[None], y=[None], mode="markers", name=name,
                             marker=dict(size=14, color=color, symbol="square")))

fig.update_layout(
    title=dict(text="충돌 판정 행렬 — 여섯 경우 × 세 가지 버전 배치", y=0.97),
    template="plotly_white", width=1100, height=580,
    margin=dict(t=170, b=80),
    legend=dict(orientation="h", y=-0.10, x=0.5, xanchor="center"))

fig.write_image("expy.png", scale=2)
_show(fig)
print("expy.png 저장 완료")
# 출력: expy.png 저장 완료

# %% [markdown]
# 왼쪽 표에서 노랑이 몰린 열이 **노드 버전**(가짜 충돌 3), 빨강이 몰린 열이
# **엣지 버전**(누락 2)이다. 논리 단위는 「양쪽에서 같은 엣지 추가」 한 칸만 노랑이고,
# 오른쪽처럼 멱등 검사를 앞에 붙이면 그 칸이 초록으로 바뀌어 6/6 이 된다.
#
# 정리하면 '충돌 아님'은 **한 노드의 다른 엣지**(겹치는 것이 없음)와
# **양쪽에서 같은 엣지 추가**(결과가 같아 멱등) 둘이다.
