# -*- coding: utf-8 -*-
"""산업단지 입주기업 검색 색인 export — data_v4/ind_firms.json.gz.

원천: 한국산업단지공단 『전국등록공장현황』(FactoryOn 등록분, 2024-12-31 기준,
  공공데이터포털 15105482 — 원시 CSV = Ledger_Rebuild/sources/ind_complex/firms/).
목적: 산단 연계 탭에서 기업명으로 검색 → 그 기업이 입주한 산업단지로 이동 (표시 참고용,
  정본 판정 불사용).
매칭: CSV 단지명 ↔ V-World dan_name(ind_bnd) — 접미어 제거 + 괄호 별칭('반월특수(시화)' 등)
  + 포함 매칭. CSV 단지명에 유형 키워드(농공 등)가 있으면 동명 단지의 유형 구분에 사용.
사용: python pipeline/export_ind_firms.py
"""
import os, sys, csv, re, json, gzip, datetime
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.path.insert(0, r'C:\Users\user\새 폴더\model')
import query as Q
import duckdb

LR = r'C:\Users\user\새 폴더\Ledger_Rebuild'
SITE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(LR, 'sources', 'ind_complex', 'firms', '전국등록공장현황_20241231.csv')
GEN = datetime.datetime.now().strftime('%Y-%m-%d %H:%M')

SUF = re.compile(r'국가산업단지|일반산업단지|도시첨단산업단지|농공단지|지방산업단지|'
                 r'전문단지|특수지역|재생사업지구|외국인투자지역|자유무역지역|산업단지|'
                 r'\s+|\.|·')
norm = lambda s: SUF.sub('', s or '')

con = Q.db()
ours = [(r[0], r[1]) for r in con.execute(
    "SELECT DISTINCT dan_name, cat_nam FROM ind_complex_bnd").fetchall()]
con.close()

# 별칭 사전: 기본명(괄호 제거)·괄호 안 토큰·정규화 전체
alias = {}                      # 정규화 별칭 → [(dan_name, cat_nam), ...]
for nm, cat in ours:
    toks = set()
    base = re.sub(r'\(.*?\)', '', nm)
    toks.add(norm(base))
    for p in re.findall(r'\((.*?)\)', nm):
        toks.add(norm(p))
    toks.add(norm(nm))
    for tk in toks:
        if len(tk) >= 2:
            alias.setdefault(tk, []).append((nm, cat))
akeys = sorted(alias, key=len, reverse=True)

TYPE_HINT = [('농공', '농공단지'), ('도시첨단', '도시첨단산업단지'),
             ('국가', '국가산업단지'), ('일반', '일반산업단지')]

def resolve(dan):
    nd = norm(dan)
    if not nd:
        return None
    hint = next((c for k, c in TYPE_HINT if k in dan), None)
    cands = None
    if nd in alias:
        cands = alias[nd]
    else:
        for k in akeys:                       # 접두 시도명 제거 대응: '서울마곡' endswith '마곡'
            if (len(k) >= 3 and (nd.endswith(k) or k in nd)) or                (len(k) == 2 and (nd.startswith(k) or nd.endswith(k))):  # '고덕국제화계획지구'→'고덕'
                cands = alias[k]
                break
        if cands is None:                      # 역포함: '반월'⊂'반월특수(시화)', '수원델타플렉스'⊂'…1'
            rc = []
            for k, v in alias.items():
                if len(nd) >= 2 and (k.startswith(nd) or nd in k):
                    rc.extend(v)
            if rc:
                cands = rc
    if not cands:
        return None
    if hint:
        typed = [c for c in cands if c[1] == hint]
        if typed:
            return typed[0]
    return sorted(cands)[0]

rows = list(csv.reader(open(SRC, encoding='cp949')))
data = [r for r in rows[1:] if len(r) >= 5 and r[2].strip()]
firms, dan_list, dan_idx = [], [], {}
n_miss = 0
miss_names = {}
for r in data:
    firm, dan, prod = r[1].strip(), r[2].strip(), r[3].strip()
    tgt = resolve(dan)
    if not tgt:
        n_miss += 1
        miss_names[dan] = miss_names.get(dan, 0) + 1
        continue
    key = tgt
    if key not in dan_idx:
        dan_idx[key] = len(dan_list)
        dan_list.append([tgt[0], tgt[1]])
    firms.append([firm, dan_idx[key], prod[:24]])

out = {'generated': GEN, 'basis': '전국등록공장현황 2024-12-31 (FactoryOn 등록분)',
       'n_source': len(data), 'n_matched': len(firms), 'n_unmatched': n_miss,
       'dans': dan_list, 'firms': firms}
fo = os.path.join(SITE, 'data_v4', 'ind_firms.json.gz')
raw = json.dumps(out, ensure_ascii=False, separators=(',', ':')).encode('utf-8')
with gzip.open(fo + '.tmp', 'wb', compresslevel=9) as z:
    z.write(raw)
os.replace(fo + '.tmp', fo)
print(f"ind_firms.json.gz: {os.path.getsize(fo)/1e6:,.1f} MB — 기업 {len(firms):,}"
      f" / 원천(산단 입주) {len(data):,} · 미매칭 {n_miss:,}행")
print('미매칭 상위:', sorted(miss_names.items(), key=lambda x: -x[1])[:8])

wcon = duckdb.connect(os.path.join(LR, 'agrivoltaic_ledger_v1.duckdb'))
wcon.execute("DELETE FROM meta_versions WHERE tbl='ind_firms'")
wcon.execute("INSERT INTO meta_versions VALUES (?,?,?,?)",
             ['ind_firms', datetime.datetime.now().strftime('%Y-%m-%d'),
              f'한국산업단지공단 전국등록공장현황(2024-12-31, data.go.kr 15105482) — 산단 입주 {len(data):,}사 중 '
              f'{len(firms):,}사를 경계 단지명과 대조(별칭·유형 힌트), 기업명 검색 표기용(판정 불사용). '
              f'원시 sources/ind_complex/firms', 'L0'])
wcon.close()
print('meta_versions 등재')
