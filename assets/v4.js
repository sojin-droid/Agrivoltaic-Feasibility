// v4 공통 — data_v4 로드·렌더 도우미. 페이지 본문에 수치 하드코딩 금지 (원칙 1).
const V4 = {
  cache: {},
  async data(name) {
    if (!this.cache[name]) {
      const r = await fetch('data_v4/' + name + '.json');
      this.cache[name] = await r.json();
    }
    return this.cache[name];
  },
  n(x) { return x.toLocaleString('ko-KR'); },                       // 필지 수
  km2(x, d = 1) { return x.toLocaleString('ko-KR', {minimumFractionDigits: d, maximumFractionDigits: d}); },
  mw(m2) { return Math.round(m2 * 0.045 / 1000).toLocaleString('ko-KR'); }, // 참고 환산: ㎡ 원값 기준
  async footer() {
    const m = await this.data('meta_v4');
    const el = document.querySelector('footer');
    if (el) el.innerHTML =
      `데이터 세대 ${m.data_generation} · 생성 ${m.generated} · ${m.verification} · ` +
      `소유 구분은 지적 원장의 유형 구분(개인 식별 아님) · ` +
      `수치는 정본 DB 조회값(model/query.py)의 export — 페이지 내 재계산 없음 · ` +
      `<a href="about.html" style="color:#888">자료 계보·한계 →</a>`;
  },
  nav(active) {
    const items = [['index.html', '결론'], ['evidence.html', '근거'], ['atlas.html', '간척 아틀라스'],
                   ['method.html', '방법·재현'], ['about.html', '자료·한계']];
    document.querySelector('nav .wrap').innerHTML =
      '<span class="brand">영농형 태양광 잠재량</span>' +
      items.map(([h, t]) => `<a href="${h}" class="${h === active ? 'on' : ''}">${t}</a>`).join('');
  },
};
