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
    python scripts/etl_ttl_person_authority.py --db <fixture.db> --ttl-dir <scope> --out-dir <new-plan-dir>
    Mặc định dry-run; --mode apply explicit cần authorization và control schema riêng.
"""

import json
import os
import re
import sqlite3
import sys
import time

import rdflib
from rdflib import BNode, URIRef
from rdflib.namespace import RDF, RDFS

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, 'data')
TTL_DIR = os.path.join(DATA_DIR, 'ttl', 'old')
# [T217] Cho phép override DB path qua --db=<path> hoặc biến môi trường ETL_DB_PATH
# để test an toàn trên DB tạm thời mà không động đến production.
def _resolve_db_path():
    for arg in sys.argv[1:]:
        if arg.startswith('--db='):
            return arg[5:]
    env = os.environ.get('ETL_DB_PATH')
    if env:
        return env
    return os.path.join(DATA_DIR, 'lineage.db')

DB_PATH = _resolve_db_path()

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
    """Chỉ năm/date explicit; không gộp chữ số, không đoán range/min/max."""
    if literal is None:
        return None
    text = str(literal).strip()
    if re.fullmatch(r'-?\d{1,4}', text):
        return int(text)
    if re.fullmatch(r'\d{4}-\d{2}-\d{2}', text):
        from datetime import date
        try:
            return date.fromisoformat(text).year
        except ValueError:
            return None
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

        if len(set(monks)) != 1:
            raise ValueError('Không xác định duy nhất subject Monk: ' + self.filename)
        monk = monks[0]
        if not isinstance(monk, URIRef):
            raise ValueError('Subject Monk phải có URI ổn định')
        self.subject_uri = str(monk)
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
            except (TypeError, ValueError) as exc:
                raise ValueError('generationOrder không hợp lệ: ' + self.filename) from exc
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


def main(argv=None):
    """T357: giữ parser; thực thi qua safe engine, mặc định plan/read-only."""
    from t357_vnpa_safe_etl import cli
    return cli(argv)


if __name__ == "__main__":
    sys.exit(main())
