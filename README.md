# 영농형 태양광 설치 가능 농지 — 전국 분석 사이트

전국 필지 전수 분석의 결과를 공개하는 정적 사이트. 데이터 세대 **v4 (앵커 개정판, 2026-08)**.

> **공개 사이트 (GitHub Pages)**: https://sojin-droid.github.io/Agrivoltaic-Feasibility/

## 구성 (레포 루트 = Pages 루트)

| 페이지 | 내용 |
|---|---|
| index.html | 결론 — 현행법 기준값과 네 가지 제도 조합 |
| evidence.html | 근거 — 조합 매트릭스(전국·간척) · 풀 분해 · 소유 세 무리 |
| atlas.html | 간척 아틀라스 — 당진·영암·해남·고흥 위성 지도, 필지 단위 소유 구분 |
| method.html | 방법·재현 — 깔때기, 판정 조건, 검증 체계 |
| about.html | 자료·한계 — 데이터 계보, 단위·환산 가정 |

## 데이터 규율

- 수치는 전부 `data_v4/*.json`에서 렌더 — 페이지 하드코딩 없음
- `data_v4/`는 정본 질의 모듈(model/query.py)을 직접 불러 생성(`pipeline/export_v4.py`) —
  판정 SQL이 두 곳에 존재하지 않는다
- export는 기준값(T14) 정확 일치 검증을 내장 — 어긋나면 파일이 생성되지 않음
- 공개 전 `pipeline/site_gate.py` 필수 통과 (무효 수치·금지 표현·외부 자원 로드·하드코딩 검사)
- 자족형: 외부 CDN·API 로드 없음 (위성 타일 내장)

## 갱신

```bash
python pipeline/export_v4.py   # 정본 DB → data_v4
python pipeline/site_gate.py   # 게이트 — PASS 필수
```

구세대(2026-07, 21개 분석구역·MW 1차·구 S0/S1/S2) 페이지·데이터는 git 이력에 보존.
전체 설계와 원칙 4축 13항은 REWORK_PLAN.md.
