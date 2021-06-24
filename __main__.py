
import flask
from flask import request, jsonify, send_from_directory
from flask_cors import CORS, cross_origin
from flask_sqlalchemy import SQLAlchemy
import json
import copy
import gzip
from sys import getsizeof
import os
import webbrowser
from threading import Timer
import base64
import requests
import datetime
# from aws_config.config import S3_KEY, S3_SECRET, S3_BUCKET
app = flask.Flask(__name__, static_folder='react/build/static')
# database

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///User.sqlite3'
# app.config['SQLALCHEMY_DATABASE_URI'] = 'postgres://fkdfvybqippedk:1fcdefdc660f3a9ac8e878c2f25aefaf46dfd3126b81ff0bb64fc0792c160f48@ec2-52-44-139-108.compute-1.amazonaws.com:5432/d3vfi3i8hpdr55'

db = SQLAlchemy(app)

# database
class Document(db.Model):
    __tablename__ = 'document'
    _id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    document_hash_key = db.Column(db.String(100), unique=True, nullable=False)
    document_name = db.Column(db.String(100), nullable=True)
    user_id = db.Column(db.String(100), db.ForeignKey('user.hash_key'))
    last_index = db.Column(db.Integer, nullable=True)
    questions = db.relationship('Question', backref='document', lazy=True)
    def __init__(self, document_hash_key,user_id, last_index, document_name):
        self.document_hash_key = document_hash_key
        self.user_id = user_id
        self.last_index = last_index
        self.document_name = document_name

class User(db.Model):
    # Defines the Table Name user
    __tablename__ = "user"
    # Makes three columns into the table id, name, email
    _id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    hash_key = db.Column(db.String(100), nullable=False)
    user_type = db.Column(db.String(50), nullable=False)
    documents = db.relationship('Document', backref='user', lazy=True)

    # A constructor function where we will pass the name and email of a user and it gets add as a new entry in the table.
    def __init__(self, hash_key, user_type):
        self.hash_key = hash_key
        self.user_type = user_type
        
class Question(db.Model):
    __tablename__ = "question"
    _id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    question_index = db.Column(db.Integer, nullable=False)
    question_data = db.Column(db.Text, nullable=True)
    document_id = db.Column(db.String(100), db.ForeignKey('document.document_hash_key') )
    def __init__(self, question_index, question, document_id):
        self.question_index = question_index
        self.question_data = question
        self.document_id = document_id

app.config["DEBUG"] = True
CORS(app, support_credentials=True)


json_object_array = []
file_name_question_bank = ''
json_object_array_source = []
approved_questions = []

@app.route('/authUserInCloud', methods=['POST'])
def auth_user_in_cloud():
    email = request.form['email']
    password = request.form['password']
    data = {
        'email': email,
        'password': password
    }
    headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}
    response = requests.post(url = 'https://www.empowerr-aws-one.ga/creator/userAuth', data=data)
    json_response = response.json()
    if json_response['status'] =='approved':
        user_data = User.query.filter_by(hash_key=email).first()
        if json_response['database'] is not None:
            decoded_db = base64.b64decode(json_response['database'])
            file_name = 'cloud_backup/User.sqlite3'
            os.makedirs(os.path.dirname(file_name), exist_ok=True)
            with open(file_name, 'wb') as f:
                print('file written')
                f.write(decoded_db)
                f.close()
            
        if user_data is None:
            print('added new user')
            new_data = User(email,'creator')
            # new_data = User('#@!123', 'physics_full', 0)
            db.session.add(new_data)
            db.session.commit()
        return {
            'status': json_response['status'],
            'email': email,
            'database': json_response['database']
        }
    return {
        'status': json_response['status']
    }

@app.route('/uploadQuestionBank', methods=['POST'])
def upload_question_bank():
    script_path = os.path.dirname(os.path.abspath(__file__))
    with open(script_path + '\\' + 'User.sqlite3', 'rb') as f:
        doc_hash_key = request.form['documentKey']
        user_hash_key = request.form['userKey']
        blob = base64.b64encode(f.read())
        # sending post request and saving response as response object 
        r = requests.post(url = "https://www.empowerr-aws-one.ga/creator/uploadQuestionBank",files={"blob":blob, "uname":user_hash_key,"doc_key": doc_hash_key})  
        # extracting response text  
        pastebin_url = r.text 
        return "The pastebin URL is:%s"%pastebin_url

# Serve React App


@app.route('/addQuestions', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    if path != "" and os.path.exists(app.static_folder + '/' + path):
        print('hello1')
        return send_from_directory(app.static_folder, path)
    else:
        print('hello')
        return send_from_directory('react/build/', 'index.html')

@app.route('/getAllQuestionBanks', methods=['POST'])
def get_all_question_banks():
    user_hash_key = request.form['userKey']
    document_data = Document.query.filter(Document.user_id == user_hash_key).all()
    # print(document_data[0].document_name)
    document_list = [{'name': doc.document_name,
                        'id': doc.document_hash_key} for doc in document_data]

    return {'document': document_list}

@app.route('/getQuestionByIndex', methods=['POST'])
def api_extractDataFromFile():
    doc_hash_key = request.form['documentKey']
    user_hash_key = request.form['userKey']
    question_index = int(request.form['index'])
    # print(question_index)
    # print(doc_hash_key)
    user_data = User.query.filter_by(hash_key=user_hash_key).first()
    if user_data is not None:
        question_data = Question.query.filter((Question.document_id == doc_hash_key) & (Question.question_index == question_index)).first()
        # all_question_data = Question.query.all()
        # print(question_data.question_data)
        return {'current_object': question_data.question_data}
    return False

@app.route('/saveQuestionByIndex', methods=['POST'])
def api_save_data_to_File():
    doc_hash_key = request.form['documentKey']
    question_string = request.form['questionData']
    user_hash_key = request.form['userKey']
    index = int(request.form['index'])
    user_data = User.query.filter_by(hash_key=user_hash_key).first()
    if user_data is not None:
        question_data = Question.query.filter((Question.document_id == doc_hash_key) & (Question.question_index == index)).first()
        question_data.question_data = question_string
        db.session.commit()
        return {'status': 'ok'}
    return False


@app.route('/auth', methods=['POST'])
def auth_key():
    req = request.get_json()
    key = request.form['key']
    user_data = User.query.filter_by(hash_key=key).first()
    if user_data is not None:
        global file_name_question_bank
        file_name_question_bank = user_data.file_name
        total_count_of_questions = Questions.query.count()
        # question_categories = Questions.query.with_entities(Questions.question_status, Questions.question_index).filter((Questions.hash_key==key) & ((Questions.question_status=='approved') | (Questions.question_status=='flag_for_later') | (Questions.question_status=='unrelated'))).all()
        question_categories = Questions.query.with_entities(Questions.question_status, Questions.question_index).filter((Questions.hash_key==key) & (Questions.question_status!='undone')).all()
        return {'response': user_data is not None,
                'last_index': user_data.last_index,
                'total_questions': total_count_of_questions,
                 'approved_questions': [data.question_index for data in question_categories if data.question_status=='approved'],
                 'saved_for_later_questions': [data.question_index for data in question_categories if data.question_status=='flag_for_later'],
                 'unrelated': [data.question_index for data in question_categories if data.question_status=='unrelated'],
                 'reported': [data.question_index for data in question_categories if data.question_status=='reported'],
            }
    return {
        'response': user_data is not None,
    }

@app.route('/addDataToPostgres', methods=['POST', 'GET'])
def serialize_data_and_enter_to_table():
    hash_key='123#@!'
    question_entries = []
    json_object_array_source= initialize_data('data_Example_set_unfiltered')
    for idx, question in enumerate(json_object_array_source):
        new_entry = Questions(hash_key, idx, 'undone', json.dumps(question))
        question_entries.append(new_entry)
    db.session.add_all(question_entries)
    db.session.commit()
    print('all_done')

@app.route('/editQuestionByUser', methods=['POST'])
def auth_key_for_user():
    req = request.get_json()
    hash_key = request.form['key']
    user_data = User.query.filter_by(hash_key=key).first()
    if user_data is not None:
        global file_name_question_bank
        file_name_question_bank = user_data.file_name
        total_count_of_questions = Questions.query.count()
        # question_categories = Questions.query.with_entities(Questions.question_status, Questions.question_index).filter((Questions.hash_key==key) & ((Questions.question_status=='approved') | (Questions.question_status=='flag_for_later') | (Questions.question_status=='unrelated'))).all()
        question_categories = Questions.query.with_entities(Questions.question_status, Questions.question_index).filter((Questions.hash_key==key) & (Questions.question_status!='undone')).all()
        return {'response': user_data is not None,
                'last_index': user_data.last_index,
                'total_questions': total_count_of_questions,
                 'approved_questions': [data.question_index for data in question_categories if data.question_status=='approved'],
                 'saved_for_later_questions': [data.question_index for data in question_categories if data.question_status=='flag_for_later'],
                 'unrelated': [data.question_index for data in question_categories if data.question_status=='unrelated'],
                 'reported': [data.question_index for data in question_categories if data.question_status=='reported'],
            }
    return {
        'response': user_data is not None,
    }

@app.route('/addValidatorData', methods=['POST', 'GET'])
def add_validator_data():
    new_data = User('test1', 'validator')
    # new_data = User('#@!123', 'physics_full', 0)
    db.session.add(new_data)
    db.session.commit()
    return 'done'

@app.route('/addDocument', methods=['POST', 'GET'])
def add_document_data():
    new_data = Document('testDoc','testDoc', 0, 'Probability')
    # new_data = User('#@!123', 'physics_full', 0)
    db.session.add(new_data)
    db.session.commit()
    return 'done doc'

@app.route('/addQuestionToDoc', methods=['POST', 'GET'])
def add_question_document_data():
    new_data = Question(0, '', 'testDoc')
    # new_data = User('#@!123', 'physics_full', 0)
    db.session.add(new_data)
    db.session.commit()
    return 'done doc question'


@app.route('/addCreatorData', methods=['POST', 'GET'])
def add_creator_data():
    new_data = User('test2','creator')
    # new_data = User('#@!123', 'physics_full', 0)
    db.session.add(new_data)
    db.session.commit()
    return 'done'

@app.route('/addNewDocument', methods=['POST', 'GET'])
def add_new_document():
    doc_hash_key = int(datetime.datetime.now().timestamp())
    user_hash_key = request.form['userKey']
    document_name = request.form['documentName']
    new_data = Document(doc_hash_key,user_hash_key, 0, document_name)
    db.session.add(new_data)
    db.session.commit()
    create_new_dummy_question(doc_hash_key,user_hash_key,0)
    return 'done doc'
    
def create_new_dummy_question(doc_hash_key,user_hash_key,question_index):
    question_instance = json.dumps({})
    print(question_index)
    new_question = Question(question_index, question_instance, doc_hash_key)
    db.session.add(new_question)
    db.session.commit()
    return 'done'
@app.route('/updateCreaorData', methods=['POST', 'GET'])
def update_creator_data():
    doc_hash_key = request.form['documentKey']
    user_hash_key = request.form['userKey']
    last_index = request.form['last_index']
    user_data = User.query.filter_by(hash_key=user_hash_key).first()
    if user_data is not None:
        document_data = Document.query.join(Question, Document.document_hash_key==Question.document_id).filter((Document.document_hash_key==doc_hash_key) & (Question.question_index == Document.last_index)).first()
        document_data.last_index = last_index
        db.session.commit()
        return 'success'
    return 'failed' 

@app.route('/validateUserAndDocument', methods=['POST', 'GET'])
def validate_user_and_doc():
    doc_hash_key = request.form['documentKey']
    user_hash_key = request.form['userKey']
    user_data = User.query.filter_by(hash_key=user_hash_key).first()
    # print(user_data.documents[0].questions[0].question_index)
    if user_data is not None:
        document_data = Document.query.join(Question, Document.document_hash_key==Question.document_id).filter((Document.document_hash_key==doc_hash_key) & (Question.question_index == Document.last_index)).first()
        # print(document_data.questions[1].question_data)
        if document_data is None:
            return {
            'status': 'ok',
            'doc_hash_key': doc_hash_key,
            'user_hash_key': user_hash_key,
            'total_questions': 1,
            'last_index': 0,
            }
        else:
            return {
                'status': 'ok',
                'doc_hash_key': doc_hash_key,
                'user_hash_key': user_hash_key,
                'total_questions': len(document_data.questions),
                'last_index': document_data.last_index,
            }
    return {
        'status': 'not found'
    }

@app.route('/createNewQuestion', methods=['POST', 'GET'])
def create_new_question():
    doc_hash_key = request.form['documentKey']
    user_hash_key = request.form['userKey']
    question_index = int(request.form['index'])
    question_instance = request.form['questionData']
    print(question_index)
    new_question = Question(question_index, question_instance, doc_hash_key)
    db.session.add(new_question)
    db.session.commit()
    return 'done'

@app.route('/question/saveQuestionInstance', methods=['POST'])
def save_question_object():
    global json_object_array
    question_instance = request.form['questionData']
    question_index = int(request.form['questionIndex'])
    hash_key = request.form['key']
    question_status = request.form['questionStatus']
    current_object = json.loads(question_instance)
    question_object = Questions.query.filter(Questions.hash_key==hash_key, Questions.question_index==question_index).first()
    question_raw_object = copy.deepcopy(json.loads(question_object.question_data))
    current_object['question'] = question_raw_object['question']
    current_object['answer'] = question_raw_object['answer']
    current_object['explanation'] = question_raw_object['explanation']
    question_object.question_status = question_status
    question_object.question_data = json.dumps(current_object)
    db.session.commit()
    # question_categories = Questions.query.with_entities(Questions.question_status, Questions.question_index).filter((Questions.hash_key==hash_key) & ((Questions.question_status=='approved') | (Questions.question_status=='flag_for_later') | (Questions.question_status=='unrelated'))).all()
    question_categories = Questions.query.with_entities(Questions.question_status, Questions.question_index).filter((Questions.hash_key==hash_key) & (Questions.question_status!='undone')).all()
    return {'current_object': current_object, 'approved_questions': [data.question_index for data in question_categories if data.question_status =='approved'],
    'saved_for_later': [data.question_index for data in question_categories if data.question_status=='flag_for_later'],
    'unrelated': [data.question_index for data in question_categories if data.question_status=='unrelated'],
    'reported': [data.question_index for data in question_categories if data.question_status=='reported']
    }


def save_global_question_bank(index, current_object):
    global json_object_array_source
    json_object_array_source[index] = current_object


@app.route('/question/saveQuestionBank', methods=['POST'])
def save_question_bank():
    response = write_file_to_s3(
        file_name_question_bank, json_object_array_source)
    return {'response': response}

@app.route('/question/saveQuestionBankGRE', methods=['POST'])
def save_question_bank_to_db():
    key = request.form['key']
    user_data = User.query.filter_by(hash_key=key).first()
    data_to_save = json_object_array_source[0:1000]
    print(getsizeof(gzip.compress(json.dumps(data_to_save).encode('utf-8'))))
    user_data.question_bank = gzip.compress(json.dumps(data_to_save).encode('utf-8'))
    db.session.commit()
    return { 'status': 'done' }

@app.route('/question/hello', methods=['POST', 'GET'])
def api_hello():
    return 'Hello'

def open_browser():
      webbrowser.open_new('http://127.0.0.1:5000/addQuestions')

db.create_all()
if __name__ == '__main__':
    Timer(1, open_browser).start()
    app.run(port=5000, use_reloader=False)
