import sqlite3

conn = sqlite3.connect('data/lineage.db')
conn.row_factory = sqlite3.Row

# Kiểm tra một dòng để hiểu cấu trúc
cursor = conn.execute('SELECT * FROM vn_person_authority WHERE id = "dien_phuc_tue_thang"')
row = cursor.fetchone()

print('Các cột có sẵn:')
for key in row.keys():
    print(f'  {key}')

print(f'\nGiá trị dila_id cho dien_phuc_tue_thang: {row["dila_id"]}')
print(f'Type dila_id: {type(row["dila_id"])}')

print(f'\nKiểm tra dila_id có NULL không: {row["dila_id"] is None}')
print(f'Kiểm tra dila_id có bằng rỗng không: {row["dila_id"] == ""}')

conn.close()