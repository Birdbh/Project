import sqlite3
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from coms.config import node_dictionary, station_Names
import datetime

# Use an absolute path for the database connection
database = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'data', 'database.db'))

conn = sqlite3.connect(database)
c = conn.cursor()

def create_tables():
    for ip_address in node_dictionary:
        values = "'"
        actual_name = None
        for ip, name in station_Names:
            if ip == ip_address:
                actual_name = name
        for node in node_dictionary[ip_address]["nodes"]:
            values += node + "' REAL, '" 
        
        values = values.removesuffix(", '")
        create_string = "CREATE TABLE IF NOT EXISTS '" + actual_name + "' (time DATETIME, " + values + ")"
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