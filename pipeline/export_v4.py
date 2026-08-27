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

# 키 이름 = query.py 의 phase 그대로 ('본값' = 정본, '구정의' = 폐지된 ρ≥0.30 참고값).
# 구판 키 '전'/'후' 는 쓰지 않는다 — 같은 자리에 뜻이 다른 값이 들어가는 사고를 막는다
# (구 '전' = 새 '본값', 구 '후' = 새 '구정의').
PH = ['본값', '구정의']
matrix = {pop: {code: dict({'name': name}, **{ph: cell(pop, code, ph) for ph in PH})
                for code, name, _ in Q.MATRIX_ZONES}
          for pop in ['전국', '간척']}

# 풀 분해(서로소·가산): 보호 = R1−R0, 진흥 = R2−R0 — ㎡ 원값 차분 후 반올림 (반올림값끼리 빼면 0.1 오차)
pools = {}
for pop in ['전국', '간척']:
    pools[pop] = {}
    for pool, hi in [('보호구역', 'R1'), ('진흥구역', 'R2')]:
        pools[pop][pool] = {ph: {'n': cell(pop, hi, ph)['n'] - cell(pop, 'R0', ph)['n'],
                                 'km2': round((cell(pop, hi, ph)['m2'] - cell(pop, 'R0', ph)['m2'])/1e6, 1),
                                 'm2': round(cell(pop, hi, ph)['m2'] - cell(pop, 'R0', ph)['m2'], 2)}
                            for ph in PH}

groups = Q.owner_groups_data()
owner = [{'group': g['group'], 'n': g['n'], 'km2': round(g['m2']/1e6, 1),
          'anchor_n': g['anchor_n'], 'anchor_km2': round(g['anchor_m2']/1e6, 1),
          'zones': {z: {'n': v[0], 'km2': round(v[1]/1e6, 1)} for z, v in g['zones'].items()}}
         for g in groups]

# 판정 보류(용도지역 미상) 병기값 — 엔진 ANCHOR summary에서 (ADR-0035)
pend = {}
_asp = os.path.join(r"C:\Users\user\새 폴더\Ledger_Rebuild", 'scenario_runs', 'ANCHOR', 'summary.json')
if os.path.exists(_asp):
    pend = json.load(open(_asp, encoding='utf-8')).get('pending_zone_null', {})

save('summary_v4.json', {
    'generated': GEN,
    'unit_note': '1차 단위 km². 참고 MW = 면적(㎡)×0.045/1000 (GCR 0.225×효율 0.20 가정) — 표시 시 가정 병기',
    'anchor': {'n': Q.ANCHOR_N, 'km2': round(Q.ANCHOR_M2/1e6, 2), 'm2': Q.ANCHOR_M2,
               'def': '지목 농지 ∧ 물리 통과(건물·수역·산단 없음) ∧ ¬경사15 ∧ ¬지목결측 '
                      '∧ ¬개발제한 ∧ ¬보전관리 ∧ ¬보전녹지 (ADR-0039 — 실경작 비율은 적격 조건 아님)',
               'touchstone': 'T16-① 정확 일치 검증 통과 (구 정의 T14는 회귀 검증으로만 유지)',
               'legacy': {'n': Q.ANCHOR_LEGACY_N, 'km2': round(Q.ANCHOR_LEGACY_M2/1e6, 2),
                          'def': '구 정의 ρ≥0.30 — 폐지(참고값, 정책 인용 금지)'},
               'pending_zone_null': pend},
    'matrix': matrix,          # 독립 조합 R0–R3 · 각 본값/구정의(참고) — 누적 사다리 아님
    'pools': pools,            # R1−R0(보호)·R2−R0(진흥), 서로소라 정확
    'owner_groups': owner,     # 유형 구분(개인 식별 아님)
})

# ── 1b. funnel: 전국 깔때기 (전체 → 전답과 → 앵커) ─────────────────────────
# ADR-0039: 실경작 비율은 적격 조건이 아니므로 깔때기 단계에서 제외한다. 팜맵 실측률과
# 구 정의(ρ≥0.30) 통과 수는 참고 항목(_ 접두)으로만 남긴다 — 단계로 그리면 폐지된 조건이
# 다시 판정처럼 읽힌다.
comp = Q.composition_data()
tot = comp[['전체필지', '전답과', '지목결측', '팜맵실측', '구정의30통과', '앵커적격']].sum()
funnel = {
    '전체 필지': int(tot['전체필지']),
    '지목 전·답·과수원': int(tot['전답과']),
    '현행법 적격(앵커)': int(tot['앵커적격']),
    '_지목결측': int(tot['지목결측']),
    '_팜맵 공간교차 실측': int(tot['팜맵실측']),
    '_구 정의(실경작 30% 이상)': int(tot['구정의30통과']),
}
save('funnel_v4.json', {'generated': GEN, 'national': funnel,
                        'note': '앵커 = 본값 적격(ADR-0039, 실경작 무관) — 지목결측은 구제 필지'
                                '(앵커 부적격, 복구 진행 중). _ 접두 항목은 참고값(단계 아님)'})

# ── 2. sgg_matrix: 시군별 R0–R3 (지도 채색·시군 표) ─────────────────────────
srows = Q.matrix_data(group_by='sgg')
# 시군 이름: 표준 경계 자산(sgg_boundary)에서 — 전 시군 커버 (config.toml 경로 단일 출처)
import toolconf
import geopandas as gpd
SIDO = {'11': '서울', '26': '부산', '27': '대구', '28': '인천', '29': '광주', '30': '대전',
        '31': '울산', '36': '세종', '41': '경기', '43': '충북', '44': '충남', '46': '전남',
        '47': '경북', '48': '경남', '50': '제주', '51': '강원', '52': '전북'}
bnd = gpd.read_file(toolconf.BND, columns=['sgg_cd', 'sgg_cd_new', 'sgg_nm'],
                    ignore_geometry=True)
names = {}
for r in bnd.itertuples():                    # 신구 코드 모두 등록 (PNU는 신코드 체계)
    for c in {str(r.sgg_cd), str(getattr(r, 'sgg_cd_new', '') or r.sgg_cd)}:
        names[c] = f"{SIDO.get(c[:2], '')} {r.sgg_nm}".strip()
# 2023 경계 이후 신설·개편 구 보완 (행정 표준명 — 수치 아님)
names.update({'27720': '대구 군위군', '28177': '인천 미추홀구',
              '41192': '경기 부천시원미구', '41194': '경기 부천시소사구',
              '41196': '경기 부천시오정구', '41670': '경기 여주시',
              '43112': '충북 청주시서원구', '43114': '충북 청주시청원구'})
sgg = {}
for r in srows:
    d = sgg.setdefault(r['sgg'], {'name': names.get(r['sgg'], r['sgg'])})
    d.setdefault(r['cell'], {})[r['phase']] = {'n': r['n'], 'km2': round(r['m2']/1e6, 2)}
save('sgg_matrix.json', {'generated': GEN, 'codes': sgg,
                         'note': '시군별 실측값이 1차 산출 — 반경·구간 묶음 없음'})

# ── 3. meta_v4: 계보 (각 페이지 푸터의 근거) ────────────────────────────────
con = Q.db()
lineage = [{'tbl': t, 'built': str(b), 'source': s, 'layer': (l or '')}
           for t, b, s, l in con.execute(
               "SELECT tbl, built, source, layer FROM meta_versions ORDER BY layer, tbl").fetchall()]
con.close()
save('meta_v4.json', {'generated': GEN,
                      'data_generation': '3판 (실경작 조건 제거 · 2026-08-27)',
                      'verification': 'export 시 앵커 상수 정확 일치 검증 통과 (T16-①)', 'lineage': lineage})

print(f"완료 — data_v4/ (생성 {GEN})")
