import json, re, sys
sys.stdout.reconfigure(encoding='utf-8')

DB_PATH = 'backend/data/artwork_era_db.json'
db = json.load(open(DB_PATH, encoding='utf-8'))

def norm(s):
    return re.sub(r'[^\w\s]', '', s.lower()).strip()

era_set = set()
for a in db['artworks']:
    era_set.add(norm(a['title']))
    era_set.add(a['artwork_id'])
    for alias in a.get('title_aliases', []):
        era_set.add(norm(alias))

js = open('frontend/src/data/artworks.js', encoding='utf-8').read()

# 각 라인에서 id, title, artist 추출
entries = []
for line in js.split('\n'):
    line = line.strip()
    if not line.startswith('{ id:'):
        continue
    mid    = re.search(r'id:\s*"([^"]+)"', line)
    mtitle = re.search(r'title:\s*"([^"]+)"', line)
    martist = re.search(r'artist:\s*"([^"]+)"', line)
    if mid and mtitle and martist:
        entries.append((mid.group(1), mtitle.group(1), martist.group(1)))

added = 0
for aid, title, artist in entries:
    if norm(title) in era_set or aid in era_set:
        continue
    skeleton = {
        "artwork_id": aid,
        "title": title,
        "title_aliases": [],
        "artist": artist,
        "art_movement": "",
        "creation_period": "",
        "historical_context": "",
        "artist_context": "",
        "visual_connection": "",
        "confidence": "pending",
        "sources": ["curated_db"]
    }
    db['artworks'].append(skeleton)
    era_set.add(aid)
    era_set.add(norm(title))
    added += 1
    print(f"Added skeleton: {aid}")

open(DB_PATH, 'w', encoding='utf-8').write(json.dumps(db, ensure_ascii=False, indent=2))
print(f"\nDone. Added {added} skeletons. Total: {len(db['artworks'])}")
