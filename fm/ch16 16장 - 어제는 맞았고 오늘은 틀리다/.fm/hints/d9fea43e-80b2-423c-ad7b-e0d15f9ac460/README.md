# `BiTemporalStore`의 사실 레코드 필드

## 질문
`BiTemporalStore`의 각 사실 레코드는 어떤 필드를 갖는가?

## 답
주어(s), 술어(p), 값(value), valid_from/valid_to, tx_from/tx_to다. 열려 있는 끝은 FOREVER(9999-12-31)로 표시한다.

## 자세한 설명

16장의 공통 예제 `code/bitemporal.py`는 이중 시간(bitemporal) 저장소를 의존성 없이 100줄로 구현한다. 각 사실(fact)은 하나의 딕셔너리이고, `_append`가 만드는 형태가 곧 레코드 스키마다.

```python
FOREVER = date(9999, 12, 31)

def _append(self, s, p, v, vf, vt, tx):
    self.facts.append({"s": s, "p": p, "value": v,
                       "valid_from": vf, "valid_to": vt,
                       "tx_from": tx, "tx_to": FOREVER})
```

### 필드 7개, 세 묶음

| 묶음 | 필드 | 의미 |
|---|---|---|
| 사실 자체 | `s`, `p`, `value` | 주어–술어–값 트리플. 예: (가온테크, 담당, 김하늘) |
| 유효 시간 (valid time) | `valid_from`, `valid_to` | **현실에서** 그 사실이 참인 기간 |
| 기록 시간 (transaction time) | `tx_from`, `tx_to` | **우리 시스템이** 그렇게 알고 있던 기간 |

- **유효 시간**은 "3월 15일에 담당이 누구였나"에 답하는 축이다.
- **기록 시간**은 "3월 15일에 우리는 누구로 알고 있었나"에 답하는 축이다. 감사팀이 "그때 왜 그렇게 처리했나"를 물으면 이 축이 필요하다.

### FOREVER 센티널

끝나는 날짜가 아직 정해지지 않은 "열린 구간"은 `NULL` 대신 `FOREVER = date(9999, 12, 31)`로 채운다.

- 새 레코드는 항상 `tx_to=FOREVER`로 들어온다. 즉 "지금도 유효한 지식"이라는 뜻이다.
- `valid_to`도 기본값이 `FOREVER`다(끝날 때까지 참인 사실).
- 정정(`correct`)이나 논리적 갱신이 일어나면 `_retire`가 기존 레코드의 `tx_to`를 그 시점(`tx_at`)으로 닫는다. 레코드는 절대 삭제하지 않고 닫기만 한다 — 그래야 과거 시점 재현이 가능하다.
- 센티널 값이라 부등호 비교 시 주의가 필요하다. 책 본문의 주석대로 `FOREVER < FOREVER`는 거짓이므로, "지금 아는 대로" 질의(`tx_at=None`)는 부등호 대신 `tx_to != FOREVER` 여부로 걸러낸다.
- 출력 함수 `fmt`는 `FOREVER`를 "—"로 표시한다.

### 왜 이렇게 나누나

- 두 시간 축을 분리하면 **만료**(그때는 맞았다: 유효 시간을 자른다)와 **정정**(그때도 틀렸다: 기록 시간을 닫는다)을 구분해 저장할 수 있다.
- 이 구분이 없으면 과거 보고서가 소급해서 바뀌어 "6월 30일에 알고 있던 대로" 같은 감사 질의에 답할 수 없다.
- 이 스키마는 SQL:2011 표준의 bitemporal 테이블(application-time period + system-versioned)과 같은 개념을 최소 형태로 옮긴 것이다.
