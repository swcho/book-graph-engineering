# `greedy_modularity()`는 왜 작은 그래프에서만 쓸 만한가

## 한 줄 답

**모든 커뮤니티 쌍을 후보로 놓고, 그 쌍 하나를 평가할 때마다 모듈러리티 $Q$를 그래프 전체에 대해 처음부터 다시 계산하기 때문이다.**

세 개의 비용이 곱으로 쌓인다.

$$
T \;=\; \underbrace{\binom{k}{2}}_{\text{후보 쌍}} \times \underbrace{\Theta(V+E)}_{\text{매번 전역 재계산}} \times \underbrace{(n-1)\text{회}}_{\text{병합}} \;=\; \Theta\!\left(n^{3}(V+E)\right)
$$

희소 그래프($E=\Theta(V)=\Theta(n)$)에서는 $\Theta(n^{4})$다. **노드가 두 배가 되면 16배 느려진다.**
그리고 뒤에서 보겠지만, 이 비용의 **97% 이상은 안 해도 되는 일**이다.

에셋 `ex4_communities.py`의 주석이 "노드 20개짜리에서만 쓸 만하다"고 못 박은 이유가 이것이고,
"실무에서는 루뱅이나 라이덴 계열을 쓴다"고 이어지는 이유도 이것이다.

---

## 0. 문제의 코드

에셋 `code/ex4_communities.py`에서 그대로 옮긴다. 비싼 지점 세 곳에 표시를 달았다.

```python
def greedy_modularity(adj):
    """작은 그래프용 탐욕 병합. 큰 그래프에는 루뱅 계열을 쓴다."""
    comms = [[v] for v in sorted(adj)]          # 싱글턴 n개에서 시작
    best_q = modularity(adj, comms)
    improved = True
    while improved and len(comms) > 1:          # ③ 병합 횟수 — 최대 n-1회
        improved = False
        best_pair, best_new = None, best_q
        for i in range(len(comms)):             # ① 모든 쌍 — C(k,2)개
            for j in range(i + 1, len(comms)):
                merged = comms[:i] + comms[i+1:j] + comms[j+1:] + [comms[i] + comms[j]]
                q = modularity(adj, merged)     # ② 전역 재계산 — Θ(V+E)
                if q > best_new + 1e-12:
                    best_new, best_pair = q, (i, j)
        if best_pair:
            i, j = best_pair
            comms = comms[:i] + comms[i+1:j] + comms[j+1:] + [comms[i] + comms[j]]
            best_q = best_new
            improved = True
    return sorted((sorted(c) for c in comms), key=len, reverse=True), best_q
```

그리고 매번 불리는 `modularity()`는 이렇게 생겼다.

```python
def modularity(adj, communities):
    m = sum(len(v) for v in adj.values()) / 2                    # O(V)
    q = 0.0
    for c in communities:
        s = set(c)                                              # 합계 O(V)
        lc = sum(1 for v in c for u in adj[v] if u in s) / 2     # 합계 O(2E)
        dc = sum(len(adj[v]) for v in c)                         # 합계 O(V)
        q += lc / m - (dc / (2 * m)) ** 2
    return q
```

이 함수는 **분할 전체를 훑는다**. 후보 쌍이 어디를 건드렸는지는 신경 쓰지 않고,
안 바뀐 커뮤니티까지 전부 다시 센다. 한 번 호출에 $\Theta(V+E)$다.

여기서 최적화하는 지표 $Q$의 정의는 뉴먼–거번의 것이다.

$$
Q \;=\; \sum_{c \in \mathcal{C}} \left[ \frac{\ell_c}{m} - \left( \frac{d_c}{2m} \right)^{2} \right]
$$

$\ell_c$는 커뮤니티 $c$ 내부 엣지 수, $d_c$는 $c$에 속한 노드들의 차수 합, $m$은 전체 엣지 수다.

---

## 1. 비용을 단계별로 세어 보자

### 1단계 — 후보 쌍의 수

라운드마다 현재 커뮤니티 $k$개의 **모든 쌍**을 시도한다.

$$
\binom{k}{2} \;=\; \frac{k(k-1)}{2} \;=\; \Theta(k^{2})
$$

첫 라운드는 $k=n$이므로 $\binom{n}{2}$개. 이건 「후보를 좁히는 장치가 아예 없다」는 뜻이다.

### 2단계 — 후보 하나를 평가하는 비용

`modularity(adj, merged)` 한 번 = $\Theta(V+E)$.

- 커뮤니티들을 순회하면서 각각 `set(c)`를 새로 만든다 → 합계 $\Theta(V)$
- `for v in c for u in adj[v]` → 모든 노드의 차수를 다 더한 것 = $2E$ → $\Theta(E)$
- 추가로 `comms[:i] + comms[i+1:j] + ...` 리스트 슬라이스 세 번 + 병합 리스트 복사 → $\Theta(k + |C_i| + |C_j|)$

즉 **두 커뮤니티를 붙였을 때의 점수 하나를 알아내려고 그래프 전체를 한 바퀴 돈다.**

### 3단계 — 병합 횟수

한 라운드에 병합은 **딱 한 번**이다. 커뮤니티 수는 $n \to n-1 \to \cdots$ 로 하나씩 줄어들고,
$Q$가 더 안 오르면 멈춘다. 그러니 라운드 수는 최대 $n-1$회.

### 곱하면

$$
T \;=\; \sum_{k=2}^{n} \binom{k}{2}\cdot\Theta(V+E) \;=\; \binom{n+1}{3}\cdot\Theta(V+E) \;\approx\; \frac{n^{3}}{6}\,\Theta(V+E)
$$

| 단계 | 무엇 | 비용 |
|---|---|---|
| ① 후보 쌍 | 매 라운드 모든 쌍 | $\binom{k}{2} = \Theta(k^2)$ |
| ② 평가 | `modularity()` 전역 재계산 | $\Theta(V+E)$ |
| ③ 라운드 | 병합 1회 = 라운드 1회 | 최대 $n-1$회 |
| **합** | | $\boldsymbol{\Theta(n^{3}(V+E))}$ → 희소면 $\boldsymbol{\Theta(n^{4})}$ |

`modularity()` 호출 횟수는 정확히 $\binom{n+1}{3}+1$이 상한이다.

### 실측 — 정말 그런지 돌려 봤다

에셋의 `greedy_modularity()`를 그대로 떼어 커뮤니티 구조가 있는 희소 그래프에 돌린 결과다
(파이썬 3, 애플 실리콘 노트북, 평균 차수 약 4.5).

| $n$ | $E$ | 시간(초) | `modularity()` 호출 | 병합 | 직전 대비 |
|---:|---:|---:|---:|---:|---:|
| 20 | 48 | 0.019 | 1,331 | 18 | — |
| 40 | 92 | 0.279 | 10,657 | 36 | **×14.7** |
| 60 | 137 | 1.428 | 35,971 | 54 | |
| 80 | 180 | 4.466 | 85,265 | 72 | **×16.0** |
| 120 | 267 | 23.08 | 287,761 | 108 | |
| 160 | 357 | 71.57 | 682,081 | 144 | **×16.0** |

$n$이 두 배가 될 때마다 시간이 정확히 **16배**. $\Theta(n^4)$ 예측 그대로다.
호출 횟수도 $\binom{161}{3} = 682{,}640$과 실측 $682{,}081$이 거의 일치한다(144회에서 멈춰 조금 적다).

에셋의 `org.py` 그래프($V=19$, $E=28$)로 실제 돌리면 **0.014초, `modularity()` 호출 1,137회, 병합 15회, $Q=0.5415$, 커뮤니티 4개**다. 순식간이다. 여기까지가 "쓸 만한" 영역이다.

같은 기울기로 밀어 보면 이렇게 된다.

| $n$ | 예상 시간 |
|---:|---|
| 320 | 19분 |
| 640 | 5.1시간 |
| 1,280 | 3.4일 |
| 10,000 | **약 35년** |

노드 1만 개는 실무에서 «작은» 그래프다. 그런데 이 구현으로는 사람 수명 단위가 나온다.
반면 루뱅은 같은 그래프를 **1초 안에** 끝낸다.

---

## 2. 이 비용은 거의 전부 낭비다

느린 게 문제가 아니라, **느린 이유가 순전히 구현 낭비**라는 게 요점이다. 낭비는 두 겹이다.

### 낭비 ① — 이어지지 않은 쌍까지 다 본다

두 커뮤니티 $C_i, C_j$를 붙였을 때 $Q$의 변화량은 닫힌 식으로 나온다.

$$
\Delta Q_{ij} \;=\; 2\left(e_{ij} - a_i a_j\right), \qquad
e_{ij} = \frac{\left|E(C_i, C_j)\right|}{2m}, \quad
a_i = \frac{\sum_{v \in C_i} \deg v}{2m}
$$

<details>
<summary>유도 (한 줄이다)</summary>

$Q = \sum_i (e_{ii} - a_i^2)$에서 $C_i, C_j$를 합치면 내부 항은 $e_{ii}+e_{jj}+2e_{ij}$가 되고 차수 비중은 $a_i + a_j$가 된다.

$$\Delta Q = \big[(e_{ii}+e_{jj}+2e_{ij}) - (a_i+a_j)^2\big] - \big[(e_{ii}-a_i^2) + (e_{jj}-a_j^2)\big] = 2e_{ij} - 2a_ia_j$$

나머지 커뮤니티의 항은 **전부 그대로**라서 소거된다. 이 식은 위 코드의 전역 재계산 결과와 오차 $1.3\times10^{-17}$ 안에서 일치함을 확인했다.
</details>

여기서 바로 보이는 것: 두 커뮤니티 사이에 **엣지가 하나도 없으면** $e_{ij}=0$이므로

$$
\Delta Q_{ij} = -2a_i a_j < 0
$$

**항상 손해다.** 계산해 볼 필요조차 없다. 그런데 소박한 구현은 이걸 매번 확인한다.

| 그래프 | 첫 라운드 쌍 수 | 엣지로 이어진 쌍 (상한) | 계산할 필요 없는 비율 |
|---|---:|---:|---:|
| `org.py` ($n=19$) | 171 | 28 | **83.6%** |
| $n=40$ | 780 | 92 | **88.2%** |
| $n=160$ | 12,720 | 357 | **97.2%** |
| $n=10^4$ (평균 차수 6) | 5,000만 | 3만 | **99.94%** |

그래프가 커질수록 낭비 비율이 1에 수렴한다. 후보 수를 $\Theta(k^2)$에서 $O(m)$으로 줄일 수 있다.

### 낭비 ② — $\Delta Q$는 국소적인데 전역을 다시 센다

위 유도의 핵심은 **$\Delta Q_{ij}$가 $C_i$와 $C_j$에만 의존한다**는 것이다. 나머지 커뮤니티가 몇 개든, 얼마나 크든 상관없다.
그런데 코드는 그 국소적인 숫자 하나를 얻으려고 $\Theta(V+E)$짜리 전역 순회를 한다.

**낭비 배수 = $\Theta(V+E)$ 그 자체**이고, 그래프 크기에 비례해 무한정 커진다.

두 낭비를 곱하면 $\Theta(k^2 (V+E))$가 $O(m)$이 된다. 라운드당 개선폭이 $n=160$에서만 이미 수만 배다.

---

## 3. 개선 1 — 뉴먼의 fast greedy: $\Delta Q$만 계산한다

> Newman (2004), *Fast algorithm for detecting community structure in networks*, Phys. Rev. E 69, 066133 ([cond-mat/0309508](https://arxiv.org/abs/cond-mat/0309508))

위의 두 낭비를 그대로 걷어낸 버전이다.

1. $Q$를 다시 계산하지 않고 $\Delta Q_{ij} = 2(e_{ij}-a_ia_j)$만 본다 → 후보 1개 평가 $\Theta(V+E) \to O(1)$
2. $e_{ij} > 0$인 쌍, 즉 **엣지로 이어진 커뮤니티 쌍만** 후보에 넣는다 → $\Theta(k^2) \to O(m)$
3. 병합 후에는 $e$ 행렬의 해당 두 행/열만 합친다 → $O(k)$

$$
O\big(n(m+n)\big) \;\xrightarrow{\ \text{희소}\ }\; O(n^{2})
$$

$\Theta(n^4)$에서 $O(n^2)$로. **$n=10^4$에서 35년이 수 초 수준으로 내려간다.** 알고리즘 골격(탐욕 병합)은 그대로다.

## 4. 개선 2 — CNM: 「최댓값 찾기」까지 힙으로 없앤다

> Clauset, Newman, Moore (2004), *Finding community structure in very large networks*, Phys. Rev. E 70, 066111 ([cond-mat/0408187](https://arxiv.org/abs/cond-mat/0408187))

뉴먼 fast greedy도 매 라운드 "$\Delta Q$가 최대인 쌍"을 선형 탐색으로 찾는다. CNM은 그것마저 자료구조로 없앤다.

- $\Delta Q_{ij}$를 **희소 행렬**로 유지(0인 칸은 아예 저장하지 않음)
- 커뮤니티마다 자기 행의 최댓값을 주는 **최대 힙** 하나
- 그 행 최댓값들을 다시 모은 **전역 최대 힙** 하나

최선의 쌍은 전역 힙의 top이므로 조회가 $O(1)$, 병합 후 갱신은 영향받은 행만 $O(\log n)$씩.

$$
O(md\log n) \;\xrightarrow{\ \text{희소·계층적}\ }\; O(n\log^{2} n)
$$

($m$ = 엣지 수, $d$ = 병합 덴드로그램의 깊이, 계층적 구조면 $d \sim \log n$)

> **networkx 사용자 주의.** `networkx.algorithms.community.greedy_modularity_communities()`가 바로 이 CNM이다.
> 에셋의 소박한 구현과 이름이 비슷하지만 안은 완전히 다르다. 그래도 노드 수백만 규모에서는 여전히
> `louvain_communities()`(networkx 3.0+)나 `leidenalg`가 낫다 — CNM은 여전히 **전역 최선 병합**이라
> 순차적이고, 병렬화가 어렵고, 탐욕 병합 특유의 낮은 $Q$ 지역 최적에 잘 빠진다.

## 5. 개선 3 — 루뱅: 병합을 버리고 「이동」으로 간다

> Blondel, Guillaume, Lambiotte, Lefebvre (2008), *Fast unfolding of communities in large networks*, J. Stat. Mech. P10008 ([arXiv:0803.0476](https://arxiv.org/abs/0803.0476))

루뱅은 발상 자체를 바꾼다. **커뮤니티 쌍을 병합하는 게 아니라, 노드 하나를 이웃의 커뮤니티로 옮긴다.**

### 1단계 — 국소 이동 (local moving)

각 노드 $i$에 대해, **이웃 노드가 속한 커뮤니티만** 후보로 놓고 옮겨 보는 이득을 계산한다.
고립된 $i$를 커뮤니티 $C$에 넣을 때의 이득은 논문의 식으로

$$
\Delta Q=\left[\frac{\Sigma_{in}+2k_{i,in}}{2m}-\left(\frac{\Sigma_{tot}+k_i}{2m}\right)^{2}\right]-\left[\frac{\Sigma_{in}}{2m}-\left(\frac{\Sigma_{tot}}{2m}\right)^{2}-\left(\frac{k_i}{2m}\right)^{2}\right]
$$

이고, 후보 커뮤니티들 사이의 **순위만 필요하므로** $i$에만 의존하는 항을 떨어내면

$$
\boxed{\ \Delta Q \;\propto\; \frac{k_{i,in}}{m}-\frac{\Sigma_{tot}\cdot k_{i}}{2m^{2}}\ }
$$

여기서 $\Sigma_{tot}$는 $C$에 속한 노드들의 차수 합, $k_i$는 $i$의 차수, $k_{i,in}$은 $i$에서 $C$로 가는 엣지 가중치 합이다.

**이게 루뱅이 얻는 이득의 정체다.**

- 커뮤니티마다 **누적값 $\Sigma_{tot}$ 하나**만 들고 있으면 되고, 병합/이동 시 덧셈 뺄셈으로 갱신된다.
- $k_{i,in}$은 $i$의 이웃만 훑으면 나온다 → 노드 $i$의 모든 후보를 다 보는 비용이 $O(\deg i)$.
- 전체 노드를 한 번 쓸면 $\sum_i \deg i = O(m)$.

소박한 구현이 후보 **하나**에 $\Theta(V+E)$를 썼다면, 루뱅은 노드 하나의 후보 **전부**를 $O(\deg i)$에 끝낸다.

### 2단계 — 집계 (aggregation)

1단계에서 나온 커뮤니티를 각각 **하나의 슈퍼노드**로 접는다. 커뮤니티 내부 엣지는 자기 루프(가중치 = 내부 엣지 수 × 2), 커뮤니티 사이 엣지는 가중치를 합쳐 하나로. 그리고 훨씬 작아진 그래프에 1단계를 다시 돌린다.

그래프가 층마다 기하급수적으로 줄어들기 때문에 층 수는 몇 개 안 되고, 실측 복잡도는 **엣지 수에 거의 선형**이다. 논문은 1억 1,800만 노드 그래프를 152분에 처리했다고 보고한다.

| | 후보 수 | 후보 1개 평가 | 라운드당 |
|---|---|---|---|
| 소박한 탐욕 (에셋) | $\binom{k}{2}$ — 모든 쌍 | $\Theta(V+E)$ 전역 재계산 | $\Theta(k^2(V+E))$ |
| 뉴먼 fast greedy | $O(m)$ — 이어진 쌍만 | $O(1)$ $\Delta Q$ | $O(m+n)$ |
| CNM | 힙 top | $O(1)$ 조회 / $O(\log n)$ 갱신 | $O(m\log n)$ 수준 |
| 루뱅 | $O(\deg i)$ — 이웃 커뮤니티만 | $O(1)$ $\Delta Q$ | $O(m)$, 이후 그래프가 축소 |

## 6. 개선 4 — 라이덴: 루뱅이 만드는 「연결 불량」을 고친다

> Traag, Waltman, van Eck (2019), *From Louvain to Leiden: guaranteeing well-connected communities*, Sci Rep 9, 5233 ([s41598-019-41695-z](https://www.nature.com/articles/s41598-019-41695-z), [arXiv:1810.08473](https://arxiv.org/abs/1810.08473))

### 무엇이 문제인가

루뱅이 수렴했을 때 보장하는 것은 딱 하나다. **"어떤 노드 하나를 옮겨도 $Q$가 오르지 않는다"**(node optimality).
이건 커뮤니티 **전체**의 모양에 대해서는 아무것도 보장하지 않는다.

구체적인 파국 시나리오:

1. 커뮤니티 $C$ 안에서 노드 $v$가 **유일한 다리** 역할을 하고 있다. $C \setminus \{v\}$는 두 조각이다.
2. 나중 쓸기에서 $v$를 이웃 커뮤니티로 옮기는 게 $Q$를 조금 올린다. 루뱅은 옮긴다.
3. 이제 $C$는 **연결이 끊긴 두 조각**이다. 그런데 여기서 어떤 **노드 하나**를 옮겨도 $Q$가 안 오른다 → 루뱅은 이걸 «수렴»으로 보고 그대로 둔다.
4. 2단계 집계가 그 끊긴 $C$를 **슈퍼노드 하나로 접어 버린다.** 이후 어떤 층에서도 다시 쪼갤 수 없다. **결함이 영구히 굳는다.**

논문의 실측: 실제 네트워크에서 **커뮤니티의 최대 25%가 «나쁘게 연결»되어 있었고, 최대 16%는 아예 연결이 끊겨 있었다.** 게다가 루뱅을 반복해서 돌리면 이 문제는 **더 나빠진다**.

실무적으로 이건 조용한 재앙이다. "커뮤니티 12번"으로 리포트에 올라간 집합의 두 절반이 서로 **엣지가 하나도 없는** 남남일 수 있다. 커뮤니티 개수도, 크기 분포도, 모듈러리티 값도 멀쩡해 보인다.

### 라이덴의 처방 — 정제 단계

라이덴은 국소 이동과 집계 **사이에 정제(refinement) 단계**를 끼워 넣어 3단계로 만든다.

1. **빠른 국소 이동 (fast local move)** — 큐를 써서, 이웃이 움직인 노드만 다시 방문한다. 루뱅처럼 매번 전 노드를 다시 쓸지 않는다. → **속도 이득**
2. **정제** — 1단계가 만든 각 커뮤니티 $C$ **안에서** 다시 싱글턴부터 시작해 병합한다. 단,
   - 자기가 속한 $C$에 **충분히 잘 연결된** 부분집합끼리만 병합할 수 있고,
   - 어느 쪽으로 병합할지는 **무작위로** 고른다 — $\Delta Q$가 클수록 뽑힐 확률이 높다.

   무작위성이 핵심이다. 탐욕적으로 항상 최선만 고르면 못 찾는 «쪼개기»를 발견한다.
3. **집계** — 슈퍼노드는 **정제된 분할** $P_{\text{refined}}$ 기준으로 만들고, 다음 층의 초기 배정은 **정제 전 분할** $P$에서 가져온다.

**이 3번이 핵심 수리다.** 쪼개져야 마땅한 커뮤니티는 그 조각들이 **서로 다른 슈퍼노드**로 남으므로, 위 층에서 여전히 갈라질 수 있다. 루뱅이 결함을 굳혔던 바로 그 지점이다.

### 보장되는 것 (논문 Table 1)

| 성질 | 뜻 | 루뱅 | 라이덴 |
|---|---|:--:|:--:|
| **매 반복** | | | |
| $\gamma$-separation | 합칠 수 있는 커뮤니티 쌍이 없다 | ✓ | ✓ |
| $\gamma$-connectivity | **커뮤니티가 연결되어 있다** | ✗ | **✓** |
| **안정 반복** | | | |
| node optimality | 노드 하나를 옮겨 개선 못 한다 | ✓ | ✓ |
| subpartition $\gamma$-density | 커뮤니티를 잘 연결된 부분들로 쪼갤 수 있고 어느 부분도 떨어져 나가지 않는다 | ✗ | **✓** |
| **점근적** | | | |
| uniform $\gamma$-density | 떼어낼 수 있는 부분집합이 없다 | ✗ | **✓** |
| subset optimality | **모든 부분집합**이 국소 최적으로 배정되어 있다 | ✗ | **✓** |

그리고 라이덴은 이 모든 걸 하면서도 **루뱅보다 빠르다** — 빠른 국소 이동 덕분이다.
품질도 좋고 보장도 강하고 속도도 빠른, 드문 종류의 순수 개선이다.

---

## 7. 라이덴으로 바꿔도 안 고쳐지는 것 — 해상도 한계

**커뮤니티 탐지 알고리즘을 바꾸는 것과 목적 함수를 바꾸는 것은 다른 일이다.**

CNM → 루뱅 → 라이덴은 모두 **같은 $Q$를 더 잘·더 빨리 최대화하는** 방법이다.
$Q$ 자체의 성질인 **해상도 한계**(resolution limit, [Fortunato & Barthélemy 2007](https://www.pnas.org/doi/10.1073/pnas.0605965104))는 그대로 남는다.

에셋 `ex5_resolution.py`가 만드는 «고리로 이어진 작은 완전 그래프들»에서, 뭉치가 많아지면
«둘씩 붙인» 오답의 $Q$가 정답의 $Q$를 이긴다. **라이덴은 그 오답을 더 빠르고 더 확실하게 찾아 줄 뿐이다.**

- 해상도 매개변수 $\gamma$를 올린다: $Q_\gamma = \sum_c \left[\frac{\ell_c}{m} - \gamma\left(\frac{d_c}{2m}\right)^2\right]$ (에셋 `ex5`의 `gamma` 인자)
- 또는 CPM(Constant Potts Model)으로 목적 함수를 갈아탄다 — 라이덴 논문 저자들이 권하는 쪽이고, `leidenalg`가 기본 지원한다. CPM은 해상도 한계가 없다.

그리고 에셋 10장 요약의 결론은 여전히 유효하다. **커뮤니티 개수는 알고리즘이 아니라 쓰임새로 정한다.**

---

## 8. 실무 정리

| 알고리즘 | 복잡도 (희소) | $n=10^4$ 체감 | 언제 |
|---|---|---|---|
| 에셋의 소박한 탐욕 | $\Theta(n^{4})$ | 약 35년 | **교육용.** 노드 수십 개 |
| 뉴먼 fast greedy | $O(n^{2})$ | 수 초 | 논문 재현용 |
| CNM (힙) | $O(md\log n)$ ~ $O(n\log^{2}n)$ | 1초 미만 | `networkx.greedy_modularity_communities` |
| 루뱅 | 실측 거의 $O(m)$ | 1초 미만 | 사실상 표준. 다만 연결 불량 위험 |
| **라이덴** | 루뱅보다 빠름 | 1초 미만 | **기본값으로 삼을 것** |

라이브러리:

```python
# 라이덴 (권장)
import leidenalg, igraph as ig
part = leidenalg.find_partition(g, leidenalg.ModularityVertexPartition)
part = leidenalg.find_partition(g, leidenalg.CPMVertexPartition, resolution_parameter=0.05)  # 해상도 한계 회피
ig.Graph.community_leiden(g, objective_function="modularity")   # python-igraph 내장

# 루뱅
import networkx as nx
nx.community.louvain_communities(G, resolution=1.0, seed=42)    # networkx 3.0+
ig.Graph.community_multilevel(g)                                # python-igraph

# CNM
nx.community.greedy_modularity_communities(G)                   # ← 에셋의 것과 이름만 비슷, 안은 힙 기반
```

체크리스트:

1. **`seed`를 고정하고, 고정했다는 사실을 문서에 적는다.** 루뱅·라이덴·라벨 전파 모두 노드 방문 순서에 결과가 흔들린다(에셋 `ex4`의 라벨 전파 시드 실험과 같은 이야기).
2. **결과 커뮤니티가 연결되어 있는지 검사한다.** 루뱅을 쓴다면 필수 — 각 커뮤니티에 대해 유도 부분그래프의 연결 성분 수를 세면 1줄이다. 라이덴이면 보장된다.
3. **커뮤니티 개수가 마음에 안 들면 알고리즘이 아니라 $\gamma$를 만진다.**
4. **`greedy_modularity_communities`가 느리다고 커뮤니티 탐지가 원래 느린 거라고 결론짓지 않는다.** 소박한 병합 계열이 느린 것이지, 문제가 어려운 게 아니다.

---

## 9. 1차 출처

| 항목 | 출처 |
|---|---|
| 모듈러리티 정의 | Newman & Girvan (2004), [cond-mat/0308217](https://arxiv.org/abs/cond-mat/0308217) |
| 탐욕 병합 fast greedy ($\Delta Q$) | Newman (2004), Phys. Rev. E 69, 066133, [cond-mat/0309508](https://arxiv.org/abs/cond-mat/0309508) |
| CNM 힙 기반 | Clauset, Newman, Moore (2004), Phys. Rev. E 70, 066111, [cond-mat/0408187](https://arxiv.org/abs/cond-mat/0408187) |
| 루뱅 | Blondel et al. (2008), J. Stat. Mech. P10008, [arXiv:0803.0476](https://arxiv.org/abs/0803.0476) |
| 라이덴 | Traag, Waltman, van Eck (2019), Sci Rep 9, 5233, [s41598-019-41695-z](https://www.nature.com/articles/s41598-019-41695-z) |
| 해상도 한계 | Fortunato & Barthélemy (2007), [PNAS 104(1)](https://www.pnas.org/doi/10.1073/pnas.0605965104) |
| networkx CNM 구현 | [greedy_modularity_communities](https://networkx.org/documentation/stable/reference/algorithms/generated/networkx.algorithms.community.modularity_max.greedy_modularity_communities.html) |

---

## 한 문장으로 다시

에셋의 `greedy_modularity()`는 **$\Delta Q$가 두 커뮤니티에만 달린 국소량이라는 사실을 쓰지 않아서**,
$O(1)$이면 될 계산을 $\Theta(V+E)$로, $O(m)$개면 될 후보를 $\Theta(k^2)$개로 부풀린다.
그래서 $\Theta(n^4)$이 되고, 노드 20개짜리 조직도에서만 쓸 만하다.
**루뱅은 그 국소성을 $\Sigma_{tot}$ 하나로 뽑아 쓰고, 라이덴은 루뱅이 그 대가로 만들어 낸 연결 불량을 정제 단계로 되돌린다.**
