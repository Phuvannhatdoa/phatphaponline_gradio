"""Bootstrap: tao app, dang ky route module va chay server."""
from core import ADMIN_DIR, DB_PATH, TTL_ARCHIVE_DIR, TTL_MASTER_DIR, TTL_OLD_DIR, _build_cate_ids_map, _load_lexicon_mem, _t130_route_direct_chain, _t130_route_expand, _t131_route_registry, _t148_load_dila_extra, _t148_threading, api_cbeta_compare, app, create_ttl_anchor_blueprint, create_ttl_profile_blueprint, ensure_places_pending_fts, ensure_places_search_fts, get_db_connection, os, t265_bp, time, verify_session
import routes_lineage  # noqa: F401
import routes_misc  # noqa: F401
import routes_namevi  # noqa: F401
import routes_pages  # noqa: F401
import routes_places  # noqa: F401
import routes_translate  # noqa: F401
import routes_ttl  # noqa: F401


app.register_blueprint(t265_bp)




app.route('/daoanh/api/cbeta/<sigla>/compare', methods=['GET'])(api_cbeta_compare)




# ============================================================
if __name__ == '__main__':
    print("=" * 60)
    print("Dao Anh Main Server (app.py)")
    print("=" * 60)
    print(f"DB: {DB_PATH}")
    print(f"TTL Old: {TTL_OLD_DIR}")
    print(f"Admin: {ADMIN_DIR}")
    print("=" * 60)
    
    # Ensure directories exist
    for d in [TTL_OLD_DIR, TTL_MASTER_DIR, TTL_ARCHIVE_DIR]:
        if not os.path.exists(d):
            os.makedirs(d)
            print(f"Created: {d}")

    # Populate FTS5 places_search_fts nếu index rỗng (1 lần ~4-5s, giúp ô tìm kiếm ID nhanh)
    try:
        t0 = time.time()
        populated = ensure_places_search_fts()
        if populated:
            print(f"[fts] Đã populate places_search_fts trong {time.time()-t0:.1f}s", flush=True)
        else:
            print("[fts] places_search_fts đã sẵn sàng", flush=True)
    except Exception as e:
        print(f"[fts] Lỗi ensure_places_search_fts: {e}", flush=True)
    try:
        t0 = time.time()
        populated = ensure_places_pending_fts()
        if populated:
            print(f"[fts] Đã populate places_pending_fts trong {time.time()-t0:.1f}s", flush=True)
        else:
            print("[fts] places_pending_fts đã sẵn sàng", flush=True)
    except Exception as e:
        print(f"[fts] Lỗi ensure_places_pending_fts: {e}", flush=True)

    # Build cache id→cate cho places_pending (1 lần ~5s, giúp trang chính load nhanh thay vì 11.7s)
    try:
        t0 = time.time()
        _build_cate_ids_map()
        print(f"[cate] Đã build cache cate ids trong {time.time()-t0:.1f}s", flush=True)
    except Exception as e:
        print(f"[cate] Lỗi build cate ids: {e}", flush=True)

    # Warm lexicon vào RAM (1 lần ~1-2s, giúp ai_judge không bị cold 77s → placevn.html timeout)
    try:
        t0 = time.time()
        n = len(_load_lexicon_mem())
        print(f"[lexicon] Đã nạp {n} dòng lexicon vào RAM trong {time.time()-t0:.1f}s", flush=True)
    except Exception as e:
        print(f"[lexicon] Lỗi load lexicon: {e}", flush=True)

    # T148: Preload DILA Person Authority XML vào RAM (background thread, không block startup)
    def _t148_preload():
        try:
            _t148_load_dila_extra()
        except Exception as _e:
            print(f'[T148] Preload lỗi: {_e}', flush=True)
    _t148_threading.Thread(target=_t148_preload, daemon=True).start()



# Đăng ký additive routes (đã có app; chỉ add_url_rule — không sửa rule cũ)

try:
    app.add_url_rule("/api/lineage/expand-primary", "t130_expand_primary", _t130_route_expand, methods=["GET"])
    app.add_url_rule("/api/lineage/direct", "t130_direct_chain", _t130_route_direct_chain, methods=["GET"])
    app.add_url_rule("/api/admin/sources/ssot", "t131_registry", _t131_route_registry, methods=["GET"])
    print("    [T130+T131] routes additive da dang ky", flush=True)
except Exception as e:
    print("    [T130+T131] CAUTION route: %s" % e, flush=True)


app.register_blueprint(create_ttl_profile_blueprint(
    os.path.dirname(__file__), get_db_connection, verify_session))


app.register_blueprint(create_ttl_anchor_blueprint(os.path.dirname(__file__), get_db_connection))



if __name__ == '__main__':
    import os as _os
    _port = int(_os.environ.get('APP_PORT', 5000))
    app.run(host='127.0.0.1', port=_port, debug=False, threaded=True, use_reloader=False)


