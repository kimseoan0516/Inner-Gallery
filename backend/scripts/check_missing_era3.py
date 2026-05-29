import json, re, sys
sys.stdout.reconfigure(encoding='utf-8')

db = json.load(open('backend/data/artwork_era_db.json', encoding='utf-8'))

def norm(s):
    return re.sub(r'[^\w\s]', '', s.lower()).strip()

era_set = set()
for a in db['artworks']:
    era_set.add(norm(a['title']))
    era_set.add(a['artwork_id'])
    for alias in a.get('title_aliases', []):
        era_set.add(norm(alias))

js = open('frontend/src/data/artworks.js', encoding='utf-8').read()

# 각 라인에서 id와 title을 추출 (같은 줄에 있음)
entries = []
for line in js.split('\n'):
    line = line.strip()
    if not line.startswith('{ id:'):
        continue
    mid = re.search(r'id:\s*"([^"]+)"', line)
    mtitle = re.search(r'title:\s*"([^"]+)"', line)
    if mid and mtitle:
        entries.append((mid.group(1), mtitle.group(1)))

missing = []
for aid, title in entries:
    t = norm(title)
    aid_norm = aid  # artwork_id도 체크
    if t in era_set or aid_norm in era_set:
        pass  # matched
    else:
        missing.append((aid, title))

print(f"artworks.js 총 {len(entries)}개")
print(f"era DB 총 {len(db['artworks'])}개")
print(f"누락: {len(missing)}개\n")
for aid, t in missing:
    print(f"  {aid}: {t}")
