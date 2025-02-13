import sqlite3
import sys
from config import node_dictionary

conn = sqlite3.connect('database.db')
c = conn.cursor()

def create_tables():
    for ip_address in node_dictionary:
        values = "'"
        for node in node_dictionary[ip_address]["nodes"]:
            values += node + "' REAL, '" 
        
        values = values.removesuffix(", '")
        create_string = "CREATE TABLE IF NOT EXISTS '" + ip_address + "' (time DATETIME, " + values + ")"
        c.execute(create_string)
    c.close()

def insert_data(ip_address, node, data):
    conn = sqlite3.connect('database.db')
    node = "'"+node+"'"
    c = conn.cursor()
    c.execute("INSERT INTO '" + ip_address + "' (time, " + node + ") VALUES (datetime('now'), " + data + ")")
    conn.commit()
    c.close()

create_tables()