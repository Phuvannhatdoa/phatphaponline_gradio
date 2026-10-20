# -*- coding: utf-8 -*-
"""term_matcher.py — T179 Phase 8b: Aho-Corasick thuần Python để lọc `match_terms`.

**VÌ SAO CẦN (và VÌ SAO HIỆN CHƯA BẬT):**
`select_rules` hiện lọc `match_terms` bằng `term in source_text` (substring) cho từng
term. Với `n_terms` nhỏ thì substring **đủ và rẻ hơn** (không cần build trie). SPEC §7
phase 8 nêu rõ điều kiện: *"Pure-Python Trie/Aho-Corasick thay substring **chỉ khi**
`n_terms ≥ 1000`"*.

Đo thật 2026-09-26: **76 unique term** (91 kể trùng) ⇒ **CHƯA ĐẠT** ⇒ trie **DORMANT**,
`select_rules` giữ nguyên đường substring. Khi số term vượt ngưỡng, đường trie tự bật —
không cần sửa code gọi.

**VÌ SAO AHO-CORASICK chứ không phải trie thuần:**
Aho-Corasick = trie + fail links ⇒ quét **một lần** toàn văn bản, tìm **mọi** term cùng lúc
(O(n + matches)) thay vì O(n × n_terms) lần `in`. Với Hán văn (UTF-8 3 byte/ký tự) ta quét
trên `str` nên vẫn đúng về mặt ký tự.

**Zero-RAM:** trie chỉ chứa đúng `n_terms` pattern đã đăng ký (76 hoặc ~1.200 khi bật) —
không nạp bảng glossary 248k vào RAM.
"""
from __future__ import annotations

# Ngưỡng bật theo SPEC §7 phase 8 — đổi ở đây, không hardcode rải rác.
TRIE_MIN_TERMS = 1000


class TermMatcher:
    """Aho-Corasick cho tập `terms` (str). `scan(text)` trả set các term có mặt trong text.

    Dùng khi `n_unique_terms >= TRIE_MIN_TERMS`. Với tập nhỏ, `substring_scan()` rẻ hơn
    (xem `scan_substring`).
    """

    __slots__ = ('goto', 'fail', 'out', 'n_terms', '_max_len', '_terms')

    def __init__(self, terms):
        # `goto`: trie dạng dict-of-dict. `out`: node -> set term kết thúc tại node đó.
        # `fail`: node -> node fallback (Aho-Corasick fail link).
        self.goto = [{}]
        self.fail = [0]
        self.out = [set()]
        self.n_terms = 0
        self._max_len = 0
        self._terms = tuple()
        seen = set()
        for t in terms or ():
            if not t or t in seen:
                continue
            seen.add(t)
            self.n_terms += 1
            if len(t) > self._max_len:
                self._max_len = len(t)
            node = 0
            for ch in t:
                nxt = self.goto[node].get(ch)
                if nxt is None:
                    nxt = len(self.goto)
                    self.goto.append({})
                    self.fail.append(0)
                    self.out.append(set())
                    self.goto[node][ch] = nxt
                node = nxt
            self.out[node].add(t)
        self._build_fail()

    def _build_fail(self):
        """BFS dựng fail link (thuần Python, không regex)."""
        from collections import deque
        q = deque()
        for ch, nxt in self.goto[0].items():
            self.fail[nxt] = 0
            q.append(nxt)
        while q:
            r = q.popleft()
            for ch, u in self.goto[r].items():
                q.append(u)
                f = self.fail[r]
                while f and ch not in self.goto[f]:
                    f = self.fail[f]
                self.fail[u] = self.goto[f].get(ch, 0)
                if self.fail[u] == u:
                    self.fail[u] = 0
                # gộp output của node fail vào node (để match kết thúc ở node cha vẫn thấy)
                if self.fail[u] != u:
                    self.out[u] |= self.out[self.fail[u]]

    def scan(self, text):
        """Trả set term nào xuất hiện trong `text` (quét 1 lần, Aho-Corasick)."""
        if not text or not self.n_terms:
            return set()
        node = 0
        found = set()
        goto, fail, out = self.goto, self.fail, self.out
        for ch in text:
            while node and ch not in goto[node]:
                node = fail[node]
            node = goto[node].get(ch, 0)
            if out[node]:
                found |= out[node]
        return found

    def scan_substring(self, text):
        """Đường substring (mặc định khi n_terms < TRIE_MIN_TERMS)."""
        if not text or not self.n_terms:
            return set()
        return {t for t in (t for t in self._terms) if t in text}

    # `scan_substring` cần danh sách term gốc (out đã gộp theo node, không đủ để
    # tái dựng tập). Lưu riêng trong `_terms` khi khởi tạo (xem `build_matcher`).


def build_matcher(terms, force=None):
    """Trả (matcher, mode) — mode ∈ {'trie', 'substring'}.

    `force`: None = theo gate `n_terms >= TRIE_MIN_TERMS`; True/False = ép (chỉ để test).
    """
    uniq = {t for t in (terms or ()) if t}
    n = len(uniq)
    use_trie = (n >= TRIE_MIN_TERMS) if force is None else bool(force)
    m = TermMatcher(uniq)
    m._terms = tuple(sorted(uniq))
    return m, ('trie' if use_trie else 'substring')


def scan_terms(text, terms, force=None):
    """Tiện ích 1 lần: chọn đường theo gate rồi trả set term khớp.

    Đây là hàm `select_rules` sẽ dùng. Ở trạng thái hiện tại (76 term) nó rơi vào
    `substring` ⇒ **hành vi y hệt trước T179** (không regression).
    """
    uniq = {t for t in (terms or ()) if t}
    n = len(uniq)
    use_trie = (n >= TRIE_MIN_TERMS) if force is None else bool(force)
    if n == 0:
        return set()
    if not use_trie:
        return {t for t in uniq if t in (text or '')}
    m = TermMatcher(uniq)
    return m.scan(text or '')
