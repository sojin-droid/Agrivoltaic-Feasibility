# -*- coding: utf-8 -*-
"""인사이트 탭 데이터 export — 구획 색인·필지층 매트릭스·격자에서 유형별 전수 계산.
원칙 1: 페이지는 이 파일의 산출(insights_v4.json)만 렌더. 계산식은 인사이트 노트와 동일.
사용: python pipeline/export_insights_v4.py"""
import os, sys, json, datetime
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

SITE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
B = os.path.join(SITE, 'data_v4')
idx = json.load(open(f'{B}\\clusters_index.json', encoding='utf-8'))['sgg']
codes = json.load(open(f'{B}\\sgg_matrix.json', encoding='utf-8'))['codes']
res = json.load(open(f'{B}\\results_v4.json', encoding='utf-8'))['runs']
summ = json.load(open(f'{B}\\summary_v4.json', encoding='utf-8'))

def v(c, cell):
    e = idx.get(c, {}).get(cell)
    return e['km2'] if e else 0.0

rows = []
for c in set(list(idx.keys()) + list(codes.keys())):
    r = dict(c=c, nm=codes.get(c, {}).get('name', c),
             r0=v(c, 'ANCHOR'), r0s=v(c, 'ANCHOR_SB'),
             a1=v(c, 'SOFT_A1'), a1s=v(c, 'SOFT_A1_SB'),
             r2=v(c, 'SOFT_R2'), r3=v(c, 'SOFT_A2'))
    r['protInc'] = round(r['a1'] - r['r0'], 2)
    r['protIncS'] = round(r['a1s'] - r['r0s'], 2)
    rows.append(r)

# ① 보호 증분 이격 소멸 16곳형
wipe = sorted([r for r in rows if r['protInc'] >= 0.3 and r['protIncS'] <= 0.05],
              key=lambda r: -r['protInc'])
keepers = sorted([r for r in rows if r['protInc'] >= 0.3 and r['protIncS'] >= 0.8*r['protInc']],
                 key=lambda r: -r['protInc'])
n_base = sum(1 for r in rows if r['protInc'] >= 0.3)

# ③ 생존율 분포 (R0≥5)
surv = sorted([dict(nm=r['nm'], c=r['c'], r0=round(r['r0'], 1), r0s=round(r['r0s'], 1),
                    pct=round(100*r['r0s']/r['r0'], 1))
               for r in rows if r['r0'] >= 5], key=lambda x: x['pct'])

# ④ 시너지
syn = sorted([dict(nm=r['nm'], c=r['c'], syn=round((r['r3']-r['r2'])-r['protInc'], 1),
                   prot=r['protInc'], both=round(r['r3']-r['r2'], 1))
              for r in rows], key=lambda x: -x['syn'])[:10]
syn_nat = round((res['SOFT_A2']['listed_area_km2'] - res['SOFT_R2']['listed_area_km2'])
                - (res['SOFT_A1']['listed_area_km2'] - res['ANCHOR']['listed_area_km2']), 1)

# ⑤ 전환율 (필지 R0후 ≥10)
conv = []
for c, d in codes.items():
    try:
        pk = d['R0']['후']['km2']
    except Exception:
        continue
    if pk >= 10:
        conv.append(dict(nm=d.get('name', c), c=c, pk=round(pk, 1),
                         ck=round(v(c, 'ANCHOR'), 1), pct=round(100*v(c, 'ANCHOR')/pk, 1)))
conv.sort(key=lambda x: x['pct'])

# ② 전국 이격 감소율
nat = [dict(t=t, pre=res[a]['listed_area_km2'], post=res[b]['listed_area_km2'],
            drop=round(100*(res[a]['listed_area_km2']-res[b]['listed_area_km2'])
                       / res[a]['listed_area_km2'], 1))
       for a, b, t in [('ANCHOR', 'ANCHOR_SB', '현행법'), ('SOFT_A1', 'SOFT_A1_SB', '+보호구역'),
                       ('SOFT_R2', 'SOFT_R2_SB', '+진흥구역'), ('SOFT_A2', 'SOFT_A2_SB', '둘 다')]]

# ⑧ 간척 특화 (필지층 매트릭스·소유)
K = summ['matrix']['간척']
NA = summ['matrix']['전국']
og = {g['group']: g for g in summ['owner_groups']}
reclaim = dict(
    drop_reclaim=round(100*(K['R3']['전']['km2']-K['R3']['후']['km2'])/K['R3']['전']['km2'], 1),
    drop_nat=round(100*(NA['R3']['전']['km2']-NA['R3']['후']['km2'])/NA['R3']['전']['km2'], 1),
    prot_inc=round(K['R1']['후']['km2']-K['R0']['후']['km2'], 1),
    r2_share=round(100*(K['R2']['후']['km2']-K['R0']['후']['km2'])
                   / (K['R3']['후']['km2']-K['R0']['후']['km2']), 1),
    out_anchor=og['간척지 외 법인']['anchor_km2'],
    in_anchor=og['간척지 내 법인']['anchor_km2'],
    pool=og['간척지 내 비법인']['km2'],
    lease_ratio=round(og['간척지 내 비법인']['km2']/og['간척지 외 법인']['anchor_km2'], 2),
    r0=K['R0']['후']['km2'], r2=K['R2']['후']['km2'],
)

out = dict(generated=datetime.datetime.now().strftime('%Y-%m-%d %H:%M'),
           n_base=n_base, wipe=wipe, keepers=keepers[:3],
           surv=surv, syn=syn, syn_nat=syn_nat, conv=conv, nat=nat, reclaim=reclaim)
fp = os.path.join(B, 'insights_v4.json')
json.dump(out, open(fp, 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
print(f"insights_v4.json: 소멸형 {len(wipe)} · 생존율 {len(surv)}시군 · 전환율 {len(conv)}시군 "
      f"· 시너지 전국 {syn_nat} · {os.path.getsize(fp)/1e3:.0f} KB")
