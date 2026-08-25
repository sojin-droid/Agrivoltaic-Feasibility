# -*- coding: utf-8 -*-
"""구획 GeoJSON 후처리 — 좌표 4자리(≈11m) 재양자화 + gzip. 285MB → 저장소 부담 축소.
지오메트리 재계산 없음(간소화 15m 유지). 산출: {sgg}_{cell}.json.gz, 원본 .json 삭제.
사용: python pipeline/compress_clusters.py"""
import os, sys, json, glob, gzip
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

SITE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CL = os.path.join(SITE, 'data_v4', 'clusters')

def rnd(cc):
    if isinstance(cc[0], list):
        return [rnd(x) for x in cc]
    return [round(cc[0], 4), round(cc[1], 4)]

before = after = 0
fs = sorted(glob.glob(os.path.join(CL, '*.json')))
for i, fp in enumerate(fs, 1):
    before += os.path.getsize(fp)
    d = json.load(open(fp, encoding='utf-8'))
    for f in d['features']:
        f['geometry']['coordinates'] = rnd(f['geometry']['coordinates'])
    raw = json.dumps(d, ensure_ascii=False, separators=(',', ':')).encode('utf-8')
    fo = fp + '.gz'
    with gzip.open(fo + '.tmp', 'wb', compresslevel=9) as z:
        z.write(raw)
    os.replace(fo + '.tmp', fo)
    after += os.path.getsize(fo)
    os.remove(fp)
    if i % 200 == 0 or i == len(fs):
        print(f"  [{i}/{len(fs)}] {before/1e6:,.0f} → {after/1e6:,.0f} MB", flush=True)
print(f"완료: {len(fs)}파일 {before/1e6:,.1f} MB → {after/1e6:,.1f} MB")
