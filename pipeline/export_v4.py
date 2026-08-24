# -*- coding: utf-8 -*-
"""data_v4 export — 정본(model/query.py)의 함수를 직접 불러 사이트 데이터를 만든다.
원칙 1(단일 출처): 이 스크립트에는 판정 SQL이 없다. 조건이 바뀌면 query.py 한 곳만 바뀐다.
원칙 13(게이트): matrix_data()가 T14 불일치 시 스스로 중단하므로 어긋난 값은 파일이 되지 않는다.

사용: python pipeline/export_v4.py            (사이트 레포 어디서든)
출력: data_v4/summary_v4.json · sgg_matrix.json · meta_v4.json
"""
import sys, os, json
from datetime import datetime
# stdout 래핑은 query.py가 import 시 수행 — 여기서 중복 래핑하면 버퍼가 닫힌다

MODEL = r"C:\Users\user\새 폴더\model"
sys.path.insert(0, MODEL)
import query as Q                     # 정본 질의 모듈

SITE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(SITE, 'data_v4')
os.makedirs(OUT, exist_ok=True)

def save(name, obj):
    fp = os.path.join(OUT, name)
    with open(fp, 'w', encoding='utf-8') as f:
        json.dump(obj, f, ensure_ascii=False, indent=1)
    print(f"  {name}: {os.path.getsize(fp)/1e3:.0f} KB")

GEN = datetime.now().strftime('%Y-%m-%d %H:%M')

# ── 1. summary_v4: 매트릭스(전국·간척) + 풀 분해 + 소유 세 무리 ─────────────
rows = Q.matrix_data()                # T14 검증 내장 — 실패 시 여기서 중단
def cell(pop, code, phase):
    r = [x for x in rows if x['pop'] == pop and x['cell'] == code and x['phase'] == phase][0]
    # m2 원값 동봉 — MW 참고 환산은 반올림 km²가 아니라 원값에서 (브리프와 자릿수 일치)
    return {'n': r['n'], 'km2': round(r['m2']/1e6, 1), 'm2': round(r['m2'], 2)}

matrix = {pop: {code: {'name': name, '전': cell(pop, code, '전'), '후': cell(pop, code, '후')}
                for code, name, _ in Q.MATRIX_ZONES}
          for pop in ['전국', '간척']}

# 풀 분해(서로소·가산): 보호 = R1−R0, 진흥 = R2−R0 — 정본 매트릭스에서 산술로만 유도
pools = {}
for pop in ['전국', '간척']:
    pools[pop] = {}
    for pool, hi in [('보호구역', 'R1'), ('진흥구역', 'R2')]:
        pools[pop][pool] = {ph: {'n': cell(pop, hi, ph)['n'] - cell(pop, 'R0', ph)['n'],
                                 'km2': round(cell(pop, hi, ph)['km2'] - cell(pop, 'R0', ph)['km2'], 1)}
                            for ph in ['전', '후']}

groups = Q.owner_groups_data()
owner = [{'group': g['group'], 'n': g['n'], 'km2': round(g['m2']/1e6, 1),
          'anchor_n': g['anchor_n'], 'anchor_km2': round(g['anchor_m2']/1e6, 1),
          'zones': {z: {'n': v[0], 'km2': round(v[1]/1e6, 1)} for z, v in g['zones'].items()}}
         for g in groups]

save('summary_v4.json', {
    'generated': GEN,
    'unit_note': '1차 단위 km². 참고 MW = 면적(㎡)×0.045/1000 (GCR 0.225×효율 0.20 가정) — 표시 시 가정 병기',
    'anchor': {'n': Q.T14_N, 'km2': round(Q.T14_M2/1e6, 2), 'm2': Q.T14_M2,
               'def': 'n_s0_ge30 ∧ ¬개발제한 ∧ ¬보전관리 ∧ ¬보전녹지 (ADR-0024 개정판)',
               'touchstone': 'T14 정확 일치 검증 통과'},
    'matrix': matrix,          # 독립 조합 R0–R3 · 각 실경작 전/후 — 누적 사다리 아님
    'pools': pools,            # R1−R0(보호)·R2−R0(진흥), 서로소라 정확
    'owner_groups': owner,     # 유형 구분(개인 식별 아님)
})

# ── 1b. funnel: 전국 깔때기 (전체 → 전답과 → 팜맵 실측 → 실체 30% → 앵커) ────
comp = Q.composition_data()
tot = comp[['전체필지', '전답과', '지목결측', '팜맵실측', '실체30통과', '앵커적격']].sum()
funnel = {
    '전체 필지': int(tot['전체필지']),
    '지목 전·답·과수원': int(tot['전답과']),
    '  그중 팜맵 공간교차 실측': int(tot['팜맵실측']),
    '실경작 30% 이상': int(tot['실체30통과']),
    '현행법 적격(앵커)': int(tot['앵커적격']),
    '_지목결측': int(tot['지목결측']),
}
save('funnel_v4.json', {'generated': GEN, 'national': funnel,
                        'note': '앵커 적격 필지 수는 T14와 동일 조건 — 지목결측은 구제 필지(앵커 부적격, 복구 진행 중)'})

# ── 2. sgg_matrix: 시군별 R0–R3 (지도 채색·시군 표) ─────────────────────────
srows = Q.matrix_data(group_by='sgg')
sgg = {}
for r in srows:
    d = sgg.setdefault(r['sgg'], {})
    d.setdefault(r['cell'], {})[r['phase']] = {'n': r['n'], 'km2': round(r['m2']/1e6, 2)}
save('sgg_matrix.json', {'generated': GEN, 'codes': sgg,
                         'note': '시군별 실측값이 1차 산출 — 반경·구간 묶음 없음'})

# ── 3. meta_v4: 계보 (각 페이지 푸터의 근거) ────────────────────────────────
con = Q.db()
lineage = [{'tbl': t, 'built': str(b), 'source': s}
           for t, b, s in con.execute("SELECT tbl, built, source FROM meta_versions").fetchall()]
con.close()
save('meta_v4.json', {'generated': GEN, 'data_generation': 'v4 (앵커 개정판 2026-08-21 기준)',
                      'verification': 'export 시 T14 정확 일치 검증 통과', 'lineage': lineage})

print(f"완료 — data_v4/ (생성 {GEN})")
