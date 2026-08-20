# 낙관적 잠금 재시도에 흔들기(jitter)를 넣는 이유

**Q.** 낙관적 잠금 재시도에 흔들기(jitter)를 넣는 이유는 무엇인가?

**A.** 22장에서 본 것처럼 **재시도가 동시에 몰리는 것을 흩기 위해서**다.

---

## 1. 문제의 코드 한 줄

31장 `ex2_optimistic.py`의 낙관적 잠금 루프 끝에 이 한 줄이 붙어 있습니다.

```python
def optimistic(db, field, value, delay, max_tries=5):
    for attempt in range(max_tries):
        with LOCK:
            props, ver = db.execute(
                "SELECT props, version FROM node WHERE id='t1'").fetchone()
        d = parse(props)
        time.sleep(delay)                 # 판단 (모델 호출 자리)
        d[field] = value
        with LOCK:
            cur = db.execute(
                "UPDATE node SET props=?, version=version+1 "
                "WHERE id='t1' AND version=?", (dump(d), ver))
            db.commit()
            if cur.rowcount == 1:
                return True               # 성공
            STATS["충돌"] += 1             # 0행 = 충돌
        time.sleep(random.uniform(0.005, 0.03))   # 흔들기 (22장)   ← 이 줄
    return False
```

`random.uniform(...)`이 없으면 어떻게 될까요? 충돌한 작업들이 **정확히 같은 시각에** 다시 읽고, 다시 판단하고, 다시 씁니다. 방금 부딪힌 상대와 또 부딪힙니다.

## 2. 왜 몰리는가 — 충돌이 만드는 동기화

낙관적 잠금의 충돌은 그 성질상 **여러 참가자에게 동시에 발생**합니다.

1. N개의 작업이 같은 노드를 읽는다 → 모두 `version = 7`을 손에 든다.
2. 하나가 먼저 쓴다 → `version = 8`이 된다.
3. 나머지 N-1개의 `UPDATE ... WHERE version=7`이 **동시에 0행**을 반환한다.
4. 대기 없이 재시도하면 N-1개가 **또 같은 순간에** 같은 지점으로 몰린다.

즉 실패 자체가 참가자들의 시계를 맞춰 줍니다. 이걸 그대로 두면 재시도가 반복될수록 「다 같이 실패 → 다 같이 재시도」가 굳어지고, 성공률이 오르지 않은 채 부하만 늡니다. 분산 시스템에서는 이걸 **재시도 폭풍(retry storm)** 또는 **떼거리 문제(thundering herd)** 라고 부릅니다.

## 3. 지수 백오프만으로는 안 된다 (22장 ex1의 요점)

여기서 흔히 하는 오해가 「지수 백오프를 넣었으니 됐다」입니다. 22장 예제가 정면으로 반박하는 지점입니다.

```python
def schedule_exp(_rng):
    """지수 백오프 — 1, 2, 4, 8, 16초."""
    t, out = 0.0, []
    for i in range(MAX_TRIES):
        t += min(BASE * (2 ** i), CAP)
        out.append(t)
    return out


def schedule_jitter(rng):
    """지수 백오프 + 흔들기 — 0~대기시간 사이 무작위."""
    t, out = 0.0, []
    for i in range(MAX_TRIES):
        t += rng.uniform(0, min(BASE * (2 ** i), CAP))
        out.append(t)
    return out
```

두 함수의 차이는 `rng.uniform(0, ...)` 하나뿐인데 결과가 갈립니다.

| 전략 | 간격 | 「다 같이」 | 결과 |
|---|---|---|---|
| 고정 간격 1초 | 1, 2, 3, 4, 5초 | 그대로 | 한 구간에 클라이언트 전부가 몰린다 |
| 지수 백오프 | 1, 3, 7, 15, 31초 | **그대로** | 봉우리 위치만 옮겼을 뿐 높이는 안 낮아진다 |
| 지수 백오프 + 흔들기 | 무작위 | 흩어짐 | 봉우리가 사라진다 |

> 「지수 백오프도 똑같이 몰린다. 다 같이 1초 뒤, 다 같이 3초 뒤에 온다. 간격만 벌렸을 뿐 «다 같이»는 그대로다. 이게 함정이다.」 (22장 ex1)

**지수 백오프는 간격을 벌리는 장치이고, 흔들기는 위상(phase)을 흩는 장치입니다.** 둘은 다른 축이라 서로를 대신하지 못합니다. 총 요청 수는 셋 다 같습니다 — 다른 건 「언제 오느냐」뿐인데 그것만으로 죽고 삽니다.

## 4. 흔들기는 늦추는 장치가 아니다

22장이 한 번 더 강조하는 반직관 포인트입니다.

> 「흔들기를 쓰면 첫 재시도가 «더 빨리» 오기도 한다. 0~1초 사이에서 뽑으니 평균 0.5초다. 고정 간격 1초보다 이르다. 그래서 흔들기는 늦추는 장치가 아니라 «흩는» 장치다.」

`uniform(0, cap)` 형태(이른바 full jitter)의 기댓값은 `cap/2`입니다. 평균 대기는 오히려 **줄어드는데** 피크는 사라집니다. 지연을 늘려서 얻는 이득이 아니라, **분포를 평평하게 만들어서** 얻는 이득이기 때문입니다.

31장 코드의 `random.uniform(0.005, 0.03)`은 하한을 조금 준 형태입니다. 최소 5ms는 무조건 쉬어서 「즉시 재충돌」을 막고, 상한까지의 무작위 폭으로 위상을 흩습니다.

### 흔들기 변형들

| 이름 | 다음 대기 | 성격 |
|---|---|---|
| No jitter | `min(cap, base·2ⁿ)` | 봉우리 그대로 |
| Full jitter | `uniform(0, min(cap, base·2ⁿ))` | 가장 잘 흩어짐. 평균 대기도 짧음 |
| Equal jitter | `v/2 + uniform(0, v/2)` | 너무 짧은 대기를 피하면서 흩음 |
| Decorrelated jitter | `min(cap, uniform(base, prev·3))` | 이전 값 기준으로 흩음 |

AWS Builders' Library의 실험 기준으로는 full jitter 계열이 대체로 가장 낫습니다. 31장 코드처럼 하한을 둔 형태는 equal jitter에 가깝습니다.

## 5. 낙관적 잠금 문맥에서 특히 중요한 이유

일반 HTTP 재시도보다 낙관적 잠금 쪽이 흔들기가 더 절실한 이유가 셋 있습니다.

**① 재시도 한 번의 값이 비싸다.** 31장 ex3이 보여 주듯 낙관적 잠금의 기대 비용은 `N × (1/(1-p)) × (판단+쓰기)`입니다. 에이전트 시스템에서는 「판단」이 모델 호출입니다. 재시도 한 번에 모델 호출 하나가 통째로 다시 듭니다. 흔들기 없이 재충돌을 반복하면 토큰과 지연이 그대로 곱해집니다.

**② 충돌률 p가 스스로 올라간다.** 재시도가 몰리면 창이 겹칠 확률이 올라가고, p가 오르면 기대 시도 횟수 `1/(1-p)`가 급격히 커지고, 그러면 더 몰립니다. 양의 되먹임입니다. 흔들기는 이 고리를 끊습니다.

**③ 라이브락(livelock)이 실제로 난다.** 두 작업이 완벽히 동기화되면 서로가 서로를 계속 밀어내면서 아무도 진전하지 못하는 상태에 빠질 수 있습니다. `max_tries`에 걸려 둘 다 실패로 끝나기도 합니다. 무작위 대기는 이 대칭을 깨는 표준 수단입니다 — 이더넷 CSMA/CD의 binary exponential backoff가 같은 원리입니다.

## 6. 같이 챙겨야 할 것들

흔들기 한 줄만으로 끝나지 않습니다. 31장·22장이 함께 요구하는 것들입니다.

- **시도 상한**: `max_tries=5`. 무한 재시도는 폭풍의 연료입니다. 소진하면 실패를 위로 올리거나 대기열(데드레터)에 넣습니다.
- **판단을 잠금 밖으로**: ① 잠금 없이 읽기 ② 잠금 없이 모델 호출 ③ 짧게 잠그고 「버전 확인 + 쓰기」. 창이 좁아지면 p 자체가 떨어져서 재시도가 아예 덜 필요해집니다.
- **멱등성(21장)**: 재시도는 같은 작업을 여러 번 시도한다는 뜻입니다. 중복 실행이 안전해야 합니다.
- **회로 차단기(22장)**: 충돌률이 계속 높으면 재시도로 버티지 말고 비관적 잠금으로 갈아타거나 유입을 끊습니다. 31장 ex3의 기준으로 충돌률 15~30% 근처가 그 갈림길입니다.

## 7. 한 줄 정리

> 낙관적 잠금의 충돌은 참가자들의 시계를 맞춰 버린다. 지수 백오프는 간격만 벌릴 뿐 「다 같이」를 못 푼다. 흔들기는 대기 시간을 무작위로 뽑아 **위상을 흩어** 재충돌·라이브락·재시도 폭풍을 끊는 장치이고, 늦추는 장치가 아니다.

## 참고

- Timeouts, retries and backoff with jitter (AWS Builders' Library) — https://aws.amazon.com/builders-library/timeouts-retries-and-backoff-with-jitter/
- Handling Overload / retry storm (Google SRE Book) — https://sre.google/sre-book/handling-overload/
- Optimistic Offline Lock — https://martinfowler.com/eaaCatalog/optimisticOfflineLock.html
- Circuit Breaker — https://martinfowler.com/bliki/CircuitBreaker.html
- 예제: `content/ch31/code/ex2_optimistic.py`(흔들기 한 줄), `ex3_lock_contention.py`(재시도 비용), `content/ch22/code/ex1_backoff.py`(봉우리 비교)
