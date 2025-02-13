import sqlite3

# Create a SQL connection to our SQLite database
con = sqlite3.connect("database.db")

cur = con.cursor()

# Retrieve the names of all the tables
cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cur.fetchall()

# Iterate over the table names and display data from each table
for table in tables:
    table_name = table[0]
    table_name = "'"+table_name+"'"
    print(f"Data from table: {table_name}")
    
    # Fetch all data from the current table
    cur.execute(f"SELECT * FROM {table_name}")
    rows = cur.fetchall()
    
    # Print each row in the current table
    print(rows)
    for row in rows:
        print(row)
    print("\n")

# Be sure to close the connection
con.close()
