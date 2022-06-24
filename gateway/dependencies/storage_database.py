from nameko.extensions import DependencyProvider

import mysql.connector
from mysql.connector import Error
from mysql.connector import pooling
import hashlib
import uuid

def getEmailDomain(email):
    return email.split('@')[1]

def hash_password(password, salt):
    pepper = "informatika_ya_petra:)"
    return hashlib.sha256(password.encode() + pepper.encode() + salt.encode()).hexdigest()

class StorageDatabaseWrapper:

    connection = None

    def __init__(self, connection):
        self.connection = connection
    
    def upload(self, username, hash_name, real_name, abstract, title):
        cursor = self.connection.cursor(buffered=True)
        cursor.execute("SELECT * FROM paper WHERE owner = %s AND file_name = %s ORDER BY version DESC", (username, real_name))
        res = cursor.fetchone()
        if res:
            cursor.execute("INSERT INTO paper (owner, path, file_name, version, abstract, title) VALUES (%s, %s, %s, %s, %s, %s)", (username, hash_name, real_name, res[6] + 1, abstract, title))
        else:   
            cursor.execute("INSERT INTO paper (owner, path, file_name, version, abstract, title) VALUES (%s, %s, %s, %s, %s, %s)", (username, hash_name, real_name, 1, abstract, title))
        self.connection.commit()
    
    def download(self, nrp, filename, email):
        if getEmailDomain(email) == 'peter.petra.ac.id':
            cursor = self.connection.cursor(buffered=True)
            cursor.execute("SELECT * FROM paper WHERE file_name = %s ORDER BY version DESC", (filename,))
            res = cursor.fetchone()
            if res:
                return res[4]
            else:
                return False
        else:
            cursor = self.connection.cursor(buffered=True)
            cursor.execute("SELECT * FROM paper WHERE owner = %s AND file_name = %s ORDER BY version DESC", (nrp, filename))
            result = cursor.fetchone()
            if result:
                return result[4]
            else:
                return False
    
class StorageDatabase(DependencyProvider):

    connection_pool = None

    def __init__(self):
        try:
            self.connection_pool = mysql.connector.pooling.MySQLConnectionPool(
                pool_name="database_pool",
                pool_size=5,
                pool_reset_session=True,
                host='localhost',
                database='paper_db',
                user='root',
                password=''
            )
        except Error as e :
            print ("Error while connecting to MySQL using Connection pool ", e)
    
    def get_dependency(self, worker_ctx):
        return StorageDatabaseWrapper(self.connection_pool.get_connection())
    
    



