# 필요 패키지: plotly, kaleido  (pip install plotly kaleido)
# kuzu 는 필요 없다. ex2_write_gate.py 의 그래프 저장소를 순수 파이썬 집합으로 대체했다.

# %% [markdown]
# # ex2_write_gate.py — 정규화가 있으면 중복 관문이 어떻게 작동하는가
#
# `ex2_write_gate.py` 는 후보 트리플을 관문 다섯 단계에 순서대로 흘린다.
#
# 1. **확신도** — `conf < 0.65` 면 버림
# 2. **정규화** — 막지 않고 «고친다». `ALIAS` 로 주어를, `CANON` 으로 관계 이름을 바꿔치기
# 3. **스키마** — `(관계, 주어타입, 목적어타입)` 이 허용 목록에 있나
# 4. **단일 값 충돌** — `이끔` 처럼 값이 하나뿐이어야 하는 관계에 다른 값이 이미 있나
# 5. **중복** — 같은 `(s, k, o)` 엣지가 이미 있나
#
# 핵심은 2번이 5번보다 **먼저** 돈다는 것이다. 중복 관문은 «같은 글자인가» 가 아니라
# «정규화 후 같은 것을 가리키는가» 를 묻게 된다.
#
# 후보 $i$ 의 판정을 $g(i)$ 라 하고 정규화 사상을 $\nu$ 라 하면, 중복 관문은
#
# $$ g_5(s, k, o) = \mathbf{1}\big[(\nu(s),\ \nu(k),\ o) \in E \big] $$
#
# 를 본다. $\nu$ 를 항등사상 $\nu = \mathrm{id}$ 로 두는 것(정규화 끄기)과
# 실제 별칭표로 두는 것의 차이가 이 노트의 전부다.

# %%
def _show(fig):
    try:
        from IPython import get_ipython
        if get_ipython() is not None:
            fig.show()
    except ImportError:
        pass


# ex2_write_gate.py 원본의 스키마·별칭표·후보 목록을 그대로 옮겼다.
TYPES = {"박민수": "Person", "민수": "Person", "PM": "Person",
         "이서연": "Person", "결제팀": "Team", "정산팀": "Team",
         "채식": "Pref", "매운맛": "Pref"}
ALLOWED = {("이끔", "Person", "Team"), ("속함", "Person", "Team"),
           ("선호", "Person", "Pref")}
SINGLE = {"이끔"}                                  # 팀장은 한 명
CANON = {"관리": "이끔", "리드": "이끔", "소속": "속함"}
ALIAS = {"민수": "박민수", "PM": "박민수"}

CANDIDATES = [
    ("박민수", "이끔", "결제팀", 0.94),
    ("이서연", "속함", "결제팀", 0.91),
    ("민수",   "이끔", "결제팀", 0.88),   # 같은 사람, 다른 이름
    ("이서연", "속함", "정산팀", 0.42),   # 확신도 낮음
    ("박민수", "이끔", "정산팀", 0.87),   # 확신 있게 틀림
    ("결제팀", "속함", "이서연", 0.92),   # 방향 뒤집힘
    ("박민수", "관리", "결제팀", 0.83),   # 같은 뜻, 다른 관계 이름
    ("이서연", "속함", "결제팀", 0.90),   # 글자 그대로 중복
    ("PM",     "이끔", "결제팀", 0.71),   # 또 다른 이름
    ("이서연", "선호", "매운맛", 0.86),
    ("박민수", "선호", "결제팀", 0.88),   # 타입 오류
]

MIN_CONF = 0.65

print(f"후보 {len(CANDIDATES)}개, MIN_CONF={MIN_CONF}")
print(f"ALIAS={ALIAS}")
print(f"CANON={CANON}")
# 출력: 후보 11개, MIN_CONF=0.65
# 출력: ALIAS={'민수': '박민수', 'PM': '박민수'}
# 출력: CANON={'관리': '이끔', '리드': '이끔', '소속': '속함'}

# %% [markdown]
# ## 관문 다섯 단계를 순수 파이썬으로
#
# 원본은 kuzu 에 질의하지만, 여기서는 이미 쓴 엣지를 `set` 에 담아 같은 판정을 낸다.
# `normalize` 인자로 2번 관문만 켜고 끌 수 있게 했다.

# %%
def gate(edges, s, k, o, conf, normalize=True):
    """관문 다섯. 걸리면 (False, 관문이름), 통과하면 (True, 정규화된 트리플)."""
    # 1) 확신도
    if conf < MIN_CONF:
        return False, "1.확신도"
    # 2) 이름 정규화 — 막지 않고 «고친다»
    if normalize:
        s = ALIAS.get(s, s)
        k = CANON.get(k, k)
    # 3) 스키마
    ts, to = TYPES.get(s), TYPES.get(o)
    if (k, ts, to) not in ALLOWED:
        return False, "3.스키마"
    # 4) 단일 값 충돌 — 이미 다른 값이 있나
    if k in SINGLE:
        for (es, ek, eo) in edges:
            if es == s and ek == k and eo != o:
                return False, "4.단일값충돌"
    # 5) 중복 — 정규화된 이름으로 본다
    if (s, k, o) in edges:
        return False, "5.중복"
    return True, (s, k, o)


def run(normalize=True, verbose=True):
    """후보 전부를 흘리고 (판정목록, 관문별 건수, 최종 엣지집합) 을 돌려준다."""
    edges, rows, caught = [], [], {}
    if verbose:
        head = "정규화 켬" if normalize else "정규화 끔"
        print(f"=== {head} ===")
        print(f"{'후보':<24}{'확신':>6}  판정")
        print("-" * 58)
    for s, k, o, conf in CANDIDATES:
        ok, why = gate(edges, s, k, o, conf, normalize)
        if ok:
            edges.append(why)
            fixed = "  (정규화됨)" if (why[0], why[1]) != (s, k) else ""
            verdict, key = f"통과{fixed}", "0.통과"
        else:
            verdict, key = f"막힘 — {why}", why
        caught[key] = caught.get(key, 0) + 1
        rows.append((s, k, o, conf, key))
        if verbose:
            label = f"{s} -{k}-> {o}"
            # 한글 폭 보정 없이 대략 정렬
            print(f"{label:<24}{conf:>6.2f}  {verdict}")
    return rows, caught, edges


rows_on, caught_on, edges_on = run(normalize=True)
# 출력: === 정규화 켬 ===
# 출력: 후보                          확신  판정
# 출력: ----------------------------------------------------------
# 출력: 박민수 -이끔-> 결제팀             0.94  통과
# 출력: 이서연 -속함-> 결제팀             0.91  통과
# 출력: 민수 -이끔-> 결제팀              0.88  막힘 — 5.중복
# 출력: 이서연 -속함-> 정산팀             0.42  막힘 — 1.확신도
# 출력: 박민수 -이끔-> 정산팀             0.87  막힘 — 4.단일값충돌
# 출력: 결제팀 -속함-> 이서연             0.92  막힘 — 3.스키마
# 출력: 박민수 -관리-> 결제팀             0.83  막힘 — 5.중복
# 출력: 이서연 -속함-> 결제팀             0.90  막힘 — 5.중복
# 출력: PM -이끔-> 결제팀              0.71  막힘 — 5.중복
# 출력: 이서연 -선호-> 매운맛             0.86  통과
# 출력: 박민수 -선호-> 결제팀             0.88  막힘 — 3.스키마

# %% [markdown]
# 「민수」·「PM」은 2번에서 «박민수»가 되고, 「관리」는 «이끔»이 된다.
# 셋 다 결국 `박민수 -이끔-> 결제팀` 이라는 **하나의 엣지**로 수렴해서
# 5번 중복 관문에 나란히 걸린다.

# %%
rows_off, caught_off, edges_off = run(normalize=False)
# 출력: === 정규화 끔 ===
# 출력: 후보                          확신  판정
# 출력: ----------------------------------------------------------
# 출력: 박민수 -이끔-> 결제팀             0.94  통과
# 출력: 이서연 -속함-> 결제팀             0.91  통과
# 출력: 민수 -이끔-> 결제팀              0.88  통과            ← 정규화 켬에서는 5.중복
# 출력: 이서연 -속함-> 정산팀             0.42  막힘 — 1.확신도
# 출력: 박민수 -이끔-> 정산팀             0.87  막힘 — 4.단일값충돌
# 출력: 결제팀 -속함-> 이서연             0.92  막힘 — 3.스키마
# 출력: 박민수 -관리-> 결제팀             0.83  막힘 — 3.스키마   ← 맞는 사실인데 억울하게 떨어짐
# 출력: 이서연 -속함-> 결제팀             0.90  막힘 — 5.중복
# 출력: PM -이끔-> 결제팀              0.71  통과            ← 정규화 켬에서는 5.중복
# 출력: 이서연 -선호-> 매운맛             0.86  통과
# 출력: 박민수 -선호-> 결제팀             0.88  막힘 — 3.스키마

# %% [markdown]
# ## 판정이 갈린 후보만 뽑아 보기

# %%
print(f"{'후보':<24}{'정규화 켬':<16}{'정규화 끔'}")
print("-" * 58)
for (s, k, o, conf, key_on), (_, _, _, _, key_off) in zip(rows_on, rows_off):
    if key_on != key_off:
        print(f"{f'{s} -{k}-> {o}':<24}{key_on:<16}{key_off}")
# 출력: 후보                      정규화 켬           정규화 끔
# 출력: ----------------------------------------------------------
# 출력: 민수 -이끔-> 결제팀            5.중복            0.통과
# 출력: 박민수 -관리-> 결제팀           5.중복            3.스키마
# 출력: PM -이끔-> 결제팀            5.중복            0.통과

# %% [markdown]
# 세 건만 갈린다. 그런데 그 셋이 그래프의 모양을 통째로 바꾼다.

# %%
def summarize(name, caught, edges):
    nodes = sorted({n for (s, _, o) in edges for n in (s, o)})
    leaders = sorted({s for (s, k, _) in edges if k == "이끔"})
    print(f"[{name}]")
    print(f"  관문별 건수: { {k: v for k, v in sorted(caught.items())} }")
    print(f"  쓴 엣지 {len(edges)}개 / 후보 {len(CANDIDATES)}개")
    for e in edges:
        print(f"    {e[0]} -{e[1]}-> {e[2]}")
    print(f"  연결된 노드 {len(nodes)}개: {nodes}")
    print(f"  «결제팀을 이끄는 사람» {len(leaders)}명: {leaders}")
    return len(edges), len(nodes), len(leaders)


on_stats = summarize("정규화 켬", caught_on, edges_on)
print()
off_stats = summarize("정규화 끔", caught_off, edges_off)
# 출력: [정규화 켬]
# 출력:   관문별 건수: {'0.통과': 3, '1.확신도': 1, '3.스키마': 2, '4.단일값충돌': 1, '5.중복': 4}
# 출력:   쓴 엣지 3개 / 후보 11개
# 출력:     박민수 -이끔-> 결제팀
# 출력:     이서연 -속함-> 결제팀
# 출력:     이서연 -선호-> 매운맛
# 출력:   연결된 노드 4개: ['결제팀', '매운맛', '박민수', '이서연']
# 출력:   «결제팀을 이끄는 사람» 1명: ['박민수']
# 출력:
# 출력: [정규화 끔]
# 출력:   관문별 건수: {'0.통과': 5, '1.확신도': 1, '3.스키마': 3, '4.단일값충돌': 1, '5.중복': 1}
# 출력:   쓴 엣지 5개 / 후보 11개
# 출력:     박민수 -이끔-> 결제팀
# 출력:     이서연 -속함-> 결제팀
# 출력:     민수 -이끔-> 결제팀
# 출력:     PM -이끔-> 결제팀
# 출력:     이서연 -선호-> 매운맛
# 출력:   연결된 노드 6개: ['PM', '결제팀', '매운맛', '민수', '박민수', '이서연']
# 출력:   «결제팀을 이끄는 사람» 3명: ['PM', '민수', '박민수']

# %% [markdown]
# ## 읽어야 할 두 가지
#
# - **중복 관문이 잡는 건수가 $4 \to 1$ 로 떨어진다.** 중복 검사 코드는 한 글자도
#   안 바꿨는데 잡는 능력이 사라진다. 관문의 성능이 자기 코드가 아니라
#   **앞 단계의 출력**에 달려 있다는 뜻이다.
# - **스키마가 잡는 건수는 $2 \to 3$ 으로 늘어난다.** 그런데 늘어난 1건
#   (`박민수 -관리-> 결제팀`) 은 *맞는 사실*이다. 「잡은 수가 늘었다」가
#   「더 잘 걸렀다」를 뜻하지 않는다.
#
# 그리고 결정적으로 「결제팀을 이끄는 사람」이 $1 \to 3$ 명이 된다.
# 28.1 절 `ex1_write_loop.py` 의 «박민수가 세 명» 상태로 되돌아간 것이다.

# %% [markdown]
# ## 순서를 뒤집으면 — 정규화를 중복 뒤로 보내면
#
# 원문이 못 박는 부분. 중복 검사를 정규화 **앞에** 두면 「민수」로 조회하는데
# 그래프에는 「박민수」 엣지만 있으니 중복이 안 걸린다. 통과시킨 다음에야
# 「박민수」로 고쳐 쓰므로 **노드는 하나인데 엣지가 겹쳐 쌓인다**.

# %%
def gate_swapped(edges, s, k, o, conf):
    """중복(5) 을 정규화(2) 앞으로 옮긴 잘못된 순서."""
    if conf < MIN_CONF:
        return False, "1.확신도"
    if (s, k, o) in edges:                    # 정규화 «전» 이름으로 중복 검사
        return False, "5.중복"
    s = ALIAS.get(s, s)
    k = CANON.get(k, k)
    ts, to = TYPES.get(s), TYPES.get(o)
    if (k, ts, to) not in ALLOWED:
        return False, "3.스키마"
    if k in SINGLE:
        for (es, ek, eo) in edges:
            if es == s and ek == k and eo != o:
                return False, "4.단일값충돌"
    return True, (s, k, o)


edges_swapped = []
for s, k, o, conf in CANDIDATES:
    ok, why = gate_swapped(edges_swapped, s, k, o, conf)
    if ok:
        edges_swapped.append(why)

from collections import Counter
dup = Counter(edges_swapped)
print(f"뒤집은 순서: 엣지 {len(edges_swapped)}개")
for e, n in dup.items():
    mark = f"   ← {n}겹 중복!" if n > 1 else ""
    print(f"  {e[0]} -{e[1]}-> {e[2]}  x{n}{mark}")
# 출력: 뒤집은 순서: 엣지 6개
# 출력:   박민수 -이끔-> 결제팀  x4   ← 4겹 중복!
# 출력:   이서연 -속함-> 결제팀  x1
# 출력:   이서연 -선호-> 매운맛  x1

# %% [markdown]
# 「민수」·「PM」뿐 아니라 「관리」까지 통과해서 `박민수 -이끔-> 결제팀` 이
# **네 겹**으로 쌓인다. 노드는 하나로 합쳐졌는데 엣지가 중복된, 원본보다 나쁜 상태다.
# (`이서연 -속함-> 결제팀` 중복만 글자가 똑같아서 걸린다.)
#
# 정규화의 «위치» 에 따라 결과가 셋으로 갈린다.
#
# | 배치 | 사람 노드 | 엣지 | 결과 |
# |---|---|---|---|
# | 정규화 → 중복 (원본) | 박민수 1 | 3 | 깨끗함 |
# | 정규화 없음 | 박민수/민수/PM 3 | 5 | 사람이 셋으로 쪼개짐 |
# | 중복 → 정규화 (뒤집음) | 박민수 1 | 6 | 같은 엣지가 4겹 |

# %% [markdown]
# ## 관문별 판정 건수 비교 (정규화 on / off)

# %%
import os
import plotly.graph_objects as go

ORDER = ["0.통과", "1.확신도", "3.스키마", "4.단일값충돌", "5.중복"]
LABEL = {"0.통과": "통과(기록됨)", "1.확신도": "1.확신도",
         "3.스키마": "3.스키마", "4.단일값충돌": "4.단일값충돌", "5.중복": "5.중복"}
x = [LABEL[k] for k in ORDER]
y_on = [caught_on.get(k, 0) for k in ORDER]
y_off = [caught_off.get(k, 0) for k in ORDER]
print(f"정규화 켬: {dict(zip(ORDER, y_on))}")
print(f"정규화 끔: {dict(zip(ORDER, y_off))}")
# 출력: 정규화 켬: {'0.통과': 3, '1.확신도': 1, '3.스키마': 2, '4.단일값충돌': 1, '5.중복': 4}
# 출력: 정규화 끔: {'0.통과': 5, '1.확신도': 1, '3.스키마': 3, '4.단일값충돌': 1, '5.중복': 1}

fig = go.Figure()
fig.add_bar(x=x, y=y_on, name="정규화 켬 (원본)",
            marker_color="#2f6f9f",
            text=y_on, textposition="outside")
fig.add_bar(x=x, y=y_off, name="정규화 끔",
            marker_color="#d08a3e",
            text=y_off, textposition="outside")
fig.update_layout(
    title=("ex2_write_gate.py — 관문별 판정 건수 (후보 11개)<br>"
           "<sub>정규화를 끄면 중복 4→1 로 무력화되고, 결제팀 리더가 1명→3명이 된다</sub>"),
    barmode="group",
    xaxis_title="관문",
    yaxis_title="건수",
    yaxis=dict(range=[0, 6.2]),
    template="simple_white",
    legend=dict(orientation="h", yanchor="bottom", y=1.0, xanchor="right", x=1),
    width=860, height=520,
    margin=dict(t=110, b=60),
)
fig.add_annotation(x="5.중복", y=4, ax=0, ay=-52, showarrow=True, arrowhead=2,
                   text="민수·PM·관리 가 정규화 뒤<br>같은 엣지로 수렴해 여기서 걸린다",
                   font=dict(size=11), align="center")
_show(fig)

_png = os.path.join(os.path.dirname(os.path.abspath(__file__)), "expy.png")
fig.write_image(_png, scale=2)
print(f"saved: {_png}")
# 출력: saved: .../94755008-5131-4764-9d73-3186b6aa0340/expy.png

# %% [markdown]
# ## 한 줄 정리
#
# 정규화는 아무것도 막지 않지만, 뒤에 오는 중복 관문의 **비교 대상을 문자열에서
# 실체로 바꿔 놓는다**. 그래서 「민수」·「PM」·「관리」가 전부
# `박민수 -이끔-> 결제팀` 하나로 수렴해 중복으로 걸린다.
# 정규화를 빼면 이 셋이 통과해 노드가 셋으로 갈라지고,
# 정규화를 중복 뒤로 미루면 노드는 하나여도 엣지가 세 겹으로 쌓인다.
