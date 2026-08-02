"""
예제 4 — MCP 서버에 붙어서 도구 목록과 스키마를 «받아 온다».

    pip install mcp
    python3 ex4_mcp_client.py

도구를 코드에 박아 두지 않고 서버에서 받아 오는 게 요점이다.
같은 클라이언트가 다른 서버에 붙으면 다른 도구를 갖게 된다.
"""

import asyncio
import json
import os

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

HERE = os.path.dirname(os.path.abspath(__file__))


async def main():
    params = StdioServerParameters(
        command="python3",
        args=[os.path.join(HERE, "mcp_server.py")],
    )

    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as s:
            info = await s.initialize()
            print(f"서버에 붙었다: {info.serverInfo.name} "
                  f"{info.serverInfo.version}")
            print(f"프로토콜 버전: {info.protocolVersion}\n")

            tools = (await s.list_tools()).tools
            print(f"서버가 알려 준 도구 {len(tools)}개\n")
            for t in tools:
                req = t.inputSchema.get("required", [])
                props = ", ".join(t.inputSchema.get("properties", {}))
                print(f"  {t.name}({props})")
                print(f"      설명   {t.description}")
                print(f"      필수   {req}")

            print("\n실제로 불러 본다.\n")
            r = await s.call_tool("find_person", {"name": "김지훈"})
            person = json.loads(r.content[0].text)
            print(f"  find_person('김지훈') → {person}")

            r = await s.call_tool("chain_of_command",
                                  {"person_id": person["id"]})
            # 목록을 돌려주는 도구는 «항목마다 content 블록 하나»로 온다.
            # r.content[0] 만 읽으면 첫 항목만 읽는 셈이다. 흔한 실수다.
            chain = [json.loads(c.text) for c in r.content]
            names = " → ".join(c["name"] for c in chain)
            print(f"  chain_of_command('{person['id']}') → {names}")

            r = await s.call_tool("find_person", {"name": "없는사람"})
            print(f"  find_person('없는사람') → {r.content[0].text}")

    print(
        f"\n(chain_of_command 는 content 블록 {2}개로 왔다. "
        "목록 도구는 항목마다 블록 하나다.)\n"
        "\n여기서 클라이언트 코드는 도구 이름을 «세 번» 말했다.\n"
        "그런데 도구의 «정의»는 한 번도 안 갖고 있다. 서버가 준 것을 그대로 쓴다.\n"
        "\n그래서 서버에 도구를 하나 추가하면 클라이언트는 안 고쳐도 된다.\n"
        "2장의 말로 하면 «지연 결합되는 서브그래프»고,\n"
        "그래프의 말로 하면 «엣지 목록을 실행 시점에 받아 오는 것»이다.\n"
        "\n대신 값을 치른다. 서버가 무엇을 줄지 컴파일 시점에 모른다.\n"
        "도구 이름이 바뀌면 실행할 때 터진다. 그 얘기는 예제 5에서."
    )


if __name__ == "__main__":
    asyncio.run(main())
