# -*- coding: utf-8 -*-
"""T232: gắn routes vào blueprint TTL hiện có, giữ gateway/session cũ."""
import json, uuid
from flask import jsonify, request
from src_python import generation_engine_v2 as engine
from src_python import ttl_profile_v2 as model

def register_generation_routes(bp,get_connection,verify_session):
    def body():
        if request.content_length and request.content_length>2*1024*1024:
            raise ValueError('Dữ liệu cấu hình vượt 2 MB.')
        value=request.get_json(silent=True)
        if not isinstance(value,dict):raise ValueError('Cần JSON object.')
        return value
    def auth():return verify_session(request.headers.get('X-Session-Token',''))
    @bp.route('/generation/schemes')
    def generation_schemes():
        c=get_connection()
        try:return jsonify(ok=True,algorithm=engine.VERSION,schemes=engine.schemes(c))
        except ValueError as e:return jsonify(ok=False,error=str(e)),422
        finally:c.close()
    @bp.route('/generation/schemes',methods=['POST'])
    def generation_save_scheme():
        if not auth():return jsonify(ok=False,error='Đăng nhập Admin để lưu mốc/hệ đếm.'),401
        c=get_connection()
        try:
            b=body()
            if not engine.table(c,'generation_v2_scheme_revisions'):
                raise ValueError('Chưa cài kho số đời v2; chạy installer có backup trước.')
            saved=engine.save_scheme(c,b.get('scheme'),b.get('expected_revision',0))
            return jsonify(ok=True,scheme=saved,note='Lưu revision mới; số đời và quan hệ cũ giữ nguyên.')
        except (ValueError,TypeError) as e:return jsonify(ok=False,error=str(e)),422
        finally:c.close()
    @bp.route('/generation/calculate/<aid>')
    def generation_calculate(aid):
        c=get_connection()
        try:
            c.execute('BEGIN');return jsonify(ok=True,report=engine.calculate_all(c,aid))
        except (ValueError,TypeError) as e:return jsonify(ok=False,error=str(e)),422
        finally:c.close()
    @bp.route('/generation/attach',methods=['POST'])
    def generation_attach():
        c=get_connection()
        try:
            b=body();p=model.normalize(b.get('profile'));c.execute('BEGIN')
            report=engine.calculate_all(c,p['person'].get('dila_id',''))
            return jsonify(ok=True,profile=engine.attach_profile(p,report),report=report)
        except (ValueError,TypeError) as e:return jsonify(ok=False,error=str(e)),422
        finally:c.close()
    @bp.route('/generation/save_result/<aid>',methods=['POST'])
    def generation_save_result(aid):
        if not auth():return jsonify(ok=False,error='Đăng nhập Admin để lưu kết quả tính.'),401
        c=get_connection()
        try:
            c.execute('BEGIN');report=engine.calculate_all(c,aid);c.rollback();rid=uuid.uuid4().hex
            if not engine.table(c,'generation_v2_calculations'):raise ValueError('Chưa cài kho số đời v2.')
            c.execute('BEGIN IMMEDIATE')
            c.execute('INSERT INTO generation_v2_calculations VALUES(?,?,?,?,?)',
              (rid,aid,model.now(),engine.canonical(report),engine.digest(report)));c.commit()
            return jsonify(ok=True,id=rid,report=report,note='Đã lưu snapshot phép tính; chưa duyệt số đời và không sửa dữ liệu cũ.')
        except (ValueError,TypeError) as e:c.rollback();return jsonify(ok=False,error=str(e)),422
        finally:c.close()
