import json, sys
sys.stdout.reconfigure(encoding='utf-8')

DB_PATH = 'backend/data/artwork_era_db.json'
db = json.load(open(DB_PATH, encoding='utf-8'))

# 제거할 중복 ID (내용이 적은 쪽)
remove_ids = {
    'one_number_31',                # no_31 (원본, 내용 풍부) 유지
    'a_sunday_afternoon_grande_jatte',  # a_sunday_on_la_grande_jatte (원본) 유지
    'where_do_we_come_from',        # where_do_we_come_from_what_are_we_where_are_we_going (원본) 유지
}

before = len(db['artworks'])
db['artworks'] = [a for a in db['artworks'] if a['artwork_id'] not in remove_ids]
after = len(db['artworks'])
print(f"중복 제거: {before} → {after}개 ({before - after}개 삭제)")

# 호쿠사이 나이 수정 (90세 → 88~89세)
fixed = 0
for a in db['artworks']:
    if a.get('artwork_id') == 'the_great_wave':
        if '90세 생애' in a.get('artist_context', ''):
            a['artist_context'] = a['artist_context'].replace('90세 생애', '88~89세 생애')
            fixed += 1
            print("호쿠사이 나이 수정 완료")

open(DB_PATH, 'w', encoding='utf-8').write(json.dumps(db, ensure_ascii=False, indent=2))
print(f"저장 완료. 최종 artworks 수: {len(db['artworks'])}")
