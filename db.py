import sqlite3

conn = sqlite3.connect('zelle_ops.sqlite')
cursor = conn.cursor()
sql = """CREATE TABLE depositos(
    id integer PRIMARY KEY,
    msg_id text NOT NULL,
    cuenta text NOT NULL,
    banco text NOT NULL,
    fecha text NOT NULL,
    remitente text NOT NULL,
    monto float NOT NULL,
    cobro boolean NOT NULL)
    """
cursor.execute(sql)