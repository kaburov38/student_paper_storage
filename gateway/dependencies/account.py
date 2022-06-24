from MySQLdb import DatabaseError
from nameko.rpc import rpc

import account_database

class AccountService:
    
    name="account_service"

    database = account_database.AccountDatabase()

    @rpc
    def register(self, nrp, password, email, nama):
        if(self.database.check_email_exist(email) or self.database.check_nrp_exist(nrp)):
            return False
        else:
            self.database.insert_user(email=email, nrp=nrp, nama=nama, password=password)
            return True
    
    @rpc
    def login(self, email, password):
        return self.database.check_login(email, password)
    
    @rpc 
    def is_nrp_exist(self, nrp):
        return self.database.check_nrp_exist(nrp)

    @rpc
    def get_student_data(self, email):
        return self.database.get_student_data(email)
