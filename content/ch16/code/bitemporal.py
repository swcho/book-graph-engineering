"""
16장 공통 — 이중 시간 저장소를 100줄로. 의존성 없음.

두 개의 시간 축을 쓴다.
  유효 시간(valid) — 현실에서 그 사실이 참인 기간
  기록 시간(tx)    — 우리 시스템이 그렇게 «알고 있던» 기간

이 둘을 나누면 두 가지 질문에 답할 수 있다.
  «3월 15일에 담당이 누구였나»            → 유효 시간으로 자른다
  «3월 15일에 우리는 누구로 알고 있었나»    → 기록 시간으로 자른다
"""

from bisect import insort
from datetime import date

FOREVER = date(9999, 12, 31)


class BiTemporalStore:
    def __init__(self):
        self.facts = []   # dict: subject, predicate, value, valid_from/to, tx_from/to

    # ---------- 쓰기 ----------
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

    def correct(self, s, p, v, valid_from, tx_at):
        """정정. «그때도 틀렸다»는 뜻이라 기존 기록을 기록 시간으로 닫는다."""
        for f in self.facts:
            if (f["s"], f["p"]) == (s, p) and f["tx_to"] == FOREVER \
                    and f["valid_from"] == valid_from:
                self._retire(f, tx_at)
        self._append(s, p, v, valid_from, FOREVER, tx_at)

    def _append(self, s, p, v, vf, vt, tx):
        self.facts.append({"s": s, "p": p, "value": v,
                           "valid_from": vf, "valid_to": vt,
                           "tx_from": tx, "tx_to": FOREVER})

    def _retire(self, f, tx_at):
        f["tx_to"] = tx_at

    # ---------- 읽기 ----------
    def query(self, s, p, valid_at=None, tx_at=None):
        """valid_at 시점에 참이었던 사실을, tx_at 시점에 우리가 알던 대로.

        tx_at 이 None 이면 «지금 아는 대로»다. 아직 안 닫힌 기록만 본다.
        FOREVER 를 넣고 부등호로 비교하면 FOREVER < FOREVER 가 거짓이라
        아무것도 안 걸린다. 제가 여기서 한 시간 헤맸다."""
        valid_at = valid_at or date.today()
        out = []
        for f in self.facts:
            if (f["s"], f["p"]) != (s, p):
                continue
            if not (f["valid_from"] <= valid_at < f["valid_to"]):
                continue
            if tx_at is None:
                if f["tx_to"] != FOREVER:      # 이미 정정·갱신된 기록은 뺀다
                    continue
            elif not (f["tx_from"] <= tx_at < f["tx_to"]):
                continue
            out.append(f)
        return out

    def history(self, s, p):
        return sorted(
            (f for f in self.facts if (f["s"], f["p"]) == (s, p)),
            key=lambda f: (f["tx_from"], f["valid_from"]))


def fmt(d):
    return "—" if d == FOREVER else d.isoformat()


def show(rows, title):
    print(f"\n{title}")
    if not rows:
        print("    (없음)")
        return
    print(f"    {'값':<10} {'유효 시작':<12} {'유효 끝':<12} "
          f"{'기록 시작':<12} {'기록 끝'}")
    for f in rows:
        print(f"    {str(f['value']):<10} {fmt(f['valid_from']):<12} "
              f"{fmt(f['valid_to']):<12} {fmt(f['tx_from']):<12} {fmt(f['tx_to'])}")
