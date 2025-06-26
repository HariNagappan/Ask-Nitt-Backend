import datetime

import bcrypt
import jwt
from flask import Blueprint, request, jsonify
from itsdangerous import HMACAlgorithm

from base_functions import SECRET_KEY, expiry_time, requires_token
from db import GetConnection
from collections import defaultdict

user_bp = Blueprint('user_bp', __name__)


@user_bp.route("/user_info",methods=["GET"])
@requires_token
def GetUserInfo(username):
    conn=GetConnection()
    cursor=conn.cursor()
    cursor.execute("SELECT COUNT(answer_id) FROM answers WHERE answered_username=?",(username,))
    helped_people=cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(question_id) FROM questions WHERE posted_username=?", (username,))
    questions_asked=cursor.fetchone()[0]
    return jsonify({"username":username,
                    "people_helped":helped_people,
                    "questions_asked":questions_asked})

@user_bp.route("/login",methods=["POST"])
def Login():
    data=request.get_json()
    username=data.get("username")
    password=data.get("password")
    print("login:",username,password)
    conn=GetConnection()
    cursor=conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username=?", (username,))
    row = cursor.fetchone()
    print("login row:",row)

    if row is None:
        conn.close()
        return jsonify(token="",msg="User not found")
    else:
        cursor.execute("SELECT password FROM users WHERE username=?", (username,))
        actual_password = cursor.fetchone()["password"]
        if bcrypt.checkpw(password.encode('utf-8'), actual_password):
            payload={
                "username":username,
                "exp":datetime.datetime.utcnow() + datetime.timedelta(seconds=expiry_time["seconds"],minutes=expiry_time["minutes"],hours=expiry_time["hours"] ,days=expiry_time["days"]),
            }
            jwt_token=jwt.encode(payload, SECRET_KEY,algorithm="HS256")
            cursor.execute("UPDATE users SET jwt_token =? WHERE username=?", (jwt_token,username))
            conn.commit()
            conn.close()
            return jsonify(token=jwt_token,msg="Login Successful")
        else:
            return jsonify(token="", msg="Incorrect password")

@user_bp.route("/signup",methods=["POST"])
def SignUp():
    data=request.get_json()
    username=data.get("username")
    password=data.get("password")
    conn=GetConnection()
    cursor=conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username=?", (username,))
    row = cursor.fetchone()
    if row is None:
        salt=bcrypt.gensalt()
        hashed_password=bcrypt.hashpw(password.encode('utf-8'), salt)
        cursor.execute("INSERT INTO users(username,password) VALUES (?,?)", (username,hashed_password))

        payload={
            "username":username,
            "exp": datetime.datetime.utcnow() + datetime.timedelta(seconds=expiry_time["seconds"],
                                                                   minutes=expiry_time["minutes"],
                                                                   hours=expiry_time["hours"],
                                                                   days=expiry_time["days"]),
        }
        jwt_token=jwt.encode(payload, SECRET_KEY,algorithm="HS256")
        cursor.execute("UPDATE users SET jwt_token=? WHERE username=?", (jwt_token,username))
        conn.commit()
        conn.close()
        return jsonify(token=jwt_token,msg="Signup Successful")
    else:
        conn.close()
        return jsonify(token="",msg="Username already exists")

@user_bp.route("/logout",methods=["POST"])
@requires_token
def Logout(username):
    conn=GetConnection()
    cursor=conn.cursor()
    cursor.execute("""UPDATE users SET jwt_token=NULL WHERE username=?""",(username,))
    conn.commit()
    conn.close()
    return jsonify(token="",msg="Logout Successful")

@user_bp.route("/tags",methods=["GET"])
def GetTags():
    conn=GetConnection()
    cursor=conn.cursor()
    cursor.execute("SELECT tag_name FROM tags WHERE tag_name IS NOT NULL ORDER BY tag_name ASC")
    tags=cursor.fetchall()
    conn.close()
    tags=list(map(lambda x:x[0],tags))
    return jsonify({"tags":tags})

def GetTagsByQuestionId(cursor,question_id):
    cursor.execute("SELECT tag_name FROM question_tags as qt LEFT JOIN tags as t ON qt.tag_id=t.tag_id WHERE qt.question_id=?",(question_id,))
    tags=cursor.fetchall()
    tags=list(map(lambda x:x[0],tags))
    if(tags==[None]):
        tags=[]
    return tags