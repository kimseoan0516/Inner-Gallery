import json, re, sys
sys.stdout.reconfigure(encoding='utf-8')

db = json.load(open('backend/data/artwork_era_db.json', encoding='utf-8'))

# era DB: title + 모든 alias를 소문자 정규화 set으로
def norm(s):
    return re.sub(r'[\s\-\'\",\.\!\?]+', ' ', s.lower()).strip()

era_set = set()
for a in db['artworks']:
    era_set.add(norm(a['title']))
    era_set.add(a['artwork_id'].replace('_', ' '))
    for alias in a.get('title_aliases', []):
        era_set.add(norm(alias))

# artworks.js 파싱 - id와 첫 번째 title만
js = open('frontend/src/data/artworks.js', encoding='utf-8').read()
# 각 엔트리: { id: "...", title: "...", titleKo: ...}
pattern = re.compile(r'\{\s*id:\s*"([^"]+)"[^\n]*\n\s*\?\s*\{[^\}]*\}|\{\s*id:\s*"([^"]+)".*?title:\s*"([^"]+)"', re.DOTALL)

# 더 간단하게: 한 줄씩 파싱
entries = []
current_id = None
for line in js.split('\n'):
    m = re.search(r'id:\s*"([^"]+)"', line)
    if m:
        current_id = m.group(1)
    m2 = re.search(r'^\s*\{.*?id:\s*"([^"]+)".*?title:\s*"([^"]+)"', line)
    if m2:
        entries.append((m2.group(1), m2.group(2)))

# title만 별도로
title_pattern = re.compile(r'\{\s*id:\s*"([^"]+)"[^,\n]*, title:\s*"([^"]+)"')
entries2 = title_pattern.findall(js)

missing = []
found = []
for aid, title in entries2:
    t = norm(title)
    # artwork_id slug도 체크
    slug = aid.replace('_', ' ')
    if t in era_set or slug in era_set:
        found.append((aid, title))
    else:
        missing.append((aid, title))

print(f"artworks.js 총 {len(entries2)}개")
print(f"era DB 총 {len(db['artworks'])}개")
print(f"매칭됨: {len(found)}개")
print(f"누락: {len(missing)}개\n")
for aid, t in sorted(missing):
    print(f"  {aid}: {t}")
