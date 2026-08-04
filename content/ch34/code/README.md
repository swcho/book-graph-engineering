# 34장 — 그래프에서 개인정보를 지운다는 것

`7부 — 운영` | [책 전체 목차](../../../README.md) | [출처 링크 모음](../../../SOURCES.md)

> 「지웠습니다」라고 답한 뒤 3주 만에 다시 연락이 왔습니다.

「지웠습니다」는 사실이었어요. *한 곳에서만요.* 이 장은 그 이야기입니다. 그래프에서 지운다는 게 무슨 뜻인지, 그리고 왜 관계형 DB보다 훨씬 어려운지요.

## 이 장의 절

| 절 | 제목 |
|---|---|
| 34.1 | 노드를 지워도 남는 것들 |
| 34.2 | 「지운다」는 한 가지가 아니다 |
| 34.3 | 이름을 지워도 특정된다 |
| 34.4 | 지우면 무엇이 같이 무너지나 |
| 34.5 | 절차를 검사 가능하게 만든다 |

## 한 장 요약

- 노드를 지워도 남는 곳이 다섯입니다. 들어오는 엣지, 자유 텍스트 안의 이름, 이벤트 로그, 백업, 검색 색인.
- 「지운다」는 한 가지가 아닙니다. 숨기기, 식별자 끊기, 가명화, 완전 삭제. 어느 것도 모든 기준을 만족하지 않아요. 완전 삭제가 제일 강해 보이는데 만족하는 기준은 제일 적습니다.
- 이름을 지워도 특정됩니다. 속성 넷을 조합하면 66%가 혼자가 돼요. 그리고 셋에서 넷으로 갈 때 절벽이 생깁니다.
- 그래프에서는 *관계 자체가 식별자*입니다. 속성을 다 지워도 이웃 모양이 유일하면 특정돼요. 이건 아직 제대로 된 해법이 없습니다.
- 지우기 전에 영향 범위를 세되, 「이어진 것을 전부 지운다」는 답이 아닙니다. 집계와 결정은 개인정보가 아니고, 남의 이력을 깨면 안 됩니다.
- 경계는 「그것이 개인을 가리키는가」입니다. 문서는 두고 「누가 작성」만 바꾸세요.
- 노드 종류별 방침 표를 만들고, 방침 없는 종류가 나오면 멈추세요. 「모르는 것을 모른다」고 말해 주는 게 이 표의 값어치입니다.
- 이벤트 로그는 못 지우니 개인정보를 직접 넣지 마세요. 식별자만 넣고, 그 식별자를 가리키는 표에서 지웁니다.
- 그리고 「완료」의 기준을 문서로 정하세요. 삭제 자체는 초 단위인데 전체는 며칠 걸립니다.

## 키워드와 1차 출처

| 키워드 | 상태 | 출처 |
|---|---|---|
| 삭제권 | [표준] | [right to erasure](https://gdpr-info.eu/art-17-gdpr/) |
| 가명화 | [표준] | [pseudonymisation](https://gdpr-info.eu/art-4-gdpr/) |
| 재식별 | [사실상 표준] | [re-identification](https://www.nist.gov/publications/de-identification-personal-information) |
| k-익명성 | [사실상 표준] | [k-anonymity](https://dataprivacylab.org/dataprivacy/projects/kanonymity/kanonymity.pdf) |
| 차등 정보보호 | [사실상 표준] | [differential privacy](https://www.microsoft.com/en-us/research/publication/differential-privacy/) |
| 데이터 최소화 | [표준] | [data minimisation](https://gdpr-info.eu/art-5-gdpr/) |
| 보존 기간 | [표준] | [retention period](https://csrc.nist.gov/pubs/sp/800/53/r5/upd1/final) |

상태 표시는 **[표준]** 공식 명세, **[사실상 표준]** 명세는 없지만 업계가 널리 쓰는 것, **[실험]** 아직 자리를 잡는 중이라는 뜻입니다.

## 예제 실행

<!-- 실행 가이드 시작 — 사람이 쓴 부분. gen-docs.py 가 건드리지 않는다. -->

확인 시점 2026년 8월. Python 3.9 이상.

```bash
cd content/ch34/code
pip install kuzu

python3 ex1_delete_scope.py     # 노드만 지우면 무엇이 남나
python3 ex2_delete_levels.py    # 「지운다」의 네 수준 (의존성 없음)
python3 ex3_reidentify.py       # 이름을 지워도 특정된다 (의존성 없음)
python3 ex4_cascade.py          # 지우면 무엇이 같이 무너지나
python3 ex5_deletion_plan.py    # 삭제 절차를 검사 가능한 형태로 (의존성 없음)
```

이 장의 예제는 «구조»를 보여 주는 것이지 법적 조언이 아닙니다.
어느 수준까지 지워야 하는지는 관할과 업종에 따라 다르고, 그건 법무가 정할 일입니다.
엔지니어가 할 일은 「그 수준을 선택했을 때 무엇이 깨지는지」를 미리 세는 것입니다.

`ex5` 는 일부러 `Photo` 종류에서 막히게 해 두었습니다.
`POLICY` 에 한 줄 추가하면 통과합니다.

<!-- 실행 가이드 끝 -->

---

**다음 부에서 만나는 것:** 여기까지가 지금 할 수 있는 것들이었습니다. 마지막 부는 «앞으로»입니다. 그리고 그 장에서 저는 이 책에서 3년 뒤에 틀렸을 가능성이 제일 큰 주장 다섯 개를 직접 지목합니다.

---

이전 [33장 쿼리 플랜을 읽으면 비용이 보인다](../../ch33/code/README.md) | [전체 목차](../../../README.md) | 다음 [35장 3년 뒤 틀렸을 가능성이 가장 큰 주장 5개](../../ch35/code/README.md)

이 장에서 틀린 곳을 찾으셨다면 [사실 오류로](https://github.com/leaf-kit/book-graph-engineering/issues/new?template=01-fact-error.yml), 상태 라벨이 어긋났다면 [라벨 이의로](https://github.com/leaf-kit/book-graph-engineering/issues/new?template=03-status-label.yml) 적어 주세요.
