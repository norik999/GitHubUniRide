import MySQLdb
from werkzeug.security import generate_password_hash

db = MySQLdb.connect(
    host="localhost",
    user="root",       
    passwd="Password", 
    db="uniride"       
)

cursor = db.cursor()

# Hash the password
admin_password = "Admin1234"
hashed_password = generate_password_hash(admin_password, method='pbkdf2:sha256', salt_length=8)

insert_query = """
    INSERT INTO Admin (Email, Password) VALUES (%s, %s)
"""
cursor.execute(insert_query, ("admin@mymail.sim.edu.sg", hashed_password))

db.commit()
cursor.close()
db.close()

print("Admin account created successfully!")
