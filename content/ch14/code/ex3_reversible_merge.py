"""
예제 3 — 되돌릴 수 있는 병합. 노드를 지우지 않고 «가리키게» 한다.

    python3 ex3_reversible_merge.py

의존성 없음. 6부 이벤트 소싱의 축소판이다.
"""

from collections import defaultdict


class MergeStore:
    """병합을 «사건»으로 기록한다. 원본 노드는 절대 지우지 않는다."""

    def __init__(self, nodes):
        self.nodes = dict(nodes)          # id -> 속성
        self.canonical = {k: k for k in nodes}   # id -> 대표 id
        self.events = []                  # 되돌리기용 이력

    def resolve(self, nid):
        seen = set()
        while self.canonical[nid] != nid and nid not in seen:
            seen.add(nid)
            nid = self.canonical[nid]
        return nid

    def merge(self, a, b, by, reason):
        ca, cb = self.resolve(a), self.resolve(b)
        if ca == cb:
            return False
        # 대표는 «정보가 더 많은» 쪽으로. 규칙을 못 박아 둔다.
        keep, drop = (ca, cb) if self._richness(ca) >= self._richness(cb) else (cb, ca)
        self.canonical[drop] = keep
        self.events.append({"op": "merge", "keep": keep, "drop": drop,
                            "by": by, "reason": reason})
        return True

    def unmerge(self, dropped):
        for i in range(len(self.events) - 1, -1, -1):
            e = self.events[i]
            if e["op"] == "merge" and e["drop"] == dropped:
                self.canonical[dropped] = dropped
                self.events.append({"op": "unmerge", "target": dropped,
                                    "undoes": i})
                return True
        return False

    def _richness(self, nid):
        return sum(1 for v in self.nodes[nid].values() if v)

    def clusters(self):
        g = defaultdict(list)
        for k in self.nodes:
            g[self.resolve(k)].append(k)
        return {k: sorted(v) for k, v in g.items() if len(v) > 1}

    def view(self, nid):
        """대표 노드의 속성 + 병합된 것들의 속성을 채워 넣는다."""
        c = self.resolve(nid)
        merged = {}
        members = [k for k in self.nodes if self.resolve(k) == c]
        for m in sorted(members, key=lambda x: -self._richness(x)):
            for k, v in self.nodes[m].items():
                if v and not merged.get(k):
                    merged[k] = v
        return c, merged, members


NODES = {
    "r01": {"name": "가온테크", "bizno": "123-45-67890", "addr": "서울 강남구 테헤란로 1",
            "ceo": "김하늘", "tel": "02-1234-5678"},
    "r04": {"name": "GAON TECH", "bizno": "123-45-67890", "addr": "", "ceo": "", "tel": ""},
    "r06": {"name": "나루소프트", "bizno": "222-33-44444", "addr": "서울 마포구 월드컵로 2",
            "ceo": "이서연", "tel": "02-2222-3333"},
    "r07": {"name": "나루소프트(주)", "bizno": "555-66-77777", "addr": "서울 마포구 월드컵로 2",
            "ceo": "이서연", "tel": "02-2222-3333"},
}


def main():
    s = MergeStore(NODES)

    print("1) 맞는 병합")
    s.merge("r01", "r04", by="auto", reason="사업자번호 일치")
    c, v, m = s.view("r04")
    print(f"   r04 를 조회하면 → 대표 {c}, 구성원 {m}")
    print(f"   합쳐진 값: {v['name']} / {v['bizno']} / {v['ceo']}")

    print("\n2) 틀린 병합 — 모회사와 자회사를 합쳐 버렸다")
    s.merge("r06", "r07", by="auto", reason="주소·대표자·전화 일치")
    print(f"   군집: {s.clusters()}")

    print("\n3) 되돌린다")
    ok = s.unmerge("r07")
    print(f"   unmerge 성공: {ok}")
    print(f"   군집: {s.clusters()}")
    c, v, _ = s.view("r07")
    print(f"   r07 이 자기 값을 되찾았나: {v['name']} / {v['bizno']}")

    print("\n4) 이력")
    for i, e in enumerate(s.events):
        print(f"   [{i}] {e}")

    print(
        "\n핵심은 «원본을 안 지운다»는 것이다.\n"
        "r07 의 속성이 그대로 남아 있으니 되돌리기가 대입 한 번이다.\n"
        "\n노드를 실제로 지우고 속성을 합쳐 버리면 이게 안 된다.\n"
        "어느 값이 어디서 왔는지 모르니까 원래대로 쪼갤 수 없다.\n"
        "\n대가는 저장 공간과 조회 비용이다. 조회할 때마다 resolve 를 거쳐야 한다.\n"
        "제 경우 노드 수가 1.4배가 됐고, 조회에 인덱스 조회 한 번이 더 붙었다.\n"
        "사흘짜리 사고를 다시 안 겪는 값으로는 쌌다."
    )


if __name__ == "__main__":
    main()
