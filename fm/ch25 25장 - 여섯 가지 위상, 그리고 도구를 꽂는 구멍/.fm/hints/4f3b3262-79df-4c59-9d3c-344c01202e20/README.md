# MCP 클라이언트는 도구 정의를 어디서 얻는가?

> **답**: 서버에서 `list_tools()`로 받아 온다. 클라이언트 코드는 도구 **이름**만 말하고 **정의**는 갖고 있지 않다.

---

## 1. 요점 한 줄

도구 목록은 **컴파일 시점에 코드에 박혀 있는 것이 아니라, 실행 시점에 서버에서 내려받는 것**이다.
25.4절의 표현대로 하면 「도구는 그래프 밖으로 나가는 엣지」이고, MCP는 **그 엣지 목록을 실행 시점에 받아 오는 방식**이다.

그래서 같은 클라이언트 바이너리가 다른 서버에 붙으면 다른 도구를 갖는다. `ex4_mcp_client.py` 첫 docstring이 그대로 이 얘기다.

```
도구를 코드에 박아 두지 않고 서버에서 받아 오는 게 요점이다.
같은 클라이언트가 다른 서버에 붙으면 다른 도구를 갖게 된다.
```

---

## 2. 호출 순서 — stdio 연결 → initialize → list_tools → call_tool

`code/ex4_mcp_client.py`는 네 단계를 정확히 이 순서로 밟는다. **순서를 건너뛸 수 없다**는 것이 포인트다.

### (0) 서버 프로세스 띄우기 파라미터

```python
params = StdioServerParameters(
    command="python3",
    args=[os.path.join(HERE, "mcp_server.py")],
)
```

MCP의 로컬 전송(transport)은 **stdio**다. 서버는 네트워크 포트가 아니라 **자식 프로세스의 stdin/stdout**으로 말한다.
그래서 `ex4`를 실행하면 `mcp_server.py`를 따로 띄울 필요가 없다 — 클라이언트가 자식 프로세스로 띄운다.
(프레임은 stdout에 한 줄 하나짜리 JSON-RPC 2.0 메시지. 서버가 로그를 stdout에 찍으면 프로토콜이 깨진다. 로그는 stderr로.)

### (1) 연결 — 파이프 두 개를 연다

```python
async with stdio_client(params) as (read, write):
    async with ClientSession(read, write) as s:
```

`stdio_client`가 프로세스를 띄우고 읽기/쓰기 스트림을 준다. `ClientSession`은 그 위에 JSON-RPC 요청·응답·알림을 얹는 계층이다.
이 시점에는 **아직 아무것도 물어보지 않았다.** 파이프만 연 상태다.

### (2) `initialize()` — 악수(handshake). 버전과 능력을 맞춘다

```python
info = await s.initialize()
print(f"서버에 붙었다: {info.serverInfo.name} {info.serverInfo.version}")
print(f"프로토콜 버전: {info.protocolVersion}")
```

MCP는 **초기화 전에 다른 요청을 보내면 안 된다.** `initialize`는 세 가지를 교환한다.

| 교환 항목 | 내용 |
|---|---|
| `protocolVersion` | 클라이언트가 원하는 버전을 제시하고, 서버가 지원하는 버전으로 응답. 안 맞으면 여기서 끊는다 |
| `capabilities` | 서버가 `tools` / `resources` / `prompts` 중 무엇을 갖고 있는지, `listChanged` 알림을 보낼 수 있는지 |
| `serverInfo` | 서버 이름·버전 (`mcp_server.py`의 `FastMCP("graph-tools")`가 여기 이름이 된다) |

`capabilities.tools`가 없으면 `list_tools()`를 부를 자격이 없다. 즉 **「도구를 물어봐도 되는가」부터 협상**한다.
파이썬 SDK 1.5.0 / 프로토콜 2024-11-05 기준(책 확인 시점 2026년 8월). 이후 스펙(2025-06-18)에서는 `initialize` 응답 뒤 `notifications/initialized` 알림까지 보내야 세션이 열린 것으로 본다 — SDK가 대신 해 준다.

### (3) `list_tools()` — **여기가 답이다**

```python
tools = (await s.list_tools()).tools
print(f"서버가 알려 준 도구 {len(tools)}개")
```

JSON-RPC 메서드 이름은 `tools/list`. 클라이언트는 도구 이름도, 인자 이름도, 타입도 **하나도 모르는 상태에서** 이걸 부른다.
그리고 응답에 온 것을 그대로 순회해서 출력한다 — `t.name`, `t.description`, `t.inputSchema`를 코드에 상수로 갖고 있지 않다.

```python
for t in tools:
    req = t.inputSchema.get("required", [])
    props = ", ".join(t.inputSchema.get("properties", {}))
    print(f"  {t.name}({props})")
    print(f"      설명   {t.description}")
    print(f"      필수   {req}")
```

이 루프는 **도구가 3개든 30개든 안 고친다.** 서버가 `@mcp.tool()` 하나를 더 붙이면 다음 실행에서 그냥 4개가 출력된다.

### (4) `call_tool()` — 이름과 인자로 부른다

```python
r = await s.call_tool("find_person", {"name": "김지훈"})
person = json.loads(r.content[0].text)

r = await s.call_tool("chain_of_command", {"person_id": person["id"]})
chain = [json.loads(c.text) for c in r.content]
```

JSON-RPC 메서드는 `tools/call`, 파라미터는 `{"name": ..., "arguments": {...}}`.
여기서 클라이언트 코드가 갖고 있는 것은 **문자열 `"find_person"`과 인자 키 `"name"`뿐**이다. 예제 마지막 문단이 이걸 정확히 짚는다.

```
여기서 클라이언트 코드는 도구 이름을 «세 번» 말했다.
그런데 도구의 «정의»는 한 번도 안 갖고 있다. 서버가 준 것을 그대로 쓴다.
```

---

## 3. 반환되는 도구 정의의 구조 — `name` / `description` / `inputSchema`

`tools/list` 응답은 도구 객체의 배열이다. 각 객체의 핵심 세 필드는 이렇다.

| 필드 | 타입 | 뜻 | 누가 정하나 |
|---|---|---|---|
| `name` | string | 호출할 때 쓰는 식별자. `call_tool`의 첫 인자 | 파이썬 함수 이름 |
| `description` | string | 모델이 **언제 이 도구를 고를지** 판단하는 근거 | 함수 docstring |
| `inputSchema` | object (JSON Schema) | 인자의 이름·타입·필수 여부 | 타입 힌트에서 자동 생성 |

`mcp_server.py`의 이 정의가

```python
@mcp.tool()
def find_person(name: str) -> dict:
    """이름으로 사람을 찾는다. 정확히 일치하는 이름만 찾는다."""
```

와이어에서는 대략 이렇게 온다.

```json
{
  "name": "find_person",
  "description": "이름으로 사람을 찾는다. 정확히 일치하는 이름만 찾는다.",
  "inputSchema": {
    "type": "object",
    "title": "find_personArguments",
    "properties": {
      "name": { "type": "string", "title": "Name" }
    },
    "required": ["name"]
  }
}
```

그래서 클라이언트의 출력이 `find_person(name)` / `필수 ['name']` 형태가 된다.
`inputSchema.properties`의 **키**가 인자 이름이고, `inputSchema.required`가 빠뜨리면 안 되는 인자 목록이다.
`chain_of_command`는 `person_id: str`이니 `properties: {person_id: {type: "string"}}`, `team_members`는 `team: str`이니 `properties: {team: {...}}`가 된다.

> **FastMCP가 하는 일**: 파이썬 함수의 이름 → `name`, docstring → `description`, 타입 힌트 → `inputSchema` (Pydantic으로 JSON Schema 생성). 즉 **스키마를 손으로 쓰지 않는다.**

### 선택 필드 (스펙 2025-06-18 기준)

| 필드 | 뜻 |
|---|---|
| `title` | 사람에게 보여 줄 이름 (`name`은 기계용) |
| `outputSchema` | 구조화된 결과(`structuredContent`)의 스키마 |
| `annotations` | 힌트: `readOnlyHint`, `destructiveHint`, `idempotentHint`, `openWorldHint` |

`annotations`는 **신뢰할 수 없는 힌트**로 취급하라고 스펙이 명시한다. 파괴적 도구를 막는 근거로 쓰지 말 것. (26장의 주제)

### 목록이 바뀌는 경우

서버가 `capabilities.tools.listChanged: true`를 걸었으면, 도구가 늘거나 줄 때 `notifications/tools/list_changed` 알림을 보낸다.
클라이언트는 그걸 받고 `tools/list`를 **다시** 부른다. 도구가 많으면 `nextCursor`로 페이지네이션도 한다.

---

## 4. 반환값 쪽에서 자주 틀리는 것 — `content`는 배열이다

`call_tool` 결과는 `content` **배열**이다. 예제가 주석으로 못을 박아 뒀다.

```python
# 목록을 돌려주는 도구는 «항목마다 content 블록 하나»로 온다.
# r.content[0] 만 읽으면 첫 항목만 읽는 셈이다. 흔한 실수다.
chain = [json.loads(c.text) for c in r.content]
```

`chain_of_command("p1")`은 `[김지훈, 박민수]` 두 항목이니 **content 블록이 2개**로 온다. `r.content[0]`만 읽으면 「김지훈」만 얻는다.
반대로 `find_person`은 dict 하나를 돌려주니 블록 1개다. 그래서 `r.content[0].text`가 맞다.
그리고 `find_person("없는사람")`도 **에러가 아니라 정상 응답**으로 `{"error": "없는사람 없음"}`이 온다 — 도구 내부의 「못 찾음」은 프로토콜 에러가 아니다.

---

## 5. 얻는 것과 치르는 값

### 얻는 것 — 지연 결합

```
서버에 도구를 하나 추가하면 클라이언트는 안 고쳐도 된다.
2장의 말로 하면 «지연 결합되는 서브그래프»고,
그래프의 말로 하면 «엣지 목록을 실행 시점에 받아 오는 것»이다.
```

`mcp_server.py`에 `@mcp.tool()` 함수를 하나 더 붙이면 끝이다. 클라이언트 재배포 없음.

### 치르는 값 — 컴파일 시점에 아무것도 모른다

```
서버가 무엇을 줄지 컴파일 시점에 모른다.
도구 이름이 바뀌면 실행할 때 터진다.
```

타입 체커도, 린터도, IDE 자동완성도 `"find_person"`이라는 문자열이 유효한지 검사해 줄 수 없다. 서버 쪽에서 함수 이름을 `search_person`으로 바꾸면 **런타임에** 터진다.

**대응** (한 장 요약의 처방): **시작할 때 목록을 검증하라.**

```python
tools = {t.name for t in (await s.list_tools()).tools}
NEEDED = {"find_person", "chain_of_command", "team_members"}
missing = NEEDED - tools
if missing:
    raise RuntimeError(f"서버에 없는 도구: {missing}")
```

부트스트랩에서 한 번 확인하면, 「세 번째 사용자 요청 처리 도중」이 아니라 「기동 시점」에 실패한다. 실패 지점을 앞으로 당기는 것이 요령이다.

---

## 6. 왜 `description`이 중요한가 (예제 5로 이어지는 고리)

`list_tools()`로 받아 온 `description`은 장식이 아니다. **모델이 어느 엣지를 탈지 고르는 함수**다.
`ex5_tool_selection.py`는 도구 코드는 그대로 두고 설명만 바꿔 선택 정확도가 오르는 것을 보인다. 좋은 설명에 들어갈 셋:

1. 무엇을 **주는지** (반환값)
2. 어떤 **말**로 물었을 때 이것인지 (사용자 어휘 — 「상사」만 쓰면 「상급자」로 물은 질문을 놓친다)
3. 언제 **안** 쓰는지 (경계)

3번이 제일 자주 빠지고 제일 크게 듣는다. FastMCP에서는 이 셋을 **docstring에 쓰면** 그대로 `description`이 되어 클라이언트로 내려간다.

---

## 7. 한 줄 정리

| 질문 | 답 |
|---|---|
| 도구 정의는 어디 있나 | **서버**. 클라이언트에는 없다 |
| 어떻게 가져오나 | `initialize()` 후 `list_tools()` (`tools/list`) |
| 무엇이 오나 | `name`, `description`, `inputSchema`(JSON Schema) |
| 클라이언트가 코드로 갖는 것 | 도구 **이름 문자열**과 인자 키뿐 |
| 대가 | 컴파일 시점 검증 불가 → 기동 시 목록 검증으로 방어 |

## 출처

- [Model Context Protocol 명세 (2025-06-18)](https://modelcontextprotocol.io/specification/2025-06-18)
- [Tools — tools/list, tools/call, Tool 객체](https://modelcontextprotocol.io/specification/2025-06-18/server/tools)
- 예제: `content/ch25/code/ex4_mcp_client.py`, `content/ch25/code/mcp_server.py`, `content/ch25/code/ex5_tool_selection.py`
