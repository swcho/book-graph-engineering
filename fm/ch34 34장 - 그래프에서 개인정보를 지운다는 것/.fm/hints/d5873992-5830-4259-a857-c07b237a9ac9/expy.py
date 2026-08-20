# %% [markdown]
# # 식별자를 끊어도 (시각, 장소) 조합이 남으면 뚫린다
#
# **질문**: 식별자 끊기의 함정은 무엇인가?
#
# **답**: "2026년 3월 12일 14시 3분 마포에서 결제" 같은 조합이 남으면 재식별이 가능하다.
#
# 34장 `ex2_delete_levels.py` 는 「지운다」의 2번 수준(식별자 끊기)에서
# *다른 데이터와 못 잇는다* 칸이 `✗` 라고 적어 두었다.
# 이 노트북은 그 `✗` 를 숫자로 재현한다.
#
# 실험 순서는 이렇다.
#
# 1. **가상 결제 로그**를 만든다. 사용자 id 는 이미 토큰(`tk-0000`)으로 치환된 상태다.
#    이름·카드번호·연락처는 어디에도 없다. 즉 «식별자 끊기»가 이미 끝난 데이터다.
# 2. 시각 해상도(분 / 10분 / 시 / 6시간 / 일)와 장소 해상도(동 / 구 / 시)를 바꿔 가며
#    `(시각, 장소)` 조합의 **유일성 비율**과 **k-익명성 위반 레코드 수**를 센다.
# 3. 카드 명세서·SNS 체크인 같은 **외부 데이터와의 링크 공격**을 시뮬레이션한다.
#    시공간 지점 $m$ 개를 알 때 토큰이 하나로 좁혀지는 비율을 $m=1..4$ 로 잰다.
#    (de Montjoye 등, *Unique in the shopping mall*, Science 2015 — 신용카드
#    메타데이터에서 시공간 지점 4개로 90% 재식별)
# 4. **일반화·억제·잡음**이 유일성을 얼마나 줄이는지, 그리고 그 대가로
#    **시간대별 분석 해상도**가 얼마나 깎이는지 트레이드오프를 본다.
#
# ## 왜 유일성이 곧 재식별인가
#
# 준식별자(quasi-identifier) 집합 $Q$ 에 대해 공개 레코드 $r$ 의 동치류를
# $E_Q(r) = \{r' : r'[Q] = r[Q]\}$ 라 하자. k-익명성은
#
# $$\min_{r} |E_Q(r)| \ge k$$
#
# 를 요구한다. $|E_Q(r)| = 1$ 이면 그 레코드는 $Q$ 만으로 유일하게 지목되고,
# 외부 데이터가 같은 $Q$ 를 갖고 있으면 조인 한 번으로 실명이 붙는다.
#
# 시공간 지점을 $m$ 개 쓸 때 후보가 남을 확률은 대략
#
# $$\Pr[\text{유일}] \approx \left(1 - \frac{1}{C}\right)^{N-1},\qquad
# C = (\text{시각 칸 수} \times \text{장소 칸 수})^{m}$$
#
# 로 $m$ 에 대해 **지수적으로** 커진다. 그래서 34장 `ex3` 가 말한
# "셋에서 넷으로 갈 때의 절벽"이 여기서도 그대로 나온다.

# %%
# 필요 패키지: plotly, kaleido (expy.png 저장용)
#   pip install plotly kaleido
# 확인 환경: Python 3.9.6 / plotly 6.8.0
# 난수 seed 고정: SEED = 34

import random
from collections import Counter, defaultdict
from datetime import datetime, timedelta

SEED = 34
rng = random.Random(SEED)


def _show(fig):
    try:
        from IPython import get_ipython
        if get_ipython() is not None:
            fig.show()
    except ImportError:
        pass


# %% [markdown]
# ## 1. 가상 결제 로그 — 식별자는 이미 끊었다
#
# 행정구역을 3단계로 둔다. 시(3) → 구(12) → 동(48).
# 사용자는 «주 생활권» 구가 하나 있고, 결제의 대부분을 거기서 한다.
# 시각은 분 단위까지 기록되고, 시간대 분포에는 출근·점심·퇴근 피크를 넣는다.
#
# 중요한 점은 이 로그에 **이름·카드번호·연락처가 하나도 없다**는 것이다.
# `user` 칸은 `tk-0000` 같은 토큰뿐이다. 34장 표현대로 "사람은 못 알아보는데 구조는 남는다".

# %%
SI_GU = {
    "서울": ["마포", "용산", "강남", "성동", "영등포", "종로"],
    "성남": ["분당", "수정", "중원"],
    "고양": ["일산동", "일산서", "덕양"],
}
# 구마다 동 4개 → 동 48개
PLACES = []            # (si, gu, dong)
GU_TO_DONGS = defaultdict(list)
for si, gus in SI_GU.items():
    for gu in gus:
        for n in range(1, 5):
            p = (si, gu, f"{gu}{n}동")
            PLACES.append(p)
            GU_TO_DONGS[gu].append(p)

# 시간대 가중치 — 8시 출근, 12~13시 점심, 18~20시 퇴근 피크
HOUR_W = [1, 1, 1, 1, 1, 2, 4, 7, 10, 7, 6, 9,
          14, 12, 8, 7, 7, 9, 13, 12, 9, 6, 4, 2]

N_USERS = 1200
BASE = datetime(2026, 3, 1)
DAYS = 30
ALL_GU = [g for gus in SI_GU.values() for g in gus]


def make_log():
    log = []
    for u in range(N_USERS):
        token = f"tk-{u:04d}"
        home = ALL_GU[u % len(ALL_GU)]
        n_tx = rng.randint(10, 30)
        for _ in range(n_tx):
            # 80% 는 주 생활권, 20% 는 그 밖
            if rng.random() < 0.8:
                si, gu, dong = rng.choice(GU_TO_DONGS[home])
            else:
                si, gu, dong = rng.choice(PLACES)
            day = rng.randrange(DAYS)
            hour = rng.choices(range(24), weights=HOUR_W, k=1)[0]
            minute = rng.randrange(60)
            dt = BASE + timedelta(days=day, hours=hour, minutes=minute)
            log.append({"user": token, "dt": dt,
                        "si": si, "gu": gu, "dong": dong,
                        "amount": rng.randrange(3, 90) * 1000})
    log.sort(key=lambda r: (r["user"], r["dt"]))
    return log


LOG = make_log()

# 답에 나온 그 레코드를 명시적으로 하나 심어 둔다
TARGET = {"user": "tk-0000", "dt": datetime(2026, 3, 12, 14, 3),
          "si": "서울", "gu": "마포", "dong": "마포2동", "amount": 12000}
LOG.append(TARGET)
LOG.sort(key=lambda r: (r["user"], r["dt"]))

print(f"레코드 {len(LOG):,}개 / 토큰 {N_USERS:,}개 / "
      f"기간 {DAYS}일 / 동 {len(PLACES)}개")
print("컬럼:", ", ".join(LOG[0].keys()))
print("\n샘플 (이름·카드번호 없음):")
for r in LOG[:4]:
    print(f"  {r['user']}  {r['dt']:%Y-%m-%d %H:%M}  "
          f"{r['si']} {r['gu']} {r['dong']}  {r['amount']:,}원")
# 출력:
# 레코드 24,083개 / 토큰 1,200개 / 기간 30일 / 동 48개
# 컬럼: user, dt, si, gu, dong, amount
#
# 샘플 (이름·카드번호 없음):
#   tk-0000  2026-03-01 12:29  서울 마포 마포4동  82,000원
#   tk-0000  2026-03-03 20:33  서울 마포 마포3동  16,000원
#   tk-0000  2026-03-04 11:39  서울 마포 마포2동  3,000원
#   tk-0000  2026-03-04 13:38  서울 강남 강남2동  25,000원

# %% [markdown]
# ## 2. 해상도를 바꿔 가며 준식별자를 만든다
#
# 준식별자(quasi-identifier)는 «그것 하나로는 식별자가 아니지만 조합하면 식별자가 되는 속성»이다.
# 여기서는 `(시각 버킷, 장소 버킷)` 둘뿐이다. 금액은 일단 뺀다.
#
# 시각 해상도를 분 단위로 두면 30일은 $30 \times 24 \times 60 = 43{,}200$ 칸이 되고,
# 동 48개와 곱하면 칸이 200만 개가 넘는다. 레코드는 2만 4천 개뿐이니
# **대부분의 칸에 사람이 하나도 없거나 하나만 있다**. 그게 함정의 정체다.

# %%
TIME_RES = [("1분", 1), ("10분", 10), ("1시간", 60), ("6시간", 360), ("1일", 1440)]
PLACE_RES = [("동", "dong"), ("구", "gu"), ("시", "si")]

EPOCH = BASE


def t_bucket(dt, minutes):
    """시각을 minutes 단위 버킷의 시작 절대분으로 내린다."""
    total = int((dt - EPOCH).total_seconds() // 60)
    return (total // minutes) * minutes


def qi(rec, minutes, place_key):
    return (t_bucket(rec["dt"], minutes), rec[place_key])


def cell_space(minutes, place_key):
    n_time = (DAYS * 24 * 60) // minutes
    n_place = {"dong": len(PLACES), "gu": len(ALL_GU), "si": len(SI_GU)}[place_key]
    return n_time * n_place


K = 5


def measure(minutes, place_key, k=K):
    groups = Counter(qi(r, minutes, place_key) for r in LOG)
    n = len(LOG)
    uniq_rec = sum(c for c in groups.values() if c == 1)
    viol_rec = sum(c for c in groups.values() if c < k)
    # 토큰 관점: 유일 레코드를 하나라도 가진 토큰은 사실상 노출된다
    exposed = {r["user"] for r in LOG if groups[qi(r, minutes, place_key)] == 1}
    return {
        "cells": cell_space(minutes, place_key),
        "groups": len(groups),
        "min_k": min(groups.values()),
        "uniq_ratio": uniq_rec / n,
        "viol_ratio": viol_rec / n,
        "viol_rec": viol_rec,
        "exposed_ratio": len(exposed) / N_USERS,
    }


GRID = {(tn, pn): measure(m, pk)
        for tn, m in TIME_RES for pn, pk in PLACE_RES}

hdr = f"{'시각':<8}{'장소':<6}{'칸 수':>12}{'최소 k':>8}{'유일 레코드':>12}{'k<5 위반':>10}{'노출 토큰':>10}"
print(hdr)
print("-" * len(hdr))
for tn, _m in TIME_RES:
    for pn, _pk in PLACE_RES:
        g = GRID[(tn, pn)]
        print(f"{tn:<8}{pn:<6}{g['cells']:>12,}{g['min_k']:>8}"
              f"{g['uniq_ratio']:>11.1%}{g['viol_ratio']:>10.1%}"
              f"{g['exposed_ratio']:>10.1%}")
# 출력:
# 시각      장소             칸 수    최소 k      유일 레코드    k<5 위반     노출 토큰
# ------------------------------------------------------------------
# 1분      동        2,073,600       1      98.4%    100.0%    100.0%
# 1분      구          518,400       1      93.8%    100.0%    100.0%
# 1분      시          129,600       1      75.8%     99.9%    100.0%
# 10분     동          207,360       1      84.8%    100.0%    100.0%
# 10분     구           51,840       1      53.7%     99.2%    100.0%
# 10분     시           12,960       1      12.4%     66.4%     86.6%
# 1시간     동           34,560       1      40.5%     97.3%     99.9%
# 1시간     구            8,640       1       6.2%     48.0%     70.5%
# 1시간     시            2,160       1       0.6%      5.0%     11.3%
# 6시간     동            5,760       1       2.6%     26.0%     40.3%
# 6시간     구            1,440       1       0.2%      3.0%      4.0%
# 6시간     시              360       2       0.0%      0.0%      0.0%
# 1일      동            1,440       5       0.0%      0.0%      0.0%
# 1일      구              360      42       0.0%      0.0%      0.0%
# 1일      시               90     159       0.0%      0.0%      0.0%

# %% [markdown]
# 표를 읽는 방법.
#
# - **1분 + 동**에서는 레코드의 98.4% 가 혼자다. 즉 «이름을 지운» 로그의 거의 모든 행이
#   그 자체로 유일 키다. 34장 표현대로, 지운 게 지워진 게 아니다.
#   `최소 k = 1` 이므로 k-익명성은 $k=2$ 조차 만족하지 못한다.
# - 해상도를 낮춰야 비로소 유일성이 떨어진다. `1일` 버킷까지 내려가야 `최소 k` 가
#   5 이상이 되고 k<5 위반이 0이 된다. 그 지점의 데이터는 "3월 12일에 마포에서 결제"다.
#   시각이 사라졌다.
# - `노출 토큰` 칸이 중요하다. `1시간 + 구` 에서 유일 레코드는 **6.2%** 뿐인데,
#   유일 레코드를 하나 이상 가진 토큰은 **70.5%** 다. 평균만 보면 안전해 보이지만
#   **레코드 하나만 뚫려도 그 토큰의 전체 이력이 열린다.** 최악을 봐야 한다.
# - `1분 + 시` 를 보라. 장소를 시(3개)까지 뭉갰는데도 유일 레코드가 75.8% 다.
#   **한쪽만 일반화하는 것은 대응이 아니다.** 시각 해상도가 살아 있으면 그것만으로 유일하다.

# %%
# 답에 나온 바로 그 레코드가 각 해상도에서 몇 명과 섞이는지
print("«2026년 3월 12일 14시 3분 마포에서 결제» — 이 조합을 공유하는 레코드 수\n")
hdr = f"{'시각':<8}{'장소':<6}{'같은 조합 레코드':>18}{'후보 토큰':>10}"
print(hdr)
print("-" * len(hdr))
for tn, m in TIME_RES:
    for pn, pk in PLACE_RES:
        key = qi(TARGET, m, pk)
        same = [r for r in LOG if qi(r, m, pk) == key]
        print(f"{tn:<8}{pn:<6}{len(same):>18,}"
              f"{len({r['user'] for r in same}):>10,}")
# 출력:
# «2026년 3월 12일 14시 3분 마포에서 결제» — 이 조합을 공유하는 레코드 수
#
# 시각      장소             같은 조합 레코드     후보 토큰
# ------------------------------------------
# 1분      동                      1         1
# 1분      구                      1         1
# 1분      시                      1         1
# 10분     동                      1         1
# 10분     구                      1         1
# 10분     시                      6         6
# 1시간     동                      1         1
# 1시간     구                      1         1
# 1시간     시                     22        21
# 6시간     동                     13        13
# 6시간     구                     32        30
# 6시간     시                    166       148
# 1일      동                     17        17
# 1일      구                     71        55
# 1일      시                    428       314
#
# → 「1시간 + 구」까지 뭉개도 후보가 여전히 1명이다.
#   이름이 없어도 «그 사람»이 확정된다. 이게 식별자 끊기의 함정이다.

# %% [markdown]
# ## 3. 링크 공격 — 외부 데이터 $m$ 개면 끝난다
#
# 공격자는 공개된 익명 로그만 보는 게 아니다. **다른 쪽 데이터**를 갖고 있다.
#
# - 카드 명세서(가족·회계팀·유출본): 결제 시각과 가맹점 위치가 분 단위로 적혀 있다
# - SNS 체크인·사진 EXIF: "지금 마포 ○○카페" + 타임스탬프
# - 교통카드·출입기록·배달 앱 주문 내역
#
# 공격자는 자기가 아는 시공간 지점 $m$ 개를 익명 로그에서 찾아
# **그 지점을 모두 포함하는 토큰**을 구한다. 후보가 하나로 좁혀지면 재식별 성공이다.
#
# de Montjoye 등(Science 2015)은 익명화된 신용카드 메타데이터 110만 명에서
# 시공간 지점 **4개**로 90% 를 특정했다. 아래는 같은 실험이다.

# %%
def link_attack(minutes, place_key, m, trials=400, seed=SEED):
    """공격자가 시공간 지점 m 개를 알 때 토큰이 하나로 좁혀지는 비율."""
    idx = defaultdict(set)
    by_user = defaultdict(list)
    for r in LOG:
        idx[qi(r, minutes, place_key)].add(r["user"])
        by_user[r["user"]].append(r)

    lrng = random.Random(seed)
    targets = lrng.sample(sorted(by_user), min(trials, len(by_user)))
    ok = 0
    tried = 0
    for u in targets:
        recs = by_user[u]
        if len(recs) < m:
            continue
        known = lrng.sample(recs, m)
        cand = None
        for r in known:
            s = idx[qi(r, minutes, place_key)]
            cand = set(s) if cand is None else (cand & s)
        tried += 1
        if len(cand) == 1:
            ok += 1
    return ok / tried if tried else float("nan")


SCENARIOS = [("1분", 1, "동", "dong"), ("1시간", 60, "구", "gu"),
             ("6시간", 360, "구", "gu"), ("1일", 1440, "구", "gu"),
             ("1일", 1440, "시", "si")]
MS = [1, 2, 3, 4]

ATTACK = {}
hdr = f"{'공개 해상도':<16}" + "".join(f"{'m=' + str(m):>8}" for m in MS)
print("링크 공격 성공률 (후보가 정확히 1개로 좁혀진 비율)\n")
print(hdr)
print("-" * len(hdr))
for tn, mins, pn, pk in SCENARIOS:
    row = [link_attack(mins, pk, m) for m in MS]
    ATTACK[(tn, pn)] = row
    print(f"{tn + ' + ' + pn:<16}" + "".join(f"{v:>7.1%}" for v in row))
# 출력:
# 링크 공격 성공률 (후보가 정확히 1개로 좁혀진 비율)
#
# 공개 해상도               m=1     m=2     m=3     m=4
# ------------------------------------------------
# 1분 + 동            98.5% 100.0% 100.0% 100.0%
# 1시간 + 구            7.2%  93.5%  99.8% 100.0%
# 6시간 + 구            0.2%  34.2%  83.5%  96.8%
# 1일 + 구             0.0%   9.8%  37.0%  53.2%
# 1일 + 시             0.0%   0.0%   2.0%  12.2%

# %% [markdown]
# 34장 `ex3_reidentify.py` 가 말한 **절벽**이 그대로 보인다.
#
# - `1일 + 구` 에서 $m=1$ 이면 0.0%. 하루 단위 + 구 단위는 안전해 *보인다*.
#   그런데 $m$ 을 2, 3, 4 로 올리면 9.8% → 37.0% → **53.2%**.
#   지점 하나 추가가 «조금 더»가 아니라 «자릿수»로 작동한다. 조합 수가 곱해지기 때문이다.
# - `1시간 + 구` 는 앞 표에서 유일 레코드가 6.2% 뿐이었다. 그런데 지점 **2개**면
#   93.5%, 3개면 99.8% 다. **레코드 단위 k-익명성이 괜찮아 보여도 궤적(trajectory)
#   단위로는 전멸한다.** 이것이 k-익명성을 레코드에만 적용하면 안 되는 이유다.
# - `1분 + 동` 은 지점 **하나**로 98.5%. 이것이 지금 대부분의 결제·접속·로그 테이블의 상태다.
#
# 그리고 공격자가 지점 4개를 아는 건 어려운 일이 아니다.
# 같이 점심 먹은 동료, 카드 명세서를 본 가족, 인스타 스토리 네 장이면 된다.
# de Montjoye 등은 실제 카드 데이터에서 4개로 90% 를 특정했고,
# 여기 `1분 + 동` 은 그보다 더 나쁘다(1개로 98.5%).

# %% [markdown]
# ## 4. 대응과 그 비용
#
# 대응은 셋이다. 그리고 셋 다 **정확도를 내주고 익명성을 산다**.
#
# | 대응 | 무엇을 하나 | 비용 |
# |---|---|---|
# | 일반화(generalization) / 버킷화 | 분 → 일, 동 → 시 | 시간대별·지역별 분석 해상도가 사라진다 |
# | 억제(suppression) | $\|E_Q(r)\| < k$ 인 레코드를 뺀다 | 데이터가 줄고, 빠지는 쪽이 편향된다 |
# | 잡음(noise) / 차등 정보보호 | 시각을 ±J분 흔든다 | 정확 조인이 깨지고 미세 패턴이 뭉개진다 |
#
# 먼저 일반화의 **유용성 비용**을 재 보자. 지표는 두 개다.
#
# 1. **시간대 복원 오차**: 공개 데이터만으로 «시간대(0~23시)별 결제 분포»를 추정할 때의
#    총변동거리(total variation distance).
#    $$\mathrm{TVD}(p, q) = \tfrac{1}{2}\sum_{h=0}^{23} |p_h - q_h|$$
#    버킷 안은 균등하다고 가정해 복원한다. 1일 버킷이면 완전 균등 → 피크 정보가 전멸한다.
# 2. **점심 피크 비중 오차**: 11~14시 결제 비중의 참값 대비 절대 오차.

# %%
def true_hour_dist():
    c = Counter(r["dt"].hour for r in LOG)
    n = len(LOG)
    return [c.get(h, 0) / n for h in range(24)]


def recovered_hour_dist(minutes):
    """버킷 내부 균등 가정으로 복원한 시간대 분포."""
    cache = {}

    def weights(offset):
        if offset not in cache:
            w = [0.0] * 24
            for i in range(minutes):
                w[((offset + i) // 60) % 24] += 1.0 / minutes
            cache[offset] = w
        return cache[offset]

    acc = [0.0] * 24
    for r in LOG:
        start = t_bucket(r["dt"], minutes)
        for h, w in enumerate(weights(start % 1440)):
            acc[h] += w
    n = len(LOG)
    return [a / n for a in acc]


def tvd(p, q):
    return 0.5 * sum(abs(a - b) for a, b in zip(p, q))


TRUE_H = true_hour_dist()
TRUE_LUNCH = sum(TRUE_H[11:14])

UTIL = {}
hdr = f"{'시각 해상도':<12}{'시간대 TVD':>12}{'점심비중 추정':>14}{'오차':>8}"
print(f"참 점심(11~14시) 비중: {TRUE_LUNCH:.1%}\n")
print(hdr)
print("-" * len(hdr))
for tn, m in TIME_RES:
    q = recovered_hour_dist(m)
    d = tvd(TRUE_H, q)
    lunch = sum(q[11:14])
    UTIL[tn] = {"tvd": d, "lunch": lunch, "err": abs(lunch - TRUE_LUNCH)}
    print(f"{tn:<12}{d:>12.3f}{lunch:>13.1%}{abs(lunch - TRUE_LUNCH):>8.1%}")
# 출력:
# 참 점심(11~14시) 비중: 22.8%
#
# 시각 해상도           시간대 TVD       점심비중 추정      오차
# ----------------------------------------------
# 1분                 0.000        22.8%    0.0%
# 10분                0.000        22.8%    0.0%
# 1시간                0.000        22.8%    0.0%
# 6시간                0.149        17.2%    5.6%
# 1일                 0.267        12.5%   10.3%

# %% [markdown]
# 여기서 트레이드오프가 드러난다.
#
# - `1시간` 버킷까지는 시간대 분석이 **손실 없이** 된다(TVD = 0). 그런데 앞 표에서
#   `1시간 + 구` 의 링크 공격 성공률은 $m=2$ 에 이미 93.5% 다. 즉 **분석에 충분한
#   해상도는 공격에도 충분하다.** 두 요구가 정확히 같은 자원을 놓고 다툰다.
# - 공격 성공률($m=4$)을 한 자릿수 근처로 누르려면 `1일 + 시` 까지 가야 하고,
#   그러면 TVD 0.267, 점심 비중은 22.8% → 12.5%(균등값)로 무너진다.
#   "점심에 결제가 몰린다"를 더는 말할 수 없다.
# - `6시간` 은 중간 타협이다. TVD 0.149, 점심 비중 오차 5.6%.
#   그 대가로 `6시간 + 구` 의 $m=4$ 성공률은 96.8% — **타협은 방어가 아니다.**
#
# 이게 «공짜가 아니다»의 구체적 의미다.

# %%
# 억제(suppression): k-익명성을 만족하지 않는 레코드를 빼면 얼마나 남나
print(f"억제: k<{K} 인 동치류의 레코드를 제거했을 때\n")
hdr = f"{'시각':<8}{'장소':<6}{'제거 레코드':>12}{'제거율':>9}{'남는 토큰':>10}"
print(hdr)
print("-" * len(hdr))
SUPPRESS = {}
for tn, m in TIME_RES:
    for pn, pk in PLACE_RES:
        groups = Counter(qi(r, m, pk) for r in LOG)
        kept = [r for r in LOG if groups[qi(r, m, pk)] >= K]
        drop = len(LOG) - len(kept)
        SUPPRESS[(tn, pn)] = drop / len(LOG)
        print(f"{tn:<8}{pn:<6}{drop:>12,}{drop / len(LOG):>8.1%}"
              f"{len({r['user'] for r in kept}):>10,}")
# 출력:
# 억제: k<5 인 동치류의 레코드를 제거했을 때
#
# 시각      장소          제거 레코드      제거율     남는 토큰
# ---------------------------------------------
# 1분      동           24,083  100.0%         0
# 1분      구           24,083  100.0%         0
# 1분      시           24,068   99.9%        15
# 10분     동           24,083  100.0%         0
# 10분     구           23,886   99.2%       177
# 10분     시           15,987   66.4%     1,179
# 1시간     동           23,444   97.3%       483
# 1시간     구           11,564   48.0%     1,200
# 1시간     시            1,211    5.0%     1,200
# 6시간     동            6,271   26.0%     1,200
# 6시간     구              718    3.0%     1,200
# 6시간     시                9    0.0%     1,200
# 1일      동                0    0.0%     1,200
# 1일      구                0    0.0%     1,200
# 1일      시                0    0.0%     1,200
#
# → 1분 단위 데이터에 k=5 를 강제하면 «전부» 지워진다(제거율 100%, 남는 토큰 0).
#   억제는 일반화 없이는 쓸 수 없는 도구다.
#   그리고 «1시간 + 동»(97.3% 제거)처럼 어중간한 지점에서는
#   드물게 움직이는 사람이 먼저 사라진다 — 억제는 **편향**을 만든다.

# %%
# 잡음(noise): 시각을 ±J분 흔들면 정확 조인은 깨지지만…
def jitter_attack(minutes, place_key, m, jitter, tol, trials=400, seed=SEED + 1):
    """공개 로그에 ±jitter 분 잡음. 공격자는 ±tol 분 창으로 매칭한다."""
    jr = random.Random(seed)
    pub = []
    for r in LOG:
        shift = jr.randint(-jitter, jitter)
        pub.append({**r, "pdt": r["dt"] + timedelta(minutes=shift)})

    idx = defaultdict(set)
    for r in pub:
        idx[(t_bucket(r["pdt"], minutes), r[place_key])].add(r["user"])

    by_user = defaultdict(list)
    for r in LOG:
        by_user[r["user"]].append(r)

    lrng = random.Random(seed)
    span = max(1, tol // minutes)
    ok = exact_ok = tried = 0
    for u in lrng.sample(sorted(by_user), min(trials, len(by_user))):
        recs = by_user[u]
        if len(recs) < m:
            continue
        known = lrng.sample(recs, m)
        tried += 1
        # (a) 정확 매칭
        cand = None
        for r in known:
            s = idx[(t_bucket(r["dt"], minutes), r[place_key])]
            cand = set(s) if cand is None else (cand & s)
        if len(cand) == 1 and u in cand:
            exact_ok += 1
        # (b) ±tol 창 매칭
        cand = None
        for r in known:
            s = set()
            b = t_bucket(r["dt"], minutes)
            for d in range(-span, span + 1):
                s |= idx[(b + d * minutes, r[place_key])]
            cand = set(s) if cand is None else (cand & s)
        if len(cand) == 1 and u in cand:
            ok += 1
    return exact_ok / tried, ok / tried


print("잡음(시각 ±J분)을 넣었을 때 — 공개 해상도 10분 + 동, m=3\n")
hdr = f"{'잡음 ±J분':<12}{'정확 매칭':>12}{'±60분 창 매칭':>14}"
print(hdr)
print("-" * len(hdr))
NOISE = {}
for J in [0, 5, 15, 60, 180]:
    e, w = jitter_attack(10, "dong", 3, J, 60)
    NOISE[J] = (e, w)
    print(f"{'±' + str(J):<12}{e:>11.1%}{w:>13.1%}")
# 출력:
# 잡음(시각 ±J분)을 넣었을 때 — 공개 해상도 10분 + 동, m=3
#
# 잡음 ±J분             정확 매칭     ±60분 창 매칭
# --------------------------------------
# ±0               100.0%       100.0%
# ±5                40.0%       100.0%
# ±15                3.8%       100.0%
# ±60                0.2%       100.0%
# ±180               0.0%         4.8%

# %% [markdown]
# 잡음의 함정이 여기 있다.
#
# - **정확 매칭**만 보면 ±15분 잡음으로 성공률이 3.8% 로 떨어진다.
#   방어에 성공한 것처럼 보인다. 이 숫자만 보고 «잡음 넣었으니 됐다»고 결론 내리기 쉽다.
# - 그런데 공격자가 «±60분 안에 있으면 같은 결제로 본다»는 **관용 창**을 쓰면
#   ±5·±15·±60분 잡음 전부에서 **100%** 가 그대로 뚫린다.
#   잡음의 크기를 아는(또는 넉넉히 잡는) 공격자에게 잡음은 방어가 아니다.
# - 관용 창(±60분)보다 훨씬 큰 ±180분을 넣으면 4.8% 로 떨어진다. 그런데 그때
#   시각 데이터의 오차는 ±3시간 — «하루를 4~6칸으로 뭉갠 것»과 같다.
#   결국 일반화와 똑같은 값을 치른 셈이고, 게다가 데이터는 «정확한 척»을 하고 있어서
#   더 위험하다(분 단위 컬럼인데 실제 오차는 3시간).
#
# 그래서 잡음은 «형식적 보증»(예: 차등 정보보호의 $\varepsilon$)과 함께 쓸 때만 의미가 있다.
# $$\Pr[M(D) \in S] \le e^{\varepsilon}\,\Pr[M(D') \in S]$$
# 이런 부등식이 없는 임의 잡음은 «흔들었으니 안전하다»는 느낌만 준다.

# %% [markdown]
# ## 5. 정리 — 함정의 정확한 형태
#
# 식별자 끊기는 «이름 칸을 비우면 끝»이라는 착각을 준다. 실제로는
#
# 1. 남은 속성 조합 $(\text{시각}, \text{장소})$ 가 **사실상 유일 키**로 작동한다.
#    1분 × 동 단위면 레코드의 98.4% 가 혼자다.
# 2. 외부 데이터가 같은 조합을 갖고 있으면 **조인 한 번**으로 실명이 붙는다.
#    지점 4개면 «하루 + 구» 단위로 뭉갠 데이터에서도 53% 가 특정된다.
# 3. 레코드 하나만 뚫려도 **그 토큰의 전체 이력**이 열린다.
#    `1시간 + 구` 는 유일 레코드가 6.2% 뿐인데 노출 토큰은 70.5% 다.
#    평균이 아니라 최악을 봐야 한다.
# 4. 대응(일반화·억제·잡음)은 전부 유용성을 대가로 받는다.
#    공격을 한 자릿수로 누르는 해상도에서는 «시간대별 분석»이 이미 죽어 있다.
#    억제는 일반화 없이는 데이터를 전부 날리고, 임의 잡음은 관용 창 하나로 무력해진다.
#
# 그리고 34장이 덧붙이는 한 줄. 그래프에서는 속성 말고 **관계 자체가 식별자**다.
# 위 실험에서 속성을 다 지워도, «이 토큰은 이 팀에 속하고 저 문서를 썼고 그 사람의 멘티다»는
# 이웃 모양이 남는다. 그 모양이 유일하면 똑같이 특정된다.

# %%
# ---- 시각화: expy.png ----
import plotly.graph_objects as go
from plotly.subplots import make_subplots

PALETTE = ["#c0392b", "#e67e22", "#16a085", "#2980b9", "#8e44ad"]

fig = make_subplots(
    rows=3, cols=2,
    subplot_titles=(
        "(1) 유일 레코드 비율 (%) — 시각 × 장소 해상도 격자",
        "(2) 링크 공격 성공률 vs 공격자가 아는 시공간 지점 수 m",
        "(3) 프라이버시-유용성 트레이드오프 (장소=구 고정)",
        "(4) 억제 비용 — k=5 강제 시 제거되는 레코드 비율",
        "(5) 잡음(±J분)의 무력함 — 공개 10분+동, m=3",
        "(6) 일반화가 지우는 것 — 시간대별 결제 분포",
    ),
    specs=[[{"type": "heatmap"}, {"type": "xy"}],
           [{"type": "xy"}, {"type": "xy"}],
           [{"type": "xy"}, {"type": "xy"}]],
    vertical_spacing=0.11, horizontal_spacing=0.11,
)

# (1) 히트맵 — 유일 레코드 비율
z = [[GRID[(tn, pn)]["uniq_ratio"] * 100 for tn, _ in TIME_RES]
     for pn, _ in PLACE_RES]
fig.add_trace(go.Heatmap(
    z=z, x=[tn for tn, _ in TIME_RES], y=[pn for pn, _ in PLACE_RES],
    colorscale="Reds", zmin=0, zmax=100, showscale=False,
    text=[[f"{v:.1f}" for v in row] for row in z],
    texttemplate="%{text}", textfont={"size": 11},
    hovertemplate="시각 %{x} / 장소 %{y}<br>유일 %{z:.1f}%<extra></extra>",
), row=1, col=1)

# (2) 링크 공격
for i, ((tn, pn), row) in enumerate(ATTACK.items()):
    fig.add_trace(go.Scatter(
        x=MS, y=[v * 100 for v in row], mode="lines+markers",
        name=f"{tn} + {pn}", line=dict(color=PALETTE[i % len(PALETTE)]),
        legendgroup="attack", legendgrouptitle_text="공개 해상도",
    ), row=1, col=2)
fig.add_hline(y=90, line_dash="dot", line_color="gray",
              annotation_text="de Montjoye 90%", annotation_font_size=10,
              row=1, col=2)

# (3) 트레이드오프: x = 시간대 TVD(유용성 손실), y = m=4 공격 성공률
tv, at, labels = [], [], []
for tn, mins in TIME_RES:
    tv.append(UTIL[tn]["tvd"])
    at.append(link_attack(mins, "gu", 4) * 100)
    labels.append(f"{tn}+구")
# 같은 좌표에 겹치는 점(TVD=0, 성공률 100%)은 라벨을 하나로 합친다
seen, texts = {}, [""] * len(tv)
for i, (x, y) in enumerate(zip(tv, at)):
    key = (round(x, 4), round(y, 1))
    if key in seen:
        texts[seen[key]] += " / " + labels[i].split("+")[0]
    else:
        seen[key] = i
        texts[i] = labels[i]
fig.add_trace(go.Scatter(
    x=tv, y=at, mode="lines+markers+text", text=texts,
    customdata=labels, textposition="bottom right", textfont=dict(size=10),
    marker=dict(size=12, color=PALETTE[0]), line=dict(color=PALETTE[0]),
    showlegend=False,
    hovertemplate="%{customdata}<br>TVD %{x:.3f} / 성공률 %{y:.1f}%<extra></extra>",
), row=2, col=1)

# (4) 억제 비용
for i, (pn, _pk) in enumerate(PLACE_RES):
    fig.add_trace(go.Bar(
        x=[tn for tn, _ in TIME_RES],
        y=[SUPPRESS[(tn, pn)] * 100 for tn, _ in TIME_RES],
        name=f"장소={pn}", marker_color=PALETTE[i],
        legendgroup="sup", legendgrouptitle_text="억제(k=5)",
    ), row=2, col=2)

# (5) 잡음
js = sorted(NOISE)
fig.add_trace(go.Scatter(
    x=[f"±{j}" for j in js], y=[NOISE[j][0] * 100 for j in js],
    mode="lines+markers", name="정확 매칭", marker_color=PALETTE[3],
    legendgroup="noise", legendgrouptitle_text="잡음 공격",
), row=3, col=1)
fig.add_trace(go.Scatter(
    x=[f"±{j}" for j in js], y=[NOISE[j][1] * 100 for j in js],
    mode="lines+markers", name="±60분 관용 창 매칭", marker_color=PALETTE[1],
    legendgroup="noise",
), row=3, col=1)

# (6) 시간대 분포 — 참값 vs 일반화 후 복원
fig.add_trace(go.Bar(
    x=list(range(24)), y=[v * 100 for v in TRUE_H],
    name="참값(분 단위)", marker_color="#bdc3c7",
    legendgroup="hour", legendgrouptitle_text="시간대 분포",
), row=3, col=2)
for i, tn in enumerate(["6시간", "1일"]):
    mins = dict(TIME_RES)[tn]
    fig.add_trace(go.Scatter(
        x=list(range(24)),
        y=[v * 100 for v in recovered_hour_dist(mins)],
        mode="lines+markers", name=f"{tn} 버킷 복원",
        marker_color=PALETTE[i], legendgroup="hour",
    ), row=3, col=2)

fig.update_xaxes(title_text="시각 해상도", row=1, col=1)
fig.update_yaxes(title_text="장소 해상도", row=1, col=1)
fig.update_xaxes(title_text="아는 지점 수 m", dtick=1, row=1, col=2)
fig.update_yaxes(title_text="성공률 (%)", range=[-4, 108], row=1, col=2)
fig.update_xaxes(title_text="시간대 분포 복원 오차 TVD  (유용성 손실 →)",
                 range=[-0.025, 0.36], row=2, col=1)
fig.update_yaxes(title_text="m=4 공격 성공률 (%)", range=[30, 112], row=2, col=1)
fig.update_xaxes(title_text="시각 해상도", row=2, col=2)
fig.update_yaxes(title_text="제거율 (%)", range=[0, 108], row=2, col=2)
fig.update_xaxes(title_text="잡음 크기 (분)", row=3, col=1)
fig.update_yaxes(title_text="m=3 성공률 (%)", range=[-4, 108], row=3, col=1)
fig.update_xaxes(title_text="시각 (0~23시)", dtick=3, row=3, col=2)
fig.update_yaxes(title_text="결제 비중 (%)", row=3, col=2)

fig.update_layout(
    height=1300, width=1280, barmode="group",
    title_text=("식별자를 끊어도 (시각, 장소) 조합이 남으면 재식별된다 — "
                f"결제 로그 {len(LOG):,}건 / 토큰 {N_USERS:,}개 / {DAYS}일"),
    template="plotly_white",
    legend=dict(tracegroupgap=14, y=1, yanchor="top", x=1.02),
)

_show(fig)

import os
_out = os.path.join(os.path.dirname(os.path.abspath(__file__))
                    if "__file__" in dir() else ".", "expy.png")
try:
    fig.write_image(_out, scale=2)
    print(f"저장: {_out}")
except Exception as e:            # kaleido 미설치 등
    print(f"expy.png 저장 실패 (kaleido 필요): {e}")
# 출력:
# 저장: .../expy.png
