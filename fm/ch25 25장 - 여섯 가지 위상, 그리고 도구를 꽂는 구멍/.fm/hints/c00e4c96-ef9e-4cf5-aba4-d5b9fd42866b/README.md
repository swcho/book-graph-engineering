# MCP에서 목록을 반환하는 도구의 응답 구조

## 질문

MCP에서 목록을 반환하는 도구의 응답은 어떤 구조로 오는가?

## 답

**항목마다 `content` 블록 하나로 온다.** `r.content[0]`만 읽으면 첫 항목만 읽는 흔한 실수가 된다.

---

## 1. 스펙 사실: `CallToolResult.content`는 «블록의 리스트»다

MCP 스펙(2025-06-18)에서 `tools/call`의 결과는 다음 모양이다.

```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "result": {
    "content": [
      { "type": "text", "text": "..." }
    ],
    "isError": false
  }
}
```

여기서 중요한 것은 `content`가 **문자열이 아니라 배열**이라는 점이다. 스펙 표현을 그대로 옮기면:

> Unstructured content is returned in the `content` field of a result, and can contain **multiple content items of different types**.

블록으로 올 수 있는 타입은 다섯 가지다.

| `type` | 내용 |
|---|---|
| `text` | `{"type": "text", "text": "..."}` |
| `image` | `{"type": "image", "data": "<base64>", "mimeType": "image/png"}` |
| `audio` | `{"type": "audio", "data": "<base64>", "mimeType": "audio/wav"}` |
| `resource_link` | `{"type": "resource_link", "uri": "file:///...", "name": "..."}` |
| `resource` | `{"type": "resource", "resource": {"uri": ..., "text": ...}}` (임베디드 리소스) |

즉 **`content`가 리스트인 이유는 원래 "여러 조각을 담을 자리"로 설계됐기 때문**이다. 텍스트 한 줄 + 스크린샷 한 장 + 파일 링크 하나를 한 응답에 담을 수 있어야 하니까. 항목 수와 블록 수를 1:1로 묶어 주는 규칙은 스펙에 없다. 그건 서버 구현의 직렬화 정책이다.

여기서 실수의 씨앗이 생긴다. 대부분의 도구가 한 블록만 돌려주기 때문에, 사람들은 `content[0].text`를 «응답 본문»이라고 외워 버린다.

## 2. 왜 목록 반환 도구는 여러 블록으로 오는가

25장 예제 4의 서버(`code/mcp_server.py`)를 보자.

```python
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("graph-tools")

@mcp.tool()
def find_person(name: str) -> dict:          # ← dict 하나를 반환
    """이름으로 사람을 찾는다. 정확히 일치하는 이름만 찾는다."""
    ...
    return {"id": pid, **p}

@mcp.tool()
def chain_of_command(person_id: str) -> list:  # ← list 를 반환
    """그 사람 위로 올라가는 보고 체계를 뿌리까지 반환한다."""
    out, cur = [], person_id
    while cur and cur in PEOPLE:
        out.append({"id": cur, "name": PEOPLE[cur]["name"]})
        cur = PEOPLE[cur]["manager"]
    return out
```

FastMCP는 파이썬 반환값을 content 블록으로 «변환»해 준다. 그 변환 규칙이 이렇다.

- 반환값이 스칼라/딕셔너리 하나 → JSON 직렬화해서 **텍스트 블록 1개**
- 반환값이 **리스트/시퀀스** → **원소마다 블록 하나**로 펼침(unwrap)
- 반환값이 이미 content 블록(또는 블록 리스트)이면 그대로 사용

그래서 `find_person("김지훈")`은 블록 1개, `chain_of_command("p1")`은 `[김지훈, 박민수]` 두 원소 → **블록 2개**가 된다. 예제 4의 마지막 출력이 그 사실을 짚는다.

```
(chain_of_command 는 content 블록 2개로 왔다. 목록 도구는 항목마다 블록 하나다.)
```

정리하면 원인은 두 겹이다.

1. **스펙 층**: `content`는 애초에 리스트다. 하나만 온다는 보장이 없다.
2. **SDK 층**: 서버가 리스트를 반환하면 SDK가 원소별 블록으로 펼친다.

## 3. 실수 대비 올바른 처리

### 잘못된 코드 — 첫 항목만 읽는다

```python
r = await s.call_tool("chain_of_command", {"person_id": "p1"})

# ✗ 블록 0번만 읽는다. 보고 체계가 5단이어도 «김지훈» 하나만 남는다.
chain = json.loads(r.content[0].text)
```

이 버그의 못된 성질은 **터지지 않는다**는 것이다. 예외도 안 나고, 타입도 맞고, 사람 이름 하나는 제대로 들어 있다. 그래서 리뷰를 통과하고, 조직도 두 단짜리 테스트 데이터에서도 통과하고, 운영에서 «보고 라인이 왜 한 명만 나와요?»로 발견된다.

### 처방 A — 전체 블록을 순회한다

예제 4의 실제 코드가 이 방식이다.

```python
r = await s.call_tool("chain_of_command", {"person_id": person["id"]})
# 목록을 돌려주는 도구는 «항목마다 content 블록 하나»로 온다.
# r.content[0] 만 읽으면 첫 항목만 읽는 셈이다. 흔한 실수다.
chain = [json.loads(c.text) for c in r.content]
names = " → ".join(c["name"] for c in chain)
```

여러 타입이 섞여 올 수 있으니 좀 더 방어적으로 쓰면 이렇다.

```python
def read_json_items(result) -> list:
    """CallToolResult 의 모든 텍스트 블록을 항목 리스트로 모은다."""
    if getattr(result, "isError", False):
        raise RuntimeError(_first_text(result))

    items = []
    for block in result.content:
        if getattr(block, "type", None) != "text":
            continue                       # image/audio/resource_link 는 건너뛴다
        items.append(json.loads(block.text))
    return items
```

이 함수는 블록이 1개든 N개든 똑같이 동작한다. **호출부가 블록 개수를 몰라도 되게 만드는 것**이 핵심이다. 개수는 서버 구현이 언제든 바꿀 수 있는 값이라서, 거기에 코드를 맞추면 안 된다.

### 처방 B — 서버가 구조화된 JSON 한 블록으로 반환한다

블록 펼침을 아예 안 일어나게 하는 쪽이 더 튼튼하다. 리스트를 «감싸서» 딕셔너리 하나로 돌려주면 된다.

```python
@mcp.tool()
def chain_of_command(person_id: str) -> dict:
    """그 사람 위로 올라가는 보고 체계를 뿌리까지 반환한다."""
    out, cur = [], person_id
    while cur and cur in PEOPLE:
        out.append({"id": cur, "name": PEOPLE[cur]["name"]})
        cur = PEOPLE[cur]["manager"]
    return {"chain": out, "count": len(out)}   # ← 리스트를 봉투에 넣는다
```

클라이언트는 이렇게 단순해진다.

```python
r = await s.call_tool("chain_of_command", {"person_id": "p1"})
chain = json.loads(r.content[0].text)["chain"]   # 블록은 항상 1개
```

덤으로 `count`, `truncated`, `next_cursor` 같은 메타데이터를 얹을 자리가 생긴다. 리스트를 그냥 반환하면 그 자리가 없다.

### 처방 C — `structuredContent` + `outputSchema`를 쓴다

2025-06-18 스펙부터 결과에 **구조화 필드**가 정식으로 들어왔다. 도구 정의에 `outputSchema`를 붙이면 결과의 `structuredContent`가 그 스키마를 따르도록 강제된다.

```json
{
  "name": "chain_of_command",
  "inputSchema": { "type": "object", "properties": { "person_id": { "type": "string" } },
                   "required": ["person_id"] },
  "outputSchema": {
    "type": "object",
    "properties": {
      "chain": {
        "type": "array",
        "items": { "type": "object",
                   "properties": { "id": { "type": "string" }, "name": { "type": "string" } },
                   "required": ["id", "name"] }
      }
    },
    "required": ["chain"]
  }
}
```

응답은 이렇게 온다.

```json
{
  "result": {
    "content": [
      { "type": "text", "text": "{\"chain\": [{\"id\": \"p1\", \"name\": \"김지훈\"}, {\"id\": \"p3\", \"name\": \"박민수\"}]}" }
    ],
    "structuredContent": {
      "chain": [
        { "id": "p1", "name": "김지훈" },
        { "id": "p3", "name": "박민수" }
      ]
    }
  }
}
```

스펙의 규칙 두 가지를 기억하면 된다.

- `outputSchema`가 있으면 서버는 **MUST** 그에 맞는 구조화 결과를 주고, 클라이언트는 **SHOULD** 검증한다.
- 하위 호환을 위해 구조화 결과를 주는 도구는 **SHOULD** 같은 내용의 JSON을 `TextContent` 블록으로도 넣는다. (그래서 위 예에도 `content`가 함께 있다.)

`structuredContent`는 **JSON 객체**여야 하므로, 리스트는 여기서도 봉투가 필요하다. FastMCP는 객체가 아닌 반환값을 `{"result": ...}`로 감싸 준다.

클라이언트는 이렇게 읽는다.

```python
r = await s.call_tool("chain_of_command", {"person_id": "p1"})
if r.structuredContent is not None:
    chain = r.structuredContent["chain"]                  # 파싱도 필요 없다
else:
    chain = [json.loads(c.text) for c in r.content]       # 구식 서버 폴백
```

## 4. 세 방식 비교

| 방식 | 클라이언트 코드 | 블록 수 | 메타데이터 자리 | 비고 |
|---|---|---|---|---|
| 리스트 반환 + `content[0]` | `json.loads(r.content[0].text)` | N | 없음 | **버그.** 조용히 첫 항목만 읽는다 |
| 리스트 반환 + 전체 순회 | `[json.loads(c.text) for c in r.content]` | N | 없음 | 예제 4의 방식. 옳지만 블록 수에 의존 |
| 봉투 dict 반환 | `json.loads(r.content[0].text)["chain"]` | 1 | 있음 | 서버를 고칠 수 있으면 이쪽 |
| `structuredContent` + `outputSchema` | `r.structuredContent["chain"]` | 1 | 있음 | 스키마 검증까지 받는다 |

## 5. 이 장의 맥락에서 왜 중요한가

25.4절의 논지는 «도구는 그래프 밖으로 나가는 엣지고, MCP는 그 엣지 목록을 실행 시점에 받아 오는 방식»이다. 지연 결합의 대가가 이것이다. **컴파일 시점에 서버가 무엇을 어떤 모양으로 줄지 모른다.**

`r.content[0]`는 그 대가를 무시한 코드다. 「응답은 블록 하나로 온다」는 가정을 코드에 박아 넣었는데, 그 가정은 서버 쪽 반환 타입 하나(`list` ↔ `dict`)만 바뀌어도 무너진다. 그리고 무너질 때 예외로 알려 주지 않는다.

그래서 장의 요약이 «시작할 때 목록을 검증하세요»로 끝난다. 검증할 것은 도구 이름과 입력 스키마만이 아니다. **결과를 어떻게 읽을지도 가정이고, 그 가정도 검증 대상이다.** 가능하면 `outputSchema`를 요구하고, 없으면 블록 전체를 순회하는 헬퍼 하나를 두고 호출부에서 인덱스를 직접 만지지 않게 한다.

## 한 줄 정리

`CallToolResult.content`는 블록의 **리스트**이고, 리스트를 반환하는 도구는 SDK가 **항목마다 블록 하나**로 펼친다. 그러니 전체를 순회하거나(처방 A), 서버가 봉투 dict / `structuredContent` 한 덩어리로 돌려주게 만들라(처방 B·C). `r.content[0]`은 조용히 첫 항목만 읽는다.

## 출처

- [MCP Specification 2025-06-18 — Server / Tools](https://modelcontextprotocol.io/specification/2025-06-18/server/tools)
- [MCP Specification 2025-06-18](https://modelcontextprotocol.io/specification/2025-06-18)
- 25장 예제 `code/ex4_mcp_client.py`, `code/mcp_server.py`
