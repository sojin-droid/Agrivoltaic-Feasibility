// v4 데이터 렌더 도우미 — 수치는 전부 data_v4에서 (원칙 1). chrome(내비·푸터 골격)은 각 페이지 정적.
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
  async footer() {
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
