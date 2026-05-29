import json, re, sys
sys.stdout.reconfigure(encoding='utf-8')

db = json.load(open('backend/data/artwork_era_db.json', encoding='utf-8'))
era_titles = set()
for a in db['artworks']:
    era_titles.add(a['title'].lower().strip())
    for alias in a.get('title_aliases', []):
        era_titles.add(alias.lower().strip())

js = open('frontend/src/data/artworks.js', encoding='utf-8').read()
ids    = re.findall(r'\{ id:\s*"([^"]+)"', js)
titles = re.findall(r'title:\s*"([^"]+)"', js)
# first title per entry (titleKo comes after)
# parse more carefully: get id+title pairs
entries = re.findall(r'\{ id:\s*"([^"]+)"[^}]+?title:\s*"([^"]+)"', js)

missing = []
for aid, title in entries:
    if title.lower().strip() not in era_titles:
        missing.append((aid, title))

print(f"artworks.js: {len(entries)}개")
print(f"era DB:      {len(db['artworks'])}개")
print(f"누락:        {len(missing)}개\n")
for aid, t in missing:
    print(f"  {aid}: {t}")
