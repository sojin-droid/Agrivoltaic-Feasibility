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
# 판 구분자는 rho 만으로 부족하다 — ADR-0039 판(θ 있던 59런)이 섞인다.
# theta_ha IS NULL 이 ADR-0041 판이고, 스모크는 정본이 아니다(인수인계 §3).
df = con.execute("""SELECT * FROM scenario_runs
                   WHERE theta_ha IS NULL AND COALESCE(track,'') <> 'smoke'""").fetch_df()
con.close()
keep = [c for c in ['name', 'universe', 'track', 'tau_m', 'n_eligible', 'eligible_area_km2',
                    'n_component', 'component_area_km2', 'm_total_mw', 'size_bands_json',
                    'grid_name', 'grid_sha', 'extra', 'ran_at']
        if c in df.columns]
rows = json.loads(df[keep].to_json(orient='records', force_ascii=False))
# 참고 MW·크기 대역은 DB 테이블에 있다(m_total_mw · size_bands_json) — summary 재조회 불필요.
# 대역은 JSON 문자열이라 여기서 풀어 둔다(발행 쪽에서 다시 파싱하지 않게).
for r in rows:
    sb = r.pop('size_bands_json', None)
    if sb:
        try:
            r['size_bands'] = json.loads(sb)
        except Exception:
            r['size_bands'] = []
out = {'generated': datetime.datetime.now().strftime('%Y-%m-%d %H:%M'),
       'note': '3판 — 우주 = 법인·국공유(ADR-0040) · 등재 문턱 폐지(ADR-0041): 값은 연접 구획 '
               '전량이다. 크기 기준이 필요하면 size_bands 를 쓰고 기준을 함께 적는다. '
               'track=policy 만 정본이고 what_if 는 가정 딱지가 필수다(ADR-0028). '
               '구판 런은 scenario_runs_edition2 아카이브',
       'runs': {r['name']: r for r in rows}}
fp = os.path.join(SITE, 'data_v4', 'results_v4.json')
json.dump(out, open(fp, 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
print(f"results_v4.json: {len(rows)}런 · {os.path.getsize(fp)/1e3:.0f} KB")
