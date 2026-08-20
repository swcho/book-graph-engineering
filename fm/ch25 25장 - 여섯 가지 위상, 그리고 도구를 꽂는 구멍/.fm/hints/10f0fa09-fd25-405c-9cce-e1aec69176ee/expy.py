# %% [markdown]
# # `ex5_tool_selection.py` — 설명만 바꿔서 무엇이 달라졌나
#
# **카드 질문**: `ex5_tool_selection.py`에서 설명만 바꿔 무엇이 달라졌는가?
#
# **카드 답**: 코드를 한 줄도 고치지 않고 도구 선택 정확도가 올랐다.
# 짧은 설명 대신 '언제 쓰나 / 언제 안 쓰나'를 넣은 설명을 썼다.
#
# 이 노트북은 원본 예제의 **단어 겹침 선택기**와 **질문 8개**를 그대로 재현해서,
# 「설명 텍스트가 곧 코드」라는 주장을 **숫자로** 확인한다.
#
# 실험 설계:
#
# - 고정: 선택기 함수 `choose`, 질문 세트 `QUERIES`, 도구 이름 3개
# - 변수: 도구 **설명 문자열**만 (`BAD` → `GOOD`)
# - 측정: 질문별 정오표, 정확도, 정확도 델타
#
# 선택기는 이렇게 정의된다. $q$ 는 질문의 토큰 집합, $d_t$ 는 도구 $t$ 설명의 토큰 집합.
#
# $$\hat{t}(q) = \arg\max_{t \in T} \; \bigl| q \cap d_t \bigr|$$
#
# 동점이면 **먼저 순회한 도구**가 이긴다(원본 코드가 `overlap > score` 로 비교하므로).
# 이 동점 규칙이 뒤에서 아주 중요해진다.
#
# 필요 패키지: plotly, kaleido (PNG 저장용)

# %%
import re

import plotly.graph_objects as go
from plotly.subplots import make_subplots


def _show(fig):
    try:
        from IPython import get_ipython
        if get_ipython() is not None:  # VSCode 셀/Jupyter에서만 렌더링
            fig.show()
    except ImportError:
        pass


KFONT = "Apple SD Gothic Neo, AppleGothic, Malgun Gothic, NanumGothic, sans-serif"
print("준비 완료")
# 출력: 준비 완료

# %% [markdown]
# ## 1. 원본 예제 그대로 옮기기
#
# 질문 8개와 정답 도구, 그리고 두 가지 설명 세트.
# `BAD` 는 「사람 조회」처럼 명사 두 개, `GOOD` 은 (1) 무엇을 주는지 (2) 어떤 말로 묻는지
# (3) 언제 안 쓰는지 셋을 담았다.

# %%
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

BAD = {
    "find_person": "사람 조회",
    "chain_of_command": "체인 조회",
    "team_members": "팀 조회",
}

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

TOOLS = list(BAD)
print("도구", TOOLS)
print("질문 수", len(QUERIES))
print("BAD 설명 총 글자수 ", sum(len(v) for v in BAD.values()))
print("GOOD 설명 총 글자수", sum(len(v) for v in GOOD.values()))
# 출력: 도구 ['find_person', 'chain_of_command', 'team_members']
# 출력: 질문 수 8
# 출력: BAD 설명 총 글자수  14
# 출력: GOOD 설명 총 글자수 206

# %% [markdown]
# ## 2. 선택기 — 코드는 여기서 끝, 그리고 절대 안 고친다
#
# 원본 `tokenize` / `choose` 를 한 글자도 바꾸지 않고 옮긴다.
# 다만 실험을 위해 도구별 점수를 함께 돌려주는 얇은 래퍼 `scores` 를 붙인다.
# (래퍼는 관측용이고, 판정 로직은 `choose` 그대로다.)

# %%
def tokenize(s):
    return set(re.findall(r"[가-힣A-Za-z]+", s))


def choose(query, descriptions):
    q = tokenize(query)
    best, score = None, -1
    for name, desc in descriptions.items():
        overlap = len(q & tokenize(desc))
        if overlap > score:
            best, score = name, overlap
    return best


def scores(query, descriptions):
    """관측용: 도구별 겹침 점수 dict."""
    q = tokenize(query)
    return {name: len(q & tokenize(desc)) for name, desc in descriptions.items()}


def evaluate(descriptions):
    """질문별 (선택, 정답, 정오, 점수표) 와 정확도."""
    rows, hit = [], 0
    for q, want in QUERIES:
        got = choose(q, descriptions)
        sc = scores(q, descriptions)
        ok = got == want
        hit += ok
        rows.append({"q": q, "want": want, "got": got, "ok": ok, "scores": sc})
    return rows, hit / len(QUERIES)


bad_rows, bad_acc = evaluate(BAD)
good_rows, good_acc = evaluate(GOOD)
print(f"BAD  정확도 {bad_acc:.0%}")
print(f"GOOD 정확도 {good_acc:.0%}")
# 출력: BAD  정확도 38%
# 출력: GOOD 정확도 88%

# %% [markdown]
# ## 3. 질문별 정오표 — 무엇이 어떻게 바뀌었나
#
# 원본 실행 결과와 같은 표를 나란히 놓는다. 옆에 각 도구가 받은 겹침 점수도 적었다.

# %%
def fmt_scores(sc):
    return " ".join(f"{n.split('_')[0]}:{v}" for n, v in sc.items())


print(f"{'질문':<22}{'정답':<18}{'BAD 선택':<18}{'GOOD 선택':<18}변화")
print("-" * 90)
flips = []
for b, g in zip(bad_rows, good_rows):
    if not b["ok"] and g["ok"]:
        change = "고쳐짐"
    elif b["ok"] and not g["ok"]:
        change = "깨짐"
    elif b["ok"]:
        change = "그대로 맞음"
    else:
        change = "그대로 틀림"
    flips.append(change)
    print(f"{b['q']:<22}{b['want']:<18}"
          f"{b['got'] + ('' if b['ok'] else '✗'):<18}"
          f"{g['got'] + ('' if g['ok'] else '✗'):<18}{change}")

print()
print(f"정확도 {bad_acc:.0%} → {good_acc:.0%}  (델타 +{good_acc - bad_acc:.0%})")
print(f"맞춘 개수 {sum(r['ok'] for r in bad_rows)}/8 → {sum(r['ok'] for r in good_rows)}/8")
print("고쳐짐", flips.count("고쳐짐"), "| 깨짐", flips.count("깨짐"),
      "| 그대로 틀림", flips.count("그대로 틀림"))
# 출력: 질문                    정답                BAD 선택           GOOD 선택          변화
# 출력: ------------------------------------------------------------------------------------------
# 출력: 김지훈이 누구야               find_person       find_person       find_person       그대로 맞음
# 출력: 김지훈 위로 누가 있어           chain_of_command  find_person✗      chain_of_command  고쳐짐
# 출력: 결제팀에 누구누구 있어           team_members      find_person✗      team_members      고쳐짐
# 출력: 박민수 상급자 알려줘            chain_of_command  find_person✗      find_person✗      그대로 틀림
# 출력: 이서연 찾아줘                find_person       find_person       find_person       그대로 맞음
# 출력: 결제팀 명단                 team_members      find_person✗      team_members      고쳐짐
# 출력: 김지훈 보고 라인 전체           chain_of_command  find_person✗      chain_of_command  고쳐짐
# 출력: 이서연 정보                 find_person       find_person       find_person       그대로 맞음
# 출력:
# 출력: 정확도 38% → 88%  (델타 +50%)
# 출력: 맞춘 개수 3/8 → 7/8
# 출력: 고쳐짐 4 | 깨짐 0 | 그대로 틀림 1

# %% [markdown]
# ## 4. BAD 가 맞춘 3개는 실력이 아니다 — 전부 0점 동점
#
# 여기가 이 예제의 진짜 핵심이다.
# `BAD` 설명(「사람 조회」/「체인 조회」/「팀 조회」)은 어떤 질문과도 단어가 **하나도** 겹치지 않는다.
# 즉 모든 도구가 0점 동점이고, `overlap > score` 라는 엄격 비교 때문에
# **딕셔너리에서 먼저 나온 도구**가 항상 이긴다.
#
# 그러니까 `BAD` 의 38% 는 「선택」이 아니라 **첫 키를 고정 반환하는 상수 함수**의 점수다.
# 정확도는 그 키가 정답에 몇 번 등장하느냐로만 결정된다 — 최빈 클래스 베이스라인.

# %%
print("BAD 점수표 (전부 0인지 확인)")
for r in bad_rows:
    print(f"  {r['q']:<22}{fmt_scores(r['scores'])}   → {r['got']}")

all_zero = all(max(r["scores"].values()) == 0 for r in bad_rows)
print(f"\n모든 질문에서 최고점이 0점인가? {all_zero}")
print(f"BAD 가 고른 도구 종류: {set(r['got'] for r in bad_rows)}")
# 출력: BAD 점수표 (전부 0인지 확인)
# 출력:   김지훈이 누구야               find:0 chain:0 team:0   → find_person
# 출력:   김지훈 위로 누가 있어           find:0 chain:0 team:0   → find_person
# 출력:   결제팀에 누구누구 있어           find:0 chain:0 team:0   → find_person
# 출력:   박민수 상급자 알려줘            find:0 chain:0 team:0   → find_person
# 출력:   이서연 찾아줘                find:0 chain:0 team:0   → find_person
# 출력:   결제팀 명단                 find:0 chain:0 team:0   → find_person
# 출력:   김지훈 보고 라인 전체           find:0 chain:0 team:0   → find_person
# 출력:   이서연 정보                 find:0 chain:0 team:0   → find_person
# 출력:
# 출력: 모든 질문에서 최고점이 0점인가? True
# 출력: BAD 가 고른 도구 종류: {'find_person'}

# %%
# 증명: BAD 의 키 순서만 바꿔도 «정확도»가 흔들린다. 설명이 정보를 안 주면 순서가 답을 정한다.
import itertools

print("BAD 딕셔너리 키 순서를 바꿔 본다 (설명 내용은 동일)")
for order in itertools.permutations(TOOLS):
    reordered = {k: BAD[k] for k in order}
    _, acc = evaluate(reordered)
    print(f"  첫 키 {order[0]:<18} 정확도 {acc:.0%}")
# 출력: BAD 딕셔너리 키 순서를 바꿔 본다 (설명 내용은 동일)
# 출력:   첫 키 find_person        정확도 38%
# 출력:   첫 키 find_person        정확도 38%
# 출력:   첫 키 chain_of_command   정확도 38%
# 출력:   첫 키 chain_of_command   정확도 38%
# 출력:   첫 키 team_members       정확도 25%
# 출력:   첫 키 team_members       정확도 25%

# %% [markdown]
# 25~38% 사이에서 진동한다. 정답 분포가 `find_person` 3개, `chain_of_command` 3개,
# `team_members` 2개이므로 정확히 「첫 키가 정답인 질문 수 / 8」이다.
#
# 반대로 `GOOD` 은 8개 질문 중 몇 개에서 **결정적 신호**(최고점 > 0)를 만들어 냈는지 세어 보자.

# %%
decisive_good = [r for r in good_rows if max(r["scores"].values()) > 0]
print(f"GOOD 에서 최고점 > 0 인 질문: {len(decisive_good)}/8")
for r in good_rows:
    top = max(r["scores"].values())
    tag = "결정적" if top > 0 else "0점 동점 → 첫 키로 추락"
    print(f"  {r['q']:<22}{fmt_scores(r['scores'])}   {tag}")
# 출력: GOOD 에서 최고점 > 0 인 질문: 4/8
# 출력:   김지훈이 누구야               find:0 chain:0 team:0   0점 동점 → 첫 키로 추락
# 출력:   김지훈 위로 누가 있어           find:0 chain:1 team:0   결정적
# 출력:   결제팀에 누구누구 있어           find:0 chain:0 team:1   결정적
# 출력:   박민수 상급자 알려줘            find:0 chain:0 team:0   0점 동점 → 첫 키로 추락
# 출력:   이서연 찾아줘                find:0 chain:0 team:0   0점 동점 → 첫 키로 추락
# 출력:   결제팀 명단                 find:0 chain:0 team:1   결정적
# 출력:   김지훈 보고 라인 전체           find:0 chain:2 team:0   결정적
# 출력:   이서연 정보                 find:0 chain:0 team:0   0점 동점 → 첫 키로 추락

# %% [markdown]
# 흥미로운 사실. `GOOD` 도 8개 중 4개는 여전히 0점 동점이고, 그 4개가 마침
# 정답이 `find_person` 인 3개 + 아직 못 고친 1개다. 즉 88% 는
# **「진짜 고른 4개」 + 「첫 키 추락이 우연히 맞은 3개」** 의 합이다.
#
# 그래서 정확도만 보면 안 되고 **결정 마진**(최고점 − 2등 점수)을 봐야 한다.
# 마진이 0이면 선택기는 아무것도 «고르지» 않았다.

# %%
def margin(r):
    vals = sorted(r["scores"].values(), reverse=True)
    return vals[0] - vals[1]


print(f"{'질문':<22}{'BAD 마진':>10}{'GOOD 마진':>11}")
print("-" * 45)
for b, g in zip(bad_rows, good_rows):
    print(f"{b['q']:<22}{margin(b):>10}{margin(g):>11}")
print("-" * 45)
print(f"{'평균':<22}{sum(margin(r) for r in bad_rows) / 8:>10.2f}"
      f"{sum(margin(r) for r in good_rows) / 8:>11.2f}")
# 출력: 질문                      BAD 마진   GOOD 마진
# 출력: ---------------------------------------------
# 출력: 김지훈이 누구야                        0          0
# 출력: 김지훈 위로 누가 있어                    0          1
# 출력: 결제팀에 누구누구 있어                    0          1
# 출력: 박민수 상급자 알려줘                     0          0
# 출력: 이서연 찾아줘                         0          0
# 출력: 결제팀 명단                          0          1
# 출력: 김지훈 보고 라인 전체                    0          2
# 출력: 이서연 정보                          0          0
# 출력: ---------------------------------------------
# 출력: 평균                              0.00       0.62

# %% [markdown]
# ## 5. 남은 하나 — 「박민수 상급자 알려줘」
#
# 설명에는 «상사»라고 썼는데 사용자는 «상급자»라고 물었다. 토큰이 안 겹친다.
# 사내 용어로 쓰고 사용자는 자기 말로 묻는, 도구 설명에서 제일 흔한 실패다.
#
# 대응은 **동의어를 설명에 넣는 것**. 여전히 코드는 안 고친다.

# %%
BETTER = dict(GOOD)
BETTER["chain_of_command"] = (
    "한 사람의 «위로 올라가는» 보고 체계를 뿌리까지 준다. "
    "상사, 상급자, 윗사람, 상사의 상사, 보고 라인, 결재선, 결재 라인을 물으면 이것이다. "
    "아래 부하 목록에는 쓰지 않는다."
)
BETTER["find_person"] = (
    "사람 «한 명»을 이름으로 찾는다. 이름, 소속 팀, 상사 아이디, 정보를 준다. "
    "누구야, 찾아줘, 정보, 프로필을 물으면 이것이다. "
    "여러 명을 찾을 때는 쓰지 않는다."
)

better_rows, better_acc = evaluate(BETTER)
for r in better_rows:
    print(f"  {r['q']:<22}{r['got']:<18}{'' if r['ok'] else '←틀림'}  "
          f"마진 {margin(r)}")
print(f"\nBETTER 정확도 {better_acc:.0%}, 평균 마진 "
      f"{sum(margin(r) for r in better_rows) / 8:.2f}")
print(f"\n요약: {bad_acc:.0%} → {good_acc:.0%} → {better_acc:.0%}  "
      "(선택기 코드 변경량 0줄)")
# 출력:   김지훈이 누구야               find_person         마진 1
# 출력:   김지훈 위로 누가 있어           chain_of_command    마진 1
# 출력:   결제팀에 누구누구 있어           team_members        마진 1
# 출력:   박민수 상급자 알려줘            chain_of_command    마진 1
# 출력:   이서연 찾아줘                find_person         마진 1
# 출력:   결제팀 명단                 team_members        마진 1
# 출력:   김지훈 보고 라인 전체           chain_of_command    마진 2
# 출력:   이서연 정보                 find_person         마진 1
# 출력:
# 출력: BETTER 정확도 100%, 평균 마진 1.12
# 출력:
# 출력: 요약: 38% → 88% → 100%  (선택기 코드 변경량 0줄)

# %% [markdown]
# ## 6. 시각화
#
# 왼쪽: 세 설명 세트의 정확도. 오른쪽 위: 질문별 정오 히트맵.
# 오른쪽 아래: 질문별 결정 마진 (0이면 「안 고른 것」).

# %%
SETS = [("BAD\n짧은 설명", bad_rows, bad_acc),
        ("GOOD\n언제 쓰나/안 쓰나", good_rows, good_acc),
        ("BETTER\n+동의어", better_rows, better_acc)]
labels = [s[0].replace("\n", "<br>") for s in SETS]
qlabels = [q for q, _ in QUERIES]

fig = make_subplots(
    rows=2, cols=2,
    column_widths=[0.32, 0.68], row_heights=[0.5, 0.5],
    specs=[[{"type": "bar", "rowspan": 2}, {"type": "heatmap"}],
           [None, {"type": "bar"}]],
    subplot_titles=("설명 세트별 정확도 (코드 동일)",
                    "질문별 정오 (초록=맞음, 빨강=틀림)",
                    "질문별 결정 마진 (0 = 동점 추락)"),
    horizontal_spacing=0.11, vertical_spacing=0.20,
)
COLORS = ["#d94f4f", "#3d8bd4", "#3faa6a"]

# (1) 정확도 막대
fig.add_trace(go.Bar(
    x=labels, y=[s[2] * 100 for s in SETS],
    text=[f"{s[2]:.0%}<br>{sum(r['ok'] for r in s[1])}/8" for s in SETS],
    textposition="outside",
    marker_color=COLORS,
    showlegend=False,
), row=1, col=1)
fig.update_yaxes(title_text="정확도 (%)", range=[0, 118], row=1, col=1)

# (2) 정오 히트맵
z = [[1 if r["ok"] else 0 for r in s[1]] for s in SETS]
fig.add_trace(go.Heatmap(
    z=z, x=qlabels, y=labels,
    colorscale=[[0.0, "#e8a0a0"], [1.0, "#8fd0a8"]],
    showscale=False, xgap=3, ygap=3,
    text=[["O" if v else "X" for v in row] for row in z],
    texttemplate="%{text}",
    textfont={"size": 15, "color": "#222"},
), row=1, col=2)
fig.update_xaxes(showticklabels=False, row=1, col=2)  # 아래 서브플롯과 라벨 공유

# (3) 마진 그룹 막대
for (lab, rows_, _), c in zip(SETS, COLORS):
    fig.add_trace(go.Bar(
        name=lab.replace("\n", " "), x=qlabels,
        y=[margin(r) for r in rows_], marker_color=c,
    ), row=2, col=2)
fig.update_yaxes(title_text="최고점 − 2등 점수", row=2, col=2)
fig.update_xaxes(tickangle=-28, row=2, col=2)

fig.update_layout(
    title_text="설명만 바꿨다 — ex5_tool_selection.py 재현 (38% → 88% → 100%)",
    barmode="group", height=760, width=1280,
    font={"family": KFONT, "size": 13},
    template="plotly_white",
    legend={"orientation": "h", "y": -0.16, "x": 0.42},
    margin={"t": 90, "b": 110},
)
for a in fig.layout.annotations:
    a.font.family = KFONT

_show(fig)

import os
_png = os.path.join(os.path.dirname(os.path.abspath(__file__)), "expy.png")
fig.write_image(_png, scale=2)
print("저장:", _png)
# 출력: 저장: .../10f0fa09-fd25-405c-9cce-e1aec69176ee/expy.png

# %% [markdown]
# ## 7. 이 카드에서 가져갈 것
#
# | 항목 | BAD | GOOD | BETTER |
# |---|---|---|---|
# | 설명 총 글자수 | 14 | 206 | 256 |
# | 선택기 코드 줄 수 변화 | — | **0** | **0** |
# | 정확도 | 38% (3/8) | 88% (7/8) | 100% (8/8) |
# | 평균 결정 마진 | 0.00 | 0.62 | 1.12 |
#
# - 바뀐 것은 **설명 문자열 하나**뿐이다. `tokenize`, `choose`, `QUERIES` 전부 그대로다.
# - `BAD` 의 38% 는 능력이 아니라 **딕셔너리 첫 키를 반환하는 상수 함수**의 점수다.
#   키 순서만 바꿔도 25%까지 떨어진다.
# - 좋은 설명에 들어간 셋: (1) 무엇을 **주는지** (2) 어떤 **말**로 물었을 때인지
#   (3) 언제 **안** 쓰는지. 셋째가 제일 자주 빠지고 제일 크게 듣는다.
# - 남은 실패 「상사 vs 상급자」는 어휘 불일치다. 동의어를 설명에 넣으면 100%.
#   실제 질문 로그에서 뽑아 넣는 게 제일 좋다.
# - 그래프의 말로: 도구 설명이 곧 **엣지 선택 함수**다. 자연어로 적어 둔 그 글이 코드다.
