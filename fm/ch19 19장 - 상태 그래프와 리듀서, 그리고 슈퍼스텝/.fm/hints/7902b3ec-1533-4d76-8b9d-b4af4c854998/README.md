# 슈퍼스텝은 어디서 왔는가 — 프리겔(Pregel)과 벌크 동기 병렬(BSP)

**질문**: 슈퍼스텝 개념의 계산 모형 뿌리는 무엇인가?

**답**: 프리겔(Pregel)과 벌크 동기 병렬(BSP)이다. 둘 다 ACM 논문이 1차 출처다.

---

## 한눈에 보는 계보

```
Valiant 1990 (CACM)          Malewicz et al. 2010 (SIGMOD)        LangGraph (2024~)
벌크 동기 병렬(BSP)     →      프리겔(Pregel)                 →     Pregel 실행기
「supersteps」 용어 도입        vertex-centric + superstep          노드/채널 + superstep
지역 계산 → 통신 → 배리어      메시지 전달, vote to halt            plan → execution → update
```

19장 본문의 「키워드와 1차 출처」 표에 이 두 논문이 그대로 실려 있습니다.

| 키워드 | 상태 | 출처 |
|---|---|---|
| 프리겔 계산 모형 | [사실상 표준] | `https://dl.acm.org/doi/10.1145/1807167.1807184` |
| 벌크 동기 병렬 | [사실상 표준] | `https://dl.acm.org/doi/10.1145/79173.79181` |

두 링크 모두 ACM Digital Library, 즉 논문 원문이 1차 출처입니다. 블로그나 프레임워크 문서가 아닙니다.

---

## 1. 뿌리 ① — 벌크 동기 병렬(BSP)

### 서지 사항 (검증됨)

- **저자**: Leslie G. Valiant (하버드대, 2010년 튜링상 수상자)
- **제목**: *A bridging model for parallel computation*
- **게재지**: **Communications of the ACM (CACM)**, Volume 33, Issue 8, August 1990, pp. 103–111
- **DOI**: `10.1145/79173.79181`

### 핵심 주장 — 「다리 놓기 모형(bridging model)」

Valiant의 논지는 병렬 알고리즘 하나를 제안한 게 아닙니다. **소프트웨어와 하드웨어 사이를 잇는 표준 추상**이 병렬 컴퓨팅에는 없다는 문제 제기였습니다.

순차 컴퓨팅에서는 **폰 노이만 모형**이 그 역할을 했습니다. 알고리즘 설계자는 폰 노이만 모형만 보고 프로그램을 짜고, 하드웨어 설계자는 폰 노이만 모형만 만족시키면 됐습니다. 양쪽이 서로를 몰라도 됐다는 게 핵심입니다. 논문 안에서 Valiant는 BSP를 두고 *"the BSP model can be viewed as a pragmatic embodiment of these positive results much as the von Neumann model is a pragmatic embodiment of Turing's theorem"* 라고 씁니다. 그리고 이런 문장도 있습니다 — *"A major purpose of such a model is simply to act as a standard on which people can agree."*

병렬 컴퓨팅에는 그런 합의된 중간층이 없었고, BSP가 그 후보라는 게 논문의 전부입니다.

### BSP 모형의 정의 — 세 가지 속성

논문 「The BSP Model」 절의 정의를 그대로 옮기면:

> The BSP model of parallel computation or a bulk-synchronous parallel computer (BSPC) is defined as the combination of three attributes:
> 1. **A number of components**, each performing processing and/or memory functions;
> 2. **A router** that delivers messages point to point between pairs of components; and
> 3. **Facilities for synchronizing** all or a subset of the components at regular intervals of *L* time units where *L* is the periodicity parameter.

이어서 **슈퍼스텝**이 등장합니다:

> A computation consists of a sequence of **supersteps**. In each superstep, each component is allocated a task consisting of some combination of local computation steps, message transmissions and (implicitly) message arrivals from other components. After each period of *L* time units, a global check is made to determine whether the superstep has been completed by all the components. If it has, the machine proceeds to the next superstep. Otherwise, the next period of *L* units is allocated to the unfinished superstep.

즉 「superstep」이라는 **단어 자체가 이 1990년 CACM 논문에서 나왔습니다**. 슈퍼스텝의 조상은 프리겔이 아니라 BSP입니다.

### BSP 슈퍼스텝의 3단계

원문은 위처럼 서술형이지만, 이후 문헌에서 표준적으로 정리된 3단계는 다음과 같습니다.

| 단계 | 영문 | 하는 일 | 중요한 성질 |
|---|---|---|---|
| 1 | **local computation** (concurrent computation) | 각 프로세스가 **자기 로컬 메모리만** 보고 계산 | 남이 이번 스텝에 쓴 값은 못 본다 |
| 2 | **communication** | 프로세스끼리 메시지 교환 (router가 담당) | 이 통신 결과는 **다음** 슈퍼스텝에서 보인다 |
| 3 | **barrier synchronisation** | 모두가 배리어에 도달할 때까지 대기 | 전원이 끝나기 전엔 아무도 다음으로 못 간다 |

> 주의: "local computation → communication → barrier synchronisation"이라는 3단계 도식은 Valiant 원문의 축자 표현이 아니라, BSP 문헌에서 널리 통용되는 정리 방식입니다. 원문은 대신 components / router / synchronization facilities라는 **세 속성**과 periodicity 파라미터 *L*로 같은 내용을 기술합니다. 인용할 때 이 구분을 지켜 주세요.

Valiant는 계산과 통신을 분리한 이유도 명시합니다 — *"In separating the components from the router, we emphasize that the tasks of computation and communication can be separated."* 계산 담당과 통신 담당을 갈라 놓아야 비용 모형(파라미터 *g*, *L*)이 깔끔하게 잡힌다는 겁니다.

### BSP가 사 오는 것과 팔아 넘기는 것

- **사 오는 것**: 결정론에 가까운 의미론. 데드락과 경쟁 조건이 구조적으로 안 생깁니다. 성능 예측이 가능합니다(*g*, *L*을 재면 됨).
- **파는 것**: 지연 시간. 가장 느린 프로세스가 배리어를 붙잡으면 전원이 기다립니다(straggler 문제).

19장에서 "같은 슈퍼스텝의 노드들은 서로가 쓴 걸 못 본다"고 못을 박는 이유가 여기 있습니다. 그건 LangGraph의 구현 편의가 아니라 **BSP 모형이 성립하기 위한 조건**입니다.

---

## 2. 뿌리 ② — 프리겔(Pregel)

### 서지 사항 (검증됨)

- **저자**: Grzegorz Malewicz, Matthew H. Austern, Aart J. C. Bik, James C. Dehnert, Ilan Horn, Naty Leiser, Grzegorz Czajkowski (전원 Google)
- **제목**: *Pregel: A System for Large-Scale Graph Processing*
- **게재지**: **SIGMOD '10** — Proceedings of the 2010 ACM SIGMOD International Conference on Management of Data, pp. 135–146
- **DOI**: `10.1145/1807167.1807184`

### 이름의 유래

논문 각주 1에 직접 적혀 있습니다.

> The name honors Leonhard Euler. The Bridges of Königsberg, which inspired his famous theorem, spanned the **Pregel** river.

쾨니히스베르크의 다리 문제 — 그래프 이론의 시조 — 가 놓여 있던 그 강 이름이 프레겔강입니다. 그래프 처리 시스템에 붙일 이름으로 이보다 적절하기 어렵습니다.

### BSP를 상속한다고 논문이 직접 말한다

프리겔 논문 서론에 이 문장이 있습니다.

> The high-level organization of Pregel programs is inspired by **Valiant's Bulk Synchronous Parallel model** [45]. Pregel computations consist of a sequence of iterations, called **supersteps**.

계보가 논문 안에서 명시적으로 선언되어 있습니다. 프리겔이 BSP에서 슈퍼스텝을 물려받았다는 건 해석이 아니라 저자 진술입니다.

### vertex-centric — "think like a vertex"

프리겔의 프로그래밍 모형은 **정점 중심(vertex-centric)** 입니다. 그래프 전체를 어떻게 순회할지 짜는 대신, **정점 하나가 한 슈퍼스텝에서 무엇을 하는가**만 함수로 씁니다.

> The function specifies behavior at a single vertex *V* and a single superstep *S*. It can read messages sent to *V* in superstep *S − 1*, send messages to other vertices that will be received at superstep *S + 1*, and modify the state of *V* and its outgoing edges.

읽는 건 **직전** 슈퍼스텝의 메시지, 보내는 건 **다음** 슈퍼스텝에 도착할 메시지. 「지금 이 슈퍼스텝 안에서 옆 정점과 주고받기」는 아예 문법에 없습니다.

논문은 이 성질을 분산 구현의 전제로 못 박습니다.

> By design the model is well suited for distributed implementations: **it doesn't expose any mechanism for detecting order of execution within a superstep**, and all communication is from superstep *S* to superstep *S + 1*.

그리고 그 대가로 얻는 것:

> The synchronicity of this model makes it easier to reason about program semantics when implementing algorithms, and ensures that Pregel programs are **inherently free of deadlocks and data races** common in asynchronous systems.

> **용어 주의**: "think like a vertex"라는 **표어 자체는 프리겔 논문 본문의 문구가 아닙니다.** 논문은 "the vertex-centric approach"라고 씁니다. 표어로 굳은 건 이후 문헌 — 특히 Tian et al., *From "Think Like a Vertex" to "Think Like a Graph"* (PVLDB 2014)와 McCune, Weninger, Madey, *Thinking Like a Vertex: A Survey of Vertex-Centric Frameworks for Large-Scale Distributed Graph Processing* (ACM Computing Surveys 48(2), 2015) — 을 거치면서입니다. 개념의 출처는 프리겔, 표어의 유행은 후속 논문. 이렇게 구분해서 쓰는 게 정확합니다.

### 프리겔이 BSP 위에 얹은 것

| 장치 | 하는 일 | 19장과의 연결 |
|---|---|---|
| **superstep** | 반복 단위. 전역 동기화 지점으로 구분 | 19.2절 「경계가 그어지는 자리」 |
| **message passing** | 정점 간 유일한 통신 수단. *S → S+1* 단방향 | 노드가 「바뀐 것」만 돌려주는 것과 같은 발상 |
| **vote to halt** | 정점이 스스로 비활성화. 전원 비활성 + 전송 중 메시지 0이면 종료 | 20장 「끝나지 않는 루프를 끝내는 법」의 조상 |
| **combiner** | 같은 목적지로 가는 메시지들을 미리 합침 | **리듀서의 직계 조상**. 논문은 "no guarantees about which messages are combined, the groupings presented to the combiner, or the order of combining"이라 명시 → **교환·결합법칙을 지켜야 한다**는 요구가 여기서 나온다 |
| **aggregator** | 슈퍼스텝 *S*의 값들을 모아 *S+1*의 모든 정점에 노출 | 전역 상태 채널 |

**combiner 항목이 이 카드에서 가장 실무적인 대목입니다.** 19장 「한 장 요약」의 *"리듀서는 교환법칙을 지켜야 합니다. `f(a,b) == f(b,a)`가 아니면 실행 순서에 따라 답이 달라지고, 그 순서는 여러분이 못 정해요"* 는 프리겔 combiner의 제약을 그대로 물려받은 것입니다. 합치는 순서를 시스템이 정하니, 순서에 의존하는 합치기 함수는 애초에 정의되지 않은 동작입니다.

`ex3_custom_reducer.py`가 이걸 실험으로 보여 줍니다. `merge_dict`는 "새 것이 이긴다"로 짰는데 실행기가 CRM을 먼저 돌려서 ERP가 「새 것」이 되어 버립니다. 반면 `keep_latest`(타임스탬프 비교)와 `keep_best`(신뢰도 비교)는 순서와 무관하게 같은 답을 냅니다. **판단 근거를 값 안에 넣어 교환법칙을 복원한 것**입니다.

---

## 3. 계보의 종착점 — LangGraph의 `Pregel` 실행기

### 클래스 이름부터가 계보 선언이다

LangGraph의 실행 엔진 클래스 이름은 그냥 **`Pregel`** 입니다. 비유가 아니라 파이썬 클래스 이름입니다.

- 임포트 경로: `langgraph.pregel.Pregel` (구현은 `langgraph.pregel.main`)
- `StateGraph`를 `.compile()` 하면 나오는 `CompiledStateGraph`는 **`Pregel`을 상속합니다** — LangGraph 저장소 `libs/langgraph/langgraph/graph/state.py`에서 확인 가능:

```python
class CompiledStateGraph(
    Pregel[StateT, ContextT, InputT, OutputT],
    Generic[StateT, ContextT, InputT, OutputT],
):
```

공식 문서(LangGraph runtime)도 명시합니다 — 이 런타임은 *"named after Google's Pregel algorithm, which describes an efficient method for large-scale parallel computation using graphs"* 이며, 실행은 *"the Pregel Algorithm / Bulk Synchronous Parallel model"* 을 따른다고.

### 용어 대응표

| BSP (1990) | Pregel (2010) | LangGraph |
|---|---|---|
| component | vertex | **node (actor)** |
| router / message | message | **channel 쓰기** |
| superstep | superstep | **superstep** |
| barrier synchronisation | global synchronization point | **update 단계 (체크포인트 저장)** |
| — | combiner | **reducer** (`Annotated[list, operator.add]`) |
| — | aggregator | 공유 채널 / 전역 상태 |
| — | vote to halt | 조건부 엣지 → `END` |

### LangGraph 슈퍼스텝의 3단계

BSP의 3단계가 LangGraph에서는 이 이름으로 나타납니다.

1. **plan** — 이번 스텝에 실행할 액터(노드)를 고른다. 첫 스텝은 입력 채널을 구독하는 노드, 이후는 **직전 스텝에 갱신된 채널**을 구독하는 노드.
2. **execution** — 고른 노드들을 **병렬로** 실행. 전원 완료 / 하나 실패 / 타임아웃까지. 이 동안 **채널 갱신은 다른 액터에게 보이지 않는다.**
3. **update** — 이 스텝에서 액터들이 쓴 값으로 채널을 갱신한다. **여기서 리듀서가 돈다.**

실행할 액터가 없거나 최대 스텝 수에 닿으면 종료. — BSP의 지역 계산 → 통신 → 배리어와 한 줄씩 대응합니다.

### 19장 예제가 이 계보를 눈으로 보여 준다

`ex2_superstep.py`가 정확히 이 지점을 실험합니다.

```python
b.add_edge(START, "A")   # A, B, C 를 같은 슈퍼스텝에 넣는다
b.add_edge(START, "B")
b.add_edge(START, "C")
```

결과는 **A·B·C가 전부 `seen=0개`를 봅니다.** 셋 다 같은 상태 사본을 받았기 때문입니다. 그리고 「경계」 노드 뒤에 오는 D·E는 앞의 결과를 전부 봅니다.

> A·B·C 가 전부 «seen=0개»를 봤다. 같은 슈퍼스텝이라 같은 상태 사본을 받았기 때문이다.
> 서로가 쓴 걸 못 본다. **이게 슈퍼스텝의 성질이다.**

이 「성질」은 LangGraph의 버그도, 최적화도, 구현 세부도 아닙니다. **1990년 CACM 논문의 정의에서 논리적으로 따라 나오는 결과**입니다. 프리겔 논문의 표현을 다시 빌리면 *"it doesn't expose any mechanism for detecting order of execution within a superstep"* — 슈퍼스텝 안의 실행 순서를 알아낼 방법을 **일부러** 노출하지 않는 것입니다.

그래서 순서가 필요하면 방법은 하나뿐입니다. **사이에 노드를 넣어 슈퍼스텝 경계를 하나 더 만드는 것.** 「같은 슈퍼스텝 안에서 서로 결과를 참조」하는 설계는 고칠 수 있는 버그가 아니라 모형 위반입니다.

`ex1_lost_update.py`가 보여 주는 갱신 유실도 같은 뿌리입니다. 리듀서 없이 셋이 같은 필드를 쓰면 LangGraph는 예외를 냅니다 — 합칠 규칙 없이 update 단계를 돌 방법이 없기 때문입니다.

---

## 4. 시험에 나올 만한 것 정리

| 물음 | 답 |
|---|---|
| 「superstep」 용어의 최초 출처는? | Valiant, *A bridging model for parallel computation*, **CACM 33(8), 1990**, pp. 103–111 |
| 프리겔 논문의 저자·학회·연도는? | Malewicz 외 6인 (Google), **ACM SIGMOD 2010**, pp. 135–146 |
| 프리겔은 BSP와 어떤 관계인가? | 논문이 직접 *"inspired by Valiant's Bulk Synchronous Parallel model"* 이라 밝힘. 슈퍼스텝을 그대로 물려받음 |
| BSP 모형의 세 속성은? | components, router, synchronization facilities (주기 파라미터 *L*) |
| BSP 슈퍼스텝 3단계는? | local computation → communication → barrier synchronisation |
| vertex-centric의 한 줄 요약은? | 그래프 순회를 짜지 말고 **정점 하나가 한 슈퍼스텝에 할 일**만 써라 |
| 리듀서의 조상은? | 프리겔의 **combiner** (합치는 순서·묶음이 보장되지 않음 → 교환·결합법칙 필수) |
| LangGraph 어디에 남아 있나? | 실행기 클래스 이름이 그대로 **`Pregel`**. `CompiledStateGraph`가 이를 상속 |

**한 문장 암기**: 슈퍼스텝은 **1990년 Valiant의 BSP**에서 태어나 **2010년 Google의 Pregel**을 거쳐 **LangGraph의 `Pregel` 클래스**로 살아 있다. 두 정거장 다 ACM 논문이다.

---

## 1차 출처

- Leslie G. Valiant, "A bridging model for parallel computation", *Communications of the ACM*, 33(8), August 1990, pp. 103–111 — https://dl.acm.org/doi/10.1145/79173.79181
- Grzegorz Malewicz, Matthew H. Austern, Aart J. C. Bik, James C. Dehnert, Ilan Horn, Naty Leiser, Grzegorz Czajkowski, "Pregel: A System for Large-Scale Graph Processing", *SIGMOD '10*, pp. 135–146 — https://dl.acm.org/doi/10.1145/1807167.1807184
- LangGraph runtime (Pregel) 문서 — https://docs.langchain.com/oss/python/langgraph/pregel
- LangGraph Graph API (StateGraph / reducer / superstep) — https://docs.langchain.com/oss/python/langgraph/graph-api

### 참고 (2차 출처, 용어 확산 경로)

- Yuanyuan Tian et al., "From 'Think Like a Vertex' to 'Think Like a Graph'", *PVLDB* 7(3), 2014 — https://dl.acm.org/doi/10.14778/2732232.2732238
- Robert Ryan McCune, Tim Weninger, Greg Madey, "Thinking Like a Vertex: A Survey of Vertex-Centric Frameworks for Large-Scale Distributed Graph Processing", *ACM Computing Surveys* 48(2), 2015 — https://dl.acm.org/doi/10.1145/2818185
