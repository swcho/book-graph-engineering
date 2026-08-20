# %% [markdown]
# # `ex2_idempotency.py` — 세 시나리오는 어떻게 갈리는가
#
# 프로세스가 죽었다 재개되면 「이미 한 일」을 다시 한다. 그게 결제라면?
# 재시도(= 죽었다 재개) 3회를 시뮬레이션해 세 시나리오를 비교한다.
#
# | 시나리오 | 우리가 키를 보내는가 | 서버가 키를 보는가 | 결과 |
# |---|---|---|---|
# | 멱등 키 없음 | ✗ | (지원함) | 3건, 15만 원 |
# | 멱등 키 있음 + 서버 지원 | ✓ | ✓ | **1건, 5만 원** |
# | 멱등 키 있음 + 서버 미지원 | ✓ | ✗ | 3건, 15만 원 |
#
# 멱등성이란 같은 요청을 $n$번 보내도 효과가 1번과 같은 성질:
#
# $$f(f(x)) = f(x)$$
#
# 결제 금액으로 쓰면, 시도 횟수 $n$에 대해
# 멱등이 성립할 때만 $\text{총액} = 50{,}000$원이고,
# 아니면 $\text{총액} = 50{,}000 \times n$원이 된다.

# %%
# 필요 패키지: plotly, kaleido (시각화 셀에만 필요. 시뮬레이션 자체는 의존성 없음)
import os


def _show(fig):
    try:
        from IPython import get_ipython
        if get_ipython() is not None:  # VSCode 셀/Jupyter에서만 렌더링
            fig.show()
    except ImportError:
        pass


# %% [markdown]
# ## 1. 가짜 결제 API
#
# 핵심은 **서버 측 멱등 키 저장소**(`seen_keys`)의 유무 토글이다.
# - `idempotent=True` 이고 키가 오면: 처음 본 키만 결제하고, 같은 키는 캐시된 영수증을 돌려준다.
# - `idempotent=False` 이거나 키가 없으면: 올 때마다 새로 결제한다.

# %%
class PaymentAPI:
    """외부 결제 API 흉내. 멱등 키를 지원하는 판과 아닌 판."""

    def __init__(self, idempotent):
        self.idempotent = idempotent   # 서버가 멱등 키를 보는가?
        self.charges = []              # 실제로 일어난 결제들
        self.seen_keys = {}            # 서버 측 멱등 키 저장소

    def charge(self, order_id, amount, key=None):
        if self.idempotent and key is not None:
            if key in self.seen_keys:
                return self.seen_keys[key], "캐시된 결과"   # 결제 안 함!
            receipt = f"R-{len(self.charges) + 1:03d}"
            self.charges.append((order_id, amount, receipt))
            self.seen_keys[key] = receipt
            return receipt, "새 결제"
        # 키가 없거나, 서버가 키를 무시하면 → 매번 새 결제
        receipt = f"R-{len(self.charges) + 1:03d}"
        self.charges.append((order_id, amount, receipt))
        return receipt, "새 결제"


# %% [markdown]
# ## 2. 재시도 루프 — 「죽었다 재개」의 반복
#
# 클라이언트는 같은 주문을 3번 보낸다. 멱등 키를 보낼지는 `use_key`로 토글.

# %%
def run(api, attempts, use_key):
    """attempts 번 재시도한다. 실제로는 «죽었다 재개»가 반복되는 것."""
    log = []
    for i in range(attempts):
        key = "order-8842" if use_key else None
        receipt, how = api.charge("order-8842", 50_000, key)
        log.append(f"시도 {i + 1}: {receipt} ({how})")
    return log


# %% [markdown]
# ## 3. 세 시나리오 실행
#
# 원본 예제와 같은 세 조합. 확인할 것은 둘이다.
# 1. **우리가 키를 보내는가** (`use_key`)
# 2. **상대가 그 키를 보는가** (`idempotent`)
#
# 둘 다 참이어야 멱등이 성립한다 — 논리곱: $\text{안전} = \text{키 전송} \land \text{서버 지원}$

# %%
cases = [
    ("멱등 키 없음",            PaymentAPI(idempotent=True),  False),
    ("멱등 키 있음 + 서버 지원",  PaymentAPI(idempotent=True),  True),
    ("멱등 키 있음 + 서버 미지원", PaymentAPI(idempotent=False), True),
]

results = []
for name, api, use_key in cases:
    log = run(api, 3, use_key)
    total = sum(a for _, a, _ in api.charges)
    results.append((name, len(api.charges), total))
    print(f"[{name}]")
    for line in log:
        print(f"    {line}")
    print(f"    실제 결제 {len(api.charges)}건, 합계 {total:,}원\n")

# 출력:
# [멱등 키 없음]
#     시도 1: R-001 (새 결제)
#     시도 2: R-002 (새 결제)
#     시도 3: R-003 (새 결제)
#     실제 결제 3건, 합계 150,000원
#
# [멱등 키 있음 + 서버 지원]
#     시도 1: R-001 (새 결제)
#     시도 2: R-001 (캐시된 결과)
#     시도 3: R-001 (캐시된 결과)
#     실제 결제 1건, 합계 50,000원
#
# [멱등 키 있음 + 서버 미지원]
#     시도 1: R-001 (새 결제)
#     시도 2: R-002 (새 결제)
#     시도 3: R-003 (새 결제)
#     실제 결제 3건, 합계 150,000원

# %% [markdown]
# ## 4. 결과 검증
#
# 답: **멱등 키가 있고 서버가 지원하는 경우만 5만 원 1건**, 나머지 둘은 15만 원 3건.
#
# 세 번째 시나리오가 특히 흥미롭다 — 우리가 키를 *보냈는데도* 중복이 났다.
# 받는 쪽이 지원해야 소용이 있는 것이다.

# %%
assert results[0] == ("멱등 키 없음", 3, 150_000)
assert results[1] == ("멱등 키 있음 + 서버 지원", 1, 50_000)
assert results[2] == ("멱등 키 있음 + 서버 미지원", 3, 150_000)
print("검증 통과: 키 전송 ∧ 서버 지원 조합만 1건 5만 원")

# 출력:
# 검증 통과: 키 전송 ∧ 서버 지원 조합만 1건 5만 원

# %% [markdown]
# ## 5. 시각화 — 시나리오별 실제 결제 총액

# %%
try:
    import plotly.graph_objects as go

    names = [r[0] for r in results]
    totals = [r[2] for r in results]
    counts = [r[1] for r in results]
    safe = [t == 50_000 for t in totals]

    # 색은 개체의 의미를 따른다: 멱등 성립(파랑) vs 중복 결제(회색)
    BLUE, GRAY = "#2a78d6", "#b7b5ac"
    colors = [BLUE if s else GRAY for s in safe]
    labels = [
        f"{t // 10_000}만 원 · {c}건" + ("  (멱등 성립)" if s else "  (중복!)")
        for t, c, s in zip(totals, counts, safe)
    ]

    fig = go.Figure(
        go.Bar(
            x=totals,
            y=names,
            orientation="h",
            marker=dict(color=colors, cornerradius=4),
            width=0.55,
            text=labels,
            textposition="outside",
            textfont=dict(size=13, color="#0b0b0b"),
        )
    )
    fig.update_layout(
        title="같은 주문을 3번 재시도하면 얼마가 결제되는가",
        xaxis=dict(
            title="실제 결제 총액 (원)",
            range=[0, 195_000],
            tickvals=[0, 50_000, 100_000, 150_000],
            ticktext=["0", "5만", "10만", "15만"],
            gridcolor="#e8e7e2",
            zerolinecolor="#c9c8c1",
        ),
        yaxis=dict(autorange="reversed"),
        plot_bgcolor="#fcfcfb",
        paper_bgcolor="#fcfcfb",
        font=dict(color="#0b0b0b", size=13),
        margin=dict(l=10, r=30, t=60, b=50),
        width=880,
        height=380,
        showlegend=False,
    )
    _show(fig)

    png_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "expy.png")
    fig.write_image(png_path, scale=2)
    print(f"저장: {png_path}")
except ImportError as e:
    print(f"시각화 생략 (plotly/kaleido 없음): {e}")

# 출력:
# 저장: .../hints/e7f3ad98-a62d-478c-92c3-e4a588899f23/expy.png

# %% [markdown]
# ## 정리
#
# - **멱등 키 없음** → 3회 시도 = 3건 결제, 15만 원. 서버가 요청을 구별할 방법이 없다.
# - **키 있음 + 서버 미지원** → 역시 3건, 15만 원. 키를 보내도 받는 쪽이 무시하면 무의미.
# - **키 있음 + 서버 지원** → 1건, 5만 원. 2·3번째 시도는 캐시된 영수증 `R-001`을 돌려받는다.
#
# 체크포인터가 「재개」를 공짜로 만들어 줘도, 부작용(결제)의 안전은
# **클라이언트의 키 전송과 서버의 키 인식이 모두** 갖춰져야 성립한다.
