# 필요 패키지: plotly, kaleido (pip install plotly kaleido)
# 표준 라이브러리만으로 마이크로벤치마크를 돌리고, 그래프 저장에만 plotly/kaleido를 쓴다.
# 아래 `# 출력:` 주석은 실제 실행 결과다(macOS/Python 3.9, 전체 6초).
# t_event 는 기계·실행마다 ±30% 정도 흔들리고, 뒤의 모든 숫자가 거기서 파생되므로
# 자릿수는 같아도 세부 값은 재실행 때 달라진다.

# %% [markdown]
# # 스냅숏 주기 $k$ 의 교환 관계
#
# 이벤트 소싱에서 현재 상태는 이벤트를 **접어서(fold)** 만든다.
# 이벤트가 $n$ 개 쌓였을 때 처음부터 재생하면 $n \cdot t_{event}$ 가 걸린다.
# 스냅숏을 $k$ 이벤트마다 찍어 두면 재생해야 할 것은 **마지막 스냅숏 이후 꼬리뿐**이라
# 재생 시간이 데이터 양 $n$ 이 아니라 주기 $k$ 로 정해진다.
#
# $$T_{replay}(k) \approx k \cdot t_{event} \qquad (\text{최악의 경우, 꼬리가 꽉 찼을 때})$$
#
# 대신 스냅숏 자체가 공간을 먹는다. 이벤트 $n$ 개 구간에 스냅숏은 $n/k$ 개 생긴다.
#
# $$S_{snap}(k) \approx \frac{n}{k} \cdot s_{snap}$$
#
# 하나는 $k$ 에 **비례**하고 하나는 $k$ 에 **반비례**한다. 그래서 교환 관계다.
#
# - $k$ 를 **짧게** → 재생 빠름, 스냅숏 저장 공간 늘어남
# - $k$ 를 **길게** → 공간 아낌, 복구 느려짐
#
# 이 노트북은 (1) 실제 재생 마이크로벤치마크로 $t_{event}$ 를 재고,
# (2) 두 비용 곡선과 가중 총비용의 최소점을 구하고,
# (3) 복구 목표 시간(RTO) 제약에서 $k_{max}$ 를 역산한다.

# %%
import math
import random
import time

import plotly.graph_objects as go


def _show(fig):
    try:
        from IPython import get_ipython
        if get_ipython() is not None:
            fig.show()
    except ImportError:
        pass


print("준비 완료")
# 출력: 준비 완료

# %% [markdown]
# ## 1. 마이크로벤치마크 — $t_{event}$ 를 실측한다
#
# 30장 `ex2_replay_cost.py` 와 같은 모양의 장난감 리듀서를 쓴다.
# 이벤트는 `(i, 주체, 관계, 대상, 연산)` 이고, 상태는 삼중항 집합이다.
# `추가` 면 넣고 `삭제` 면 뺀다 — 이벤트 하나당 해시 집합 연산 한 번.

# %%
rng = random.Random(11)


def make_events(n):
    out = []
    for i in range(n):
        s = f"e{rng.randint(0, 400)}"
        o = f"t{rng.randint(0, 40)}"
        op = "추가" if rng.random() < 0.72 else "삭제"
        out.append((i, s, "속함", o, op))
    return out


def replay(events, start_state=None):
    st = set(start_state) if start_state else set()
    for _i, s, k, o, op in events:
        if op == "추가":
            st.add((s, k, o))
        else:
            st.discard((s, k, o))
    return st


BENCH_N = 400_000
bench_events = make_events(BENCH_N)

# 워밍업 한 번, 그다음 3회 측정해서 중앙값
replay(bench_events[:20_000])
samples = []
for _ in range(3):
    t0 = time.perf_counter()
    state = replay(bench_events)
    samples.append(time.perf_counter() - t0)
samples.sort()
elapsed = samples[1]

T_EVENT = elapsed / BENCH_N          # 초/이벤트
print(f"이벤트 {BENCH_N:,} 개 재생: {elapsed * 1000:.1f} ms (3회 중앙값)")
print(f"t_event = {T_EVENT * 1e6:.3f} us/이벤트  ({1 / T_EVENT:,.0f} 이벤트/초)")
print(f"최종 상태 삼중항 수: {len(state):,}")
# 출력: 이벤트 400,000 개 재생: 93.9 ms (3회 중앙값)
# 출력: t_event = 0.235 us/이벤트  (4,261,311 이벤트/초)
# 출력: 최종 상태 삼중항 수: 11,823
# (시간 값은 기계마다 다르다. 아래 모든 계산은 이 실측값에서 파생된다.)

# %% [markdown]
# ## 2. 스냅숏 크기 $s_{snap}$ 도 실측한다
#
# 스냅숏은 「그 시점의 상태 전체」다. 위에서 나온 상태를 직렬화해서
# **삼중항 하나당 바이트 수**를 재고, 실제 규모의 그래프(삼중항 2천만 개)로 늘려 잡는다.
# 벤치마크 상태는 장난감 크기라 그대로 쓰면 저장 비용이 없는 셈이 되어 버린다.

# %%
snap_blob = "\n".join(f"{s}\t{k}\t{o}" for s, k, o in sorted(state)).encode()
BYTES_PER_TRIPLE = len(snap_blob) / len(state)

STATE_TRIPLES = 20_000_000                   # 모델링할 백본 그래프의 삼중항 수
S_SNAP = BYTES_PER_TRIPLE * STATE_TRIPLES    # 바이트/스냅숏
EVENT_BYTES = 48                             # 이벤트 하나의 대략적 저장 크기(참고용)

print(f"벤치마크 스냅숏: {len(snap_blob):,} bytes / 삼중항 {len(state):,} 개")
print(f"삼중항당 {BYTES_PER_TRIPLE:.1f} bytes")
print(f"→ 삼중항 {STATE_TRIPLES:,} 개 규모 s_snap = {S_SNAP / 1024 ** 3:.2f} GiB")
print(f"스냅숏 1개 = 이벤트 {S_SNAP / EVENT_BYTES:,.0f} 개어치 공간")
# 출력: 벤치마크 스냅숏: 183,010 bytes / 삼중항 11,823 개
# 출력: 삼중항당 15.5 bytes
# 출력: → 삼중항 20,000,000 개 규모 s_snap = 0.29 GiB
# 출력: 스냅숏 1개 = 이벤트 6,449,646 개어치 공간

# %% [markdown]
# ## 3. 두 비용 곡선과 총비용
#
# 총 이벤트 $n$ 을 고정하고 $k$ 를 훑는다. 총비용은 단위가 다른 두 값(초와 바이트)을
# 섞어야 하므로 가중합으로 정의한다.
#
# $$C(k) = w_t \cdot k\,t_{event} \;+\; w_s \cdot \frac{n}{k}\,s_{snap}$$
#
# $w_t$ 는 「재생 1초의 값어치」, $w_s$ 는 「저장 1바이트의 값어치」다.
# 미분해서 0으로 두면 최소점이 닫힌 형태로 나온다.
#
# $$k^{*} = \sqrt{\frac{w_s\, n\, s_{snap}}{w_t\, t_{event}}}$$
#
# 여기서는 재생 1초를 $1\,\text{원}$, 저장 1 GiB 를 $0.02\,\text{원}$ 으로 잡았다
# (운영 비용 감각을 아무렇게나 넣은 값이니, 자기 환경 숫자로 바꿔서 보면 된다).

# %%
N_TOTAL = 50_000_000            # 누적 이벤트 수
W_T = 1.0                       # 원 / 재생 1초
W_S = 0.02 / (1024 ** 3)        # 원 / 저장 1바이트

ks = [int(round(10 ** (i / 20))) for i in range(60, 161)]   # 1e3 ~ 1e8, 로그 등간격
ks = sorted(set(k for k in ks if k >= 1000))

replay_s = [k * T_EVENT for k in ks]
storage_b = [(N_TOTAL / k) * S_SNAP for k in ks]
total = [W_T * r + W_S * s for r, s in zip(replay_s, storage_b)]

i_min = min(range(len(ks)), key=lambda i: total[i])
k_star_exact = math.sqrt(W_S * N_TOTAL * S_SNAP / (W_T * T_EVENT))

print(f"n = {N_TOTAL:,} 이벤트")
print(f"격자 최소점  k = {ks[i_min]:,}  총비용 {total[i_min]:.2f} 원")
print(f"  재생 {replay_s[i_min]:.2f} s, 스냅숏 {storage_b[i_min] / 1024 ** 3:.2f} GiB")
print(f"닫힌 해   k* = {k_star_exact:,.0f}")
# 출력: n = 50,000,000 이벤트
# 출력: 격자 최소점  k = 1,122,018  총비용 0.52 원
# 출력:   재생 0.26 s, 스냅숏 12.85 GiB
# 출력: 닫힌 해   k* = 1,108,435
# (최소점에서 두 비용의 «기여분»이 서로 같아진다 — 0.26원 vs 0.26원. 이게 교환 관계의 균형점이다.)

# %% [markdown]
# ## 4. 복구 목표 시간(RTO)에서 $k_{max}$ 를 역산한다
#
# 최적화보다 먼저 오는 것은 **제약**이다. 30장의 조언이 그거다 —
# 「3초 안에 복구」가 목표면 3초에 재생할 수 있는 이벤트 수를 재고 그만큼을 주기로 잡는다.
#
# $$k_{max} = \frac{\text{RTO} \cdot \alpha}{t_{event}}$$
#
# $\alpha$ 는 안전 여유(스냅숏 적재, 디스크 I/O, 콜드 캐시 몫). 여기서는 $\alpha = 0.5$,
# 즉 예산의 절반만 순수 재생에 쓴다고 본다.

# %%
ALPHA = 0.5


def plan(rto):
    """RTO 로 상한을 긋고, 그 안에서 비용 최소점을 고른다."""
    k_max = (rto * ALPHA) / T_EVENT
    k = min(k_max, k_star_exact)
    return k_max, k, k * T_EVENT, (N_TOTAL / k) * S_SNAP / 1024 ** 3


print(f"{'RTO(s)':>7}{'k_max':>14}{'채택 k':>14}{'최악 재생(s)':>14}"
      f"{'스냅숏 수':>11}{'스냅숏 공간(GiB)':>18}{'제약':>8}")
print("-" * 88)
for rto in (0.1, 0.2, 0.5, 1.0, 3.0, 10.0):
    k_max, k, t, gib = plan(rto)
    tag = "RTO" if k_max < k_star_exact else "비용"
    print(f"{rto:>7.1f}{k_max:>14,.0f}{k:>14,.0f}{t:>14.2f}"
          f"{N_TOTAL / k:>11,.0f}{gib:>18.1f}{tag:>8}")

RTO = 0.5
K_MAX, K_CHOSEN, T_WORST, GIB = plan(RTO)
print(f"\n[선택 시나리오] RTO = {RTO}s, 안전 여유 alpha = {ALPHA}")
print(f"  k_max = RTO*alpha / t_event = {RTO}*{ALPHA} / {T_EVENT * 1e6:.3f}us = {K_MAX:,.0f}")
print(f"  비용 최소점 k*                                        = {k_star_exact:,.0f}")
print(f"  채택 k = min(k_max, k*)                              = {K_CHOSEN:,.0f}")
print(f"  → 최악 재생 {T_WORST:.2f}s, 스냅숏 {N_TOTAL / K_CHOSEN:,.0f}개 {GIB:.1f} GiB")
# 출력:  RTO(s)         k_max        채택 k    최악 재생(s)     스냅숏 수    스냅숏 공간(GiB)      제약
# 출력: ----------------------------------------------------------------------------------------
# 출력:    0.1       213,066       213,066          0.05       235             67.7     RTO
# 출력:    0.2       426,131       426,131          0.10       117             33.8     RTO
# 출력:    0.5     1,065,328     1,065,328          0.25        47             13.5     RTO
# 출력:    1.0     2,130,655     1,108,435          0.26        45             13.0      비용
# 출력:    3.0     6,391,966     1,108,435          0.26        45             13.0      비용
# 출력:   10.0    21,306,553     1,108,435          0.26        45             13.0      비용
# 출력:
# 출력: [선택 시나리오] RTO = 0.5s, 안전 여유 alpha = 0.5
# 출력:   k_max = RTO*alpha / t_event = 0.5*0.5 / 0.235us = 1,065,328
# 출력:   비용 최소점 k*                                        = 1,108,435
# 출력:   채택 k = min(k_max, k*)                              = 1,065,328
# 출력:   → 최악 재생 0.25s, 스냅숏 47개 13.5 GiB
#
# 주의: "스냅숏 공간"은 n 구간의 스냅숏을 모두 보관할 때의 값이다 (n/k 개 x s_snap).
#       RTO 가 빡빡할수록(위쪽 행) k 가 작아지고 공간이 그만큼 커진다 — 이게 교환 관계다.

# %% [markdown]
# ## 5. 그래프 — 재생 시간, 스냅숏 공간, 총비용
#
# 로그 x축에서 보면 두 비용이 서로 반대 방향의 직선이고, 합이 V자를 그린다.
# 왼쪽 벽은 저장 비용, 오른쪽 벽은 복구 시간, 그리고 RTO 선이 오른쪽을 잘라 낸다.

# %%
fig = go.Figure()

fig.add_trace(go.Scatter(
    x=ks, y=replay_s, name="재생 시간 (s)", yaxis="y",
    mode="lines", line=dict(color="#2563eb", width=2)))
fig.add_trace(go.Scatter(
    x=ks, y=[b / 1024 ** 3 for b in storage_b], name="스냅숏 공간 (GiB)", yaxis="y",
    mode="lines", line=dict(color="#16a34a", width=2)))
fig.add_trace(go.Scatter(
    x=ks, y=total, name="총비용 (원, 가중합)", yaxis="y",
    mode="lines", line=dict(color="#dc2626", width=3, dash="dot")))
fig.add_trace(go.Scatter(
    x=[ks[i_min]], y=[total[i_min]], name=f"최소점 k*={k_star_exact:,.0f}",
    mode="markers", marker=dict(color="#dc2626", size=12, symbol="diamond")))

fig.add_trace(go.Scatter(
    x=[K_MAX, K_MAX], y=[min(replay_s), max(storage_b) / 1024 ** 3],
    name=f"RTO {RTO}s → k_max={K_MAX:,.0f}",
    mode="lines", line=dict(color="#f59e0b", width=2, dash="dash")))
fig.add_annotation(x=math.log10(K_MAX), y=math.log10(max(storage_b) / 1024 ** 3),
                   text=f"RTO {RTO}s 상한<br>k_max={K_MAX:,.0f}",
                   showarrow=False, xanchor="right", yanchor="top",
                   font=dict(color="#b45309", size=12), bgcolor="rgba(255,255,255,0.7)")

fig.update_layout(
    title=dict(text="스냅숏 주기 k 의 교환 관계 — 재생 시간 vs 스냅숏 공간"),
    xaxis=dict(title="스냅숏 주기 k (이벤트)", type="log"),
    yaxis=dict(title="비용 (로그 축: 초 / GiB / 원)", type="log"),
    legend=dict(orientation="h", y=-0.2),
    template="plotly_white", width=1000, height=600)

fig.write_image("expy.png")
_show(fig)
print("expy.png 저장 완료")
# 출력: expy.png 저장 완료

# %% [markdown]
# ## 정리
#
# - 재생 시간은 $n$ 이 아니라 $k$ 가 정한다. 이벤트가 5천만 개든 5억 개든 재생할 것은 최대 $k$ 개다.
# - 짧은 $k$: 재생 빠름 / 스냅숏 개수 $n/k$ 가 늘어 저장 공간 폭증.
# - 긴 $k$: 공간 아낌 / 최악 복구 시간 $k \cdot t_{event}$ 가 길어짐.
# - **순서는 이렇다**: 먼저 RTO 로 $k_{max}$ 를 역산해 상한을 긋고,
#   그 안에서 비용 최소점 $k^{*}$ 를 고른다 — $k = \min(k_{max}, k^{*})$.
# - 이건 새로 발명한 게 아니다. 데이터베이스의 WAL + 체크포인트가 정확히 같은 계산을 한다.
