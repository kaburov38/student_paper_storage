from ast import Param
from nameko.extensions import DependencyProvider

import mysql.connector
from mysql.connector import Error
from mysql.connector import pooling
import hashlib
import uuid

def hash_password(password, salt):
    pepper = "informatika_ya_petra:)"
    return hashlib.sha256(password.encode() + pepper.encode() + salt.encode()).hexdigest()

class AccountDatabaseWrapper:

    connection = None

    def __init__(self, connection):
        self.connection = connection
    
    def check_email_exist(self, email):
        cursor = self.connection.cursor()
        cursor.execute("SELECT * FROM student WHERE email = %s", (email,))
        result = cursor.fetchone()
        if result:
            return True
        else:
            return False
    
    def check_nrp_exist(self, nrp):
        cursor = self.connection.cursor()
        cursor.execute("SELECT * FROM student WHERE nrp = %s", (nrp,))
        result = cursor.fetchone()
        if result:
            return True
        else:
            return False
    
    def insert_user(self, email, nrp, nama, password):
        cursor = self.connection.cursor()
        salt = str(uuid.uuid4())
        password_hash = hash_password(password, salt)
        cursor.execute("INSERT INTO student (nrp, nama, email, password, salt) VALUES (%s, %s, %s, %s, %s)", (nrp, nama, email, password_hash, salt))
        self.connection.commit()
        return True
    
    def check_login(self, email, password):
        cursor = self.connection.cursor()
        cursor.execute("SELECT * FROM student WHERE email = %s", (email,))
        result = cursor.fetchone()
        if result:
            password_hash = hash_password(password, result[4])
            if password_hash == result[3]:
                return True
            else:
                return False
        else:
            return False
    
    def get_student_data(self, email):
        cursor = self.connection.cursor()
        cursor.execute("SELECT * FROM student WHERE email = %s", (email,))
        result = cursor.fetchone()
        if result:
            return {
                "nrp": result[0],
                "nama": result[1],
                "email": result[2]
            }
        else:
            return None
    
class AccountDatabase(DependencyProvider):

    connection_pool = None

    def __init__(self):
        try:
            self.connection_pool = mysql.connector.pooling.MySQLConnectionPool(
                pool_name="database_pool",
                pool_size=5,
                pool_reset_session=True,
                host='localhost',
                database='student_db',
                user='root',
                password=''
            )
        except Error as e :
            print ("Error while connecting to MySQL using Connection pool ", e)
    
    def get_dependency(self, worker_ctx):
        return AccountDatabaseWrapper(self.connection_pool.get_connection())
    
    



