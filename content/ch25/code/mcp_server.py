"""
예제 4에서 붙일 MCP 서버. 그래프 조회 도구 셋을 노출한다.

    python3 mcp_server.py        # 직접 실행하면 stdio 로 기다린다

이 파일은 예제 4가 자식 프로세스로 띄운다.
"""

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("graph-tools")

PEOPLE = {
    "p1": {"name": "김지훈", "team": "결제", "manager": "p3"},
    "p2": {"name": "이서연", "team": "결제", "manager": "p3"},
    "p3": {"name": "박민수", "team": "결제", "manager": None},
}


@mcp.tool()
def find_person(name: str) -> dict:
    """이름으로 사람을 찾는다. 정확히 일치하는 이름만 찾는다."""
    for pid, p in PEOPLE.items():
        if p["name"] == name:
            return {"id": pid, **p}
    return {"error": f"{name} 없음"}


@mcp.tool()
def chain_of_command(person_id: str) -> list:
    """그 사람 위로 올라가는 보고 체계를 뿌리까지 반환한다."""
    out, cur = [], person_id
    while cur and cur in PEOPLE:
        out.append({"id": cur, "name": PEOPLE[cur]["name"]})
        cur = PEOPLE[cur]["manager"]
    return out


@mcp.tool()
def team_members(team: str) -> list:
    """팀 이름으로 구성원 전부를 반환한다."""
    return [{"id": k, "name": v["name"]}
            for k, v in PEOPLE.items() if v["team"] == team]


if __name__ == "__main__":
    mcp.run()
