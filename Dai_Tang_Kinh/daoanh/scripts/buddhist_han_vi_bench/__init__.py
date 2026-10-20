# -*- coding: utf-8 -*-
"""BUDDHIST-HAN-VI-BENCH — benchmark CBETA Hán→Việt (T167 Phase 7).

Xây dựng 500 real CBETA passages (category-tagged, deterministic), tính metric
deterministic từ validator + data thật, cấu trúc chỗ trống cho metric CẦN người
duyệt (KHÔNG bịa benchmark score).

Phân nhánh trách nhiệm:
  - select   : chọn 500 passages thật, tag category → data/benchmark/buddhist_han_vi_bench.json
  - score    : chạy metric deterministic (validator A-G + glossary + place/name) → ..._scored.json
  - report   : tổng hợp markdown/JSON theo category + chỗ trống human metrics
  - human    : nhập điểm CON NGƯỜI (Semantic Fidelity, Doctrinal Fidelity, v.v.) → ..._human.json

Usage:
  python -m scripts.buddhist_han_vi_bench select [--out PATH] [--size 500] [--seed 20260925]
  python -m scripts.buddhist_han_vi_bench score  [--set PATH] [--out PATH]
  python -m scripts.buddhist_han_vi_bench report [--set PATH] [--out PATH]
  python -m scripts.buddhist_han_vi_bench human  <passage_id> --sf 4 --dr 5 --cf 3 --te 4 --cp 5 --df 4 --cs 3 --oa 5 --hs 4 [--reviewer NAM] [--out PATH]
"""
import os

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_DIR = os.path.join(BASE, 'data', 'benchmark')
DB_PATH = os.path.join(BASE, 'data', 'lineage.db')

DEFAULT_SET = os.path.join(DATA_DIR, 'buddhist_han_vi_bench.json')
DEFAULT_SCORED = os.path.join(DATA_DIR, 'buddhist_han_vi_bench_scored.json')
DEFAULT_HUMAN = os.path.join(DATA_DIR, 'buddhist_han_vi_bench_human.json')

CATEGORIES = [
    'ordinary_classical', 'buddhist_terminology', 'person_names', 'place_names',
    'titles', 'long_syntax', 'repetitive_canonical', 'polysemy', 'verse', 'context_dependent',
]

# Metric code chuẩn (Phase 7 spec) — deterministic hoặc human-only
METRICS = {
    'semantic_fidelity': 'Semantic Fidelity',
    'doctrinal_fidelity': 'Doctrinal Fidelity',
    'terminology_accuracy': 'Terminology Accuracy',
    'canonical_names_accuracy': 'Canonical Person/Place Accuracy',
    'context_consistency': 'Context Consistency',
    'omission_addition': 'Omission/Addition/Hallucination Rate',
    'human_acceptance': 'Human Scholarly Acceptance',
}

AUTO_METRICS = [
    'terminology_accuracy',
    'canonical_names_accuracy',
    'context_consistency',
    'omission_addition',
]
HUMAN_METRICS = [
    'semantic_fidelity',
    'doctrinal_fidelity',
    'human_acceptance',
]