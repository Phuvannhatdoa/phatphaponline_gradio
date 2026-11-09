-- T500 — Schema additive cho quan hệ quyển (đã Admin duyệt 2026-10-29, theo tasks/T500 mục 3).
-- TRẠNG THÁI: BẢN NHÁP. CHƯA ÁP DỤNG VÀO DB.
-- Áp dụng chỉ khi Admin cho phép (--apply), sau khi backup lineage.db và chạy dry-run.
-- Không sửa bảng cũ. Không thêm cột vào dila_catalog_works.

BEGIN;

CREATE TABLE IF NOT EXISTS work_volumes (
    work_id          TEXT    NOT NULL,   -- = dila_catalog_works.cbeta_id (ví dụ T0220)
    juan_no          INTEGER NOT NULL,   -- số quyển, bắt đầu từ 1
    cbeta_node_n     TEXT,               -- node CBETA nguồn (ví dụ CBETA.003.001.001)
    juan_source      TEXT    NOT NULL,   -- 'api_range' (API có juan_end) hoặc 'label_count' (đọc từ nhãn "(N卷)")
    source_snapshot  TEXT    NOT NULL,   -- ví dụ 'cbeta_catalog_api/2026-10-29'
    PRIMARY KEY (work_id, juan_no)
);

CREATE TABLE IF NOT EXISTS volume_files (
    work_id   TEXT    NOT NULL,
    juan_no   INTEGER NOT NULL,
    file_id   TEXT    NOT NULL,          -- ví dụ T05n0220
    PRIMARY KEY (work_id, juan_no),
    FOREIGN KEY (work_id, juan_no) REFERENCES work_volumes (work_id, juan_no)
);

CREATE TABLE IF NOT EXISTS work_alias (
    work_id      TEXT NOT NULL,         -- mã trong DB
    alt_work_id  TEXT NOT NULL,         -- mã tương đương từ node alt (ví dụ JB214)
    note         TEXT,
    PRIMARY KEY (work_id, alt_work_id)
);

COMMIT;

-- ROLLBACK (không ảnh hưởng dữ liệu cũ):
-- DROP TABLE IF EXISTS volume_files;
-- DROP TABLE IF EXISTS work_alias;
-- DROP TABLE IF EXISTS work_volumes;
