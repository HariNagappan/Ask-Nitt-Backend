from functools import wraps

import jwt
from flask import request, jsonify

from db import GetConnection


def AddTags():
    conn=GetConnection()
    cursor=conn.cursor()
    cursor.executescript("""INSERT INTO tags (tag_name) VALUES
    ('python'),
    ('flask'),
    ('django'),
    ('api'),
    ('html'),
    ('css'),
    ('javascript'),
    ('react'),
    ('nodejs'),
    ('express'),
    ('sql'),
    ('sqlite'),
    ('postgresql'),
    ('mysql'),
    ('mongodb'),
    ('oop'),
    ('recursion'),
    ('linkedlist'),
    ('binarytree'),
    ('sorting'),
    ('algorithms'),
    ('datastructures'),
    ('debugging'),
    ('webdev'),
    ('backend'),
    ('frontend'),
    ('android'),
    ('jetpackcompose'),
    ('kotlin'),
    ('java'),
    ('c++'),
    ('c'),
    ('pandas'),
    ('numpy'),
    ('matplotlib'),
    ('plotly'),
    ('regex'),
    ('string'),
    ('integer'),
    ('dictionary'),
    ('set'),
    ('tuple'),
    ('list'),
    ('comprehension'),
    ('lambda'),
    ('decorator'),
    ('iterator'),
    ('generator'),
    ('class'),
    ('inheritance'),
    ('polymorphism'),
    ('abstraction'),
    ('encapsulation'),
    ('flask-login'),
    ('authentication'),
    ('authorization'),
    ('session'),
    ('cookie'),
    ('jwt'),
    ('security'),
    ('encryption'),
    ('hashing'),
    ('bcrypt'),
    ('sqlalchemy'),
    ('orm'),
    ('mvc'),
    ('rest'),
    ('restful'),
    ('api-testing'),
    ('http'),
    ('https'),
    ('postman'),
    ('unit-test'),
    ('pytest'),
    ('unittest'),
    ('exception'),
    ('try-except'),
    ('logging'),
    ('deployment'),
    ('gunicorn'),
    ('nginx'),
    ('render'),
    ('vercel'),
    ('heroku'),
    ('github'),
    ('git'),
    ('version-control'),
    ('ci-cd'),
    ('docker'),
    ('container'),
    ('virtualenv'),
    ('venv'),
    ('requirements.txt'),
    ('pip'),
    ('package'),
    ('module'),
    ('import'),
    ('relative-import'),
    ('project-structure'),
    ('sqlite3'),
    ('foreign-key'),
        (null)
    """)
    conn.commit()
    conn.close()
def CreateTableIfNotExist():
    conn = GetConnection()
    cursor = conn.cursor()
    cursor.execute("""CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                                                        username NOT NULL UNIQUE, 
                                                        password TEXT NOT NULL,
                                                        jwt_token TEXT)""")
    cursor.execute("""CREATE TABLE IF NOT EXISTS questions
                      (
                          question_id INTEGER PRIMARY KEY AUTOINCREMENT,
                          title TEXT NOT NULL ,
                          question TEXT NOT NULL ,
                          posted_username TEXT NOT NULL,
                          question_timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                      )""")
    cursor.execute("""CREATE TABLE IF NOT EXISTS answers
                      (
                          question_id INTEGER NOT NULL ,
                          answer_id INTEGER PRIMARY KEY AUTOINCREMENT ,   
                          answered_username TEXT,
                          answer_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL ,
                          answer TEXT,
                          upvotes INTEGER DEFAULT 0,
                          downvotes INTEGER DEFAULT 0,
                          FOREIGN KEY (question_id) REFERENCES questions(question_id)
                      )""")
    cursor.execute("""CREATE TABLE IF NOT EXISTS tags
                      (
                          tag_id INTEGER PRIMARY KEY NOT NULL,
                          tag_name UNIQUE
                      )""")
    cursor.execute("""CREATE TABLE IF NOT EXISTS question_tags
                      (
                          question_id INTEGER NOT NULL,
                          tag_id INTEGER NOT NULL ,
                          FOREIGN KEY (question_id) REFERENCES questions(question_id),
                          FOREIGN KEY (tag_id) REFERENCES tags(tag_id)
                          
                      )""")#UNIQUE (question_id, tag_id)
    #cursor.execute("""CREATE TABLE IF NOT EXISTS allowed_users_to_see_detail""")
    conn.commit()
    cursor.execute("""SELECT COUNT(*) FROM tags""")
    val=cursor.fetchone()[0]
    if(val==0):
        AddTags()
    conn.close()

def requires_token(func):
    @wraps(func)
    def decorator(*args, **kwargs):
        token=request.headers.get("Authorization")
        try:
            payload=jwt.decode(token,SECRET_KEY, algorithms=["HS256"])
            username=payload.get("username")
            print("from decorator,username=", username)
        except jwt.ExpiredSignatureError:
            return jsonify(token="", error_msg="Expired Signature")
        except jwt.InvalidTokenError:
            return jsonify(token="",error_msg="Invalid Token")
        return func(username,*args, **kwargs)
    return decorator




SECRET_KEY="my_secret_key_123_456_&*#@%$^&!@#$%!#$!^&I#!!"
expiry_time={"seconds":5,"minutes":0,"hours":0,"days":0}
