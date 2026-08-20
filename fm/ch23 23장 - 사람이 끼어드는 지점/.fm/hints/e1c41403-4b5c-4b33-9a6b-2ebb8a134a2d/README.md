# 네 눈 원칙(four-eyes principle)의 출처

> **Q.** 네 눈 원칙(four-eyes principle)의 출처는 무엇으로 제시되는가?
> **A.** BIS(국제결제은행)의 **bcbs230** 문서다. 상태는 **[사실상 표준]**으로 분류된다.

23장 「키워드와 1차 출처」 표의 마지막 줄이 정답의 근거입니다.

| 키워드 | 상태 | 출처 |
|---|---|---|
| 감사 추적 | **[표준]** | [audit trail](https://www.w3.org/TR/prov-o/) |
| 네 눈 원칙 | **[사실상 표준]** | [four-eyes principle](https://www.bis.org/publ/bcbs230.pdf) |

같은 표 안에서 바로 윗줄인 「감사 추적」만 **[표준]**이고, 「네 눈 원칙」을 포함한 나머지는 전부 **[사실상 표준]**입니다. 이 대비가 이 카드의 진짜 요점입니다.

---

## 1. bcbs230이 정확히 무슨 문서인가

암기용 한 줄로는 "BIS 문서"면 충분하지만, 실제 정체를 알아 두면 헷갈리지 않습니다.

| 항목 | 값 |
|---|---|
| 발행 기관 | **BIS**(Bank for International Settlements, 국제결제은행) 산하 **BCBS**(바젤은행감독위원회) |
| 문서 번호 | `bcbs230` |
| 제목 | **Core Principles for Effective Banking Supervision** (효과적인 은행감독을 위한 핵심원칙) |
| 발행 시점 | 2012년 9월 |
| URL | `https://www.bis.org/publ/bcbs230.pdf` |

주의할 점 두 가지입니다.

- **BIS ≠ BCBS이지만 실무에서는 같이 부릅니다.** BCBS는 BIS에 사무국을 두고 있고, 발행물은 `bis.org` 도메인에 `bcbs###` 번호로 올라갑니다. 그래서 "BIS의 bcbs230"이라는 표현이 성립합니다.
- **bcbs230은 「운영리스크 관리 원칙」이 아닙니다.** 번호가 비슷해서 자주 섞이는데, 운영리스크 쪽은 `bcbs195`(Principles for the Sound Management of Operational Risk, 2011), 리스크 데이터 집계 쪽은 유명한 `bcbs239`입니다. bcbs230은 감독당국이 은행을 평가할 때 쓰는 **29개 핵심원칙 + 평가 기준(essential/additional criteria)** 문서입니다.

---

## 2. bcbs230 안에서 "four eyes"가 실제로 나오는 자리

문서 전체에서 `four eyes`라는 표현은 **딱 한 번**, **Principle 26 (Internal control and audit)**의 **Essential criteria 1(c)**에 나옵니다. 원문 그대로 옮기면 이렇습니다.

> **(c)** checks and balances (or "four eyes principle"): segregation of duties, cross-checking, dual control of assets, double signatures; and

우리말로 하면 "견제와 균형(이른바 '네 눈 원칙'): **직무 분리, 교차 확인, 자산의 이중 통제, 이중 서명**" 입니다.

Principle 26의 원칙 본문은 이렇게 시작합니다.

> The supervisor determines that banks have adequate internal control frameworks ... These include clear arrangements for delegating authority and responsibility; **separation of the functions** that involve committing the bank, paying away its funds, and accounting for its assets and liabilities; reconciliation of these processes; safeguarding the bank's assets; and appropriate independent internal audit and compliance functions ...

즉 **"은행을 구속하는 행위(계약)"와 "자금을 실제로 내보내는 행위"와 "장부에 기록하는 행위"를 서로 다른 사람이 맡으라**는 요구입니다. 23장의 환불 예제가 정확히 이 구조입니다 — 초안 작성(구속), 승인(게이트), 실행(자금 지급).

Essential criteria 1은 통제 항목을 네 갈래로 나열하는데, 네 눈 원칙은 그중 **(c) checks and balances** 한 칸일 뿐입니다.

| 항목 | 내용 |
|---|---|
| (a) organisational structure | 직무·책임 정의, 권한 위임(예: 대출 승인 한도), 핵심 기능 분리 |
| (b) accounting policies and processes | 계정 대사, 통제 목록, 경영 보고 |
| **(c) checks and balances ("four eyes principle")** | **직무 분리, 교차 확인, 자산 이중 통제, 이중 서명** |
| (d) safeguarding assets | 물리적 통제, 전산 접근 통제 |

**보강 사실:** 2024년 4월 개정판(`d573`, Core Principles for effective banking supervision)에서도 Principle 26 Essential criteria 1(c)에 `"four-eyes principle"`이라는 표현이 **하이픈만 붙은 채 그대로** 살아 있습니다. bcbs230 자체는 통합 바젤 프레임워크(BCP 편)로 흡수됐지만, 이 문구는 12년 넘게 유지된 셈이라 출처로 인용하기에 안정적입니다.

---

## 3. 세 용어 구분: four-eyes / dual control / segregation of duties

bcbs230이 이 셋을 한 줄에 나란히 놓았기 때문에 자주 혼동됩니다. 실무 뉘앙스는 다릅니다.

| 용어 | 뜻 | 초점 |
|---|---|---|
| **Four-eyes principle** (네 눈 원칙) | 한 건의 결정에 **눈 두 쌍(= 사람 둘)** 이 관여한다 | *한 건*에 대한 승인 절차. 흔히 maker–checker(작성자–검토자) |
| **Dual control** (이중 통제) | 하나의 자산/작업에 **두 명이 동시에** 있어야 실행된다 | 금고 열쇠 두 개, 이중 서명. 실행 시점의 물리적·기술적 잠금 |
| **Segregation of duties** (직무 분리) | **역할 자체**를 나눠서 한 사람이 전 과정을 못 밟게 한다 | 조직 설계. 사람이 아니라 *직무*의 분리 |

관계로 정리하면: **직무 분리**는 조직도 수준의 구조, **네 눈 원칙**은 그 구조가 한 건의 승인 흐름에서 나타나는 모습, **이중 통제**는 그것을 실행 시점에 강제하는 잠금 장치입니다. 네 눈 원칙이 셋의 대표 이름표 역할을 하다 보니 bcbs230도 괄호로 묶어 "(or 'four eyes principle')"이라고 붙여 놓았습니다.

---

## 4. 왜 [표준]이 아니라 [사실상 표준]인가

23장 각주의 정의부터 다시 봅니다.

> **[표준]** 공식 명세, **[사실상 표준]** 명세는 없지만 업계가 널리 쓰는 것, **[실험]** 아직 자리를 잡는 중

네 눈 원칙이 [사실상 표준]인 이유는 네 가지로 나뉩니다.

**(1) bcbs230은 명세가 아니라 감독 원칙이다.**
`RFC`나 `W3C Recommendation`처럼 "이 필드는 이 타입이고 이 값을 가진다"를 규정하는 문서가 아닙니다. "감독당국은 은행이 적절한 내부통제 체계를 갖췄는지 *판단한다(determines)*"라는 형태의 원칙 서술입니다. 준수 여부를 기계적으로 검증할 대상이 없습니다.

**(2) bcbs230 자체가 법적 구속력이 없다.**
BCBS는 입법 기관이 아니고, Core Principles는 각국 감독당국이 자국 법규에 옮겨 담아야 효력이 생깁니다. BIS 스스로도 이 문서를 "*de facto* minimum standard"라고 표현합니다. 출처 문서부터가 사실상 표준이니, 거기서 인용된 개념이 [표준]이 될 수는 없습니다.

**(3) 용어가 bcbs230에서 만들어진 게 아니다.**
문서는 "(or 'four eyes principle')"이라고 **괄호 안에서 별명처럼** 언급합니다. 즉 이미 업계에서 그렇게들 부르니까 그 이름을 빌려 온 것입니다. 정의를 창설한 게 아니라 관행을 기록한 것이고, 이게 [사실상 표준]의 전형적인 모습입니다.

**(4) 구현이 제각각이다.**
"두 사람"이 누구여야 하는지, 요청자와 승인자가 같은 팀이어도 되는지, 승인자에게 무엇을 보여 줘야 하는지 — 어느 것도 규정돼 있지 않습니다. GitHub의 required reviewers, AWS IAM의 다중 승인, 결제 시스템의 maker-checker가 전부 "네 눈 원칙"을 자처하지만 세부는 다 다릅니다.

**대조군으로 「감사 추적」을 보세요.** 이쪽은 [표준]이고 출처가 [W3C PROV-O](https://www.w3.org/TR/prov-o/)입니다. PROV-O는 W3C Recommendation이고, `prov:Activity` / `prov:Agent` / `prov:wasAssociatedWith` 같은 **어휘가 명세로 고정**돼 있습니다. 같은 표 안에서 [표준]과 [사실상 표준]을 가르는 선이 바로 "검증 가능한 공식 명세가 있는가"입니다.

---

## 5. 23장의 승인 게이트·감사 기록과 어떻게 이어지는가

네 눈 원칙은 23장 본문에 단독 절로 등장하지 않고, **승인 게이트와 감사 기록 전체를 떠받치는 배경 규범**으로 깔려 있습니다. 절별로 짚으면 이렇습니다.

### 23.1 멈추는 것은 예외가 아니다 — 두 번째 눈을 그래프 안에 넣기

`ex1_interrupt.py`의 `사람확인` 노드가 네 눈 원칙의 구현체입니다.

```python
답 = interrupt({
    "물음": "이 환불을 승인하시겠습니까?",
    "금액": s["금액"],
    "근거": "고객 요청 · 상품 미개봉",
})
```

에이전트가 **첫 번째 눈**(초안 작성 = maker), 사람이 **두 번째 눈**(승인 = checker)입니다. bcbs230이 말하는 "committing the bank"와 "paying away its funds"의 분리를, LangGraph에서는 `interrupt()`로 노드 사이에 문을 달아 만듭니다. 중요한 건 이것이 **예외 처리가 아니라 정상 경로**라는 점 — 네 눈 원칙은 사고가 났을 때만 발동하는 게 아니라 상시 통제입니다.

### 23.2 중단점 앞에 부작용을 두지 마라 — 두 번째 눈이 보기 *전에* 돈이 나가면 안 된다

`ex2_node_reruns.py`가 보여 주는 함정은 단순한 재실행 버그를 넘어섭니다. `interrupt()` 앞에 부작용이 있으면 **승인 전에 이미 외부 행위가 일어난 것**이고, 그러면 네 눈 원칙이 형식만 남고 실질이 사라집니다. 승인 화면은 떠 있는데 자금은 이미 나간 상태 — 감사 관점에서는 통제 부재입니다.

```python
def 좋은노드(s: S) -> S:
    답 = interrupt("승인하시겠습니까?")      # 부작용 «앞»에 둔다
    호출수["조회"] += 1                       # 승인 «후»에만 밖으로 나간다
```

### 23.3 어디에 문을 달 것인가 — 통제가 유명무실해지는 지점

`ex3_gate_policy.py`의 결론이 bcbs230의 정신과 정확히 맞물립니다.

> «전부 사람»은 검토 시간이 용량의 3배가 넘는다. (…) 담당자가 대충 보기 시작하고, 결국 «전부 자동»과 같아진다.

네 눈 원칙을 "모든 건에 적용"하면 두 번째 눈이 **감지 못 하는 눈**이 됩니다. 서류상으로는 100% 이중 승인인데 실질 통제율은 0인 상태 — 감사가 가장 싫어하는 형태입니다. 그래서 23장은 문턱을 취향이 아니라 **용량**으로 정하라고 합니다. 검토 시간이 용량의 70%를 넘지 않는 문턱 중 가장 낮은 것.

bcbs230 Principle 26 Essential criteria 1(a)가 "clear delegation of authority (**eg clear loan approval limits**)"라고 *금액 한도*를 예시로 든 것도 같은 맥락입니다. 23장이 "시작은 금액이 좋다. 계산이 되고, 설명이 되고, **감사도 통과한다**"고 쓴 이유가 여기 있습니다.

### 23.4 사람이 답을 안 하면 — 자동 승인은 네 번째 눈을 지우는 일

`ex4_no_answer.py`의 `p_approve`(무조건 자동 승인)는 시간이 지나면 두 번째 눈을 그냥 없애 버립니다. 네 눈 원칙 관점에서 무응답 정책은 **"통제를 언제 포기할 것인가"의 정책**입니다. 그래서 `p_escalate`처럼 소액·저위험만 통과시키고 나머지는 **상급자에게 올려서 다른 두 번째 눈을 붙이는** 쪽이 원칙에 맞습니다. 23장 요약의 "등급 올리기는 판단을 올리는 장치가 아니라 주의를 끄는 장치"가 이 지점입니다.

### 23.5 무엇을 보여 줬는지 남긴다 — 네 눈 원칙의 증명 가능성

`ex5_audit.py`의 스키마가 결정적입니다.

```sql
actor        TEXT,          -- 두 번째 눈이 «누구»였나
decision     TEXT,
shown        TEXT NOT NULL, -- 그 눈이 «무엇을» 봤나
state_hash   TEXT NOT NULL  -- 그 순간의 상태 지문
```

`actor` 없이는 네 눈 원칙을 **증명할 수 없고**(같은 사람이 양쪽을 눌렀는지 알 수 없음), `shown` 없이는 두 번째 눈이 **실제로 봤는지** 알 수 없습니다. 23장 본문의 실화가 정확히 그 사례입니다.

> 승인은 났는데 사고가 났고, 화면에 «3회차 환불»이 안 떠 있었다는 게 기록으로 남아 있었다. **담당자 잘못이 아니라 화면 잘못이었다.**

`state_hash`는 여기서 한 발 더 나갑니다. 승인 시점과 실행 시점의 상태가 다르면 **그 승인은 다른 건에 대한 승인**이므로, 두 번째 눈이 본 적 없는 내용이 나가는 셈입니다. 지문이 다르면 다시 묻는 이유입니다. 다만 "결정에 영향을 주는 필드만 해시" — 매번 다시 물으면 사람이 확인 없이 누르기 시작하고, 그러면 23.3의 함정으로 되돌아갑니다.

---

## 6. 흔히 틀리는 지점

| 오해 | 사실 |
|---|---|
| bcbs239 아닌가? | 아니다. bcbs239는 리스크 데이터 집계·보고 원칙. 네 눈 원칙 출처는 **bcbs230** |
| 운영리스크 관리 원칙 문서다 | 아니다. 그건 bcbs195. bcbs230은 **Core Principles for Effective Banking Supervision** |
| BIS가 아니라 BCBS 아닌가? | 둘 다 맞다. BCBS 발행물이 BIS 사이트에 `bcbs###`로 게시된다. 카드는 "BIS의 bcbs230"으로 표기 |
| 공식 규격이니 [표준] 아닌가? | 아니다. 감독 원칙이지 명세가 아니고, 법적 구속력도 없고, 용어도 업계에서 빌려 온 것 → **[사실상 표준]** |
| 문서 전체가 네 눈 원칙을 다룬다 | 아니다. **Principle 26 Essential criteria 1(c)** 한 줄에 괄호로 언급될 뿐 |
| 네 눈 = 감사 추적 | 다르다. 네 눈은 **[사실상 표준]**(bcbs230), 감사 추적은 **[표준]**(W3C PROV-O) |

---

## 7. 한 줄 암기

> **네 눈 원칙 = BIS bcbs230(Core Principles for Effective Banking Supervision, 2012.9) Principle 26 EC 1(c) → 「checks and balances (or "four eyes principle")」 → 명세가 아닌 감독 원칙이라 [사실상 표준].**
> 같은 표에서 W3C PROV-O를 문 「감사 추적」만 [표준]이다.

---

## 참고 링크

- [BIS bcbs230 — Core Principles for Effective Banking Supervision (2012.9)](https://www.bis.org/publ/bcbs230.pdf) — 23장 키워드 표의 인용 출처
- [BCBS d573 — Core Principles for effective banking supervision (2024.4)](https://www.bis.org/bcbs/publ/d573.pdf) — 개정판. Principle 26 EC 1(c)에 `"four-eyes principle"` 문구 유지
- [BCBS Publications 목록](https://www.bis.org/bcbs/publications.htm) — bcbs195 / bcbs230 / bcbs239 번호 구분 확인용
- [W3C PROV-O](https://www.w3.org/TR/prov-o/) — 같은 표의 「감사 추적」 출처. [표준]과 [사실상 표준]의 대조군
- [LangGraph — Interrupts](https://docs.langchain.com/oss/python/langgraph/interrupts) — 사람 개입·중단점·재개 명령의 출처
- [Azure Architecture — Gatekeeper pattern](https://learn.microsoft.com/en-us/azure/architecture/patterns/gatekeeper) — 승인 관문의 출처
