import sqlite3
from ..coms.config import node_dictionary

conn = sqlite3.connect('database.db')

c = conn.cursor()

for ip_address in node_dictionary:
    values = ""
    for node in node_dictionary[ip_address]["nodes"]:
        values += node + " REAL," 
    
    values.rstrip(",")
    c.execute("CREATE TABLE IF NOT EXISTS " + ip_address + " (time DATETIME, " + values + ")")

def insert_data(ip_address, node, data):
    c.execute("INSERT INTO " + ip_address + " (time, " + node + ") VALUES (datetime('now'), " + data + ")")
    conn.commit()
