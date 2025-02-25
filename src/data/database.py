import sqlite3
import sys
sys.path.append('src/coms')
from coms.config import node_dictionary

import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
import datetime

database = "Project/src/data/database.db"

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
    print("ip_address: " + str(ip_address) + " time: " + str(datetime.datetime.now()) + " node: " + node + " data: " + data)
    c.execute("INSERT INTO '" + ip_address + "' (time, " + node + ") VALUES (datetime('now', 'localtime'), " + data + ")")
    conn.commit()
    c.close()