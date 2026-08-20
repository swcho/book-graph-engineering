# %% [markdown]
# # `fails()` 함수는 왜 해시를 쓰는가?
#
# 18장의 `fails()`는 LLM 단계의 «실패»를 흉내 내는 가짜 함수다.
# `random.random()` 대신 **SHA-256 해시**를 쓰는 이유는 하나 —
# **결정론적 실패 판정**을 위해서다.
#
# - 단계 이름·시도 횟수·시드를 `"{step_name}|{attempt}|{seed}"`로 묶어 SHA-256으로 해싱
# - 같은 입력이면 언제 어디서 돌려도 **같은 결과**가 나온다 (재현 가능한 실험)
# - 해시 출력은 사실상 균등분포이므로, 앞 4바이트를 $[0,1)$ 실수로 바꾸면
#   $P(r < p) \approx p$ — 목표 실패 확률 $p$를 그대로 흉내 낼 수 있다
#
# $$r = \frac{\text{int}(h[0..4])}{2^{32}-1} \sim U(0,1), \qquad \text{fail} \iff r < p$$

# %%
# 필요 패키지: plotly, kaleido (시각화·PNG 저장용. 없으면 시각화 셀만 건너뜀)
import hashlib
from pathlib import Path


def _show(fig):
    try:
        from IPython import get_ipython
        if get_ipython() is not None:  # VSCode 셀/Jupyter에서만 렌더링
            fig.show()
    except ImportError:
        pass


HERE = Path(__file__).resolve().parent if "__file__" in dir() else Path.cwd()

# %% [markdown]
# ## 1. 책의 `fails()` 재구현
#
# 원본 그대로: 네 단계 각각에 실측 기반 실패 확률이 붙어 있다.

# %%
STEPS = [
    # 이름, 걸리는 시간(초), 토큰, 실패 확률
    ("문서 찾기",   12, 3_200, 0.05),
    ("요약",         8, 5_100, 0.08),
    ("초안 작성",   31, 8_400, 0.18),
    ("검토",        14, 4_300, 0.10),
]

FAIL_P = {name: p for name, _, _, p in STEPS}


def fails(step_name, attempt, seed=0):
    """결정론적 «실패» 판정. 같은 입력이면 같은 결과가 나온다."""
    h = hashlib.sha256(f"{step_name}|{attempt}|{seed}".encode()).digest()
    r = int.from_bytes(h[:4], "big") / 0xFFFFFFFF
    return r < FAIL_P[step_name]


# 내부에서 뽑히는 r 값도 따로 보고 싶으니 헬퍼를 하나 더
def draw_r(step_name, attempt, seed=0):
    h = hashlib.sha256(f"{step_name}|{attempt}|{seed}".encode()).digest()
    return int.from_bytes(h[:4], "big") / 0xFFFFFFFF


for name in FAIL_P:
    r = draw_r(name, attempt=1, seed=0)
    print(f"{name:6s}  r={r:.4f}  p={FAIL_P[name]:.2f}  -> 실패? {fails(name, 1, 0)}")
# 출력:
# 문서 찾기   r=0.9328  p=0.05  -> 실패? False
# 요약      r=0.6729  p=0.08  -> 실패? False
# 초안 작성   r=0.3421  p=0.18  -> 실패? False
# 검토      r=0.1106  p=0.10  -> 실패? False

# %% [markdown]
# ## 2. 재현성 확인 — 같은 입력이면 항상 같은 결과
#
# `random.random()`이었다면 호출할 때마다 결과가 달라져서
# «체인 vs 그래프» 비교 실험이 매번 다른 얘기를 하게 된다.
# 해시 기반이면 몇 번을 다시 돌려도, 프로세스를 재시작해도 판정이 똑같다.

# %%
# 같은 (단계, 시도, 시드)를 1000번 호출해도 결과는 하나
results = {fails("초안 작성", attempt=3, seed=7) for _ in range(1000)}
print("1000번 반복 호출 결과 집합:", results)

# 시드/시도가 바뀌면 판정도 바뀔 수 있다 (독립적인 «주사위»)
for seed in range(5):
    row = [fails("초안 작성", attempt=a, seed=seed) for a in range(1, 7)]
    print(f"seed={seed}: 시도 1~6 실패 여부 = {row}")
# 출력:
# 1000번 반복 호출 결과 집합: {False}
# seed=0: 시도 1~6 실패 여부 = [False, False, False, True, False, False]
# seed=1: 시도 1~6 실패 여부 = [False, False, False, False, False, False]
# seed=2: 시도 1~6 실패 여부 = [False, True, False, False, False, False]
# seed=3: 시도 1~6 실패 여부 = [False, False, False, False, False, False]
# seed=4: 시도 1~6 실패 여부 = [False, False, True, False, False, False]

# %% [markdown]
# ## 3. 대조: `random.random()`이었다면?
#
# 전역 난수는 호출 순서에 따라 값이 달라진다.
# 즉 «검토 단계, 3번째 시도»의 실패 여부가
# 그 앞에서 난수를 몇 번 썼는지에 **의존**하게 된다.
# 해시 방식은 입력만으로 값이 정해지므로 호출 순서와 무관하다.

# %%
import random

random.seed(42)
a = [random.random() < 0.18 for _ in range(3)]

random.seed(42)
random.random()  # 앞에서 난수를 한 번 «다른 용도»로 소비
b = [random.random() < 0.18 for _ in range(3)]

print("random 방식: 호출 순서가 다르면 판정이 어긋난다 ->", a, "vs", b)
print("해시 방식:   순서 무관, 입력이 같으면 항상",
      [fails("초안 작성", i, 42) for i in range(3)])
# 출력:
# random 방식: 호출 순서가 다르면 판정이 어긋난다 -> [False, True, False] vs [True, False, False]
# 해시 방식:   순서 무관, 입력이 같으면 항상 [True, False, False]
# (참고: random 예시의 True/False 배치는 파이썬 버전에 따라 다를 수 있음)

# %% [markdown]
# ## 4. 해시값의 균등분포 — 목표 실패율에 수렴하는가
#
# SHA-256 출력은 통계적으로 균등하므로 $r \sim U(0,1)$로 취급할 수 있고,
# 표본 수 $n$이 커지면 관측 실패율이 목표 $p$로 수렴해야 한다:
#
# $$\hat{p}_n = \frac{1}{n}\sum_{i=1}^{n} \mathbb{1}[r_i < p] \xrightarrow{n\to\infty} p$$

# %%
N = 20_000
print(f"{'단계':8s} {'목표 p':>8s} {'관측 실패율(n=20000)':>20s}")
observed = {}
for name, _, _, p in STEPS:
    hits = sum(fails(name, attempt=1, seed=s) for s in range(N))
    observed[name] = hits / N
    print(f"{name:8s} {p:8.3f} {observed[name]:20.4f}")
# 출력:
# 단계           목표 p      관측 실패율(n=20000)
# 문서 찾기       0.050               0.0527
# 요약          0.080               0.0803
# 초안 작성       0.180               0.1809
# 검토          0.100               0.0989

# %% [markdown]
# ## 5. 시각화 — 시드 수를 늘릴수록 관측 실패율이 목표선에 붙는다

# %%
try:
    import plotly.graph_objects as go

    fig = go.Figure()
    colors = ["#4C78A8", "#F58518", "#54A24B", "#B279A2"]
    ns = list(range(200, N + 1, 200))

    for (name, _, _, p), c in zip(STEPS, colors):
        flags = [fails(name, attempt=1, seed=s) for s in range(N)]
        cum, running = [], 0
        for i, f in enumerate(flags, 1):
            running += f
            if i % 200 == 0:
                cum.append(running / i)
        fig.add_trace(go.Scatter(x=ns, y=cum, mode="lines",
                                 name=f"{name} (p={p})", line=dict(color=c)))
        fig.add_hline(y=p, line=dict(color=c, dash="dot", width=1))

    fig.update_layout(
        title="SHA-256 기반 fails(): 누적 관측 실패율의 목표 확률 수렴",
        xaxis_title="시드 표본 수 n", yaxis_title="누적 실패율",
        template="plotly_white", width=820, height=480,
        legend=dict(orientation="h", y=-0.2),
    )
    _show(fig)
    fig.write_image(str(HERE / "expy.png"), scale=2)  # kaleido 필요
    print("expy.png 저장 완료")
except ImportError as e:
    print("시각화 건너뜀 (패키지 없음):", e)
# 출력:
# expy.png 저장 완료

# %% [markdown]
# ## 정리
#
# | 방식 | 재현성 | 균등분포 | 호출 순서 의존 |
# |---|---|---|---|
# | `random.random()` | 시드 고정해도 호출 순서에 민감 | O | **O (문제)** |
# | SHA-256 해시 | 입력만으로 완전 결정 | O (통계적 균등) | X |
#
# 요컨대 `fails()`는 해시를 **«입력에만 의존하는 순수 함수형 난수»**로 쓴다.
# 덕분에 API 키 없이도, 몇 번을 다시 돌려도 똑같이 재현되는 실험이 되면서
# 실패 확률 자체는 실측값 $p$를 정확히 따라간다.
