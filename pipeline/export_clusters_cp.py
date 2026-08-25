# -*- coding: utf-8 -*-
"""소유 필터(CP — 법인·국공유만 병합, ADR-0038) 구획 지도 데이터 export.

export_clusters_v4.py와 동일한 기하 처리(dissolve·15m 간소화·좌표 4자리·gzip)를
CP 4칸에만 적용하고, 기존 clusters_index.json에 **병합**한다(기존 8칸 색인 보존).
사용: python pipeline/export_clusters_cp.py
"""
import os, sys, json, gzip, datetime
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
import pandas as pd
import geopandas as gpd
import shapely

ROOT = r"C:\Users\user\새 폴더"
LR = os.path.join(ROOT, 'Ledger_Rebuild')
CAD = os.path.join(ROOT, 'Cadastre_All')
RUNS = os.path.join(LR, 'scenario_runs')
SITE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(SITE, 'data_v4', 'clusters')

CELLS = ['ANCHOR_CP', 'ANCHOR_CP_SB', 'SOFT_R2_CP', 'SOFT_R2_CP_SB']
SIMPLIFY_M = 15.0
GEN = datetime.datetime.now().strftime('%Y-%m-%d %H:%M')

nodes = pd.read_parquet(os.path.join(LR, 'engine_cache', 'nodes.parquet'),
                        columns=['pnu', 'area'])
area = pd.Series(nodes['area'].values, index=nodes['pnu'].values)
del nodes

mem, comp_area = {}, {}
for c in CELLS:
    m = pd.read_parquet(os.path.join(RUNS, c, 'members.parquet'))
    m['sgg'] = m['pnu'].str[:5]
    m['a'] = area.reindex(m['pnu'].values).values
    comp_area[c] = m.groupby('lab')['a'].sum() / 1e6
    mem[c] = m
    print(f"{c}: 멤버 {len(m):,} · 등재 구획 {m['lab'].nunique():,}", flush=True)

sggs = sorted(set().union(*[set(m['sgg'].unique()) for m in mem.values()]))
print(f"대상 시군 {len(sggs)}", flush=True)


def rnd4(cc):
    if isinstance(cc[0], (list, tuple)):
        return [rnd4(x) for x in cc]
    return [round(cc[0], 4), round(cc[1], 4)]


span = {c: set(mem[c].groupby('lab')['sgg'].nunique().pipe(lambda s: s[s > 1]).index)
        for c in CELLS}

for i, sgg in enumerate(sggs, 1):
    g = None
    for c in CELLS:
        fo = os.path.join(OUT, f'{sgg}_{c}.json.gz')
        if os.path.exists(fo):
            continue
        if g is None:
            g = gpd.read_file(os.path.join(CAD, f'{sgg}.gpkg')).to_crs(5186)
            g = g.drop_duplicates('pnu').set_index('pnu')
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
                gj = {'type': gj['type'], 'coordinates': rnd4(list(gj['coordinates']))}
                feats.append({'type': 'Feature', 'geometry': gj,
                              'properties': {'id': int(lab),
                                             'a': round(float(comp_area[c].get(lab, 0.0)), 2),
                                             'n': int(n_by.get(lab, 0)),
                                             'sp': 1 if lab in span[c] else 0}})
        raw = json.dumps({'type': 'FeatureCollection', 'cell': c, 'sgg': sgg,
                          'features': feats}, ensure_ascii=False,
                         separators=(',', ':')).encode('utf-8')
        with gzip.open(fo + '.tmp', 'wb', compresslevel=9) as z:
            z.write(raw)
        os.replace(fo + '.tmp', fo)
    if i % 10 == 0 or i == len(sggs):
        print(f"  [{i}/{len(sggs)}] {sgg} 완료", flush=True)

# ── 색인 병합 (기존 8칸 보존) ──
ixp = os.path.join(SITE, 'data_v4', 'clusters_index.json')
index = json.load(open(ixp, encoding='utf-8'))
for c in CELLS:
    if c not in index['cells']:
        index['cells'].append(c)
for sgg in sggs:
    ent = index['sgg'].setdefault(sgg, {})
    for c in CELLS:
        ms = mem[c][mem[c]['sgg'] == sgg]
        ids = set(ms['lab'].unique())
        ent[c] = {'k': len(ids),
                  'km2': round(float(comp_area[c].reindex(list(ids)).sum()), 1) if ids else 0.0}
index['generated_cp'] = GEN
json.dump(index, open(ixp, 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
print(f"완료 — CP {len(sggs)}시군 × 4칸 + 색인 병합 ({GEN})", flush=True)
