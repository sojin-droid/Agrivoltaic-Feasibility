// v4 데이터 렌더 도우미 — 수치는 전부 data_v4에서 (원칙 1). chrome(내비·푸터 골격)은 각 페이지 정적.
// 각주: 브리프 공통 번호 [1]–[16] + 사이트 확장 [17]–[21]. 본문 마커 <sup class="fnref">[n]</sup>.
// 통일 형식 — 발행처, 『자료명』, 판·취득 경로 (일자). 그리고 '용도' 설명 한 줄.
const FOOTNOTES = {
  1: '국토교통부, 『연속지적도(LSMD) 및 토지·임야 원장 속성 정리본』, 2025년판 — 252개 시군 전수 39,726,310필지 (지오메트리·지목·소유 유형·용도지역·장부면적).<span class="fn-note">용도: 분석의 뼈대 — 필지 식별(PNU)과 면적·지목·소유 구분·용도지역 판정의 원천. 이격 보수의 주택 판정(대지 필지 대리)도 이 원장 기준.</span>',
  2: '농림축산식품부, 『팜맵(농경지 전자지도)』, 2025년판 — 공공데이터포털 15104481–15104491, 항공·위성 판독(촬영 2019–2024 혼재).<span class="fn-note">용도: 실경작 판정 — 필지와 공간교차해 경작 면적 비율을 재고(전답과의 99.4% 실측), 30% 문턱으로 "실경작 확인" 층을 구성함.</span>',
  3: '한국농어촌공사, 『지구·공구 토지정보』, 2025년판 — 공공데이터포털 15116438, 지번 원장 45,193필지.<span class="fn-note">용도: "간척 농지" 식별의 유일한 근거. 민간 공유수면 매립지는 이 원장에 없어 분석 범위 밖.</span>',
  4: '농림축산식품부, 「국가관리 간척지 13지구 고시」, 2025년 6월.<span class="fn-note">용도: 국가관리 간척지 명단 — 간척 원장의 지구 구분 검증에 사용.</span>',
  5: '국토교통부 V-World, 『농업진흥지역도(LT_C_AGRIXUE101)』 — 2026-08-21 수집, 진흥구역 16,996·보호구역 43,442 폴리곤(속성 코드 UEA110/120 검증).<span class="fn-note">용도: 진흥구역·보호구역 구분 — 필지 대표점 교차로 조합 R1–R3을 계산.</span>',
  6: '「농지법」 §2·§28②·§32 · 「국토의 계획 및 이용에 관한 법률 시행령」 별표15·18·22 · 「개발제한구역법 시행령」 §19 — 법제처 국가법령정보센터 원문 대조 (2026-08-21~24).<span class="fn-note">용도: 배제 3종(개발제한구역·보전관리지역·보전녹지지역)의 확정 근거 — 법문에 열거된 경우만 배제한다는 원문 재검증의 결과.</span>',
  7: '「농지법」 §36①4호의2 — 시행규칙 2025-10-31판 확인 (부령 미제정).<span class="fn-note">용도: 영농형 대상 농지의 부령 위임 조항 — 보호구역 개방(수단 A)이 지나갈 법적 통로.</span>',
  8: '「농지법 시행령」 §30①3호 — 2025-06-02 개정 반영판.<span class="fn-note">용도: 농업보호구역 내 태양에너지 설비 1만㎡ 미만 허용 — 보호구역 개방의 기존 선례 조항.</span>',
  9: '「농지법 시행령」 §28①3호다목.<span class="fn-note">용도: 저수지 상류 500m를 보호구역 변경 대상으로 명시 — 보호구역의 지정 성격(수자원 인접) 해석 근거.</span>',
  10: '「영농형 태양광 발전사업의 활성화 및 지원에 관한 법률」 — 법률 제21804호, 2026-06-16 공포, 2026-12-17 시행, §6①·§8·§10.<span class="fn-note">용도: 사업 규모를 부지면적부터 정의(면적을 1차 단위로 쓰는 근거)하고, 재생에너지지구 경로(§6①2호)를 규정.</span>',
  11: '「재생에너지 개발·이용·보급 촉진법」 §27조의3 및 시행령 개정안 — 기후에너지환경부 보도자료(2026-08-11 국무회의 의결), 원문 PDF 보존(sha256 관리), 법 시행 2026-09-18.<span class="fn-note">용도: 이격거리 상한제(주거 200m·도로 이격 금지) — 본 분석 "이격 보수" 층의 기준. 측정 방법 고시는 미제정이라 하한 처리.</span>',
  12: '본 연구 정본 데이터베이스(agrivoltaic_ledger_v1)와 도구(agv) — 원장·판정(elig_v2)·구역 태그(agpromo_tag)·간척 태그(reclaim_tag)·배제 사유(exclusion_reason)·연접·시나리오 테이블. 회귀 검사 전량 통과 상태의 산출 (2판, 2026-08-25).<span class="fn-note">용도: 이 사이트 모든 수치의 직접 출처 — 페이지는 이 DB의 export만 렌더함.<br>자산별 구축 시점·원천 전량은 자료·한계 탭의 계보 표.</span>',
  13: '환산 계수 0.045 kW/㎡ = 설치밀도(GCR) 0.225 × 모듈 효율 0.20 — 솔라시도 영농형 실계획과 ±0.6% 이내 대조 검증.<span class="fn-note">용도: 참고 MW 환산 — 면적이 1차 산출이고 MW는 이 가정이 얹힌 파생값이라 항상 "참고"로 병기.</span>',
  14: '현행법 기준값(T14 상수) = 3,272,555필지 · 4,099,643,674.95㎡ — 2판 (ADR-0035, 2026-08-25 승인).<span class="fn-note">용도: 모든 비교의 고정 기준 — 데이터 생성 시 재조회와 정확 일치하지 않으면 산출이 중단됨.<br>개정 이력: 초판 → 배제 규정 원문 재검증 → 지목 복구 적용(2판).<br>용도지역 미상 67,875필지·30.53km²는 판정 보류로 별도 병기.</span>',
  15: '「농지법」 §37② — 국가법령정보센터 원문 대조.<span class="fn-note">용도: 우량농지 등에 대한 제한이 §36 타용도 일시사용 허가·협의에도 적용됨을 명시 — 시나리오의 법적 층위 해석.</span>',
  16: '「농촌공간 재구조화 및 재생지원에 관한 법률」 §12①5호·§13② — 원문 대조.<span class="fn-note">용도: 재생에너지지구의 지정 절차와 총량 상한 — 진흥구역 개방(수단 B)의 실행 형태.</span>',
  17: '행정표준코드관리시스템(code.go.kr), 『법정동코드 전체자료』(2026-08-19 취득) 및 시군 경계 2023년판(신·구 행정코드 대조).<span class="fn-note">용도: 시군 이름·경계 표기 — 표기용 참조 자료로, 수치 산출에는 쓰지 않음.</span>',
  18: '「농지법 시행규칙」 §32 — 2025-10-31판.<span class="fn-note">용도: 타인 소유 농지의 타용도 일시사용 신청에 소유자 사용승낙서 경로를 규정 — 간척지 임차 논의의 절차적 근거.</span>',
  19: 'Esri World Imagery — © Esri, Maxar, Earthstar Geographics.<span class="fn-note">용도: 지도·아틀라스의 위성 배경 — 표시 전용이며 수치 산출에는 쓰지 않음. 아틀라스는 타일을 파일에 내장(오프라인 열람 가능).</span>',
  20: 'Leaflet 1.9.4 (오픈소스, BSD-2 라이선스) — 외부 CDN이 아니라 저장소에 내장.<span class="fn-note">용도: 지도 탭의 대화형 렌더링 — 표시 전용.</span>',
  21: '농촌진흥청 토양환경정보(흙토람)의 토양 경사 구분(ASIT_SOILSLOPE) 기반 경사 판정 레이어 — 정본 DB 파생.<span class="fn-note">용도: 경사 15% 초과 필지 배제 판정.</span>',
};
const FN_GROUPS = [
  ['데이터 원천', [1, 2, 3, 5, 17, 21]],
  ['법령·행정자료', [4, 6, 7, 8, 9, 10, 11, 15, 16, 18]],
  ['본 연구 산출·기준값', [12, 14]],
  ['환산·배경지도·소프트웨어', [13, 19, 20]],
];
const V4 = {
  cache: {},
  async data(name) {
    if (!this.cache[name]) {
      const r = await fetch('data_v4/' + name + '.json');
      this.cache[name] = await r.json();
    }
    return this.cache[name];
  },
  n(x) { return x.toLocaleString('ko-KR'); },
  km2(x, d = 1) { return x.toLocaleString('ko-KR', {minimumFractionDigits: d, maximumFractionDigits: d}); },
  mw(m2) { return Math.round(m2 * 0.045 / 1000).toLocaleString('ko-KR'); }, // 참고 환산: ㎡ 원값 기준
  // 카운트업 — 동적 삽입 수치용 (site.js .count는 정적 DOM 전용이라 별도 구현)
  countup(el, target, decimals = 0) {
    if (matchMedia('(prefers-reduced-motion: reduce)').matches) {
      el.textContent = this.km2(target, decimals); return;
    }
    const io = new IntersectionObserver(es => {
      es.forEach(e => {
        if (!e.isIntersecting) return;
        io.unobserve(el);
        const dur = 1400, t0 = performance.now(), self = this;
        (function tick(t) {
          const p = Math.min((t - t0) / dur, 1);
          el.textContent = self.km2(target * (1 - Math.pow(1 - p, 3)), decimals);
          if (p < 1) requestAnimationFrame(tick);
        })(t0);
      });
    }, {threshold: .5});
    io.observe(el);
  },
  // 각주 목록 — 모든 페이지 최하단(푸터 앞) 자동 삽입. 본문의 [n] 마커가 여기로 앵커된다.
  footnotes() {
    const ftr = document.querySelector('footer.v4');
    if (!ftr || document.getElementById('fnsec')) return;
    const sec = document.createElement('section');
    sec.id = 'fnsec';
    sec.innerHTML = `<div class="wrap">
      <div class="sec-head" style="margin-bottom:18px"><div>
        <p class="eyebrow">Sources</p><h2>출처</h2></div></div>` +
      FN_GROUPS.map(([g, nums]) =>
        `<div class="fn-group">${g}</div><ol class="fnlist">` +
        nums.map(n => `<li id="fn-${n}" value="${n}">${FOOTNOTES[n]}</li>`).join('') +
        `</ol>`).join('') +
      `<div class="fn">번호 [1]–[16]은 정책 브리프와 공통, [17]–[21]은 사이트 추가분.
      본문 위첨자 [n]을 누르면 해당 출처로 이동. 자산별 구축 이력 전체는
      <a href="about.html" style="color:var(--leaf-deep)">자료·한계 탭의 계보 표</a>.</div>
    </div>`;
    ftr.parentNode.insertBefore(sec, ftr);
    // 본문 마커를 링크로 활성화
    document.querySelectorAll('sup.fnref').forEach(s => {
      const n = (s.textContent.match(/\d+/) || [])[0];
      if (n) s.innerHTML = `<a href="#fn-${n}">[${n}]</a>`;
    });
  },
  async footer() {
    this.footnotes();
    const m = await this.data('meta_v4');
    const el = document.querySelector('footer.v4 .wrap');
    if (el) el.innerHTML =
      `<div>PLANiT Institute · 영농형 태양광 — 전국 설치 가능 농지 분석</div>` +
      `<div>데이터 세대 ${m.data_generation} · 생성 ${m.generated} · ${m.verification} · ` +
      `소유 구분은 지적 원장의 유형 구분(개인 식별 아님) · ` +
      `수치는 정본 DB 조회값의 export — 페이지 내 재계산 없음 · ` +
      `<a href="about.html">자료 계보·한계 →</a></div>`;
  },
};
