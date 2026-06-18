import pymysql
import sys

conn = pymysql.connect(
    host='localhost', user='root', password='Pratik@123',
    database='medicvista_retailer', charset='utf8mb4'
)
cur = conn.cursor()

sql_path = '../setup_database.sql'
with open(sql_path, 'r', encoding='utf-8') as f:
    sql = f.read()

statements = [s.strip() for s in sql.split(';') if s.strip()]
ok = fail = 0
for stmt in statements:
    clean = '\n'.join(l for l in stmt.split('\n') if not l.strip().startswith('--')).strip()
    if not clean:
        continue
    try:
        cur.execute(clean)
        conn.commit()
        ok += 1
    except Exception as e:
        msg = str(e)
        if 'Duplicate' in msg or 'already exists' in msg:
            pass  # already exists, fine
        else:
            print(f'  SKIP: {msg[:100]}')
        fail += 1

cur.execute('SHOW TABLES')
tables = [t[0] for t in cur.fetchall()]
conn.close()

print(f'\nResult: {ok} executed, {fail} skipped')
print(f'Total tables in medicvista_retailer: {len(tables)}')
for t in sorted(tables):
    print(f'  + {t}')
print('\nDatabase setup complete!')
