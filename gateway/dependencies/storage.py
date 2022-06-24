from MySQLdb import DatabaseError
from nameko.rpc import rpc
import pickle
import werkzeug
import uuid
import sys

import storage_database

class StorageService:
    
    name="storage_service"

    database = storage_database.StorageDatabase()

    @rpc
    def upload(self, username, hash_name, real_name, abstarct, title):
        return self.database.upload(username, hash_name, real_name, abstarct, title)
    
    @rpc
    def download(self, nrp, filename, email):
        return self.database.download(nrp, filename, email)
