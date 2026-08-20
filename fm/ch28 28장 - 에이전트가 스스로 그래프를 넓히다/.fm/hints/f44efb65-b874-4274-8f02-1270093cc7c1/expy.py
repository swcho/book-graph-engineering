# %% [markdown]
# # 정규화 → 중복 검사, 순서가 갈라놓는 것
#
# 28장 「쓰기 앞에 관문 넷」의 핵심 한 줄을 실행해서 확인한다.
#
# > 정규화가 중복 검사보다 **먼저** 돌아야 한다.
# > 거꾸로 하면 「민수」와 「박민수」가 달라 보여서 중복이 안 걸린다.
#
# 같은 후보 목록을 두 가지 순서로 흘려서 최종 노드 수와 엣지 수가 어떻게 갈리는지 본다.
#
# 필요 패키지: plotly, kaleido (시각화 셀에서만 사용. 없으면 앞 셀들은 그대로 돈다)

# %%
# 필요 패키지: plotly, kaleido


def _show(fig):
    try:
        from IPython import get_ipython

        if get_ipython() is not None:
            fig.show()
    except ImportError:
        pass


# %% [markdown]
# ## 1. 재료 — 별칭표, 관계 정규형표, 후보 트리플
#
# 별칭(alias)은 **같은 개체의 다른 표면형**이고,
# 정규형(canonical form)은 **같은 뜻의 다른 관계 이름**이다.
# 둘 다 «막는» 관문이 아니라 «고치는» 관문이라는 점이 중요하다.

# %%
ALIAS = {"민수": "박민수", "PM": "박민수"}          # 개체 별칭 → 정규 이름
CANON = {"관리": "이끔", "리드": "이끔", "소속": "속함"}  # 관계 별칭 → 정규 관계

# 추출기가 뽑아 온 후보. 표면형이 제각각이다.
CANDIDATES = [
    ("박민수", "이끔", "결제팀"),
    ("이서연", "속함", "결제팀"),
    ("민수", "이끔", "결제팀"),      # 같은 사람, 다른 이름
    ("박민수", "관리", "결제팀"),    # 같은 뜻, 다른 관계 이름
    ("이서연", "속함", "결제팀"),    # 대놓고 중복
    ("PM", "이끔", "결제팀"),        # 또 다른 이름
    ("박민수", "이끔", "결제팀"),    # 대놓고 중복
    ("이서연", "소속", "결제팀"),    # 관계 이름만 다른 중복
]


def normalize(s, k, o):
    return ALIAS.get(s, s), CANON.get(k, k), ALIAS.get(o, o)


print(f"후보 {len(CANDIDATES)}개")
print("정규화하면 실제로는 서로 다른 사실이 몇 개인가:",
      len({normalize(*t) for t in CANDIDATES}), "개")
# 출력:
# 후보 8개
# 정규화하면 실제로는 서로 다른 사실이 몇 개인가: 2 개


# %% [markdown]
# ## 2. 두 가지 순서를 각각 구현한다
#
# **순서 A (정규화 → 중복)**: 표면형을 먼저 정규 이름으로 바꾼 다음, 이미 있는지 본다.
#
# **순서 B (중복 → 정규화)**: 표면형 그대로 「이미 있는지」를 먼저 본다.
# 이 판정에서 「민수」는 처음 보는 개체로 확정되고, **노드가 그 자리에서 생긴다.**
# 뒤늦게 정규화가 돌아도 이미 갈라진 노드를 되돌리지는 못한다.
# 개체 식별(identity)을 확정하는 단계가 먼저 오면, 그 뒤의 정규화는 사후약방문이다.

# %%
def run_pipeline(candidates, normalize_first):
    """(노드 집합, 엣지 리스트, 단계별 로그) 를 돌려준다."""
    seen = set()      # 중복 판정에 쓰는 키 집합
    nodes = set()
    edges = []
    log = []

    for s, k, o in candidates:
        raw = (s, k, o)
        if normalize_first:
            # 1) 정규화가 먼저 → 2) 정규형끼리 중복 비교
            key = normalize(s, k, o)
        else:
            # 1) 중복 검사가 먼저 → 표면형 그대로 비교 (정규화는 이 판정 뒤)
            key = raw

        if key in seen:
            log.append((raw, "막힘 — 중복", None))
            continue

        seen.add(key)
        written = key if normalize_first else raw
        nodes.update({written[0], written[2]})
        edges.append(written)
        log.append((raw, "통과", written))

    return nodes, edges, log


def report(title, normalize_first):
    nodes, edges, log = run_pipeline(CANDIDATES, normalize_first)
    print(f"\n[{title}]")
    print(f"{'후보':<24}{'판정':<14}쓴 것")
    print("-" * 62)
    for raw, verdict, written in log:
        w = "" if written is None else f"{written[0]} -{written[1]}-> {written[2]}"
        print(f"{f'{raw[0]} -{raw[1]}-> {raw[2]}':<24}{verdict:<14}{w}")
    print(f"→ 노드 {len(nodes)}개 {sorted(nodes)}")
    print(f"→ 엣지 {len(edges)}개")
    return nodes, edges


nodes_a, edges_a = report("순서 A — 정규화 → 중복 검사", normalize_first=True)
nodes_b, edges_b = report("순서 B — 중복 검사 → 정규화", normalize_first=False)
# 출력:
#
# [순서 A — 정규화 → 중복 검사]
# 후보                      판정            쓴 것
# --------------------------------------------------------------
# 박민수 -이끔-> 결제팀           통과            박민수 -이끔-> 결제팀
# 이서연 -속함-> 결제팀           통과            이서연 -속함-> 결제팀
# 민수 -이끔-> 결제팀             막힘 — 중복
# 박민수 -관리-> 결제팀           막힘 — 중복
# 이서연 -속함-> 결제팀           막힘 — 중복
# PM -이끔-> 결제팀               막힘 — 중복
# 박민수 -이끔-> 결제팀           막힘 — 중복
# 이서연 -소속-> 결제팀           막힘 — 중복
# → 노드 3개 ['결제팀', '박민수', '이서연']
# → 엣지 2개
#
# [순서 B — 중복 검사 → 정규화]
# 후보                      판정            쓴 것
# --------------------------------------------------------------
# 박민수 -이끔-> 결제팀           통과            박민수 -이끔-> 결제팀
# 이서연 -속함-> 결제팀           통과            이서연 -속함-> 결제팀
# 민수 -이끔-> 결제팀             통과            민수 -이끔-> 결제팀
# 박민수 -관리-> 결제팀           통과            박민수 -관리-> 결제팀
# 이서연 -속함-> 결제팀           막힘 — 중복
# PM -이끔-> 결제팀               통과            PM -이끔-> 결제팀
# 박민수 -이끔-> 결제팀           막힘 — 중복
# 이서연 -소속-> 결제팀           통과            이서연 -소속-> 결제팀
# → 노드 5개 ['PM', '결제팀', '민수', '박민수', '이서연']
# → 엣지 6개


# %% [markdown]
# ## 3. 조회해 보면 차이가 드러난다
#
# 28장 예제 1의 「그래프를 열어 보니 박민수가 세 명이었습니다」가 바로 이것이다.
# 넣은 사실은 전부 **맞는 사실**이었는데도 답이 갈린다.

# %%
def leaders(edges, team="결제팀"):
    return sorted({s for s, k, o in edges if o == team and k in ("이끔", "관리", "리드")})


print("순서 A — «결제팀을 이끄는 사람»:", leaders(edges_a))
print("순서 B — «결제팀을 이끄는 사람»:", leaders(edges_b))
print()
print(f"노드 수: A {len(nodes_a)} vs B {len(nodes_b)}")
print(f"엣지 수: A {len(edges_a)} vs B {len(edges_b)}")
# 출력:
# 순서 A — «결제팀을 이끄는 사람»: ['박민수']
# 순서 B — «결제팀을 이끄는 사람»: ['PM', '민수', '박민수']
#
# 노드 수: A 3 vs B 5
# 엣지 수: A 2 vs B 6


# %% [markdown]
# ## 4. 왜 순서가 뒤바뀌면 못 잡나 — 동치관계로 보기
#
# 중복 검사는 두 후보가 «같은가»를 묻는 판정이다. 어떤 동등성 기준을 쓰느냐가 전부다.
#
# - 순서 B(중복이 먼저)가 쓰는 기준: 표면형이 글자 그대로 같은가
#
# $$x \sim_{\text{raw}} y \iff x = y$$
#
# - 순서 A(정규화가 먼저)가 쓰는 기준: 정규화 함수 $\nu$ 로 보낸 뒤 같은가
#
# $$x \sim_{\nu} y \iff \nu(x) = \nu(y)$$
#
# $\nu$ 는 멱등(idempotent)이고 여러 표면형을 하나로 뭉개므로 $\nu$ 는 단사가 아니다.
# 따라서 두 동치관계 사이에는 진부분집합 관계가 성립한다.
#
# $$\sim_{\text{raw}} \subsetneq \sim_{\nu}$$
#
# 즉 **표면형 비교가 잡는 중복은 정규형 비교가 잡는 중복의 부분집합**이다.
# 순서를 뒤집으면 그 차집합 $\sim_{\nu} \setminus \sim_{\text{raw}}$ 만큼이 통째로 새어 나간다.
#
# 상인 집합의 크기로도 같은 말을 할 수 있다. 후보 집합 $C$ 에 대해
#
# $$|\nu(C)| \le |C|$$
#
# 이고, 최종 노드 수는 순서 A가 $|\nu(C)|$ 쪽, 순서 B가 $|C|$ 쪽에 붙는다.
#
# 그리고 **되돌릴 수 없다**는 점이 핵심이다.
# 중복 검사는 개체의 identity를 확정하는 단계라서, 여기서 갈라진 노드는
# 나중에 정규화를 돌려도 자동으로 합쳐지지 않는다.
# 이미 두 노드에 각각 엣지가 붙어 버렸기 때문이다 (22장의 «되돌릴 수 없는 일»).

# %%
raw_pairs = set()
nu_pairs = set()
for i, x in enumerate(CANDIDATES):
    for y in CANDIDATES[i + 1:]:
        if x == y:
            raw_pairs.add((x, y))
        if normalize(*x) == normalize(*y):
            nu_pairs.add((x, y))

print(f"|~raw| 가 잡는 쌍: {len(raw_pairs)}")
print(f"|~nu|  가 잡는 쌍: {len(nu_pairs)}")
print(f"부분집합인가: {raw_pairs <= nu_pairs}")
print(f"새어 나가는 쌍(차집합): {len(nu_pairs - raw_pairs)}")
print(f"|C| = {len(set(CANDIDATES))}, |nu(C)| = {len({normalize(*t) for t in CANDIDATES})}")
# 출력:
# |~raw| 가 잡는 쌍: 2
# |~nu|  가 잡는 쌍: 12
# 부분집합인가: True
# 새어 나가는 쌍(차집합): 10
# |C| = 6, |nu(C)| = 2


# %% [markdown]
# ## 5. 별칭 비율을 올리면 격차가 어떻게 벌어지나
#
# 실무 그래프에서 별칭이 섞이는 비율 $p$ 는 도메인마다 다르다.
# $p$ 를 0에서 1까지 움직이면서 두 순서의 최종 노드 수를 재 본다.
#
# 사람 이름 $M$ 명, 각 사람마다 별칭 후보가 몇 개씩 있고,
# 트리플 $N$ 개를 뽑을 때 확률 $p$ 로 정규 이름 대신 별칭을 쓴다고 하자.
# 순서 A의 노드 수는 $p$ 와 무관하게 거의 평평하고,
# 순서 B는 $p$ 가 오를수록 별칭 노드가 쌓여 위로 벌어진다.

# %%
import random

PEOPLE = {f"P{i}": [f"P{i}-별칭{j}" for j in range(1, 4)] for i in range(1, 13)}
TEAMS = [f"T{i}" for i in range(1, 4)]
ALIAS_BIG = {a: p for p, al in PEOPLE.items() for a in al}


def sample_graph(p, n=400, seed=7):
    rng = random.Random(seed)
    out = []
    for _ in range(n):
        person = rng.choice(list(PEOPLE))
        name = rng.choice(PEOPLE[person]) if rng.random() < p else person
        out.append((name, "속함", rng.choice(TEAMS)))
    return out


def node_count(cands, normalize_first):
    seen, nodes = set(), set()
    for s, k, o in cands:
        norm = (ALIAS_BIG.get(s, s), k, o)
        key = norm if normalize_first else (s, k, o)
        if key in seen:
            continue
        seen.add(key)
        w = norm if normalize_first else (s, k, o)
        nodes.update({w[0], w[2]})
    return len(nodes)


ps = [i / 20 for i in range(21)]
curve_a = [node_count(sample_graph(p), True) for p in ps]
curve_b = [node_count(sample_graph(p), False) for p in ps]

for p in (0.0, 0.25, 0.5, 0.75, 1.0):
    cs = sample_graph(p)
    print(f"별칭 비율 {p:>4.0%}  →  순서 A 노드 {node_count(cs, True):>3}개, "
          f"순서 B 노드 {node_count(cs, False):>3}개")
# 출력:
# 별칭 비율   0%  →  순서 A 노드  15개, 순서 B 노드  15개
# 별칭 비율  25%  →  순서 A 노드  15개, 순서 B 노드  50개
# 별칭 비율  50%  →  순서 A 노드  15개, 순서 B 노드  51개
# 별칭 비율  75%  →  순서 A 노드  15개, 순서 B 노드  50개
# 별칭 비율 100%  →  순서 A 노드  15개, 순서 B 노드  39개


# %% [markdown]
# ## 6. 그림으로
#
# 왼쪽: 8개짜리 예제의 노드/엣지 수. 오른쪽: 별칭 비율에 따른 노드 수 곡선.
#
# 오른쪽 곡선에서 순서 A는 «진짜 개체 수»에 딱 붙어 평평하다.
# 순서 B는 $p$ 가 오르면 치솟다가 $p \to 1$ 근처에서 도로 내려온다.
# 별칭만 쓰이면 별칭끼리는 표면형이 같아져서 그때는 중복이 다시 걸리기 때문이다.
# 즉 **표면형이 섞일 때가 제일 위험하다.** 현실이 정확히 그 구간이다.

# %%
import plotly.graph_objects as go
from plotly.subplots import make_subplots

fig = make_subplots(
    rows=1, cols=2,
    subplot_titles=("예제 8개 후보의 결과", "별칭 비율 p 에 따른 노드 수"),
)

fig.add_trace(go.Bar(name="순서 A (정규화→중복)", x=["노드 수", "엣지 수"],
                     y=[len(nodes_a), len(edges_a)],
                     marker_color="#2E86AB",
                     text=[len(nodes_a), len(edges_a)], textposition="outside"),
              row=1, col=1)
fig.add_trace(go.Bar(name="순서 B (중복→정규화)", x=["노드 수", "엣지 수"],
                     y=[len(nodes_b), len(edges_b)],
                     marker_color="#D1495B",
                     text=[len(nodes_b), len(edges_b)], textposition="outside"),
              row=1, col=1)

fig.add_trace(go.Scatter(x=ps, y=curve_a, mode="lines",
                         name="순서 A (정규화→중복)",
                         line=dict(color="#2E86AB", width=3),
                         showlegend=False),
              row=1, col=2)
fig.add_trace(go.Scatter(x=ps, y=curve_b, mode="lines",
                         name="순서 B (중복→정규화)",
                         line=dict(color="#D1495B", width=3),
                         showlegend=False),
              row=1, col=2)
fig.add_hline(y=len(PEOPLE) + len(TEAMS), line_dash="dot", line_color="gray",
              annotation_text="진짜 개체 수", row=1, col=2)

fig.update_xaxes(title_text="별칭 비율 p", tickformat=".0%", row=1, col=2)
fig.update_yaxes(title_text="개수", row=1, col=1)
fig.update_yaxes(title_text="최종 노드 수", row=1, col=2)
fig.update_layout(
    title="정규화와 중복 검사의 순서가 그래프 크기를 갈라놓는다",
    barmode="group", template="plotly_white", height=460, width=1100,
)

_show(fig)

import os

fig.write_image(os.path.join(os.path.dirname(os.path.abspath(__file__)), "expy.png"),
                scale=2)
print("expy.png 저장 완료")
# 출력: expy.png 저장 완료


# %% [markdown]
# ## 7. 정리
#
# | | 순서 A (정규화 → 중복) | 순서 B (중복 → 정규화) |
# |---|---|---|
# | 「민수 -이끔-> 결제팀」 | 중복으로 막힘 | 통과 → 새 노드 «민수» |
# | 「박민수 -관리-> 결제팀」 | 중복으로 막힘 | 통과 → 엣지 중복 |
# | 최종 노드 | 3개 | 5개 |
# | 최종 엣지 | 2개 | 6개 |
# | 「결제팀을 이끄는 사람」 | 박민수 | PM, 민수, 박민수 |
#
# - 중복 검사는 **동등성 기준**에 전적으로 의존한다. 정규화가 그 기준을 만든다.
# - 기준을 만들기 «전»에 검사하면 $\sim_{\text{raw}}$ 로 재게 되고, 이건 $\sim_{\nu}$ 의 진부분집합이다.
# - 그래서 순서는 취향이 아니라 정확성 문제다. 정규화가 먼저다.
# - 그리고 한 번 갈라진 노드는 나중 정규화로 자동 복구되지 않는다.
#   쓰기 관문은 «막을 수 있을 때» 막아야 한다.
