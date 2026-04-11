import sqlite3
from werkzeug.security import generate_password_hash
from datetime import datetime, timedelta

# Conexão com o banco
conn = sqlite3.connect("instance/database.db")  # ajuste o caminho se necessário
cur = conn.cursor()

# Dados
username = 'cjr'
raw_password = '1234'
password_hash = generate_password_hash(raw_password)  # gerando hash da senha
is_admin = 0
date_expiry = (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d %H:%M:%S')

# Inserção no banco
cur.execute('''
    INSERT INTO user (username, password_hash, is_admin)
    VALUES (?, ?, ?)
''', (username, password_hash, is_admin))

# Commit e fechamento
conn.commit()
conn.close()
