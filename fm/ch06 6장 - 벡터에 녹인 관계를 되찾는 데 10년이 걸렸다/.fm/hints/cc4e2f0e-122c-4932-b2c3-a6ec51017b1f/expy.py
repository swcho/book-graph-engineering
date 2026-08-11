# %% [markdown]
# # `ex1_rag_limits.py` 해부 — 글자 2-gram TF-IDF 코사인 검색과 TOP_K=4의 벽
#
# 6장 예제 1은 **의존성 없이** 순수 파이썬으로 벡터 검색을 구현한다.
# 1장에서 쓴 것과 똑같은 방식이다.
#
# | 구성요소 | 선택 |
# |---|---|
# | 토큰화 | 글자 2-gram (character bigram) |
# | 가중치 | TF-IDF (smoothed idf, `+1`) |
# | 유사도 | L2 정규화 후 내적 = 코사인 유사도 |
# | 반환 | `TOP_K = 4` |
#
# 이 노트북은 같은 알고리즘을 처음부터 다시 짜서
# **국소 질문은 잘 맞히지만 전역 질문은 top-k로 못 푼다**는 것을 보인다.
#
# 필요 패키지: plotly, kaleido (`pip install plotly kaleido`) — 검색 로직 자체는 표준 라이브러리만 쓴다.

# %%
import math
import re
from collections import Counter

TOP_K = 4  # ex1_rag_limits.py 와 동일


def _show(fig):
    try:
        from IPython import get_ipython
        if get_ipython() is not None:  # VSCode 셀/Jupyter에서만 렌더링
            fig.show()
    except ImportError:
        pass


# corpus.py 와 동일한 장애 회고 12건 (이 파일만으로 돌도록 복사해 둔다)
DOCS = [
    ("d01", "결제 서비스 장애. 재시도 로직이 중복 결제를 만들었다. 멱등 키가 없었다."),
    ("d02", "쿠폰 발급 장애. 같은 요청이 두 번 들어와 쿠폰이 두 장 나갔다."),
    ("d03", "배송 조회 지연. 캐시가 만료되며 원본 DB로 요청이 몰렸다."),
    ("d04", "회원 탈퇴 처리 실패. 외부 API 타임아웃 뒤 재시도했는데 상태가 어긋났다."),
    ("d05", "정산 배치 중단. 부분 성공 상태에서 롤백을 안 했다."),
    ("d06", "알림 중복 발송. 큐 재처리 시 이미 보낸 건을 다시 보냈다."),
    ("d07", "이미지 업로드 실패율 상승. 스토리지 지역 장애. 재시도로 복구."),
    ("d08", "포인트 적립 누락. 이벤트 소비자가 죽은 뒤 오프셋이 밀렸다."),
    ("d09", "주문 취소 이중 처리. 사용자가 버튼을 두 번 눌렀다."),
    ("d10", "검색 색인 지연. 색인 작업이 실패해도 아무도 몰랐다. 알림이 없었다."),
    ("d11", "환불 금액 오류. 부분 환불 재시도가 전액 환불을 만들었다."),
    ("d12", "로그인 실패 급증. 인증 서버 배포 중 세션 저장소가 비었다."),
]

# 사람이 미리 읽고 붙여 둔 «원인» 라벨. 검색기는 이걸 못 본다.
CAUSE_OF = {
    "d01": {"재시도", "멱등성 없음"}, "d02": {"중복 요청", "멱등성 없음"},
    "d03": {"캐시 만료"},            "d04": {"재시도", "상태 불일치"},
    "d05": {"부분 실패", "롤백 없음"}, "d06": {"재처리", "멱등성 없음"},
    "d07": {"외부 장애"},            "d08": {"소비자 중단", "오프셋 밀림"},
    "d09": {"중복 요청", "멱등성 없음"}, "d10": {"관측 부재"},
    "d11": {"재시도", "부분 실패"},   "d12": {"배포", "상태 초기화"},
}

GLOBAL_QUESTION = "우리 장애 회고 전체에서 반복되는 원인은 무엇인가?"
GROUND_TRUTH = {"멱등성 없음", "재시도"}

print(f"문서 {len(DOCS)}건, TOP_K = {TOP_K}")
# 출력: 문서 12건, TOP_K = 4

# %% [markdown]
# ## 1. 왜 하필 «글자 2-gram»인가
#
# 한국어는 교착어라서 어간에 어미·조사가 계속 붙는다.
# 같은 «재시도»가 문서마다 다른 모습으로 나타난다.
#
# - d04: `재시도했는데`
# - d07: `재시도로`
# - d11: `재시도가`
#
# **공백 토큰화**로는 이 셋이 전부 다른 단어다. 질의 `재시도`와 하나도 안 겹친다.
# 제대로 자르려면 형태소 분석기(mecab, khaiii …)가 필요한데, 사전·설치·신조어 문제가 따라온다.
#
# **글자 n-gram**은 사전 없이 이 문제를 우회한다. `재시도로` → `재시`, `시도`, `도로`.
# 질의 `재시도` → `재시`, `시도`. 두 개가 겹친다. **부분 일치가 공짜로 생긴다.**
#
# $n=2$는 한국어에서 흔한 타협점이다. 한국어 형태소는 대개 1~2음절이라 2-gram이
# 어간 조각을 잘 잡고, 1-gram은 변별력이 없고 3-gram 이상은 활용형에 쉽게 깨진다.

# %%
def grams(t, n=2):
    """ex1_rag_limits.py 와 동일. 한글/영문/숫자만 남기고 n글자씩 슬라이딩."""
    s = re.sub(r"[^0-9A-Za-z가-힣]", "", t)
    return [s[i:i + n] for i in range(len(s) - n + 1)]


변형들 = ["재시도", "재시도했는데", "재시도로", "재시도가"]
for w in 변형들:
    print(f"{w:>10} → {grams(w)}")
# 출력:        재시도 → ['재시', '시도']
# 출력:  재시도했는데 → ['재시', '시도', '도했', '했는', '는데']
# 출력:      재시도로 → ['재시', '시도', '도로']
# 출력:      재시도가 → ['재시', '시도', '도가']

q = set(grams("재시도"))
print("\n공백 토큰화 겹침:", [w for w in 변형들[1:] if w == "재시도"])
print("2-gram 겹침:", {w: sorted(q & set(grams(w))) for w in 변형들[1:]})
# 출력:
# 출력: 공백 토큰화 겹침: []
# 출력: 2-gram 겹침: {'재시도했는데': ['시도', '재시'], '재시도로': ['시도', '재시'], '재시도가': ['시도', '재시']}

# %% [markdown]
# ## 2. TF-IDF 가중치
#
# 문서 $d$ 안 gram $g$의 가중치는
#
# $$w_{g,d} = \mathrm{tf}(g,d)\cdot \mathrm{idf}(g)$$
#
# `ex1`이 쓰는 정의는 이렇다.
#
# $$\mathrm{tf}(g,d) = (\text{문서 } d \text{ 안 } g \text{의 등장 횟수}),\qquad
# \mathrm{idf}(g) = \ln\!\frac{N+1}{\mathrm{df}(g)+1} + 1$$
#
# - $N$: 전체 문서 수 (여기서는 12)
# - $\mathrm{df}(g)$: $g$가 나타난 **문서 수** (총 등장 횟수가 아니다)
# - 분자·분모의 `+1`은 **스무딩**. df가 0이거나 df=N일 때 발산/0을 막는다.
# - 끝의 `+1`은 **바닥 깔기**. 모든 문서에 나오는 gram($\mathrm{df}=N$)도 idf가 0이 아니라
#   $\ln\frac{N+1}{N+1}+1 = 1$이 되어 완전히 사라지지는 않는다. scikit-learn의
#   `TfidfVectorizer(smooth_idf=True)`와 같은 공식이다.
#
# 직관: **드문 gram일수록 idf가 크다.** 12건 전부에 나오는 gram은 변별력이 없으니 1,
# 한 건에만 나오는 gram은 $\ln\frac{13}{2}+1 \approx 2.87$로 무겁게 친다.

# %%
tfs = [Counter(grams(d[1])) for d in DOCS]
df = Counter()
for tf in tfs:
    df.update(tf.keys())
N = len(DOCS)
idf = {g: math.log((N + 1) / (df[g] + 1)) + 1 for g in df}

print(f"전체 고유 2-gram: {len(idf)}개\n")
print("df 가 큰 gram (흔함 → idf 낮음)")
for g, c in df.most_common(5):
    print(f"  '{g}'  df={c:2d}  idf={idf[g]:.3f}")
print("\ndf=1 인 gram 예시 (희귀 → idf 최대)")
for g in ["멱등", "쿠폰", "롤백"]:
    print(f"  '{g}'  df={df[g]:2d}  idf={idf[g]:.3f}")
# 출력: 전체 고유 2-gram: 240개
# 출력:
# 출력: df 가 큰 gram (흔함 → idf 낮음)
# 출력:   '재시'  df= 4  idf=1.956
# 출력:   '시도'  df= 4  idf=1.956
# 출력:   '었다'  df= 4  idf=1.956
# 출력:   '실패'  df= 4  idf=1.956
# 출력:   '장애'  df= 3  idf=2.179
# 출력:
# 출력: df=1 인 gram 예시 (희귀 → idf 최대)
# 출력:   '멱등'  df= 1  idf=2.872
# 출력:   '쿠폰'  df= 1  idf=2.872
# 출력:   '롤백'  df= 1  idf=2.872
#
# 참고: '재시'/'시도' 의 df=4 는 2-gram 이 실제로 활용형을 가로질러 매칭한 증거다.
# «재시도로»(d07), «재시도했는데»(d04), «재시도가»(d11), «재시도»(d01) 가 한 gram 으로 묶였다.

# %% [markdown]
# ## 3. 코사인 유사도
#
# 두 벡터의 코사인 유사도는
#
# $$\cos(\mathbf{q},\mathbf{d}) = \frac{\mathbf{q}\cdot\mathbf{d}}{\|\mathbf{q}\|\,\|\mathbf{d}\|}
# = \sum_g \hat q_g\,\hat d_g \quad\text{(단, } \hat v = v/\|v\| \text{)}$$
#
# 즉 **미리 L2 정규화해 두면 코사인은 그냥 내적**이다. `ex1`의 `vec()`가 정규화까지 해 두고,
# 점수는 `sum(qv[g] * dv[g])` 한 줄로 끝난다.
#
# 왜 코사인인가: 길이로 나누기 때문에 **문서 길이에 안 휘둘린다.**
# 긴 회고문은 gram이 많아 원시 내적이 커지지만, 코사인은 «방향»만 본다.
# 값은 $[0, 1]$ (음수 성분이 없으므로).

# %%
def vec(c):
    """Counter → L2 정규화된 TF-IDF 희소벡터."""
    v = {g: x * idf.get(g, 0) for g, x in c.items()}
    nm = math.sqrt(sum(y * y for y in v.values())) or 1
    return {g: y / nm for g, y in v.items()}


DOC_VECS = [vec(tf) for tf in tfs]


def search(query, k=TOP_K):
    qv = vec(Counter(grams(query)))
    scored = [(sum(qv[g] * dv[g] for g in qv.keys() & dv.keys()), i)
              for i, dv in enumerate(DOC_VECS)]
    scored.sort(reverse=True)
    return scored[:k]


def show_hits(query, k=TOP_K):
    print(f"질문: {query}")
    for s, i in search(query, k):
        print(f"  [{s:.3f}] {DOCS[i][0]} {DOCS[i][1]}")


# 정규화 검증
print("‖d01‖ =", round(math.sqrt(sum(y * y for y in DOC_VECS[0].values())), 6))
# 출력: ‖d01‖ = 1.0

# %% [markdown]
# ## 4. 국소 질문 — 잘 된다
#
# **국소(local) 질문** = 답이 한 조각 안에 통째로 들어 있는 질문.
# 이런 질문에서는 2-gram TF-IDF 코사인만으로도 충분하다.

# %%
for q in ["쿠폰이 두 번 발급된 사고", "캐시가 만료되어 DB에 부하가 몰린 건", "멱등 키가 없어서 생긴 중복 결제"]:
    show_hits(q, k=3)
    print()
# 출력: 질문: 쿠폰이 두 번 발급된 사고
# 출력:   [0.610] d02 쿠폰 발급 장애. 같은 요청이 두 번 들어와 쿠폰이 두 장 나갔다.
# 출력:   [0.080] d09 주문 취소 이중 처리. 사용자가 버튼을 두 번 눌렀다.
# 출력:   [0.000] d12 로그인 실패 급증. 인증 서버 배포 중 세션 저장소가 비었다.
# 출력:
# 출력: 질문: 캐시가 만료되어 DB에 부하가 몰린 건
# 출력:   [0.523] d03 배송 조회 지연. 캐시가 만료되며 원본 DB로 요청이 몰렸다.
# 출력:   [0.000] d12 로그인 실패 급증. 인증 서버 배포 중 세션 저장소가 비었다.
# 출력:   [0.000] d11 환불 금액 오류. 부분 환불 재시도가 전액 환불을 만들었다.
# 출력:
# 출력: 질문: 멱등 키가 없어서 생긴 중복 결제
# 출력:   [0.579] d01 결제 서비스 장애. 재시도 로직이 중복 결제를 만들었다. 멱등 키가 없었다.
# 출력:   [0.064] d06 알림 중복 발송. 큐 재처리 시 이미 보낸 건을 다시 보냈다.
# 출력:   [0.000] d12 로그인 실패 급증. 인증 서버 배포 중 세션 저장소가 비었다.

# %% [markdown]
# 1위 점수가 0.52~0.61, 2위는 0.08 이하, 3위는 0.000이다. **신호가 압도적으로 뚜렷하다.**
# 답이 한 조각 안에 통째로 들어 있으니 top-1만 컨텍스트에 넣어도 충분하다.
# `TOP_K=4`는 이런 질문에는 오히려 넉넉한 예산이다.

# %% [markdown]
# ## 5. 전역 질문 — TOP_K=4의 벽
#
# **전역(global) 질문** = 답이 어느 조각에도 없고, 전체를 세어야 나오는 질문.
#
# > 「우리 장애 회고 전체에서 반복되는 원인은 무엇인가?」
#
# 정답은 `{멱등성 없음, 재시도}`인데, 이건 12건을 **다 세어야** 나온다.

# %%
print(f"질문: {GLOBAL_QUESTION}\n")
hits = search(GLOBAL_QUESTION, TOP_K)
print(f"상위 {TOP_K}개 조각")
for s, i in hits:
    print(f"  [{s:.3f}] {DOCS[i][0]} {DOCS[i][1]}  ← 원인 {sorted(CAUSE_OF[DOCS[i][0]])}")
# 출력: 질문: 우리 장애 회고 전체에서 반복되는 원인은 무엇인가?
# 출력:
# 출력: 상위 4개 조각
# 출력:   [0.185] d05 정산 배치 중단. 부분 성공 상태에서 롤백을 안 했다.  ← 원인 ['롤백 없음', '부분 실패']
# 출력:   [0.100] d07 이미지 업로드 실패율 상승. 스토리지 지역 장애. 재시도로 복구.  ← 원인 ['외부 장애']
# 출력:   [0.090] d02 쿠폰 발급 장애. 같은 요청이 두 번 들어와 쿠폰이 두 장 나갔다.  ← 원인 ['멱등성 없음', '중복 요청']
# 출력:   [0.089] d01 결제 서비스 장애. 재시도 로직이 중복 결제를 만들었다. 멱등 키가 없었다.  ← 원인 ['멱등성 없음', '재시도']

# %%
# top-4 만 보고 원인을 세어 보면?
top4_causes = Counter()
for _, i in hits:
    top4_causes.update(CAUSE_OF[DOCS[i][0]])
answer = {c for c, _ in top4_causes.most_common(2)}
print("top-4 안 원인 분포:", dict(top4_causes))
print("여기서 뽑은 답 :", sorted(answer))
print("정답           :", sorted(GROUND_TRUTH))
print("맞았나         :", "예" if answer == GROUND_TRUTH else "아니오")
# 출력: top-4 안 원인 분포: {'롤백 없음': 1, '부분 실패': 1, '외부 장애': 1, '멱등성 없음': 2, '중복 요청': 1, '재시도': 1}
# 출력: 여기서 뽑은 답 : ['롤백 없음', '멱등성 없음']
# 출력: 정답           : ['멱등성 없음', '재시도']
# 출력: 맞았나         : 아니오

# %% [markdown]
# 대부분의 원인이 1건씩이라 **순위가 거의 안 갈린다.** 2위를 «롤백 없음»(1건)이 동점으로 차지했다.
# 진짜 2위인 «재시도»는 전체 3건이지만 top-4 안에는 d01 하나만 들어와 1건으로 보인다.
# 1위 점수 0.185도 국소 질문의 0.52~0.61에 한참 못 미친다 — 검색기 스스로 «자신 없음»을 말하고 있다.
#
# 왜 이렇게 되나: 질의의 2-gram은 `우리`, `장애`, `회고`, `전체`, `반복`, `원인`, `무엇` …인데
# «반복되는 원인»은 **어느 문서에도 글자로 적혀 있지 않다.** 문서들은 각자 자기 사고만 서술한다.
# 표면 문자열이 겹치는 정도로는 «전체에서 몇 번 나왔나»를 잴 수 없다.
#
# 게다가 1위 d05가 뜬 이유는 «반복되는 원인»과 무관하다 —
# 「정산 배치 중단. 부분 성공 상태에서 롤백을 안 했다」가 짧아서 정규화 후 gram당 무게가 컸을 뿐이다.

# %%
# 얼마나 안 겹치는지 전체 순위로 확인
for s, i in search(GLOBAL_QUESTION, len(DOCS)):
    print(f"  {DOCS[i][0]} {s:.4f}")
# 출력:   d05 0.1854
# 출력:   d07 0.0996
# 출력:   d02 0.0903
# 출력:   d01 0.0890
# 출력:   d12 0.0000
# 출력:   d11 0.0000
# 출력:   d10 0.0000
# 출력:   d09 0.0000
# 출력:   d08 0.0000
# 출력:   d06 0.0000
# 출력:   d04 0.0000
# 출력:   d03 0.0000

# %% [markdown]
# **12건 중 8건이 정확히 0점이다.** 질의와 겹치는 2-gram이 하나도 없다.
# 5위 아래의 «순위»는 순위가 아니라 그냥 동점 정렬 순서다.
# 전역 질문에서는 **랭킹 자체가 존재하지 않는다.**
#
# ## 6. TOP_K를 올리면 되나?
#
# «조각을 더 넣기»가 통하는지 $k = 1 \ldots 12$로 확인한다.
# (동점 구간이 있으니 아래 곡선의 k>4 부분은 «운»에 가깝다는 점을 감안하고 보자.)

# %%
ranked = search(GLOBAL_QUESTION, len(DOCS))
필요문서 = sorted(d for d, cs in CAUSE_OF.items() if cs & GROUND_TRUTH)
print("정답을 세려면 봐야 하는 문서:", 필요문서, f"({len(필요문서)}건)")

recall_curve, correct_at_k = [], []
for k in range(1, len(DOCS) + 1):
    ids = [DOCS[i][0] for _, i in ranked[:k]]
    recall_curve.append(sum(1 for d in 필요문서 if d in ids))
    cnt = Counter()
    for d in ids:
        cnt.update(CAUSE_OF[d])
    correct_at_k.append({c for c, _ in cnt.most_common(2)} == GROUND_TRUTH)

for k in range(1, len(DOCS) + 1):
    mark = "O" if correct_at_k[k - 1] else "X"
    print(f"  k={k:2d}  필요문서 {recall_curve[k-1]}/{len(필요문서)} 회수   답 맞음 {mark}")
# 출력: 정답을 세려면 봐야 하는 문서: ['d01', 'd02', 'd04', 'd06', 'd09', 'd11'] (6건)
# 출력:   k= 1  필요문서 0/6 회수   답 맞음 X
# 출력:   k= 2  필요문서 0/6 회수   답 맞음 X
# 출력:   k= 3  필요문서 1/6 회수   답 맞음 X
# 출력:   k= 4  필요문서 2/6 회수   답 맞음 X
# 출력:   k= 5  필요문서 2/6 회수   답 맞음 X
# 출력:   k= 6  필요문서 3/6 회수   답 맞음 X
# 출력:   k= 7  필요문서 3/6 회수   답 맞음 X
# 출력:   k= 8  필요문서 4/6 회수   답 맞음 X
# 출력:   k= 9  필요문서 4/6 회수   답 맞음 X
# 출력:   k=10  필요문서 5/6 회수   답 맞음 X
# 출력:   k=11  필요문서 6/6 회수   답 맞음 O
# 출력:   k=12  필요문서 6/6 회수   답 맞음 O

# %% [markdown]
# **정답이 나오는 건 k=11부터다. 12건 중 11건 — «검색»이 아니라 사실상 «전량 스캔»이다.**
# 문서가 12건이라 우연히 가능했을 뿐이다.
#
# 문서가 12만 건이면? 컨텍스트 창에 12만 건을 못 넣는다.
# 그리고 «반복되는 원인»의 정확한 순위는 12만 건을 **전부** 세어야 나온다.
# top-k를 아무리 키워도 «전부»에 도달하지 못한다 — **이것이 조각 검색의 벽이다.**
#
# 6장의 풀이는 **세는 시점을 옮기는 것**이다.
# 질의 시점에 k개를 세는 대신, **색인 시점에 전부 훑어 커뮤니티 요약으로 접어 둔다**
# (`ex2_graphrag_lite.py`). 질의 시점에는 접어 둔 것을 펴기만 하면 된다.

# %% [markdown]
# ## 7. 시각화

# %%
import plotly.graph_objects as go
from plotly.subplots import make_subplots

SURFACE = "#fcfcfb"
INK = "#0b0b0b"
INK2 = "#52514e"
GRID = "#e4e3df"
BLUE = "#2a78d6"    # 그 외 문서
ORANGE = "#eb6834"  # 정답에 필요한 문서

ids = [d for d, _ in DOCS]
필요집합 = set(필요문서)


def score_map(query):
    m = dict.fromkeys(ids, 0.0)
    for s, i in search(query, len(DOCS)):
        m[DOCS[i][0]] = s
    return [m[d] for d in ids]


LOCAL_Q = "캐시가 만료되어 DB에 부하가 몰린 건"
local_scores = score_map(LOCAL_Q)
global_scores = score_map(GLOBAL_QUESTION)
cut = sorted(global_scores, reverse=True)[TOP_K - 1]
first_ok = next((k for k in range(1, len(DOCS) + 1) if correct_at_k[k - 1]), len(DOCS))

fig = make_subplots(
    rows=2, cols=2,
    specs=[[{}, {}], [{"colspan": 2}, None]],
    row_heights=[0.56, 0.44], vertical_spacing=0.20, horizontal_spacing=0.10,
    subplot_titles=(
        "국소 질문 「캐시 만료로 DB에 부하가 몰린 건」 — 1위가 압도한다",
        "전역 질문 「반복되는 원인은?」 — 12건 중 8건이 점수 0",
        f"top-k 를 키워 봐도: 정답을 세는 데 필요한 문서 {len(필요문서)}건의 회수량",
    ),
)

for col, scores in ((1, local_scores), (2, global_scores)):
    for label, color, keep in (("정답 원인(재시도·멱등성 없음) 보유 문서", ORANGE, True),
                               ("그 외 문서", BLUE, False)):
        xs = [d for d in ids if (d in 필요집합) == keep]
        ys = [scores[ids.index(d)] for d in xs]
        fig.add_trace(
            go.Bar(x=xs, y=ys, name=label, marker_color=color,
                   marker_line=dict(color=SURFACE, width=2),
                   showlegend=(col == 1), legendgroup=label,
                   hovertemplate="%{x}<br>코사인 %{y:.3f}<extra></extra>"),
            row=1, col=col)

# 전역 질문 패널에 TOP_K 컷오프 선
fig.add_hline(y=cut, line=dict(color=INK2, width=1.5, dash="dot"),
              annotation_text=f"TOP_K={TOP_K} 컷오프 ({cut:.3f})",
              annotation_font=dict(size=11, color=INK2),
              annotation_position="top right", row=1, col=2)

ks = list(range(1, len(DOCS) + 1))
fig.add_trace(
    go.Scatter(x=ks, y=recall_curve, mode="lines+markers", showlegend=False,
               line=dict(color=ORANGE, width=2), marker=dict(size=9),
               hovertemplate="k=%{x}<br>%{y}/6 회수<extra></extra>"),
    row=2, col=1)
fig.add_vrect(x0=0.5, x1=TOP_K + 0.5, fillcolor=INK2, opacity=0.07,
              line_width=0, row=2, col=1)
fig.add_annotation(x=2.5, y=5.6, text="실제 TOP_K=4 구간<br>2/6 밖에 못 본다", showarrow=False,
                   font=dict(size=11, color=INK2), row=2, col=1)
fig.add_annotation(x=first_ok, y=len(필요문서),
                   text=f"k={first_ok} — 12건 중 11건,<br>사실상 전량 스캔", showarrow=True,
                   arrowhead=0, arrowcolor=INK2, ax=-58, ay=-26, align="left",
                   font=dict(size=11, color=INK), row=2, col=1)

fig.update_yaxes(title_text="코사인 유사도", range=[0, 0.66], row=1, col=1)
fig.update_yaxes(range=[0, 0.66], row=1, col=2)
fig.update_yaxes(title_text="회수한 문서 수", range=[0, 7.4],
                 dtick=2, row=2, col=1)
fig.update_xaxes(title_text="top-k 의 k", dtick=1, row=2, col=1)
fig.update_xaxes(categoryorder="array", categoryarray=ids, row=1, col=1)
fig.update_xaxes(categoryorder="array", categoryarray=ids, row=1, col=2)
fig.update_xaxes(showgrid=False, linecolor=GRID, tickfont=dict(color=INK2, size=11))
fig.update_yaxes(gridcolor=GRID, zeroline=False, linecolor=GRID,
                 tickfont=dict(color=INK2, size=11))
fig.update_layout(
    title=dict(text="글자 2-gram TF-IDF 코사인 검색: 국소는 되고 전역은 안 된다",
               font=dict(size=17, color=INK)),
    template="simple_white", paper_bgcolor=SURFACE, plot_bgcolor=SURFACE,
    font=dict(color=INK, size=12), bargap=0.25,
    legend=dict(orientation="h", y=1.055, x=0, yanchor="bottom",
                font=dict(color=INK2, size=11)),
    width=1000, height=680, margin=dict(l=70, r=30, t=120, b=60),
)
for a in fig.layout.annotations[:3]:
    a.font.size = 12.5
    a.font.color = INK

fig.write_image("expy.png", scale=2)
_show(fig)
print("expy.png 저장 완료")
# 출력: expy.png 저장 완료

# %% [markdown]
# ## 정리
#
# | 질문 | `ex1_rag_limits.py` 의 답 |
# |---|---|
# | 어떤 검색 방식? | 1장과 같은 **글자 2-gram TF-IDF 코사인 유사도** |
# | 왜 글자 2-gram? | 형태소 분석기 없이 «재시도했는데» ↔ «재시도» 부분 일치를 얻으려고 |
# | TF-IDF 정의 | $\mathrm{tf}\cdot(\ln\frac{N+1}{\mathrm{df}+1}+1)$, 스무딩 + 바닥 1 |
# | 왜 코사인? | L2 정규화 후 내적. 문서 길이에 안 휘둘린다 |
# | `TOP_K` | **4** — 상위 4개 조각만 컨텍스트로 넘긴다 |
# | 의존성 | **없음.** `math`, `re`, `collections` 표준 라이브러리만 |
#
# TOP_K=4는 조각 검색의 **정보 예산**이다. 국소 질문에는 넉넉하고,
# 전역 질문에는 원리적으로 부족하다 — 12건 중 8건을 못 본 채 «전체»를 말해야 하기 때문이다.
