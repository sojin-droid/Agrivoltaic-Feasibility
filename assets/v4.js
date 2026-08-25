// v4 데이터 렌더 도우미 — 수치는 전부 data_v4에서 (원칙 1). chrome(내비·푸터 골격)은 각 페이지 정적.
// 각주: 브리프 공통 번호 체계 [1]–[16] — 본문 마커 <sup class="fnref">[n]</sup>, 목록은 모든 페이지 하단 자동 렌더.
const FOOTNOTES = {
  1: '국토교통부 연속지적도(LSMD) 및 토지 원장 정리본, 252개 시군 전수 (39,726,310필지).',
  2: '농림축산식품부 팜맵 2025 — 공공데이터포털 15104481–15104491, 항공·위성 판독, 촬영 2019–2024 혼재. 전답과 필지의 99.4%가 공간교차 실측.',
  3: '한국농어촌공사 지구공구 토지정보(2025) — 공공데이터포털 15116438. 지번 원장 45,193필지, 민간 매립 미등재.',
  4: '농림축산식품부 고시, 국가관리 간척지 13지구 (2025.6).',
  5: '국토교통부 V-World 농업진흥지역도(LT_C_AGRIXUE101, 2026-08-21 수집) — 진흥구역 16,996·보호구역 43,442 폴리곤, 속성 코드(UEA110/120)로 구분 검증.',
  6: '농지법 §2·§28②·§32, 국토계획법 시행령 별표15·18·22, 개발제한구역법 시행령 §19 — 법제처 국가법령정보센터 원문 (2026-08-21–24 대조, 로컬 법령 KB 조문 4,093·별표 278).',
  7: '농지법 §36①4호의2 (영농형 대상 농지의 부령 위임 — 미제정, 시행규칙 2025-10-31판 확인).',
  8: '농지법 시행령 §30①3호 (농업보호구역 내 태양에너지 발전설비 1만㎡ 미만 허용, 개정 2025-06-02 반영판).',
  9: '농지법 시행령 §28①3호다목 (저수지 상류 500m의 보호구역 변경 대상 명시).',
  10: '영농형 태양광 발전사업의 활성화 및 지원에 관한 법률 (법률 제21804호, 공포 2026-06-16, 시행 2026-12-17) §6①·§8·§10.',
  11: '재생에너지 개발·이용·보급 촉진법 §27조의3 및 시행령 개정안 — 기후에너지환경부 보도자료(2026-08-11 국무회의 의결), 원문 PDF 보존·전문 데이터베이스 등재(sha256 관리).',
  12: '본 연구 정본 데이터베이스(agrivoltaic_ledger_v1: elig_v2·agpromo_tag·reclaim_tag·exclusion_reason) 및 도구(agv). 기준값은 검사 T14로 정확 일치 고정, 회귀 검사 전량 통과 상태의 산출(2판, 2026-08-25). 구역 구성·증분·통과율·지구 순위는 동 DB 조회값.',
  13: '환산 계수 0.045 kW/㎡ = 설치밀도 0.225 × 효율 0.20 — 솔라시도 실계획 대비 ±0.6% 검증.',
  14: '현행법 기준값 = 고정 상수 (T14, 2판·ADR-0035·2026-08-25 사용자 승인): 3,272,555필지 · 4,099,643,674.95㎡. 개정 이력: 초판 → 배제 규정 원문 재검증(ADR-0024) → 지목 복구 적용(2판). 용도지역 미상 67,875필지·30.53km²는 판정 보류로 별도 병기.',
  15: '농지법 §37② — 우량농지 등에 대한 제한이 §36 타용도 일시사용 허가·협의에도 적용됨을 명시 (국가법령정보센터 원문 대조).',
  16: '농촌공간 재구조화 및 재생지원에 관한 법률 §12①5호(재생에너지지구)·§13②(총량 상한) — 영농형법 §6①2호의 인용 법률 (원문 대조).',
};
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
        <p class="eyebrow">Sources</p><h2>출처</h2></div></div>
      <ol class="fnlist">` +
      Object.keys(FOOTNOTES).map(n =>
        `<li id="fn-${n}" value="${n}">${FOOTNOTES[n]}</li>`).join('') +
      `</ol>
      <div class="fn">번호 체계는 정책 브리프와 공통. 본문 위첨자 [n]을 누르면 해당 출처로 이동.</div>
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
