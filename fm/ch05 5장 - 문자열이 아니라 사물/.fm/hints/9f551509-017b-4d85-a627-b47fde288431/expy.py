# %% [markdown]
# # `thing_search()`는 어떻게 사물을 판별하는가
#
# 5장 `code/ex4_things_not_strings.py`의 핵심 함수를 손으로 뜯어본다.
#
# 판별은 **두 단계**다.
#
# 1. **이름 필터** — 질문 문자열 안에 사물의 `name`이 들어 있는 후보만 남긴다.
# 2. **술어 겹침 점수** — 질문의 낱말이 그 사물의 속성 키(술어)와 겹치는 개수를 세어
#    점수를 매기고, 점수 내림차순으로 정렬한다.
#
# 즉 "이 이름을 가진 후보들 중에서, 질문이 요구하는 술어를 가진 놈"을 고른다.
# **술어 목록이 곧 그 사물의 정체**라는 5장의 주장이 코드로는 이 한 줄이다.
#
# 필요 패키지: plotly (시각화), kaleido (PNG 저장). 로직 자체는 순수 파이썬으로 의존성 없음.

# %%
# 시각화 헬퍼 — 노트북/셀 환경에서만 렌더링한다. fig.show()를 직접 부르지 않는다.
def _show(fig):
    try:
        from IPython import get_ipython

        if get_ipython() is not None:  # VSCode 셀/Jupyter에서만 렌더링
            fig.show()
    except ImportError:
        pass


# %% [markdown]
# ## 1. 재료 — 이름이 같고 술어가 다른 세 사물
#
# `ex4_things_not_strings.py`의 `THINGS`를 그대로 가져온다.
# 세 사물 모두 이름은 "타지마할"이다. 다른 것은 **속성 키(술어) 목록**뿐이다.

# %%
THINGS = {
    "t1": {
        "name": "타지마할",
        "type": "건물",
        "props": {"위치": "인도 아그라", "완공": "1653", "입장료": "1,100루피"},
    },
    "t2": {
        "name": "타지마할",
        "type": "음악가",
        "props": {"장르": "블루스", "활동시작": "1968", "본명": "헨리 세인트클레어 프레드릭스"},
    },
    "t3": {
        "name": "타지마할",
        "type": "식당",
        "props": {"지역": "서울 이태원", "영업시간": "11:00-22:00", "평점": "4.2"},
    },
}

DOCS = [
    "타지마할은 인도 아그라에 있는 무굴 제국의 묘당이다.",
    "타지마할의 앨범은 블루스와 카리브 음악을 섞었다.",
    "이태원 타지마할은 저녁 예약이 어렵다.",
    "타지마할 입장료가 올해 인상되었다.",
]

for tid, t in THINGS.items():
    print(f"{tid} {t['type']:<4} 술어 {list(t['props'])}")
# 출력:
# t1 건물   술어 ['위치', '완공', '입장료']
# t2 음악가  술어 ['장르', '활동시작', '본명']
# t3 식당   술어 ['지역', '영업시간', '평점']

# %% [markdown]
# ## 2. 비교군 — 문자열 검색
#
# ```python
# def string_search(q):
#     return [d for d in DOCS if all(w in d for w in q.split())]
# ```
#
# 질문의 모든 낱말이 문서 문자열에 들어 있는지만 본다. 사물 개념이 아예 없다.


# %%
def string_search(q):
    return [d for d in DOCS if all(w in d for w in q.split())]


for q in ["타지마할", "타지마할 입장료", "타지마할 앨범", "타지마할 예약"]:
    hits = string_search(q)
    print(f"[{q}] {len(hits)}건")
    for d in hits:
        print("   -", d)
# 출력:
# [타지마할] 4건
#    - 타지마할은 인도 아그라에 있는 무굴 제국의 묘당이다.
#    - 타지마할의 앨범은 블루스와 카리브 음악을 섞었다.
#    - 이태원 타지마할은 저녁 예약이 어렵다.
#    - 타지마할 입장료가 올해 인상되었다.
# [타지마할 입장료] 1건
#    - 타지마할 입장료가 올해 인상되었다.
# [타지마할 앨범] 1건
#    - 타지마할의 앨범은 블루스와 카리브 음악을 섞었다.
# [타지마할 예약] 1건
#    - 이태원 타지마할은 저녁 예약이 어렵다.

# %% [markdown]
# 그냥 "타지마할"로 물으면 건물·음악가·식당 문서가 한 목록에 섞여 나온다.
# **어느 사물 이야기인지는 사람이 골라야 한다.** 검색기는 문자열만 봤다.
#
# ## 3. `thing_search()` — 두 단계
#
# ```python
# def thing_search(q):
#     words = q.split()
#     scored = []
#     for tid, t in THINGS.items():
#         if t["name"] not in q:            # (1) 이름 필터
#             continue
#         hit = sum(1 for w in words for k in t["props"] if k in w or w in k)  # (2) 술어 겹침
#         scored.append((hit, tid, t))
#     scored.sort(reverse=True, key=lambda x: x[0])                            # (3) 점수 정렬
#     return scored
# ```
#
# 점수를 식으로 쓰면, 질문 낱말 집합 $Q$와 사물 $t$의 술어 집합 $P_t$에 대해
# 이상적인 형태는 교집합의 크기다.
#
# $$\mathrm{score}_{\text{ideal}}(t) = |Q \cap P_t|$$
#
# 다만 코드가 실제로 세는 것은 **부분 문자열 관계를 만족하는 (낱말, 술어) 쌍의 개수**다.
# $w \sqsubseteq k$ 를 "$w$가 $k$의 부분 문자열"이라고 쓰면
#
# $$\mathrm{score}(t) = \bigl|\{(w,k) \in Q \times P_t \;\mid\; k \sqsubseteq w \;\lor\; w \sqsubseteq k\}\bigr|$$
#
# 정확히 같을 때만 세는 $|Q \cap P_t|$ 와 달리, 이 쪽은 한 낱말이 여러 술어에 걸리면
# 중복으로 세어지므로 $\mathrm{score}(t) \ge |Q \cap P_t|$ 가 된다.
# 조사가 붙은 "영업시간은"을 잡아 주는 관용성과, 뒤에서 볼 오탐이 같은 뿌리에서 나온다.


# %%
def thing_search(q):
    """질문에 나온 낱말이 어느 사물의 «술어»와 겹치는지 본다."""
    words = q.split()
    scored = []
    for tid, t in THINGS.items():
        if t["name"] not in q:  # (1) 이름 필터
            continue
        hit = sum(1 for w in words for k in t["props"] if k in w or w in k)  # (2) 술어 겹침
        scored.append((hit, tid, t))
    scored.sort(reverse=True, key=lambda x: x[0])  # (3) 점수 정렬
    return scored


def trace(q):
    """어느 (낱말, 술어) 쌍이 점수를 만들었는지까지 보여 준다."""
    words = q.split()
    print(f"질문 {q!r} → 낱말 {words}")
    for tid, t in THINGS.items():
        if t["name"] not in q:
            print(f"  {tid} {t['type']:<4} 이름 필터에서 탈락")
            continue
        pairs = [(w, k) for w in words for k in t["props"] if k in w or w in k]
        print(f"  {tid} {t['type']:<4} 점수 {len(pairs)}  근거 {pairs}")
    ranked = thing_search(q)
    print(f"  ⇒ 정렬 {[(h, tid, t['type']) for h, tid, t in ranked]}")
    print(f"  ⇒ 확정 {ranked[0][2]['type']}" if ranked else "  ⇒ 후보 없음")


trace("타지마할 입장료")
# 출력:
# 질문 '타지마할 입장료' → 낱말 ['타지마할', '입장료']
#   t1 건물   점수 1  근거 [('입장료', '입장료')]
#   t2 음악가  점수 0  근거 []
#   t3 식당   점수 0  근거 []
#   ⇒ 정렬 [(1, 't1', '건물'), (0, 't2', '음악가'), (0, 't3', '식당')]
#   ⇒ 확정 건물

# %% [markdown]
# "입장료"라는 술어를 가진 사물이 하나뿐이라 답이 **한 번에** 정해졌다.
# 문자열 검색에는 이런 손잡이가 없다.
#
# ## 4. 여러 질의를 나란히

# %%
QUERIES = [
    "타지마할",
    "타지마할 입장료",
    "타지마할 앨범",
    "타지마할 예약",
    "타지마할 장르 본명",
    "타지마할 영업시간은",
]

print(f"{'질의':<22}{'t1건물':>7}{'t2음악가':>9}{'t3식당':>8}   확정      문자열검색")
for q in QUERIES:
    ranked = thing_search(q)
    score = {tid: h for h, tid, _ in ranked}
    top = ranked[0][2]["type"] if ranked else "-"
    tie = " (동점)" if len(ranked) > 1 and ranked[0][0] == ranked[1][0] else ""
    print(
        f"{q:<22}{score.get('t1', '-'):>7}{score.get('t2', '-'):>9}"
        f"{score.get('t3', '-'):>8}   {top}{tie:<7} {len(string_search(q))}건"
    )
# 출력:
# 질의                       t1건물    t2음악가    t3식당   확정      문자열검색
# 타지마할                        0        0       0   건물 (동점)   4건
# 타지마할 입장료                    1        0       0   건물        1건
# 타지마할 앨범                     0        0       0   건물 (동점)   1건
# 타지마할 예약                     0        0       0   건물 (동점)   1건
# 타지마할 장르 본명                  0        2       0   음악가        0건
# 타지마할 영업시간은                  0        0       1   식당        0건

# %% [markdown]
# 읽는 법.
#
# - **"타지마할 입장료"** → t1만 점수 1. 정답이 유일하게 결정된다.
# - **"타지마할 장르 본명"** → t2가 점수 2. 술어를 두 개 맞혀서 확신이 커진다.
# - **"타지마할 영업시간은"** → 낱말은 "영업시간은"인데 `k in w` 덕에 술어 "영업시간"을 잡는다.
#   조사가 붙어도 통하는 이유.
# - **"타지마할 앨범" / "타지마할 예약" / 그냥 "타지마할"** → 세 사물 모두 0점.
#   `sort`가 안정 정렬이라 딕셔너리 삽입 순서가 그대로 남아 **t1(건물)이 1위로 뽑힌다.**
#   "앨범"은 음악가, "예약"은 식당 이야기인데도 틀린다.
#   문자열 검색은 오히려 이 두 질의에서 맞는 문서를 찾아냈다는 점이 뼈아프다.
#
# ## 5. 실험 A — 이름 필터를 빼면?

# %%
OTHER = {
    "x1": {"name": "경복궁", "type": "건물", "props": {"위치": "서울 종로", "완공": "1395", "입장료": "3,000원"}},
}


def thing_search_nofilter(q, pool):
    """(1) 이름 필터를 지운 판본."""
    words = q.split()
    scored = [
        (sum(1 for w in words for k in t["props"] if k in w or w in k), tid, t) for tid, t in pool.items()
    ]
    scored.sort(reverse=True, key=lambda x: x[0])
    return scored


POOL = dict(THINGS, **OTHER)
q = "타지마할 입장료"
print("이름 필터 있음:", [(h, tid, t["name"], t["type"]) for h, tid, t in thing_search(q)])
print("이름 필터 없음:", [(h, tid, t["name"], t["type"]) for h, tid, t in thing_search_nofilter(q, POOL)])
# 출력:
# 이름 필터 있음: [(1, 't1', '타지마할', '건물'), (0, 't2', '타지마할', '음악가'), (0, 't3', '타지마할', '식당')]
# 이름 필터 없음: [(1, 't1', '타지마할', '건물'), (1, 'x1', '경복궁', '건물'), (0, 't2', '타지마할', '음악가'), (0, 't3', '타지마할', '식당')]

# %% [markdown]
# 이름 필터가 없으면 **경복궁이 타지마할과 동점 1위로 올라온다.** 경복궁도 "입장료" 술어를 가졌으니까.
# 즉 점수만으로는 "무엇에 대한 질문인가"를 못 정한다. 이름 필터가 후보 집합을 만들고,
# 점수는 그 안에서 **누가 그 후보인가**만 가린다. 두 단계는 역할이 다르다.
#
# 반대로 이름 필터가 너무 빡빡해서 생기는 문제도 있다.

# %%
for q in ["타즈마할 입장료", "Taj Mahal 입장료", "타지마할역 근처 입장료"]:
    ranked = thing_search(q)
    print(f"{q!r} → 후보 {len(ranked)}개 {[t['type'] for _, _, t in ranked]}")
try:
    thing_search("타즈마할 입장료")[0]
except IndexError as e:
    print("thing_search('타즈마할 입장료')[0] →", type(e).__name__, e)
# 출력:
# '타즈마할 입장료' → 후보 0개 []
# 'Taj Mahal 입장료' → 후보 0개 []
# '타지마할역 근처 입장료' → 후보 3개 ['건물', '음악가', '식당']
# thing_search('타즈마할 입장료')[0] → IndexError list index out of range

# %% [markdown]
# `t["name"] not in q`는 정확한 부분 문자열 일치라서
# 오타("타즈마할")나 다른 표기("Taj Mahal")는 전부 탈락하고 결과가 빈 리스트가 된다.
# `ex4`의 `main()`처럼 `thing_search(q)[0]`을 바로 쓰면 `IndexError`가 난다.
# 반대로 "타지마할역"(지하철역)처럼 이름을 부분 문자열로 포함하기만 하면
# 세 후보가 그대로 전부 통과한다(과탐). 필터가 엄격한 동시에 허술하다.
#
# ## 6. 실험 B — 동점과 부분 문자열 오탐

# %%
# (a) 동점: 승자는 실력이 아니라 dict 삽입 순서로 결정된다.
q = "타지마할 앨범"
print("원래 순서:", [(h, t["type"]) for h, _, t in thing_search(q)])

_orig = dict(THINGS)
THINGS.clear()
THINGS.update({"t3": _orig["t3"], "t2": _orig["t2"], "t1": _orig["t1"]})  # 삽입 순서만 뒤집기
print("순서 뒤집기:", [(h, t["type"]) for h, _, t in thing_search(q)])
THINGS.clear()
THINGS.update(_orig)  # 원상 복구
# 출력:
# 원래 순서: [(0, '건물'), (0, '음악가'), (0, '식당')]
# 순서 뒤집기: [(0, '식당'), (0, '음악가'), (0, '건물')]

# %%
# (b) 부분 문자열 오탐: 짧은 낱말 하나가 엉뚱한 술어에 걸린다.
for q in ["타지마할 시", "타지마할 시작", "타지마할 장", "타지마할 지역영업시간"]:
    trace(q)
    print()
# 출력:
# 질문 '타지마할 시' → 낱말 ['타지마할', '시']
#   t1 건물   점수 0  근거 []
#   t2 음악가  점수 1  근거 [('시', '활동시작')]
#   t3 식당   점수 1  근거 [('시', '영업시간')]
#   ⇒ 정렬 [(1, 't2', '음악가'), (1, 't3', '식당'), (0, 't1', '건물')]
#   ⇒ 확정 음악가
#
# 질문 '타지마할 시작' → 낱말 ['타지마할', '시작']
#   t1 건물   점수 0  근거 []
#   t2 음악가  점수 1  근거 [('시작', '활동시작')]
#   t3 식당   점수 0  근거 []
#   ⇒ 정렬 [(1, 't2', '음악가'), (0, 't1', '건물'), (0, 't3', '식당')]
#   ⇒ 확정 음악가
#
# 질문 '타지마할 장' → 낱말 ['타지마할', '장']
#   t1 건물   점수 1  근거 [('장', '입장료')]
#   t2 음악가  점수 1  근거 [('장', '장르')]
#   t3 식당   점수 0  근거 []
#   ⇒ 정렬 [(1, 't1', '건물'), (1, 't2', '음악가'), (0, 't3', '식당')]
#   ⇒ 확정 건물
#
# 질문 '타지마할 지역영업시간' → 낱말 ['타지마할', '지역영업시간']
#   t1 건물   점수 0  근거 []
#   t2 음악가  점수 0  근거 []
#   t3 식당   점수 2  근거 [('지역영업시간', '지역'), ('지역영업시간', '영업시간')]
#   ⇒ 정렬 [(2, 't3', '식당'), (0, 't1', '건물'), (0, 't2', '음악가')]
#   ⇒ 확정 식당

# %% [markdown]
# - "시" 한 글자가 "활동시작"과 "영업시간"에 동시에 걸린다. 정규화·형태소 분석이 없어서다.
# - "지역영업시간"은 붙여 쓴 **한** 낱말인데 t3의 술어 두 개에 각각 걸려 점수 2를 얻는다.
#   $\mathrm{score}(t_3)=2 > |Q \cap P_{t_3}|=0$ — 쌍을 세는 정의의 부작용으로, 낱말 하나가
#   점수를 두 번 낸다. 정답 사물을 고르긴 했지만 "술어 두 개를 맞혔다"는 근거는 허수다.
#
# ## 7. 점수 행렬 히트맵

# %%
import plotly.graph_objects as go

MATRIX_QUERIES = [
    "타지마할",
    "타지마할 입장료",
    "타지마할 앨범",
    "타지마할 예약",
    "타지마할 장르 본명",
    "타지마할 영업시간은",
    "타지마할 평점 지역",
    "타지마할 위치 완공",
]
TIDS = ["t1", "t2", "t3"]
LABELS = [f"{tid}<br>{THINGS[tid]['type']}" for tid in TIDS]

Z, TEXT = [], []
for q in MATRIX_QUERIES:
    score = {tid: h for h, tid, _ in thing_search(q)}
    row = [score.get(tid, 0) for tid in TIDS]
    ranked = thing_search(q)
    win = ranked[0][1] if ranked else None
    ambiguous = len(ranked) > 1 and ranked[0][0] == ranked[1][0]
    Z.append(row)
    TEXT.append([f"{v}{'?' if (tid == win and ambiguous) else ('★' if tid == win else '')}" for tid, v in zip(TIDS, row)])

fig = go.Figure(
    go.Heatmap(
        z=Z,
        x=LABELS,
        y=MATRIX_QUERIES,
        text=TEXT,
        texttemplate="%{text}",
        textfont={"size": 15},
        colorscale="Blues",
        zmin=0,
        zmax=2,
        colorbar={"title": "술어<br>겹침"},
    )
)
fig.update_layout(
    title="thing_search() 점수 행렬 — ★ 1위, ? 동점 1위(순서로 결정)",
    xaxis_title="같은 이름의 사물 (술어 목록이 다르다)",
    yaxis_title="질의",
    yaxis={"autorange": "reversed"},
    width=780,
    height=520,
    margin={"l": 170, "t": 80},
)
_show(fig)

import pathlib

_png = pathlib.Path(__file__).with_name("expy.png") if "__file__" in globals() else pathlib.Path("expy.png")
fig.write_image(str(_png), scale=2)  # kaleido 필요
print("saved:", _png)
# 출력:
# saved: .../9f551509-017b-4d85-a627-b47fde288431/expy.png

# %% [markdown]
# ## 8. 정리
#
# | | 문자열 검색 | `thing_search()` |
# |---|---|---|
# | 단위 | 문서 | 사물 |
# | 판단 근거 | 낱말이 문서에 있나 | 낱말이 **술어 키**와 겹치나 |
# | 결과 | 건물·음악가·식당이 섞인 목록 | 후보 중 하나로 **확정** |
# | 애매함 해소 | 사람 몫 | 술어 목록이 대신 한다 |
#
# 근본적으로 다른 지점: `thing_search()`는 **"어떤 술어를 가졌나"로 정체를 판별한다.**
# 술어 목록이 곧 사물의 정체이므로, 질문이 요구하는 술어를 보면 어느 사물인지 역추적할 수 있다.
#
# 한계는 위 실험이 전부 보여 줬다.
#
# 1. 이름 필터가 정확한 부분 문자열 일치 — 오타·다른 표기·별칭에 무력하고, 결과가 빈 리스트가 된다.
# 2. `k in w or w in k` 부분 문자열 매칭 — 짧은 낱말이 엉뚱한 술어에 걸리고, 한 낱말이 중복 계산된다.
# 3. 정규화가 없다 — 조사·형태 변화가 우연히 통할 때도 있고 안 통할 때도 있다.
# 4. 동의어를 모른다 — "앨범"과 "장르", "예약"과 "영업시간"이 이어지지 않는다.
# 5. 동점 처리가 없다 — 0점 동점이면 삽입 순서로 승자가 정해진다. 신뢰도도 "모르겠다"도 없다.
#
# 실제 엔티티 링킹은 이 자리에 **임베딩 유사도, 별칭/표기 사전, 문맥(앞뒤 문장·사용자 이력),
# 인기도 사전확률, 후보 재순위화 모델**을 넣는다. 그래도 골격은 같다.
# 후보를 좁히고, 그 사물이 가진 술어와 질문이 얼마나 맞는지 재는 것.
