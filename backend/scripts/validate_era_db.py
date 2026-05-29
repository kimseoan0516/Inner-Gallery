"""
era DB 무결성 검증 스크립트
실행: python backend/scripts/validate_era_db.py
"""
import json, re, sys
sys.stdout.reconfigure(encoding='utf-8')

DB_PATH = 'backend/data/artwork_era_db.json'
db = json.load(open(DB_PATH, encoding='utf-8'))
artworks = db['artworks']

issues = []

# 1. artwork_id 중복 체크
ids = [a['artwork_id'] for a in artworks]
seen = set()
for aid in ids:
    if aid in seen:
        issues.append(f'[중복 ID] {aid}')
    seen.add(aid)

# 2. title 중복 체크 (대소문자 무시)
def norm(s): return re.sub(r'[^\w]', '', s.lower())
title_map = {}
for a in artworks:
    t = norm(a['title'])
    if t in title_map:
        issues.append(f'[중복 title] "{a["title"]}" → {a["artwork_id"]} vs {title_map[t]}')
    title_map[t] = a['artwork_id']

# 3. artist 필드 누락 체크 (비어있는 경우만)
for a in artworks:
    if a.get('confidence') == 'verified' and not a.get('artist', '').strip():
        issues.append(f'[artist 필드 비어있음] {a["artwork_id"]}')

# 4. verified인데 핵심 필드 비어있는 경우
for a in artworks:
    if a.get('confidence') == 'verified':
        for field in ['art_movement', 'creation_period', 'historical_context', 'artist_context', 'visual_connection']:
            if not a.get(field, '').strip():
                issues.append(f'[verified 빈 필드] {a["artwork_id"]}: {field}')

# 결과 출력
print(f'총 {len(artworks)}개 검사')
print(f'이슈 {len(issues)}건\n')
if issues:
    for i in issues:
        print(f'  {i}')
else:
    print('  이상 없음 ✓')
