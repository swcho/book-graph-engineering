# 2장 예제 실행 가이드

확인 시점 2026년 8월. Python 3.9 이상.
예제 2만 LangGraph가 필요하고, 나머지는 **의존성 없음**입니다.

```bash
cd content/ch02/code
python3 ex1_one_file.py       # 한 파일에 다 넣은 단일 에이전트 — 30분 실습의 '전'
python3 ex2_two_nodes.py      # 노드 두 개짜리 그래프 — 30분 실습의 '후'
python3 ex3_depends_on.py     # depends_on 은 DAG 엣지다. 위상 정렬 → 슈퍼스텝
python3 ex4_star_vs_mesh.py   # 성형과 메시, 메시지 수를 세어 본다
```

## 예제 2만 설치가 필요합니다

```bash
pip install "langgraph>=1.0,<2.0"
```

확인 시점 LangGraph 1.0.1 기준입니다. **API 키는 필요 없습니다.**

## API 키 없이 어떻게 돌아가나

`harness.py`의 `fake_model`이 진짜 언어 모델을 대신합니다. 가짜지만 아무렇게나 만든 가짜는 아니고, 진짜 모델이 흔히 보이는 성질 두 가지를 흉내 냅니다.

1. 지시가 길어지면 뒤쪽 요구사항을 빠뜨린다.
2. 빠뜨린 걸 지적해 주면 그때 채운다.

이 두 성질이 2장 전체의 논거입니다. 모델을 바꿔도 정도만 달라지지 성질은 남습니다.

## 예제 1과 예제 2를 나란히 보세요

두 예제는 **프롬프트가 글자 하나까지 같습니다.** 달라진 건 구조뿐입니다. 그런데 산출물이 다릅니다. 2장이 하려는 말이 그겁니다.

```bash
python3 ex1_one_file.py  > /tmp/before.txt
python3 ex2_two_nodes.py > /tmp/after.txt
diff /tmp/before.txt /tmp/after.txt
```

## 숫자는 직접 바꿔서 보세요

`ex4_star_vs_mesh.py` 위쪽 두 상수는 팀마다 다릅니다. 자기 팀 값으로 바꿔서 돌려 보면 엣지 하나가 얼마짜리인지 나옵니다.

```python
AVG_TOKENS_PER_MSG = 1_200      # 요청 + 응답 합. 직접 재서 바꾸세요.
PRICE_PER_MTOK_KRW = 4_000      # 100만 토큰당 원. 2026년 8월 기준 대략치.
```
