import sqlite3
import sys
sys.path.append('src/coms')
from config import node_dictionary

database = 'src/database/database.db'

conn = sqlite3.connect(database)
c = conn.cursor()

def create_tables():
    for ip_address in node_dictionary:
        values = "'"
        for node in node_dictionary[ip_address]["nodes"]:
            values += node + "' REAL, '" 
        
        values = values.removesuffix(", '")
        create_string = "CREATE TABLE IF NOT EXISTS '" + ip_address + "' (time DATETIME, " + values + ")"
        c.execute(create_string)
        print("Table created for: ", ip_address)
    c.close()

def insert_data(ip_address, node, data):
    conn = sqlite3.connect(database)
    node = "'"+node+"'"
    c = conn.cursor()
    c.execute("INSERT INTO '" + ip_address + "' (time, " + node + ") VALUES (datetime('now'), " + data + ")")
    conn.commit()
    c.close()

def insert_random_date():
    conn = sqlite3.connect(database)
    c = conn.cursor()
    for ip_address in node_dictionary:
        for node in node_dictionary[ip_address]["nodes"]:
            c.execute("INSERT INTO '" + ip_address + "' (time, '" + node + "') VALUES (datetime('now'), " + str(1) + ")")
            conn.commit()
            print("Data inserted for: ", ip_address, " | Node: ", node)
    c.close()


create_tables()
insert_random_date()