"""
20장 공통 — 종료 조건 네 가지를 한곳에. 의존성 없음.

핵심은 «어떤 이유로 끝났는지»를 돌려주는 것이다.
불리언 하나만 돌려주면 호출한 쪽이 다르게 대응할 수 없다.
"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Guards:
    max_rounds: int = 5
    max_cost: float = 100.0
    max_seconds: float = 120.0
    stall_limit: int = 2          # 몇 번 연속 안 나아지면 멈출까

    # 실행 중에 채워지는 것들
    rounds: int = 0
    cost: float = 0.0
    elapsed: float = 0.0
    scores: list = field(default_factory=list)

    def record(self, cost: float, seconds: float, score: Optional[float]):
        self.rounds += 1
        self.cost += cost
        self.elapsed += seconds
        if score is not None:
            self.scores.append(score)

    def stalled(self) -> bool:
        """최근 stall_limit+1 개 점수가 나아지지 않았나.
        «같음»도 정체로 본다. 나빠지는 것만 잡으면 늦다."""
        n = self.stall_limit + 1
        if len(self.scores) < n:
            return False
        window = self.scores[-n:]
        best_before = min(window[:-1])
        return window[-1] >= best_before

    def check(self) -> Optional[str]:
        """멈출 이유가 있으면 «그 이유»를, 없으면 None."""
        if self.rounds >= self.max_rounds:
            return "횟수 상한"
        if self.cost >= self.max_cost:
            return "예산 상한"
        if self.elapsed >= self.max_seconds:
            return "시간 상한"
        if self.stalled():
            return "진전 없음"
        return None
