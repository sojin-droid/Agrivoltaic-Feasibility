# -*- coding: utf-8 -*-
"""구획(등재 클러스터) 폴리곤 export — 지도 탭 데이터 (시나리오별·시군별).

원천: 정본 scenario_runs/{cell}/members.parquet (pnu→성분 lab, 1판·ADR-0034 승인)
      + engine_cache/nodes.parquet(장부면적) + Cadastre_All 지오메트리.
산출: data_v4/clusters/{sgg}_{cell}.json — 등재 구획을 시군 구간별로 dissolve·간소화한
      GeoJSON(4326). 성분이 여러 시군에 걸치면 각 시군 파일에 그 구간이 들어가고
      속성 a(구획 전체 km²)는 동일, part=1 로 표시.
      data_v4/clusters_index.json — 시군×시나리오 요약(선택 목록·통계용).

체크포인트: 시군 단위(6칸 전부 존재 시 건너뜀). 재실행 안전.
사용: python pipeline/export_clusters_v4.py
"""
import os, sys, json, glob, datetime
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
import numpy as np, pandas as pd
import geopandas as gpd
import shapely

ROOT = r"C:\Users\user\새 폴더"
LR = os.path.join(ROOT, 'Ledger_Rebuild')
CAD = os.path.join(ROOT, 'Cadastre_All')
RUNS = os.path.join(LR, 'scenario_runs')
SITE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(SITE, 'data_v4', 'clusters')
os.makedirs(OUT, exist_ok=True)

CELLS = ['ANCHOR', 'ANCHOR_SB', 'SOFT_A1', 'SOFT_A1_SB', 'SOFT_A2', 'SOFT_A2_SB']
SIMPLIFY_M = 15.0
GEN = datetime.datetime.now().strftime('%Y-%m-%d %H:%M')

# ── 멤버·면적 적재 (한 번) ──
nodes = pd.read_parquet(os.path.join(LR, 'engine_cache', 'nodes.parquet'),
                        columns=['pnu', 'area'])
area = pd.Series(nodes['area'].values, index=nodes['pnu'].values)
del nodes

mem = {}
comp_area = {}
for c in CELLS:
    m = pd.read_parquet(os.path.join(RUNS, c, 'members.parquet'))
    m['sgg'] = m['pnu'].str[:5]
    m['a'] = area.reindex(m['pnu'].values).values
    comp_area[c] = m.groupby('lab')['a'].sum() / 1e6          # 구획 전체 km² (장부면적)
    mem[c] = m
    print(f"{c}: 멤버 {len(m):,} · 등재 구획 {m['lab'].nunique():,}", flush=True)

sggs = sorted(set().union(*[set(m['sgg'].unique()) for m in mem.values()]))
print(f"대상 시군 {len(sggs)}", flush=True)

for i, sgg in enumerate(sggs, 1):
    outs = {c: os.path.join(OUT, f'{sgg}_{c}.json') for c in CELLS}
    if all(os.path.exists(p) for p in outs.values()):
        continue
    g = gpd.read_file(os.path.join(CAD, f'{sgg}.gpkg')).to_crs(5186)
    g = g.drop_duplicates('pnu').set_index('pnu')
    for c in CELLS:
        fo = outs[c]
        if os.path.exists(fo):
            continue
        ms = mem[c][mem[c]['sgg'] == sgg]
        feats = []
        if len(ms):
            sub = g.reindex(ms['pnu'].values)
            ok = sub.geometry.notna().values
            sub = sub[ok]
            labs = ms['lab'].values[ok]
            n_by = pd.Series(1, index=labs).groupby(level=0).sum()
            for lab, geo in gpd.GeoSeries(sub.geometry.values).groupby(labs):
                u = shapely.union_all(geo.values)
                u = shapely.simplify(u, SIMPLIFY_M)
                if u.is_empty:
                    continue
                u4326 = gpd.GeoSeries([u], crs=5186).to_crs(4326).iloc[0]
                gj = shapely.geometry.mapping(u4326)
                def rnd(cc):
                    if isinstance(cc[0], (list, tuple)):
                        return [rnd(x) for x in cc]
                    return [round(cc[0], 5), round(cc[1], 5)]
                gj = {'type': gj['type'], 'coordinates': rnd(list(gj['coordinates']))}
                feats.append({'type': 'Feature', 'geometry': gj,
                              'properties': {'id': int(lab),
                                             'a': round(float(comp_area[c].get(lab, 0.0)), 2),
                                             'n': int(n_by.get(lab, 0))}})
        tmp = fo + '.tmp'
        json.dump({'type': 'FeatureCollection', 'cell': c, 'sgg': sgg,
                   'features': feats},
                  open(tmp, 'w', encoding='utf-8'), ensure_ascii=False,
                  separators=(',', ':'))
        os.replace(tmp, fo)
    if i % 10 == 0 or i == len(sggs):
        print(f"  [{i}/{len(sggs)}] {sgg} 완료", flush=True)

# ── 걸침 표시 후처리 + 색인 ──
span = {c: set(mem[c].groupby('lab')['sgg'].nunique().pipe(lambda s: s[s > 1]).index)
        for c in CELLS}
index = {'generated': GEN, 'cells': CELLS, 'sgg': {}}
for sgg in sggs:
    ent = {}
    for c in CELLS:
        fo = os.path.join(OUT, f'{sgg}_{c}.json')
        if not os.path.exists(fo):
            continue
        d = json.load(open(fo, encoding='utf-8'))
        changed = False
        for f in d['features']:
            sp = 1 if f['properties']['id'] in span[c] else 0
            if f['properties'].get('sp', None) != sp:
                f['properties']['sp'] = sp
                changed = True
        if changed:
            tmp = fo + '.tmp'
            json.dump(d, open(tmp, 'w', encoding='utf-8'), ensure_ascii=False,
                      separators=(',', ':'))
            os.replace(tmp, fo)
        ids = {f['properties']['id'] for f in d['features']}
        ent[c] = {'k': len(ids),
                  'km2': round(float(comp_area[c].reindex(list(ids)).sum()), 1)}
    index['sgg'][sgg] = ent
json.dump(index, open(os.path.join(SITE, 'data_v4', 'clusters_index.json'), 'w',
                      encoding='utf-8'), ensure_ascii=False, indent=0)
print(f"완료 — clusters/ {len(glob.glob(os.path.join(OUT, '*.json'))):,}파일 + 색인 ({GEN})",
      flush=True)
