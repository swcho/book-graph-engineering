# 26장 — 무엇을 못 하게 할 것인가

`4부 — 에이전트 그래프 엔지니어링 (트랙 2)` | [책 전체 목차](../../../README.md) | [출처 링크 모음](../../../SOURCES.md)

> 권한 검토 회의에서 30분 동안 「읽기만 주면 안전하죠」를 확인했습니다.

지난 장이 「무엇을 할 수 있게 할까」였다면 이 장은 반대입니다. 그리고 이쪽이 훨씬 어렵습니다. 할 수 있게 하는 건 하나씩 더하면 되는데, 못 하게 하는 건 *조합*을 봐야 하거든요.

## 이 장의 절

| 절 | 제목 |
|---|---|
| 26.1 | 권한은 목록이 아니라 경로다 |
| 26.2 | 금지 목록은 반드시 샌다 |
| 26.3 | 읽어 온 글 안에 명령이 섞여 있다 |
| 26.4 | 하나가 뚫렸을 때 어디까지 |
| 26.5 | 막은 것도 기록한다 |

## 한 장 요약

- 권한은 목록이 아니라 경로입니다. 개별로 무해한 권한이 조합되면 유출 경로가 돼요. 도구를 하나씩 보지 말고 「어느 권한이 나가는 문인가」를 물으세요. 대개 셋입니다. 나가는 네트워크, 임의 실행, 쓰기.
- 그리고 「나가는 경로」를 셀 때 네트워크만 보지 마세요. 로그, 에러 메시지, 그리고 응답 자체도 나가는 경로입니다.
- 금지 목록은 반드시 샙니다. 셀 수 있는 것만 막는데 우회 방법은 셀 수 없거든요. 허용 목록은 손이 계속 가는 대신 안 샙니다. 다만 명령 이름만 허용하면 부족하고 인자까지 봐야 합니다. 문자열이 아니라 정규화한 결과를 비교하세요.
- 프롬프트 인젝션은 프롬프트로 못 막습니다. 경계 표시와 입력 검사는 확률을 낮추고, 권한 차단만이 가능성을 없앱니다. 1순위는 「이 에이전트가 애초에 할 수 없게」입니다.
- 언젠가 뚫린다고 가정하고 폭발 반경을 재세요. 최소 권한은 「자기 일에 필요한 것만」이 아니라 「어떤 하나도 치명 조합을 갖지 않게」입니다.
- 「읽기는 안전하다」가 틀렸습니다. 읽기도 돈을 쓰고, 흔적을 남기고, 상대를 아프게 합니다.
- 막은 것도 기록하세요. 「사람이 뒤집은 비율」이 정책 품질 지표입니다. 100% 뒤집히는 규칙은 사람 시간만 쓰고 있는 겁니다.

## 키워드와 1차 출처

| 키워드 | 상태 | 출처 |
|---|---|---|
| 최소 권한 | [사실상 표준] | [least privilege](https://csrc.nist.gov/glossary/term/least_privilege) |
| 허용 목록 | [사실상 표준] | [allowlist](https://cheatsheetseries.owasp.org/cheatsheets/Input_Validation_Cheat_Sheet.html) |
| 프롬프트 인젝션 | [사실상 표준] | [prompt injection](https://genai.owasp.org/llmrisk/llm01-prompt-injection/) |
| 간접 인젝션 | [사실상 표준] | [indirect prompt injection](https://genai.owasp.org/llmrisk/llm01-prompt-injection/) |
| 폭발 반경 | [사실상 표준] | [blast radius](https://sre.google/sre-book/addressing-cascading-failures/) |
| 권한 상승 | [표준] | [privilege escalation](https://attack.mitre.org/tactics/TA0004/) |
| 샌드박스 | [사실상 표준] | [sandbox](https://gvisor.dev/docs/) |
| 감사 로그 | [표준] | [audit log](https://csrc.nist.gov/pubs/sp/800/53/r5/upd1/final) |

상태 표시는 **[표준]** 공식 명세, **[사실상 표준]** 명세는 없지만 업계가 널리 쓰는 것, **[실험]** 아직 자리를 잡는 중이라는 뜻입니다.

## 예제 실행

<!-- 실행 가이드 시작 — 사람이 쓴 부분. gen-docs.py 가 건드리지 않는다. -->

확인 시점 2026년 8월. Python 3.9 이상. 외부 의존성 없음.

```bash
cd content/ch26/code
python3 ex1_permission_graph.py   # 권한을 목록이 아니라 도달 경로로
python3 ex2_deny_vs_allow.py      # 금지 목록은 왜 반드시 새는가
python3 ex3_injection.py          # 문서 안에 섞인 명령
python3 ex4_blast_radius.py       # 하나가 뚫렸을 때 어디까지
python3 ex5_audit_trail.py        # 차단 로그가 정책을 고친다
```

`ex3` 은 모델을 부르지 않습니다. 실제 인젝션 성공률을 재려면 모델이 필요한데,
그 실험은 공격 문자열을 책에 싣게 되므로 여기서는 «구조»만 보여 줍니다.

<!-- 실행 가이드 끝 -->

---

**다음 부에서 만나는 것:** 여기까지가 에이전트 그래프였습니다. 다음 부에서 두 트랙이 합류합니다. 3부의 지식 그래프가 에이전트의 «기억»이 되고, 에이전트가 그 그래프를 «스스로 넓히기» 시작해요. 그리고 그때 이 장의 권한 얘기가 훨씬 무거워집니다. 읽는 것과 쓰는 것이 같은 그래프에서 일어나니까요.

---

이전 [25장 여섯 가지 위상, 그리고 도구를 꽂는 구멍](../../ch25/code/README.md) | [전체 목차](../../../README.md) | 다음 [27장 에이전트에게 기억을 주는 가장 싼 방법](../../ch27/code/README.md)

이 장에서 틀린 곳을 찾으셨다면 [사실 오류로](https://github.com/leaf-kit/book-graph-engineering/issues/new?template=01-fact-error.yml), 상태 라벨이 어긋났다면 [라벨 이의로](https://github.com/leaf-kit/book-graph-engineering/issues/new?template=03-status-label.yml) 적어 주세요.
