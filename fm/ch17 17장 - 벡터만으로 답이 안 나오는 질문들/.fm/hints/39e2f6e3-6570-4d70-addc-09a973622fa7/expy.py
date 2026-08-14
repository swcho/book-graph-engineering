# %% [markdown]
# # `ex1_routing.py`의 규칙 기반 라우터는 어떻게 판정하는가?
#
# 17장 예제 1의 라우터는 LLM도, 분류 모델도 아니다. **낱말 목록 두 개와 `if` 두 줄**이 전부다.
#
# 판정 순서:
#
# 1. 질문에 **집계 낱말**("전체", "몇 건", "가장", "자주", "평균", "총" …)이 하나라도 있으면 → **전역집계**
# 2. 아니면 **다중홉 낱말**("공통", "누구", "관련", "함께", "같은")이 있으면 → **다중홉**
# 3. 둘 다 없으면 → **사실조회** (기본값, 벡터 검색으로)
#
# 순서가 곧 우선순위다. 두 목록의 낱말이 동시에 있으면 먼저 검사하는 전역집계가 이긴다.

# %%
# 필요 패키지: plotly, kaleido (시각화 셀에만 필요, 라우터 자체는 의존성 없음)
import os


def _show(fig):
    try:
        from IPython import get_ipython
        if get_ipython() is not None:  # VSCode 셀/Jupyter에서만 렌더링
            fig.show()
    except ImportError:
        pass


# ex1_routing.py의 라우터를 그대로 옮겨온다
AGG_WORDS = ["전체", "몇 건", "가장", "자주", "평균", "총", "별로", "추세", "반복"]
MULTI_WORDS = ["공통", "누구", "관련", "함께", "같은"]


def route(q):
    if any(w in q for w in AGG_WORDS):      # 1순위: 집계 낱말 → 전역집계
        return "전역집계"
    if any(w in q for w in MULTI_WORDS):    # 2순위: 다중홉 낱말 → 다중홉
        return "다중홉"
    return "사실조회"                        # 3순위: 나머지 전부 → 사실조회(벡터)


print("AGG_WORDS  :", AGG_WORDS)
print("MULTI_WORDS:", MULTI_WORDS)
# 출력: AGG_WORDS  : ['전체', '몇 건', '가장', '자주', '평균', '총', '별로', '추세', '반복']
# 출력: MULTI_WORDS: ['공통', '누구', '관련', '함께', '같은']

# %% [markdown]
# ## 질문을 넣어 보면
#
# 어떤 낱말이 걸려서 어느 엔진으로 갔는지 추적해 본다.

# %%
def route_traced(q):
    """route()와 같은 판정 + 어떤 낱말이 걸렸는지 반환"""
    hit = [w for w in AGG_WORDS if w in q]
    if hit:
        return "전역집계", hit
    hit = [w for w in MULTI_WORDS if w in q]
    if hit:
        return "다중홉", hit
    return "사실조회", []


questions = [
    "재고 서비스 장애 원인은?",              # 아무 낱말도 없음
    "전체 장애 중 가장 잦은 원인은?",        # 집계 낱말 2개
    "타임아웃 장애는 몇 건인가?",            # "몇 건"
    "김지훈과 함께 일한 담당자는 누구?",     # 다중홉 낱말 2개
    "커넥션 풀 관련 문서를 공통으로 다룬 사람은?",  # 다중홉 낱말 2개
    "가장 자주 함께 등장한 원인은?",         # 집계+다중홉 동시 → 집계가 이김
]

print(f"{'질문':<32} {'라우팅':<8} 걸린 낱말")
print("-" * 60)
for q in questions:
    r, hit = route_traced(q)
    print(f"{q:<32} {r:<8} {hit or '(없음 → 기본값)'}")
# 출력: 재고 서비스 장애 원인은?                 사실조회     (없음 → 기본값)
# 출력: 전체 장애 중 가장 잦은 원인은?           전역집계     ['전체', '가장']
# 출력: 타임아웃 장애는 몇 건인가?               전역집계     ['몇 건']
# 출력: 김지훈과 함께 일한 담당자는 누구?         다중홉      ['누구', '함께']
# 출력: 커넥션 풀 관련 문서를 공통으로 다룬 사람은?    다중홉      ['공통', '관련']
# 출력: 가장 자주 함께 등장한 원인은?            전역집계     ['가장', '자주']

# %% [markdown]
# 마지막 질문이 핵심이다. "함께"(다중홉 낱말)가 있어도 "가장", "자주"(집계 낱말)가
# **먼저 검사되므로** 전역집계로 간다. `if`의 순서가 곧 우선순위 설계다.
#
# ## 이 라우터의 약점 — 낱말이 없으면 무조건 사실조회
#
# 집계 의도인데 집계 낱말을 안 쓴 질문은 그대로 벡터 검색(사실조회)으로 흘러간다.
# 그러면 빈 답이 아니라 **그럴듯한 오답**이 나온다 — 이게 17.2절의 요지다.

# %%
tricky = [
    ("장애 원인 순위를 알려줘", "전역집계"),      # '순위'는 목록에 없음
    ("타임아웃 건수는?", "전역집계"),             # '건수'만으로는 안 걸림
    ("두 사람이 겹치는 문서는?", "다중홉"),       # '겹치는'은 목록에 없음
]

for q, real in tricky:
    r = route(q)
    mark = "정상" if r == real else f"오라우팅! (실제 의도: {real})"
    print(f"«{q}» → {r:<6} {mark}")
# 출력: «장애 원인 순위를 알려줘» → 사실조회   오라우팅! (실제 의도: 전역집계)
# 출력: «타임아웃 건수는?» → 사실조회   오라우팅! (실제 의도: 전역집계)
# 출력: «두 사람이 겹치는 문서는?» → 사실조회   오라우팅! (실제 의도: 다중홉)

# %% [markdown]
# ## 판정 흐름 시각화
#
# 질문 하나가 세 단계 필터를 차례로 통과하는 구조를 그림으로 본다.

# %%
import plotly.graph_objects as go

fig = go.Figure()

# 판정 단계 상자 (위 → 아래)
steps = [
    (0.5, 0.90, "질문 q", "#94a3b8"),
    (0.5, 0.68, "집계 낱말 있나?<br>전체·몇 건·가장·자주·평균·총 …", "#f59e0b"),
    (0.5, 0.40, "다중홉 낱말 있나?<br>공통·누구·관련·함께·같은", "#3b82f6"),
    (0.5, 0.12, "기본값", "#64748b"),
]
engines = [
    (0.88, 0.68, "전역집계", "#f59e0b"),
    (0.88, 0.40, "다중홉<br>(그래프 순회)", "#3b82f6"),
    (0.88, 0.12, "사실조회<br>(벡터 검색)", "#10b981"),
]

for x, y, label, color in steps:
    fig.add_shape(type="rect", x0=x - 0.22, x1=x + 0.22, y0=y - 0.075, y1=y + 0.075,
                  line=dict(color=color, width=2), fillcolor="white")
    fig.add_annotation(x=x, y=y, text=label, showarrow=False, font=dict(size=13))

for x, y, label, color in engines:
    fig.add_shape(type="rect", x0=x - 0.10, x1=x + 0.10, y0=y - 0.075, y1=y + 0.075,
                  line=dict(color=color, width=2), fillcolor=color, opacity=0.85)
    fig.add_annotation(x=x, y=y, text=f"<b>{label}</b>", showarrow=False,
                       font=dict(size=13, color="white"))

# 세로 화살표 (아니오 경로)
for y0, y1 in [(0.825, 0.755), (0.605, 0.475), (0.325, 0.195)]:
    fig.add_annotation(x=0.5, y=y1, ax=0.5, ay=y0, xref="x", yref="y",
                       axref="x", ayref="y", showarrow=True,
                       arrowhead=2, arrowwidth=2, arrowcolor="#64748b")
fig.add_annotation(x=0.545, y=0.545, text="아니오", showarrow=False, font=dict(size=11, color="#64748b"))
fig.add_annotation(x=0.545, y=0.265, text="아니오", showarrow=False, font=dict(size=11, color="#64748b"))

# 가로 화살표 (예 경로 / 기본값)
for y, txt in [(0.68, "예"), (0.40, "예"), (0.12, "")]:
    fig.add_annotation(x=0.775, y=y, ax=0.725, ay=y, xref="x", yref="y",
                       axref="x", ayref="y", showarrow=True,
                       arrowhead=2, arrowwidth=2, arrowcolor="#64748b")
    if txt:
        fig.add_annotation(x=0.745, y=y + 0.045, text=txt, showarrow=False,
                           font=dict(size=11, color="#64748b"))

fig.update_layout(
    title="ex1_routing.py 규칙 기반 라우터의 판정 흐름 (위에서 아래로, 먼저 걸리는 쪽이 이긴다)",
    xaxis=dict(visible=False, range=[0, 1.05]),
    yaxis=dict(visible=False, range=[0, 1.02]),
    width=880, height=520, plot_bgcolor="white", margin=dict(l=20, r=20, t=60, b=20),
)

_show(fig)
_here = os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else "."
fig.write_image(os.path.join(_here, "expy.png"), scale=2)
print("expy.png 저장 완료")
# 출력: expy.png 저장 완료

# %% [markdown]
# ## 정리
#
# - 판정은 **부분 문자열 매칭 두 번**이다: `any(w in q for w in AGG_WORDS)` → 전역집계,
#   `any(w in q for w in MULTI_WORDS)` → 다중홉, 나머지는 사실조회.
# - 검사 순서가 우선순위다: 집계 낱말이 다중홉 낱말보다 먼저 이긴다.
# - 목록에 없는 표현("순위", "건수", "겹치는")은 전부 사실조회로 새고, 벡터 엔진이
#   **그럴듯한 오답**을 낸다. 그래서 본문은 "규칙으로 먼저 거르고, 애매한 것만 모델에게
#   보내고, 결과를 캐시하라"고 말한다.
