from distutils.command.upload import upload
from http import cookies
from math import comb
from tkinter.tix import Tree
from urllib import response
from nameko.web.handlers import http
from requests import session
from werkzeug.wrappers import Response
import uuid
import json
from nameko.rpc import RpcProxy
import hashlib
from datetime import datetime
from whoosh.fields import Schema, TEXT, ID
from whoosh import index
from whoosh.qparser import QueryParser
import os

from gateway.dependencies.session import SessionProvider
import re
def emailValid(email):
    # pass the regular expression
    # and the string into the fullmatch() method
    regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    if(re.fullmatch(regex, email)):
        return True
 
    else:
        return False

def hash_file_name(file_name, salt):
    pepper = "ndak"
    return hashlib.sha256(file_name.encode() + pepper.encode() + salt.encode()).hexdigest()

def save_document(idx, author, title, abstract):
    schema = Schema(path=ID(unique=True),title=TEXT(stored=True), author=TEXT(stored=True), abstract=TEXT(stored=True))
    try:
        os.mkdir('indexdir')
        ix = index.create_in("indexdir", schema)
    except:
        ix = index.open_dir('indexdir')
    writer = ix.writer()
    writer.update_document(path=idx, title=title, author=author, abstract=abstract)
    writer.commit()

def search_document(search_str, field="author"):
    schema = Schema(path=ID(stored=True),title=TEXT(stored=True), author=TEXT(stored=True), abstract=TEXT(stored=True))
    try:
        os.mkdir('indexdir')
        ix = index.create_in("indexdir", schema)
    except:
        ix = index.open_dir('indexdir')
    with ix.searcher() as searcher:
        query = QueryParser(field, ix.schema).parse(search_str)
        results = searcher.search(query, terms=True, limit=20)
        res_str = ""
        score_str = ""
        content = ""
        result = []
        for r in results:
            result.append({
                "title": r['title'],
                "author": r['author'],
                "abstract": r['abstract'],
            })
    return Response(json.dumps(result), mimetype='application/json')


class Service:
    name="gateway_service"

    session_provider = SessionProvider()
    account_rpc = RpcProxy('account_service')
    storage_rpc = RpcProxy('storage_service')

    @http('POST', '/register')
    def register(self, request):
        register_info = json.loads(request.get_data())
        email = register_info['email']
        nrp = register_info['nrp']
        nama = register_info['nama']
        password = register_info['password']

        if(not emailValid(email)):
            return Response("Invalid Email", status=400)
        
        if(self.account_rpc.register(nrp=nrp, email=email, nama=nama, password=password)):
            user_data = {
                'nrp': nrp,
                'email': email,
                'nama': nama,
            }
            session_id = self.session_provider.set_session(user_data)
            response = Response('Register Success')
            response.set_cookie('SESSID', session_id)
            return response
        else:
            return Response('Username already exist')

    @http('POST', '/login')
    def login(self, request):
        login_info = json.loads(request.get_data())
        email = login_info['email']
        password = login_info['password']
        if(self.account_rpc.login(email, password)):
            user_data = self.account_rpc.get_student_data(email)
            if(user_data):
                session_id = self.session_provider.set_session(user_data)
                response = Response('Login Success')
                response.set_cookie('SESSID', session_id)
                return response
            else:
                return Response('Login Failed')
        else:
            return Response('Username or Password is wrong')
    
    @http('POST', '/upload')
    def upload(self, request):
        cookies = request.cookies
        if(cookies):
            session_id = cookies['SESSID']
            if(session_id):
                session_data = self.session_provider.get_session(session_id)
                if(session_data):
                    nrp = session_data['nrp']
                    abstarct = request.form['abstract']
                    title = request.form['title']
                    file = request.files['file']
                    author = session_data['nama']
                    hash_name = nrp + str(datetime.now())
                    salt = str(uuid.uuid4())
                    hash_name = hash_file_name(hash_name, salt)
                    real_name = file.filename
                    ext = real_name.split('.')[-1]
                    if(ext != 'pdf'):
                        return Response('File extension must be pdf', status=400)
                    hash_name += '.' + ext
                    file_path = './storage/'+ hash_name
                    if(self.account_rpc.is_nrp_exist(nrp)):
                        with open(file_path, 'wb') as f:
                            f.write(file.read())
                        save_document(str(nrp+real_name), author, title, abstarct)
                        self.storage_rpc.upload(nrp, hash_name, real_name, abstarct, title)
                        return Response('Upload Success')
                    else:
                        return Response('Username Does Not Exist')
                else:
                    return Response('You need to Login First')
            else:
                return Response('You need to Login First')
        else:
            return Response('You need to Login First')

    @http('GET', '/download/<string:filename>')
    def download(self, request, filename):
        cookies = request.cookies
        if(cookies):
            session_id = cookies['SESSID']
            if(session_id):
                session_data = self.session_provider.get_session(session_id)
                if(session_data):
                    nrp = session_data['nrp']
                    email = session_data['email']
                    hash_name = self.storage_rpc.download(nrp, filename, email)
                    if(hash_name):
                        file_path = './storage/'+ hash_name
                        with open(file_path, 'rb') as f:
                            response = Response(f.read(), mimetype='application/pdf')
                            response.headers['Content-Disposition'] = 'attachment; filename=' + filename
                            return response
                    else:
                        return Response('File Not Found')
                else:
                    return Response('You need to Login First')
            else:
                return Response('You need to Login First')
        else:
            return Response('You need to Login First')
    
    @http('GET', '/search/author/<string:author>')
    def search_author(self, request, author):
        return search_document(author, field="author")
    
    @http('GET', '/search/title/<string:title>')
    def search_title(self, request, title):
        return search_document(title, field="title")
    
    @http('GET', '/search/abstract/<string:abstract>')
    def search_abstract(self, request, abstract):
        return search_document(abstract, field="abstract")

    @http('GET', '/logout')
    def logout(self, request):
        cookies = request.cookies
        if(cookies):
            self.session_provider.delete(request.cookies.get('SESSID'))
            response = Response('Logout Success')
            response.delete_cookie('SESSID')
            return response
        else:
            return Response('You need to Login First')
