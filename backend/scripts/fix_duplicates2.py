import json, sys
sys.stdout.reconfigure(encoding='utf-8')

DB_PATH = 'backend/data/artwork_era_db.json'
db = json.load(open(DB_PATH, encoding='utf-8'))

# 제거할 중복 ID (내용이 적은 쪽 삭제, 원본 유지)
remove_ids = {
    'the_third_of_may',       # the_third_of_may_1808 (원본) 유지
    'guernica_picasso',       # guernica (원본) 유지
    'the_kiss_klimt',         # the_kiss (원본) 유지
    'the_son_of_man_magritte', # the_son_of_man (원본) 유지
}

before = len(db['artworks'])
db['artworks'] = [a for a in db['artworks'] if a['artwork_id'] not in remove_ids]
after = len(db['artworks'])
print(f"중복 제거: {before} → {after}개 ({before - after}개 삭제)")
for rid in remove_ids:
    print(f"  삭제: {rid}")

open(DB_PATH, 'w', encoding='utf-8').write(json.dumps(db, ensure_ascii=False, indent=2))
print(f"\n저장 완료. 최종 artworks 수: {len(db['artworks'])}")
