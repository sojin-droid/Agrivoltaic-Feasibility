/* terms.js — 표시명 계층 + 용어 통일 (2026-07-16 확정, site_copy_fixes §4-1)
   원칙: '저소유' 문자열 금지. 필드명→표시명 단일 소스. 전 페이지 공용. */
(function (global) {
  "use strict";

  // 시나리오 (2026-07-20 확정: S0 현행 / S1 재생에너지지구 / S2 확장)
  const SCENARIO = {
    S0: { label: "현행", full: "S0 — 현행 농지법 (진흥·보호·자연환경·시설 제외)" },
    S1: { label: "재생에너지지구", full: "S1 — 재생에너지지구 지정 (진흥+보호 포함, 자연환경보전 제외, 시설 포함)" },
    S2: { label: "확장", full: "S2 — 확장 (S1 + 자연환경보전지역 포함)" },
  };
  const DEFAULT_SCENARIO = "S1";  // 기본 탭

  // 판정 3단
  const STATUS = {
    "유력":      { label: "유력",      sub: "특구 지정 요건 확보 (≥100MW)", fg: "#276749", bg: "#c6f6d5" },
    "지정 가능": { label: "지정 가능", sub: "특구 지정 가능 (50–100MW)", fg: "#975a16", bg: "#fefcbf" },
    "요건 미달": { label: "요건 미달", sub: "관내 실행 물량 부재",       fg: "#9b2c2c", bg: "#fed7d7" },
  };
  // B(산단 거점) 전용 프레이밍 — "요건 미달" 대신
  const B_FRAME = "관내 실행 물량 부재 → 인접 농업 시군 연계 필요";

  // 지표 표시명 (필드→한글). '저소유/저개인소유/저(低)' 계열 전면 금지.
  const METRIC = {
    seg_mw:       "잠재 물량(MW)",
    b_mw_t30:     "실행 가능 물량(MW)",   // 성격: 개인소유 비율이 낮은 블록 합산
    indiv:        "개인소유 비율",
    unk:          "소유주 미확인 비율",
    grid_pool_mw: "계통 여유(MW)",
    demand_gwh:   "연간 전력수요(GWh)",
    threshold_t:  "문턱 t (개인소유 상한)",
  };

  // 자주 쓰는 문구 (금지어 교체 결과)
  const PHRASE = {
    anchor:        "개인소유 비율이 낮은 필지",
    candidateType: "개인소유 비율이 낮은 후보지구",
    choropleth:    "읍면동별 계통 여유 지도",
    unknownOwner:  "소유주 미확인",
    priorityList:  "우선 검토 후보",
  };

  // 표준 설치단위 (3MW = 6.7ha 상당)
  const UNIT = { mw: 3.0, ha: 6.7, note: "표준 설치단위 = 3MW(6.7ha 상당)" };

  // 커버리지 각주 (전 페이지 공용 1회 표기)
  const COVERAGE_NOTE =
    "분석 단위: 25개 분석구역 — A 경기·충남 15개(15개 시군) + B 전국 산단 거점 10개(시 4·군 1·자치구 5). " +
    "천안·용인·안산·포항처럼 비자치 일반구로 분리된 원장 코드는 생활권(시) 단위로 병합·재블록화(재분리 금지). " +
    "원장 물리 코드 기준 총 30개. 울산은 구·군별 판정, 표시만 광역 그룹.";

  const T = {
    SCENARIO, DEFAULT_SCENARIO, STATUS, B_FRAME, METRIC, PHRASE, UNIT, COVERAGE_NOTE,
    // 헬퍼
    statusBadge(status) {
      const s = STATUS[status] || { label: status, fg: "#555", bg: "#eee" };
      return `<span class="badge" style="color:${s.fg};background:${s.bg}">${s.label}</span>`;
    },
    mw(v, digits) { return v == null ? "—" : Number(v).toLocaleString("ko-KR",
      { maximumFractionDigits: digits == null ? 0 : digits }); },
  };
  global.TERMS = T;
})(typeof window !== "undefined" ? window : globalThis);
