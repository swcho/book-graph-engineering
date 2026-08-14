# `correct()`는 `assert_fact()`와 무엇이 다른가?

**답: 같은 `valid_from`을 가진 열린 기록을 기록 시간으로 닫고, 새 값을 같은 유효 기간으로 다시 넣는다. 유효 기간을 자르지 않는다.**

## 배경 — 만료와 정정은 다르다

16장의 이중 시간(bitemporal) 저장소 `BiTemporalStore`에는 쓰기 연산이 두 개 있다.

| 연산 | 의미 | 한 줄 요약 |
|---|---|---|
| `assert_fact()` | **만료(갱신)** | 「그때는 맞았고, 지금은 값이 바뀌었다」 |
| `correct()` | **정정** | 「그때도 틀렸다. 처음부터 다른 값이었다」 |

두 연산은 시간 축 두 개 중 **어느 축을 건드리느냐**가 다르다.

- **유효 시간(valid time)** — 현실에서 그 사실이 참인 기간
- **기록 시간(transaction time)** — 우리 시스템이 그렇게 «알고 있던» 기간

## `assert_fact()` — 유효 기간을 자른다

```python
def assert_fact(self, s, p, v, valid_from, tx_at, valid_to=FOREVER):
    """새 사실을 기록한다. 같은 (s, p) 의 겹치는 기간은 유효 시간을 잘라 준다."""
    for f in self.facts:
        if (f["s"], f["p"]) != (s, p) or f["tx_to"] != FOREVER:
            continue
        if f["valid_from"] < valid_from < f["valid_to"]:
            # 기존 사실의 유효 기간을 잘라 «논리적 갱신»을 만든다
            self._retire(f, tx_at)
            self._append(s, p, f["value"], f["valid_from"], valid_from, tx_at)
    self._append(s, p, v, valid_from, valid_to, tx_at)
```

새 사실의 `valid_from`이 기존 열린 기록의 유효 기간 **안에 끼어들면**, 기존 기록의 유효 기간을 `valid_from`에서 **잘라서** 「그 전까지는 옛 값, 그 뒤부터는 새 값」을 만든다. 옛 값 자체는 여전히 「그때는 참이었다」로 남는다.

## `correct()` — 유효 기간을 자르지 않는다

```python
def correct(self, s, p, v, valid_from, tx_at):
    """정정. «그때도 틀렸다»는 뜻이라 기존 기록을 기록 시간으로 닫는다."""
    for f in self.facts:
        if (f["s"], f["p"]) == (s, p) and f["tx_to"] == FOREVER \
                and f["valid_from"] == valid_from:
            self._retire(f, tx_at)
    self._append(s, p, v, valid_from, FOREVER, tx_at)
```

동작을 뜯어 보면,

1. **같은 `valid_from`을 가진** 아직 열린(`tx_to == FOREVER`) 기록을 찾는다 — 「같은 유효 기간을 주장하는 기존 기록」이다.
2. 그 기록의 **`tx_to`를 `tx_at`으로 닫는다** (`_retire`). 유효 시간은 건드리지 않는다. 「이 기록은 tx_at까지만 우리가 믿었던 내용」이라는 뜻.
3. 새 값을 **같은 `valid_from`, 같은 유효 기간(FOREVER)** 으로 다시 넣는다.

즉 현실이 바뀐 게 아니라 **우리의 지식이 틀렸던 것**이므로, 유효 시간 축은 그대로 두고 기록 시간 축에서만 옛 기록을 은퇴시킨다.

## 결과 비교 (ex2_correction.py)

같은 「A → B」 변경이라도 두 연산의 결과는 다르다.

```python
# 만료: 5월에 등급이 실제로 바뀌었다
st.assert_fact("가온테크", "등급", "A", valid_from=D(2026,1,1), tx_at=D(2026,1,1))
st.assert_fact("가온테크", "등급", "B", valid_from=D(2026,5,1), tx_at=D(2026,5,1))

# 정정: 처음부터 B였는데 A로 잘못 적었다
st.assert_fact("가온테크", "등급", "A", valid_from=D(2026,1,1), tx_at=D(2026,1,1))
st.correct("가온테크", "등급", "B", valid_from=D(2026,1,1), tx_at=D(2026,5,1))
```

| 질의 | 만료 시나리오 | 정정 시나리오 |
|---|---|---|
| 3월 1일 등급 (지금 아는 대로) | **A** — 그때는 진짜 A였다 | **B** — 그때도 B였는데 잘못 적었다 |
| 3월 1일 등급 (4월 시점 지식으로) | A | A — 4월에는 둘 다 A로 알고 있었다 |
| 6월 1일 등급 (지금 아는 대로) | B | B |

정정 시나리오에서도 「4월 시점 지식으로」 물으면 A가 나온다는 점이 핵심이다. 옛 기록이 삭제되지 않고 기록 시간으로만 닫혔기 때문에, **과거 보고서를 그대로 재현**할 수 있다.

## 왜 이 구분이 중요한가

- **만료를 정정으로 처리하면** 과거 보고서가 소급해서 바뀐다. 감사에서 「6월 30일 자 보고서를 다시 뽑아 달라」는 요청에 답할 수 없게 된다.
- **정정을 만료로 처리하면** 틀린 값이 「그때는 참이었다」로 과거에 영원히 남는다.
- 실무에서 사람이 이 둘을 자주 헷갈리므로, 입력 화면에서 「값이 바뀐 건가요, 잘못 적은 건가요?」를 직접 묻는 것이 낫다.

## 기억 포인트

- `assert_fact()` = 만료/갱신 → **유효 시간 축**을 자른다 (기존 기간을 새 `valid_from`에서 절단)
- `correct()` = 정정 → **기록 시간 축**만 닫는다 (같은 `valid_from`의 열린 기록을 `tx_at`으로 은퇴시키고, 같은 유효 기간으로 새 값 삽입)
- 두 경우 모두 기존 행을 **삭제하지 않는다** — 이중 시간 저장소는 append-only에 가깝게 동작해 과거 시점 재현을 보장한다.
