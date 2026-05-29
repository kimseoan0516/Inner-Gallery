"""era_db에 스켈레톤 항목 추가 — artworks.js에 있지만 era_db에 없는 현대미술 29개"""
import json

SKELETONS = [
    {
        "artwork_id": "pollock_number31",
        "title": "One: Number 31",
        "title_aliases": ["number 31", "no 31", "넘버 31", "action painting"],
        "artist": "Jackson Pollock",
        "art_movement": "",
        "creation_period": "",
        "historical_context": "",
        "artist_context": "",
        "visual_connection": "",
        "confidence": "pending",
        "sources": ["curated_db"]
    },
    {
        "artwork_id": "pollock_lavender_mist",
        "title": "Lavender Mist: Number 1",
        "title_aliases": ["lavender mist", "라벤더 미스트", "lavender fog"],
        "artist": "Jackson Pollock",
        "art_movement": "",
        "creation_period": "",
        "historical_context": "",
        "artist_context": "",
        "visual_connection": "",
        "confidence": "pending",
        "sources": ["curated_db"]
    },
    {
        "artwork_id": "warhol_soup_cans",
        "title": "Campbell's Soup Cans",
        "title_aliases": ["soup cans", "campbell", "캠벨", "수프 캔"],
        "artist": "Andy Warhol",
        "art_movement": "",
        "creation_period": "",
        "historical_context": "",
        "artist_context": "",
        "visual_connection": "",
        "confidence": "pending",
        "sources": ["curated_db"]
    },
    {
        "artwork_id": "rothko_no61",
        "title": "No. 61 (Rust and Blue)",
        "title_aliases": ["no 61", "rust and blue", "녹과 파랑", "로스코"],
        "artist": "Mark Rothko",
        "art_movement": "",
        "creation_period": "",
        "historical_context": "",
        "artist_context": "",
        "visual_connection": "",
        "confidence": "pending",
        "sources": ["curated_db"]
    },
    {
        "artwork_id": "rothko_orange_yellow",
        "title": "Orange and Yellow",
        "title_aliases": ["orange yellow", "오렌지 노랑", "color field"],
        "artist": "Mark Rothko",
        "art_movement": "",
        "creation_period": "",
        "historical_context": "",
        "artist_context": "",
        "visual_connection": "",
        "confidence": "pending",
        "sources": ["curated_db"]
    },
    {
        "artwork_id": "okeeffe_black_iris",
        "title": "Black Iris",
        "title_aliases": ["black iris", "검은 붓꽃", "검은 아이리스"],
        "artist": "Georgia O'Keeffe",
        "art_movement": "",
        "creation_period": "",
        "historical_context": "",
        "artist_context": "",
        "visual_connection": "",
        "confidence": "pending",
        "sources": ["curated_db"]
    },
    {
        "artwork_id": "koons_michael_jackson",
        "title": "Michael Jackson and Bubbles",
        "title_aliases": ["michael jackson koons", "마이클 잭슨 쿤스", "bubbles koons"],
        "artist": "Jeff Koons",
        "art_movement": "",
        "creation_period": "",
        "historical_context": "",
        "artist_context": "",
        "visual_connection": "",
        "confidence": "pending",
        "sources": ["curated_db"]
    },
    {
        "artwork_id": "hirst_spot_painting",
        "title": "Spot Paintings",
        "title_aliases": ["spot painting", "점 그림", "pharmaceutical paintings", "hirst dots"],
        "artist": "Damien Hirst",
        "art_movement": "",
        "creation_period": "",
        "historical_context": "",
        "artist_context": "",
        "visual_connection": "",
        "confidence": "pending",
        "sources": ["curated_db"]
    },
    {
        "artwork_id": "murakami_dob",
        "title": "Mr. DOB",
        "title_aliases": ["mr dob", "미스터 DOB", "슈퍼플랫", "superflat character"],
        "artist": "Takashi Murakami",
        "art_movement": "",
        "creation_period": "",
        "historical_context": "",
        "artist_context": "",
        "visual_connection": "",
        "confidence": "pending",
        "sources": ["curated_db"]
    },
    {
        "artwork_id": "aiweiwei_remembering",
        "title": "Remembering",
        "title_aliases": ["remembering", "기억하기", "backpacks installation", "배낭 설치"],
        "artist": "Ai Weiwei",
        "art_movement": "",
        "creation_period": "",
        "historical_context": "",
        "artist_context": "",
        "visual_connection": "",
        "confidence": "pending",
        "sources": ["curated_db"]
    },
    {
        "artwork_id": "aiweiwei_forever_bicycles",
        "title": "Forever Bicycles",
        "title_aliases": ["forever bicycles", "자전거 설치", "bicycle installation", "영원한 자전거"],
        "artist": "Ai Weiwei",
        "art_movement": "",
        "creation_period": "",
        "historical_context": "",
        "artist_context": "",
        "visual_connection": "",
        "confidence": "pending",
        "sources": ["curated_db"]
    },
    {
        "artwork_id": "close_phil",
        "title": "Phil",
        "title_aliases": ["phil close", "필 클로스", "photorealism portrait"],
        "artist": "Chuck Close",
        "art_movement": "",
        "creation_period": "",
        "historical_context": "",
        "artist_context": "",
        "visual_connection": "",
        "confidence": "pending",
        "sources": ["curated_db"]
    },
    {
        "artwork_id": "sherman_history_portraits",
        "title": "History Portraits",
        "title_aliases": ["history portraits", "역사 초상", "history portraits sherman"],
        "artist": "Cindy Sherman",
        "art_movement": "",
        "creation_period": "",
        "historical_context": "",
        "artist_context": "",
        "visual_connection": "",
        "confidence": "pending",
        "sources": ["curated_db"]
    },
    {
        "artwork_id": "saville_plan",
        "title": "Plan",
        "title_aliases": ["plan saville", "플랜", "body map painting"],
        "artist": "Jenny Saville",
        "art_movement": "",
        "creation_period": "",
        "historical_context": "",
        "artist_context": "",
        "visual_connection": "",
        "confidence": "pending",
        "sources": ["curated_db"]
    },
    {
        "artwork_id": "doig_blotter",
        "title": "Blotter",
        "title_aliases": ["blotter doig", "블로터", "figure lake", "호수 인물"],
        "artist": "Peter Doig",
        "art_movement": "",
        "creation_period": "",
        "historical_context": "",
        "artist_context": "",
        "visual_connection": "",
        "confidence": "pending",
        "sources": ["curated_db"]
    },
    {
        "artwork_id": "doig_echo_lake",
        "title": "Echo Lake",
        "title_aliases": ["echo lake doig", "에코 호수", "에코레이크"],
        "artist": "Peter Doig",
        "art_movement": "",
        "creation_period": "",
        "historical_context": "",
        "artist_context": "",
        "visual_connection": "",
        "confidence": "pending",
        "sources": ["curated_db"]
    },
    {
        "artwork_id": "baselitz_eagle",
        "title": "Adler (Eagle)",
        "title_aliases": ["eagle baselitz", "독수리", "adler", "inverted eagle", "거꾸로 그림"],
        "artist": "George Baselitz",
        "art_movement": "",
        "creation_period": "",
        "historical_context": "",
        "artist_context": "",
        "visual_connection": "",
        "confidence": "pending",
        "sources": ["curated_db"]
    },
    {
        "artwork_id": "beuys_fat_chair",
        "title": "Fat Chair",
        "title_aliases": ["fat chair", "지방 의자", "fettstuhl", "보이스 의자"],
        "artist": "Joseph Beuys",
        "art_movement": "",
        "creation_period": "",
        "historical_context": "",
        "artist_context": "",
        "visual_connection": "",
        "confidence": "pending",
        "sources": ["curated_db"]
    },
    {
        "artwork_id": "abramovic_rhythm_0",
        "title": "Rhythm 0",
        "title_aliases": ["rhythm 0", "리듬 0", "ritmo 0", "abramovic performance"],
        "artist": "Marina Abramović",
        "art_movement": "",
        "creation_period": "",
        "historical_context": "",
        "artist_context": "",
        "visual_connection": "",
        "confidence": "pending",
        "sources": ["curated_db"]
    },
    {
        "artwork_id": "kruger_i_shop",
        "title": "Untitled (I Shop Therefore I Am)",
        "title_aliases": ["i shop therefore i am", "쇼핑 고로 존재", "kruger shop"],
        "artist": "Barbara Kruger",
        "art_movement": "",
        "creation_period": "",
        "historical_context": "",
        "artist_context": "",
        "visual_connection": "",
        "confidence": "pending",
        "sources": ["curated_db"]
    },
    {
        "artwork_id": "walker_gone",
        "title": "Gone: An Historical Romance",
        "title_aliases": ["gone historical romance", "실루엣", "walker silhouette", "slavery art"],
        "artist": "Kara Walker",
        "art_movement": "",
        "creation_period": "",
        "historical_context": "",
        "artist_context": "",
        "visual_connection": "",
        "confidence": "pending",
        "sources": ["curated_db"]
    },
    {
        "artwork_id": "wiley_napoleon",
        "title": "Napoleon Leading the Army over the Alps",
        "title_aliases": ["napoleon alps wiley", "알프스 나폴레옹 와일리", "wiley napoleon"],
        "artist": "Kehinde Wiley",
        "art_movement": "",
        "creation_period": "",
        "historical_context": "",
        "artist_context": "",
        "visual_connection": "",
        "confidence": "pending",
        "sources": ["curated_db"]
    },
    {
        "artwork_id": "paik_global_groove",
        "title": "Global Groove",
        "title_aliases": ["global groove", "글로벌 그루브", "백남준 비디오", "paik video"],
        "artist": "Nam June Paik",
        "art_movement": "",
        "creation_period": "",
        "historical_context": "",
        "artist_context": "",
        "visual_connection": "",
        "confidence": "pending",
        "sources": ["curated_db"]
    },
    {
        "artwork_id": "leeufan_with_winds",
        "title": "With Winds",
        "title_aliases": ["with winds", "바람과 함께", "이우환 바람", "lee ufan winds"],
        "artist": "Lee Ufan",
        "art_movement": "",
        "creation_period": "",
        "historical_context": "",
        "artist_context": "",
        "visual_connection": "",
        "confidence": "pending",
        "sources": ["curated_db"]
    },
    {
        "artwork_id": "tuymans_the_body",
        "title": "The Body",
        "title_aliases": ["the body tuymans", "몸 튀망", "figure painting tuymans"],
        "artist": "Luc Tuymans",
        "art_movement": "",
        "creation_period": "",
        "historical_context": "",
        "artist_context": "",
        "visual_connection": "",
        "confidence": "pending",
        "sources": ["curated_db"]
    },
    {
        "artwork_id": "rauch_die_furt",
        "title": "Die Furt",
        "title_aliases": ["die furt", "여울목", "rauch furt", "neue leipziger"],
        "artist": "Neo Rauch",
        "art_movement": "",
        "creation_period": "",
        "historical_context": "",
        "artist_context": "",
        "visual_connection": "",
        "confidence": "pending",
        "sources": ["curated_db"]
    },
    {
        "artwork_id": "polke_potato_house",
        "title": "Kartoffelhaus (Potato House)",
        "title_aliases": ["potato house", "감자 집", "kartoffelhaus", "polke potato"],
        "artist": "Sigmar Polke",
        "art_movement": "",
        "creation_period": "",
        "historical_context": "",
        "artist_context": "",
        "visual_connection": "",
        "confidence": "pending",
        "sources": ["curated_db"]
    },
    {
        "artwork_id": "dumas_dead_marilyn",
        "title": "Dead Marilyn",
        "title_aliases": ["dead marilyn dumas", "죽은 마릴린", "dumas marilyn"],
        "artist": "Marlene Dumas",
        "art_movement": "",
        "creation_period": "",
        "historical_context": "",
        "artist_context": "",
        "visual_connection": "",
        "confidence": "pending",
        "sources": ["curated_db"]
    },
    {
        "artwork_id": "suh_fallen_star",
        "title": "Fallen Star",
        "title_aliases": ["fallen star", "떨어진 별", "서도호 별", "suh installation"],
        "artist": "Do Ho Suh",
        "art_movement": "",
        "creation_period": "",
        "historical_context": "",
        "artist_context": "",
        "visual_connection": "",
        "confidence": "pending",
        "sources": ["curated_db"]
    },
]

with open('backend/data/artwork_era_db.json', encoding='utf-8') as f:
    data = json.load(f)

existing_ids = {a['artwork_id'] for a in data['artworks']}
added = 0
for sk in SKELETONS:
    if sk['artwork_id'] not in existing_ids:
        data['artworks'].append(sk)
        added += 1
        print(f'추가: {sk["artwork_id"]}')
    else:
        print(f'이미 존재 (스킵): {sk["artwork_id"]}')

with open('backend/data/artwork_era_db.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print(f'\n완료: {added}개 스켈레톤 추가 / 총 {len(data["artworks"])}개')
