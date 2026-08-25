# -*- coding: utf-8 -*-
"""5단 결론 서사 수치 export — data_v4/narrative_v4.json (ADR-0038 포함).

전량 model/query.py 표준 질의·scenario_runs 등재분에서만 산출(즉석 정의 없음).
게이트: scenario_runs의 ANCHOR가 T14 상수와 정확 일치하지 않으면 중단.
사용: python pipeline/export_narrative_v4.py
"""
import os, sys, json, datetime
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.path.insert(0, r'C:\Users\user\새 폴더\model')
import query as Q

SITE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LR = r"C:\Users\user\새 폴더\Ledger_Rebuild"

con = Q.db()
# ── 게이트: ANCHOR = T14 ──
a = con.execute("""SELECT n_eligible, eligible_area_km2, n_listed, listed_area_km2, m_mw
                   FROM scenario_runs WHERE name='ANCHOR'""").fetchone()
assert a[0] == Q.T14_N and abs(a[1] - Q.T14_M2/1e6) < 0.01, f"[FAIL] ANCHOR ≠ T14: {a}"

# ── 런 요약 + 크기 분포 ──
RUNS = ['ANCHOR', 'ANCHOR_SB', 'SOFT_A1', 'SOFT_A1_SB', 'SOFT_R2', 'SOFT_R2_SB',
        'SOFT_A2', 'SOFT_A2_SB', 'ANCHOR_CP', 'ANCHOR_CP_SB', 'SOFT_R2_CP', 'SOFT_R2_CP_SB']
size = {d['run']: d for d in Q.clusters_size_data(RUNS)}
runs = {}
for name, ne, ek, nl, lk, mw in con.execute(f"""
    SELECT name, n_eligible, eligible_area_km2, n_listed, listed_area_km2, m_mw
    FROM scenario_runs WHERE name IN ({','.join(['?']*len(RUNS))})""", RUNS).fetchall():
    s = size.get(name, {})
    runs[name] = {'n_eligible': ne, 'eligible_km2': ek, 'n_listed': nl,
                  'listed_km2': lk, 'mw': round(mw),
                  'ge50': s.get('ge50'), 'ge100': s.get('ge100'),
                  'max_ha': round(s.get('max_ha', 0))}

# ── 소유 × 이격 (필지층) ──
owner_sb = Q.owner_setback_data()

# ── 대형 구획(무필터)의 소유 구성 — 국공유 = 02/04/05, 법인 = 06 (ADR-0038 코드 확정) ──
NODES = os.path.join(LR, 'engine_cache', 'nodes.parquet').replace('\\', '/')
T50 = 50_000 / Q.KW
comp = {}
for run in ['ANCHOR', 'SOFT_R2']:
    mp = os.path.join(LR, 'scenario_runs', run, 'members.parquet').replace('\\', '/')
    r = con.execute(f"""
      WITH m AS (SELECT lab, pnu FROM read_parquet('{mp}')),
      ca AS (SELECT lab, SUM(n.area) a FROM m JOIN read_parquet('{NODES}') n USING(pnu)
             GROUP BY lab HAVING a >= {T50}),
      c AS (SELECT m.lab, SUM(l.calculatedarea) tot,
              SUM(l.calculatedarea) FILTER (l.ownership IN ('02','04','05','06')) op,
              SUM(l.calculatedarea) FILTER (l.ownership='01') indiv
            FROM m JOIN ca USING(lab) JOIN ledger l USING(pnu) GROUP BY m.lab)
      SELECT COUNT(*), COUNT(*) FILTER (COALESCE(op,0)/tot >= 0.5),
             100*SUM(COALESCE(indiv,0))/SUM(tot) FROM c""").fetchone()
    comp[run] = {'ge50': r[0], 'majority_op': r[1], 'indiv_share_pct': round(r[2], 0)}

# ── CP 대형 구획 소재(상위) — 간척 여부·지구명 ──
def cp_big_of(run):
    cpp = os.path.join(LR, 'scenario_runs', run, 'clusters.parquet').replace('\\', '/')
    mpp = os.path.join(LR, 'scenario_runs', run, 'members.parquet').replace('\\', '/')
    out = []
    for lab, mw, n, rec, dist, sgg in con.execute(f"""
        WITH big AS (SELECT lab, mw FROM read_parquet('{cpp}') WHERE mw >= 50),
        m AS (SELECT b.lab, b.mw, mm.pnu FROM big b JOIN read_parquet('{mpp}') mm USING(lab))
        SELECT m.lab, ANY_VALUE(m.mw), COUNT(*),
          100.0*COUNT(*) FILTER (rt.pnu IS NOT NULL)/COUNT(*),
          ANY_VALUE(rt.ekr_district), MODE(SUBSTR(m.pnu,1,5))
        FROM m LEFT JOIN reclaim_tag rt USING(pnu)
        GROUP BY m.lab ORDER BY 2 DESC""").fetchall():
        out.append({'mw': round(mw), 'n': n, 'reclaim_pct': round(rec),
                    'district': dist, 'sgg': sgg})
    return out

cp_top = cp_big_of('SOFT_R2_CP')
cp_top_anchor = cp_big_of('ANCHOR_CP')
con.close()

out = {
    'generated': datetime.datetime.now().strftime('%Y-%m-%d %H:%M'),
    'edition': '2판 (ADR-0035) · 소유 필터 ADR-0038',
    'kw_per_m2': Q.KW,
    'threshold': {'mw50_ha': round(50_000/Q.KW/1e4, 1), 'mw100_ha': round(100_000/Q.KW/1e4, 1)},
    'runs': runs,
    'owner_setback': owner_sb,
    'big_composition': comp,
    'cp_big': cp_top,
    'cp_big_anchor': cp_top_anchor,
}
fo = os.path.join(SITE, 'data_v4', 'narrative_v4.json')
json.dump(out, open(fo, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print(f"완료 — narrative_v4.json ({out['generated']}) · 런 {len(runs)} · CP 대형 {len(cp_top)}")
