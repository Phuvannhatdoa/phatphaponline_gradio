"""
ETL: Xây dựng bảng Authority Nhân Vật Việt Nam (vn_person_authority) từ 16 file TTL thiền sư.

Lưu đồ:
  data/ttl/old/*.ttl  --(rdflib parse)-->  vn_person_authority
                                           vn_person_relations (thầy/trò/nhân vật liên quan)
                                           vn_person_places    (địa danh liên quan)
                                           vn_person_works     (tác phẩm)
                                           vn_person_events    (sự kiện đời/năm)

Hai định dạng TTL được xử lý tự động:
  1. Định dạng giàu (TS-Bach-Van-Thu-Doan, TS-Dai-Hue-Tong-Cao...):
     - Tên qua crm:P1_is_identified_by / E41_Appellation + bkg:hasAppellationType
     - Năm sinh/tử qua crm:E67_Birth / crm:E69_Death + crm:P4_has_time-span
     - Có bkg:associatedPlaces, bkg:authoredWorks, bkg:hasKeyLifeEvent, bkg:hasContribution, bkg:hasPhilosophicalStance, bkg:hasRelatedFigure
  2. Định dạng dòng phái (TS-Thiet-Dinh-An-Triem, Ton-Gia-Dao-Tin...):
     - Năm sinh/tử qua bkg:BirthEvent / bkg:DeathEvent + bkg:year
     - Có bkg:hasTeacher, bkg:hasDisciple, bkg:generationOrder, bkg:isLineageFounder

Usage:
    python scripts/etl_ttl_person_authority.py
"""

import json
import os
import re
import sqlite3
import time

import rdflib
from rdflib import BNode, URIRef
from rdflib.namespace import RDF, RDFS

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, 'data')
TTL_DIR = os.path.join(DATA_DIR, 'ttl', 'old')
DB_PATH = os.path.join(DATA_DIR, 'lineage.db')

# Namespaces sử dụng trong file TTL
BKG = rdflib.Namespace('http://www.phatphaponline.org/ontology/buddhist-kg#')
CRM = rdflib.Namespace('http://www.cidoc-crm.org/cidoc-crm/')
# Chú ý: thuộc tính namespace của rdflib KHÔNG tự chuyển "_" thành "-",
# nên dùng URIRef trực tiếp cho predicate có dấu gạch ngang.
CRM_P4_HAS_TIME_SPAN = URIRef('http://www.cidoc-crm.org/cidoc-crm/P4_has_time-span')


def get_conn():
    """Mở kết nối SQLite với row_factory."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def local_name(uri):
    """Lấy phần tên rút gọn của URI (ví dụ: ex:monk/dai_hue_tong_cao -> dai_hue_tong_cao)."""
    s = str(uri)
    return s.rsplit('/', 1)[-1]


def extract_year(literal):
    """Trích năm (int) từ literal thời gian. Trả None nếu không hợp lệ."""
    try:
        text = str(literal).strip()
        # Lọc lấy chuỗi số (hỗ trợ "1089", "1140", "1712")
        digits = ''.join(ch for ch in text if ch.isdigit())
        if digits:
            return int(digits)
    except Exception:
        pass
    return None


class TTLMonkParser:
    """Parse một file TTL và trích xuất dữ liệu nhân vật cùng các bảng phụ trợ."""

    def __init__(self, graph, filename):
        self.g = graph
        self.filename = filename
        self.person = {}
        self.relations = []
        self.places = []
        self.works = []
        self.events = []

    def label_of(self, node):
        """Lấy nhãn tiếng Việt của node (rdfs:label @vi), fallback nhãn bất kỳ."""
        labels = list(self.g.objects(node, RDFS.label))
        for l in labels:
            if getattr(l, 'language', None) == 'vi':
                return str(l)
        if labels:
            return str(labels[0])
        return ''

    def parse(self):
        """Parse toàn bộ graph, đưa kết quả vào các thuộc tính của class."""
        # Tìm node chính: subject có kiểu bkg:Monk
        monks = list(self.g.subjects(RDF.type, BKG.Monk))
        if not monks:
            # Một số file dòng phái không khai báo rõ; dùng node có rdfs:label @vi và hasTeacher/hasDisciple
            for s in self.g.subjects(BKG.hasTeacher, None):
                monks.append(s)
                break
        if not monks:
            # File Tôn Giả Đạo Tín: không có hasTeacher, dùng node có isLineageFounder
            for s in self.g.subjects(BKG.isLineageFounder, None):
                monks.append(s)
                break
        if not monks:
            print(f"  [CẢNH BÁO] Không tìm thấy node Monk trong {self.filename}")
            return

        monk = monks[0]
        slug = local_name(monk)
        self.person = {
            'id': slug,
            'ttl_filename': self.filename,
            'name_vi': self.label_of(monk),
            'name_zh': '',
            'dharma_title': '',
            'dharma_lineage': str(self.g.value(monk, BKG.dharmaLineageName, default='') or '').strip(),
            'generation_order': None,
            'is_lineage_founder': 0,
            'gender': '',
            'biographical_note_vi': str(self.g.value(monk, BKG.biographicalNote, default='') or '').strip(),
            'birth_year': None,
            'death_year': None,
            'appellations': [],
            'status': 'pending',
        }

        # --- Giới tính (có thể là URIRef <bkg:Male> hoặc literal "bkg:Male") ---
        gender = self.g.value(monk, BKG.gender)
        if gender is not None:
            self.person['gender'] = local_name(gender)
            if ':' in self.person['gender']:
                self.person['gender'] = self.person['gender'].rsplit(':', 1)[-1]

        # --- Thứ tự thế hệ & sáng lập dòng ---
        gen = self.g.value(monk, BKG.generationOrder)
        if gen is not None:
            try:
                self.person['generation_order'] = int(str(gen))
            except (TypeError, ValueError):
                pass
        founder = self.g.value(monk, BKG.isLineageFounder)
        if founder is not None:
            self.person['is_lineage_founder'] = 1 if str(founder).lower() in ('true', '1') else 0

        # --- Danh hiệu (appellation) ---
        for app in self.g.objects(monk, CRM.P1_is_identified_by):
            if isinstance(app, BNode):
                label = self.label_of(app)
                app_type = str(self.g.value(app, BKG.hasAppellationType, default='') or '').strip()
                # Giá trị appellation type là literal dạng "bkg:DharmaName" -> rút gọn "DharmaName"
                app_kind = app_type.rsplit(':', 1)[-1] if app_type else ''
                lang = getattr(self.g.value(app, RDFS.label, default=None), 'language', '')
                if not label:
                    continue
                self.person['appellations'].append({
                    'label': label,
                    'lang': lang,
                    'type': app_kind,
                })
                # Đặt name_zh / dharma_title cho cột tiện truy vấn
                if not self.person['name_zh'] and lang == 'zh':
                    self.person['name_zh'] = label
                if not self.person['dharma_title'] and app_kind == 'DharmaTitle':
                    self.person['dharma_title'] = label

        # --- Quan hệ: thầy / trò / nhân vật liên quan ---
        for pred, rel_type in ((BKG.hasTeacher, 'hasTeacher'),
                               (BKG.hasDisciple, 'hasDisciple'),
                               (BKG.hasRelatedFigure, 'hasRelatedFigure')):
            for target in self.g.objects(monk, pred):
                self.relations.append({
                    'person_id': slug,
                    'relation_type': rel_type,
                    'target_id': local_name(target),
                    'target_label_vi': self.label_of(target),
                    'ttl_filename': self.filename,
                })

        # --- Địa danh liên quan ---
        for place in self.g.objects(monk, BKG.associatedPlaces):
            place_type = str(self.g.value(place, BKG.placeType, default='') or '').strip()
            # Giá trị placeType là chuỗi literal dạng "bkg:Monastery" -> rút gọn thành "Monastery"
            if ':' in place_type:
                place_type = place_type.rsplit(':', 1)[-1]
            self.places.append({
                'person_id': slug,
                'place_id': local_name(place),
                'place_label_vi': self.label_of(place),
                'place_type': local_name(place_type) if place_type else '',
                'ttl_filename': self.filename,
            })

        # --- Tác phẩm ---
        for work in self.g.objects(monk, BKG.authoredWorks):
            self.works.append({
                'person_id': slug,
                'work_id': local_name(work),
                'work_title_vi': self.label_of(work),
                'ttl_filename': self.filename,
            })

        # --- Sự kiện: sinh, tử, sự kiện đời, đóng góp, lập trường ---
        # 1. Sinh/tử (định dạng giàu: crm:E67_Birth / crm:E69_Death + P4_has_time-span)
        birth_event = self.g.value(monk, BKG.birthEvent)
        death_event = self.g.value(monk, BKG.deathEvent)
        if birth_event is not None:
            self.person['birth_year'] = extract_year(self.g.value(birth_event, CRM_P4_HAS_TIME_SPAN))
            # Định dạng dòng phái dùng bkg:year
            if self.person['birth_year'] is None:
                self.person['birth_year'] = extract_year(self.g.value(birth_event, BKG.year))
            self.events.append({
                'person_id': slug, 'event_type': 'Birth',
                'event_id': local_name(birth_event),
                'event_label_vi': '', 'event_year': self.person['birth_year'],
                'ttl_filename': self.filename,
            })
        if death_event is not None:
            self.person['death_year'] = extract_year(self.g.value(death_event, CRM_P4_HAS_TIME_SPAN))
            if self.person['death_year'] is None:
                self.person['death_year'] = extract_year(self.g.value(death_event, BKG.year))
            self.events.append({
                'person_id': slug, 'event_type': 'Death',
                'event_id': local_name(death_event),
                'event_label_vi': '', 'event_year': self.person['death_year'],
                'ttl_filename': self.filename,
            })

        # 2. Sự kiện chính / đóng góp / lập trường triết học (có nhãn)
        for pred, ev_type in ((BKG.hasKeyLifeEvent, 'KeyLifeEvent'),
                              (BKG.hasContribution, 'Contribution'),
                              (BKG.hasPhilosophicalStance, 'PhilosophicalStance')):
            for ev in self.g.objects(monk, pred):
                year = extract_year(self.g.value(ev, CRM_P4_HAS_TIME_SPAN))
                if year is None:
                    year = extract_year(self.g.value(ev, BKG.year))
                self.events.append({
                    'person_id': slug, 'event_type': ev_type,
                    'event_id': local_name(ev),
                    'event_label_vi': self.label_of(ev), 'event_year': year,
                    'ttl_filename': self.filename,
                })


SCHEMA = """
-- Bảng Authority nhân vật (SSOT cho nhân vật thiền sư Việt Nam)
CREATE TABLE IF NOT EXISTS vn_person_authority (
    id TEXT PRIMARY KEY,
    ttl_filename TEXT NOT NULL,
    name_vi TEXT,
    name_zh TEXT,
    dharma_title TEXT,
    dharma_lineage TEXT,
    generation_order INTEGER,
    is_lineage_founder INTEGER DEFAULT 0,
    gender TEXT,
    biographical_note_vi TEXT,
    birth_year INTEGER,
    death_year INTEGER,
    appellations TEXT,
    dila_id TEXT,
    status TEXT DEFAULT 'pending',
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- Quan hệ giữa các nhân vật (thầy/trò/nhân vật liên quan)
CREATE TABLE IF NOT EXISTS vn_person_relations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    person_id TEXT NOT NULL,
    relation_type TEXT NOT NULL,
    target_id TEXT,
    target_label_vi TEXT,
    ttl_filename TEXT,
    UNIQUE(person_id, relation_type, target_id)
);

-- Địa danh liên quan đến nhân vật
CREATE TABLE IF NOT EXISTS vn_person_places (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    person_id TEXT NOT NULL,
    place_id TEXT NOT NULL,
    place_label_vi TEXT,
    place_type TEXT,
    ttl_filename TEXT,
    UNIQUE(person_id, place_id)
);

-- Tác phẩm do nhân vật trước tác
CREATE TABLE IF NOT EXISTS vn_person_works (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    person_id TEXT NOT NULL,
    work_id TEXT NOT NULL,
    work_title_vi TEXT,
    ttl_filename TEXT,
    UNIQUE(person_id, work_id)
);

-- Sự kiện trong đời nhân vật (sinh/tử/sự kiện chính/đóng góp/lập trường)
CREATE TABLE IF NOT EXISTS vn_person_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    person_id TEXT NOT NULL,
    event_type TEXT NOT NULL,
    event_id TEXT,
    event_label_vi TEXT,
    event_year INTEGER,
    ttl_filename TEXT,
    UNIQUE(person_id, event_type, event_id)
);

CREATE INDEX IF NOT EXISTS idx_vn_person_rel_person ON vn_person_relations(person_id);
CREATE INDEX IF NOT EXISTS idx_vn_person_places_person ON vn_person_places(person_id);
CREATE INDEX IF NOT EXISTS idx_vn_person_works_person ON vn_person_works(person_id);
CREATE INDEX IF NOT EXISTS idx_vn_person_events_person ON vn_person_events(person_id);
"""


def main():
    start = time.time()
    conn = get_conn()
    conn.executescript(SCHEMA)

    # Đọc ttl_mapping để gắn dila_id cho nhân vật đã xác minh
    dila_map = {}
    for r in conn.execute("SELECT ttl_filename, dila_id FROM ttl_mapping WHERE dila_id IS NOT NULL"):
        dila_map[r['ttl_filename']] = r['dila_id']

    ttl_files = sorted(f for f in os.listdir(TTL_DIR) if f.endswith('.ttl'))
    if not ttl_files:
        print(f"Không tìm thấy file TTL nào trong {TTL_DIR}")
        return

    print(f"Tìm thấy {len(ttl_files)} file TTL trong {TTL_DIR}\n")

    # Reset dữ liệu cũ (idempotent)
    for t in ('vn_person_events', 'vn_person_works', 'vn_person_places',
              'vn_person_relations', 'vn_person_authority'):
        conn.execute(f"DELETE FROM {t}")
    conn.commit()

    people = []
    all_relations = []
    all_places = []
    all_works = []
    all_events = []

    for fname in ttl_files:
        path = os.path.join(TTL_DIR, fname)
        key = fname[:-4]  # bỏ đuôi .ttl
        print(f"Parsing {fname} ...")
        try:
            g = rdflib.Graph()
            g.parse(path, format='turtle')
            parser = TTLMonkParser(g, key)
            parser.parse()
            if not parser.person:
                continue

            person = parser.person
            person['dila_id'] = dila_map.get(key, '')
            person['appellations'] = json.dumps(person['appellations'], ensure_ascii=False)

            # Ghi chú: sinh/tử có trong note nhưng không có event -> thử trích nhanh (1089-1163 / 1712–1789)
            if person['birth_year'] is None and person['death_year'] is None \
                    and person['biographical_note_vi']:
                note = person['biographical_note_vi']
                # Ưu tiên bắt cặp khoảng năm dạng "1089-1163" hoặc "(1025-1072)"
                m = re.search(r'(\d{3,4})\s*[-–]\s*(\d{3,4})', note)
                if m:
                    by, dy = int(m.group(1)), int(m.group(2))
                    if 700 <= by <= 2025 and 700 <= dy <= 2025:
                        person['birth_year'] = by
                        person['death_year'] = dy
                if person['birth_year'] is None:
                    years = [int(x) for x in note.split()
                             if x.isdigit() and 700 <= int(x) <= 2025]
                    if years:
                        person['birth_year'] = min(years)
                        person['death_year'] = max(years) if max(years) != person['birth_year'] else None

            people.append(person)
            all_relations.extend(parser.relations)
            all_places.extend(parser.places)
            all_works.extend(parser.works)
            all_events.extend(parser.events)
            print(f"  -> {person['name_vi']} (sinh {person['birth_year']}, tử {person['death_year']}, "
                  f"{len(parser.relations)} quan hệ, {len(parser.places)} địa danh, "
                  f"{len(parser.works)} tác phẩm, {len(parser.events)} sự kiện)")
        except Exception as e:
            print(f"  [LỖI] {fname}: {e}")

    # --- Ghi vào DB ---
    print("\n--- Ghi vào vn_person_authority ---")
    p_count = 0
    for p in people:
        try:
            conn.execute(
                """INSERT OR REPLACE INTO vn_person_authority
                   (id, ttl_filename, name_vi, name_zh, dharma_title, dharma_lineage,
                    generation_order, is_lineage_founder, gender, biographical_note_vi,
                    birth_year, death_year, appellations, dila_id, status)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (p['id'], p['ttl_filename'], p['name_vi'], p['name_zh'], p['dharma_title'],
                 p['dharma_lineage'], p['generation_order'], p['is_lineage_founder'],
                 p['gender'], p['biographical_note_vi'], p['birth_year'], p['death_year'],
                 p['appellations'], p['dila_id'], p['status'])
            )
            p_count += 1
        except Exception as e:
            print(f"  [LỖI] insert person {p['id']}: {e}")

    def insert_many(table, cols, rows):
        n = 0
        placeholders = ','.join(['?'] * len(cols))
        for r in rows:
            try:
                conn.execute(f"INSERT OR IGNORE INTO {table} ({','.join(cols)}) VALUES ({placeholders})",
                             tuple(r[c] for c in cols))
                n += 1
            except Exception as e:
                print(f"  [LỖI] insert {table}: {e}")
        return n

    print("--- Ghi vn_person_relations ---")
    r_count = insert_many('vn_person_relations',
                          ['person_id', 'relation_type', 'target_id', 'target_label_vi', 'ttl_filename'],
                          all_relations)
    print("--- Ghi vn_person_places ---")
    pl_count = insert_many('vn_person_places',
                           ['person_id', 'place_id', 'place_label_vi', 'place_type', 'ttl_filename'],
                           all_places)
    print("--- Ghi vn_person_works ---")
    w_count = insert_many('vn_person_works',
                          ['person_id', 'work_id', 'work_title_vi', 'ttl_filename'],
                          all_works)
    print("--- Ghi vn_person_events ---")
    e_count = insert_many('vn_person_events',
                          ['person_id', 'event_type', 'event_id', 'event_label_vi', 'event_year', 'ttl_filename'],
                          all_events)

    conn.commit()

    elapsed = time.time() - start
    print(f"\n=== KẾT QUẢ ===")
    print(f"  vn_person_authority : {p_count} nhân vật")
    print(f"  vn_person_relations : {r_count} quan hệ")
    print(f"  vn_person_places    : {pl_count} địa danh")
    print(f"  vn_person_works     : {w_count} tác phẩm")
    print(f"  vn_person_events    : {e_count} sự kiện")
    print(f"  Thời gian           : {elapsed:.1f}s")
    conn.close()


if __name__ == '__main__':
    main()
