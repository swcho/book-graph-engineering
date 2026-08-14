# «전체 통과 여부» 하나만 보면 안 되는 이유

> **Q.** SHACL 검증에서 '전체 통과 여부' 값만 보면 안 되는 이유는 무엇인가?
>
> **A.** 기록(Info) 등급 하나만 걸려도 False가 나온다. 이 값으로 적재를 막으면 «표시 이름이 없다» 때문에 파이프라인이 선다.

출처: 13장 「검증하지 않은 그래프는 그냥 링크 뭉치다」 13.2절 *전부 막으면 아무것도 안 들어온다* / `code/ex1_shacl_severity.py`, `code/shapes.ttl`, `code/data.ttl`

---

## 1. «전체 통과 여부»가 정확히 무엇인가

`ex1_shacl_severity.py`가 찍는 그 값의 정체는 SHACL 검증 보고서의 `sh:conforms`다.

```python
ok, report, _ = validate(data, shacl_graph=shapes, inference="none", advanced=True)
...
print(f"전체 통과 여부: {ok}\n")
```

`validate()`가 돌려주는 첫 번째 값 `ok`가 보고서 노드의 `sh:conforms`에 그대로 대응한다.
그리고 이 값의 표준 정의가 문제의 핵심이다.

> The value of `sh:conforms` is `true` if and only if the validation did not produce any validation results, and `false` otherwise.
> — [SHACL, §3.5 Validation Report](https://www.w3.org/TR/shacl/#validation-report)

읽어야 할 부분은 **"any validation results"**다. 결과가 **하나라도** 생기면 `false`.
어떤 종류인지, 얼마나 심각한지는 조건에 들어 있지 않다.

## 2. 심각도는 «통과 여부»에 영향을 주지 않는다

여기서 흔히 하는 착각이 있다. `sh:severity`를 붙여 놨으니 심각한 것만 통과 여부에 반영되겠지, 하는 기대다. 표준은 정반대로 못 박아 놨다.

| 개념 | 어디에 붙나 | 하는 일 |
|---|---|---|
| `sh:severity` | **형태(shape)** 정의에 선언 | 이 제약을 어겼을 때 결과에 찍을 등급을 정한다. 생략하면 기본값 `sh:Violation` |
| `sh:resultSeverity` | **결과(result)** 하나하나에 기록 | 실제로 어긴 그 건의 등급. 값은 반드시 IRI 하나 |
| `sh:conforms` | **보고서 전체**에 하나 | 결과가 0건이면 `true`, 1건 이상이면 `false` |

표준 문서의 [§2.1.3 Severity](https://www.w3.org/TR/shacl/#severity)는 심각도가 **"has no impact on the validation"** 이라고 명시한다.
즉 심각도는 **보고서를 읽는 쪽이 쓰라고 만든 라벨**이지, 검증 엔진이 통과/실패를 가르는 데 쓰는 스위치가 아니다.

표준이 정의한 세 등급은 다음과 같다. 모두 `sh:Severity`의 인스턴스이고, **셋 다 똑같이 `sh:conforms`를 `false`로 만든다.**

- `sh:Violation`
- `sh:Warning`
- `sh:Info`

## 3. 이 장의 데이터에서 실제로 무슨 일이 벌어지나

`shapes.ttl`은 회사·계약 형태에 심각도를 셋으로 나눠 붙여 놨다.

```turtle
# 차단 — 사업자번호가 없으면 이 노드는 다른 것과 병합될 수 없다
sh:property [ sh:path ex:bizNumber ;
    sh:minCount 1 ; sh:maxCount 1 ;
    sh:pattern "^[0-9]{3}-[0-9]{2}-[0-9]{5}$" ;
    sh:severity sh:Violation ;
    sh:message "사업자번호가 없거나 형식이 틀렸다" ] ;

# 경고 — 등급으로 필터하는 질의가 조용히 빈 결과를 낸다
sh:property [ sh:path ex:grade ;
    sh:minCount 1 ; sh:in ("A" "B" "C") ;
    sh:severity sh:Warning ;
    sh:message "등급이 없거나 A/B/C 밖이다" ] ;

# 기록 — 화면에 빈칸이 보일 뿐
sh:property [ sh:path rdfs:label ;
    sh:minCount 1 ;
    sh:severity sh:Info ;
    sh:message "표시 이름이 없다" ] .
```

`data.ttl`에는 등급별로 하나씩 일부러 어긴 노드가 들어 있다.

| 노드 | 어긴 것 | 등급 | 실제 피해 |
|---|---|---|---|
| `ex:Naru` | `bizNumber`가 `"1234567890"` — 하이픈 없음 | 차단 | 병합 키가 깨진다. 되돌리기 어렵다 |
| `ex:C9` | 이 계약을 체결한 회사가 없음 (고아 노드) | 차단 | 참조 무결성이 깨진다 |
| `ex:Raon` | `grade`가 `"Z"` — A/B/C 밖 | 경고 | 등급 필터 질의가 조용히 빈 결과 |
| `ex:C5` | `amount`가 `-1` | 경고 | 합계 집계가 틀린다 |
| **`ex:Daol`** | **`rdfs:label`이 없음** | **기록** | **화면에 빈칸 하나** |

여기서 `ex:Daol` 한 건만 남기고 나머지를 전부 고쳤다고 해 보자. 그래도 `ok`는 여전히 `False`다.
«표시 이름이 없다»는 것 때문에.

그래서 코드가 붙여 놓은 경고 문구가 이렇다.

```text
«전체 통과 여부»가 False 인 게 함정이다.
기록 등급 하나만 걸려도 False 가 나온다. 그래서 이 값만 보고
적재를 막으면 «표시 이름이 없다» 때문에 파이프라인이 선다.
```

이게 13장 서두의 «적재를 막았더니 데이터가 안 들어왔습니다»가 벌어지는 정확한 메커니즘이다.
그리고 그 다음 이야기가 더 나쁘다 — 파이프라인이 서면 사람들은 검증을 **끄거나 우회한다**. 13장 요약이 말하는 «우회 경로가 주 경로가 되는 게 최악»이 그 지점이다.

## 4. 코드는 어떻게 게이트를 다시 만드나

`ex1_shacl_severity.py`는 `ok` 하나를 버리지는 않되, **거기에 판단을 걸지 않는다.** 대신 보고서를 뜯어서 심각도별로 다시 센다.

```python
SH = Namespace("http://www.w3.org/ns/shacl#")
LEVEL = {"Violation": "차단", "Warning": "경고", "Info": "기록"}
...
rows = []
for r in report.subjects(URIRef(str(SH) + "resultSeverity"), None):
    sev  = str(report.value(r, SH.resultSeverity)).rsplit("#", 1)[-1]
    node = str(report.value(r, SH.focusNode)).rsplit("/", 1)[-1]
    msg  = str(report.value(r, SH.resultMessage) or "")
    rows.append((LEVEL.get(sev, sev), node, msg))
```

읽는 방식이 중요하다.

1. `report`는 문자열이 아니라 **RDF 그래프**다. 세 번째 반환값(사람이 읽는 텍스트)이 아니라 두 번째 반환값을 쓴다.
2. `report.subjects(sh:resultSeverity, None)` — `sh:resultSeverity`를 가진 주어를 모두 긁는다. 표준이 «모든 검증 결과는 `sh:resultSeverity`를 정확히 하나 가진다»고 보장하므로, 이게 곧 «결과 전부»를 뽑는 방법이 된다.
3. 각 결과에서 `sh:resultSeverity`(등급) / `sh:focusNode`(어느 노드가) / `sh:resultMessage`(무엇을 어겼나) 셋을 꺼낸다. 이 셋이 있어야 «누가 무엇을 얼마나 심각하게»가 나온다.
4. 등급을 «차단 → 경고 → 기록» 순으로 정렬하고 `Counter`로 개수를 센다.

```python
cnt = Counter(r[0] for r in rows)
print(f"\n차단 {cnt['차단']}건 · 경고 {cnt['경고']}건 · 기록 {cnt['기록']}건")
```

**이 세 숫자가 진짜 게이트 입력값이다.** `ok` 하나로는 만들 수 없는 판단이 여기서 나온다.

```text
실무에서는 심각도별로 나눠서 처리한다.
  차단 → 적재 거부. 사람이 원천을 고쳐야 한다.
  경고 → 적재는 하고 대시보드에 올린다. 질의가 틀릴 수 있으니까.
  기록 → 주간 보고서에 숫자만. 추세가 나빠지면 그때 본다.
```

정리하면 게이트 조건은 `ok == True`가 아니라 이렇게 생겨야 한다.

```python
if cnt["차단"] > 0:
    적재_거부()          # 되돌릴 수 없는 것만 막는다
else:
    적재_진행()
    대시보드에_올린다(cnt["경고"])
    주간보고서에_적는다(cnt["기록"])
```

`shapes.ttl` 주석이 심각도를 나누는 기준을 한 줄씩 달아 놓은 것도 같은 이야기다.

- `sh:Violation` — **되돌릴 수 없는 것**. 병합 키가 깨지거나 고아 노드가 생기는 것.
- `sh:Warning` — **질의가 틀리는 것**. 데이터는 들어가지만 답이 어긋난다.
- `sh:Info` — **보기 나쁠 뿐인 것**. 화면 빈칸.

13장 요약이 말하는 «차단 기준은 「되돌릴 수 없는가」 하나로 정하세요»가 이 분류의 근거다.

## 5. pySHACL의 우회 옵션 — 알아 두되 의존하지 말 것

pySHACL은 `sh:conforms`가 심각도를 무시한다는 불편을 알고 있어서, 검증기 쪽에 완화 옵션을 준다.

| 옵션 | 동작 |
|---|---|
| `allow_infos=True` | "Shapes marked with severity of Info will not cause result to be invalid." |
| `allow_warnings=True` | "Shapes marked with severity of **Warning or Info** will not cause result to be invalid." |

```python
ok, report, _ = validate(data, shacl_graph=shapes, allow_warnings=True)
```

이렇게 하면 «차단만 잡는 boolean»을 얻을 수는 있다. 다만 두 가지를 기억해야 한다.

- 이건 **pySHACL 구현의 편의 기능**이지 SHACL 표준의 `sh:conforms` 정의가 아니다. 다른 검증기로 갈아타면 없을 수 있다.
- 켜는 순간 **경고·기록의 개수를 잃는다.** boolean 하나로 다시 돌아가는 셈이라, 「경고가 210 → 1,310으로 6배 늘었다」 같은 추세(13.5절 `ex5_quality_metrics.py`)를 못 본다.

그래서 `ex1`이 고른 방식이 낫다. **완화 옵션으로 boolean을 바꾸는 대신, 보고서를 직접 세어 등급별 숫자를 남긴다.** 게이트도 되고 지표도 된다.

## 6. 이 카드가 걸리는 지점

- «`ok`가 `False`니까 데이터가 심각하게 잘못됐다» — 아니다. `rdfs:label` 하나 빠져도 `False`다.
- «`sh:severity`를 붙였으니 검증기가 알아서 걸러 준다» — 아니다. 표준상 심각도는 검증에 영향이 없고(`has no impact on the validation`), 보고서를 **읽는 쪽**이 해석해야 한다.
- «그럼 심각도는 왜 있나» — 파이프라인이 서지 않게 하려고 있다. 코드 마지막 줄이 그대로 답이다. *«SHACL 이 sh:severity 를 표준으로 제공하는 이유가 이거다.»*
- «심각도를 안 적으면 어떻게 되나» — 전부 `sh:Violation`로 취급된다(표준 기본값). 즉 **아무 생각 없이 형태만 쓰면 모든 제약이 차단 등급**이 되고, 그게 «전부 막으면 아무것도 안 들어온다»의 출발점이다.

## 7. 한 줄 정리

`sh:conforms`는 «결과가 0건인가»만 답하는 값이고 심각도를 전혀 반영하지 않는다. 그래서 적재 게이트는 이 boolean이 아니라 **`sh:resultSeverity`별로 센 차단/경고/기록 개수** 위에 세워야 한다.

## 참고

- [Shapes Constraint Language (SHACL) — §3.5 Validation Report](https://www.w3.org/TR/shacl/#validation-report)
- [SHACL — §2.1.3 Severity (`sh:severity`)](https://www.w3.org/TR/shacl/#severity)
- [pySHACL — validate() 옵션](https://github.com/RDFLib/pySHACL)
