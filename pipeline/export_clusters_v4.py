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

# 정본 8칸 (ADR-0040 개명판). 대조군(@all)은 지도에 그리지 않는다 — 지도는 정본을 보이는
# 화면이고, 대조군 병기는 수치 표가 맡는다(전량 적재 시 용량이 두 배가 되기도 한다).
CELLS = ['R0_current', 'R0_current_SB', 'R1_protect', 'R1_protect_SB',
         'R2_promo', 'R2_promo_SB', 'R3_zone_all', 'R3_zone_all_SB']
# 적응 단순화 — 구획 크기에 비례한 허용오차(등가반경의 1/20), [1,10]m 클립.
# 평탄 허용오차를 쓰면 작은 구획이 뭉개진다(정본 우주 구획 중앙 면적 700㎡ = 반경 약 15m).
SIMP_RATIO, SIMP_MIN, SIMP_MAX = 1/20.0, 1.0, 10.0
# 좌표 정밀도 — 위상 인식(set_precision). 단순 반올림은 얇은 구획을 자기교차로 만든다.
GRID_M = 0.5
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
            geoms = sub.geometry.values[ok]
            labs = ms['lab'].values[ok]
            if len(geoms):
                # ── 구획별 합집합을 한 번에 (구획 수가 30만이라 파이썬 루프는 못 버틴다) ──
                grouped = (gpd.GeoSeries(geoms)
                           .groupby(labs).agg(lambda gs: shapely.union_all(gs.values)))
                uniq = grouped.index.values
                merged = np.asarray(grouped.values, dtype=object)
                # 적응 허용오차 — 등가반경의 1/20, [1,10]m. 평탄 허용오차는 작은 구획을 죽인다
                area = shapely.area(merged)
                tol = np.clip(np.sqrt(area / np.pi) * SIMP_RATIO, SIMP_MIN, SIMP_MAX)
                merged = shapely.simplify(merged, tol)
                # 양자화 전에 유효화한다 — set_precision 은 무효 입력에서 TopologyException 을
                # 던진다(실측: side location conflict). 던지면 그 시군 전체가 멈춘다.
                bad = ~shapely.is_valid(merged)
                if bad.any():
                    merged[bad] = shapely.make_valid(merged[bad])
                try:
                    merged = shapely.set_precision(merged, GRID_M)   # 위상 인식 양자화
                except Exception:
                    # 배열 단위로 실패하면 개별로 시도하고, 끝내 안 되는 것은 양자화를
                    # 건너뛴다 — 좌표가 조금 길어질 뿐, 형태를 잃거나 버리지는 않는다
                    out_g, n_skip = [], 0
                    for _g in merged:
                        try:
                            out_g.append(shapely.set_precision(_g, GRID_M))
                        except Exception:
                            out_g.append(_g)
                            n_skip += 1
                    merged = np.asarray(out_g, dtype=object)
                    if n_skip:
                        print(f"    ※ {sgg}/{c}: 양자화 건너뜀 {n_skip}구획(위상 충돌)",
                              flush=True)
                bad = ~shapely.is_valid(merged)
                if bad.any():
                    merged[bad] = shapely.make_valid(merged[bad])
                keep = ~shapely.is_empty(merged)
                gs = gpd.GeoSeries(merged[keep], crs=5186).to_crs(4326)
                n_by = pd.Series(1, index=labs).groupby(level=0).sum()
                for lab, geo in zip(uniq[keep], gs.values):
                    gj = shapely.geometry.mapping(geo)
                    # 좌표는 여기서 반올림하지 않는다 — 양자화는 위상 인식으로 이미 끝났고,
                    # 여기서 또 자르면 그때 자기교차가 생긴다(인수인계 §7 실측).
                    feats.append({'type': 'Feature',
                                  'geometry': {'type': gj['type'],
                                               'coordinates': list(gj['coordinates'])},
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
