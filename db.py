import sqlite3


def GetConnection():
    conn = sqlite3.connect('users.db')
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row
    return conn