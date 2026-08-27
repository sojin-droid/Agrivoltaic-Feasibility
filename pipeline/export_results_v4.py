# -*- coding: utf-8 -*-
"""격자 1판 결과 export — scenario_runs 테이블(정본)을 그대로 사이트 데이터로.
사용: python pipeline/export_results_v4.py  →  data_v4/results_v4.json"""
import os, sys, json, datetime
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
import duckdb

LR = r"C:\Users\user\새 폴더\Ledger_Rebuild"
SITE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
con = duckdb.connect(os.path.join(LR, 'agrivoltaic_ledger_v1.duckdb'), read_only=True)
# 구판(ADR-0039 이전, rho 값이 있는 런)은 사이트로 내보내지 않는다 — 아카이브 전용
# (Ledger_Rebuild/scenario_runs_edition2 · DB scenario_runs_edition2)
df = con.execute("SELECT * FROM scenario_runs WHERE rho IS NULL").fetch_df()
con.close()
keep = [c for c in ['name', 'rho', 'tau_m', 'theta_ha', 'n_eligible', 'eligible_area_km2',
                    'n_component', 'n_listed', 'listed_area_km2', 'M_mw', 'extra', 'ran_at']
        if c in df.columns]
rows = json.loads(df[keep].to_json(orient='records', force_ascii=False))
# 참고 MW: DB 테이블에 없음 — 각 런 디렉터리 summary.json(엔진 산출, ㎡ 원값 기준)에서
# 파라미터가 본값과 일치할 때만 가져온다 (태그 런이 덮어쓴 stale summary 오인 방지).
# rho 는 ADR-0039 로 폐지돼 params 에 없으므로 대조 대상이 아니다.
for r in rows:
    sp = os.path.join(LR, 'scenario_runs', r['name'], 'summary.json')
    if os.path.exists(sp):
        s = json.load(open(sp, encoding='utf-8'))
        if (s.get('name') == r['name']
                and 'rho' not in s['params']
                and abs(s['params'].get('tau_m', -1) - (r.get('tau_m') or 21.0)) < 1e-9
                and abs(s['params'].get('theta_ha', -1) - (r.get('theta_ha') or 6.6667)) < 1e-3
                and abs(s.get('listed_area_km2', -1) - r['listed_area_km2']) < 0.11):
            r['M_mw'] = s.get('M_mw')
out = {'generated': datetime.datetime.now().strftime('%Y-%m-%d %H:%M'),
       'note': '본값 판 (ADR-0039) — 실경작 비율은 적격 조건이 아님. 면적은 장부면적 기준, '
               'MW는 참고 환산(0.045kW/㎡). 구 정의 런은 scenario_runs_edition2 아카이브',
       'runs': {r['name']: r for r in rows}}
fp = os.path.join(SITE, 'data_v4', 'results_v4.json')
json.dump(out, open(fp, 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
print(f"results_v4.json: {len(rows)}런 · {os.path.getsize(fp)/1e3:.0f} KB")
