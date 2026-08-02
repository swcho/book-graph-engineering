# 25장 예제 실행 가이드

확인 시점 2026년 8월. Python 3.9 이상.

```bash
cd content/ch25/code
python3 ex1_topologies.py       # 여섯 위상 비교 (의존성 없음)
python3 ex2_fanout.py           # 펴는 값과 합류 값 (의존성 없음)
python3 ex3_router.py           # 라우터 정확도와 교환 (의존성 없음)

pip install mcp
python3 ex4_mcp_client.py       # 진짜 MCP 서버에 붙는다 (mcp_server.py 를 띄운다)

python3 ex5_tool_selection.py   # 도구 설명이 선택을 정한다 (의존성 없음)
```

`ex4` 는 `mcp_server.py` 를 자식 프로세스로 띄웁니다. 따로 실행하지 않아도 됩니다.
확인 시점의 mcp 파이썬 SDK 는 1.5.0 이고 프로토콜 버전은 2024-11-05 였습니다.
