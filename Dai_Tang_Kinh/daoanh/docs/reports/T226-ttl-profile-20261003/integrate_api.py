from pathlib import Path
p=Path('app.py')
raw=p.read_bytes()
marker=b"if __name__ == '__main__':"
at=raw.rfind(marker)
insert="# T226: ho so co chung cu, chi luu revision staging.\r\nfrom api_ttl_profile_v2 import create_ttl_profile_blueprint\r\napp.register_blueprint(create_ttl_profile_blueprint(\r\n    os.path.dirname(__file__), get_db_connection, verify_session))\r\n\r\n".encode()
if b'app.register_blueprint(create_ttl_profile_blueprint(' not in raw:p.write_bytes(raw[:at]+insert+raw[at:])
print('T226 blueprint registered')
