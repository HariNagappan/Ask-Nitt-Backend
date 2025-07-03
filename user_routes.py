import datetime

import bcrypt
import jwt
from flask import Blueprint, request, jsonify
from itsdangerous import HMACAlgorithm

from base_functions import SECRET_KEY, expiry_time, requires_token, FriendRequestStatus
from db import GetConnection
from collections import defaultdict

user_bp = Blueprint('user_bp', __name__)



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
            conn.close()
            return jsonify(token=jwt_token,msg="Login Successful")
        else:
            conn.close()
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
        conn.commit()
        conn.close()
        return jsonify(token=jwt_token,msg="Signup Successful")
    else:
        conn.close()
        return jsonify(token="",msg="Username already exists")

@user_bp.route("/current_user_info",methods=["GET"])
@requires_token
def GetCurrentUserInfo(username):
    conn=GetConnection()
    cursor=conn.cursor()
    cursor.execute("SELECT COUNT(answer_id) FROM answers WHERE answered_username=?",(username,))
    helped_people=cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(question_id) FROM questions WHERE posted_username=?", (username,))
    questions_asked=cursor.fetchone()[0]
    cursor.execute("SELECT joined_on from users WHERE username=?", (username,))
    joined_on=cursor.fetchone()["joined_on"]
    conn.close()
    return jsonify({"username":username,
                    "people_helped":helped_people,
                    "questions_asked":questions_asked,
                    "joined_on":joined_on,
                    "friend_status":FriendRequestStatus.NOT_SENT.value#dummy status,
                    })


@user_bp.route("/user_info",methods=["GET"])
@requires_token
def GetOtherUserInfo(username):
    conn=GetConnection()
    cursor=conn.cursor()
    other_username=request.args.get("other_username")
    cursor.execute("SELECT user_id FROM users WHERE username=?", (other_username,))
    other_user_id=cursor.fetchone()["user_id"]
    cursor.execute("SELECT user_id FROM users WHERE username=?", (username,))
    current_user_id = cursor.fetchone()["user_id"]
    cursor.execute("SELECT COUNT(answer_id) FROM answers WHERE answered_username=?",(other_username,))
    helped_people=cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(question_id) FROM questions WHERE posted_username=?", (other_username,))
    questions_asked=cursor.fetchone()[0]
    cursor.execute("SELECT joined_on from users WHERE username=?", (other_username,))
    joined_on = cursor.fetchone()["joined_on"]
    cursor.execute("SELECT status FROM friend_requests WHERE (sender_id=? and reciever_id=?) or (reciever_id=? and sender_id=?)", (current_user_id,other_user_id,current_user_id,other_user_id))
    friend_status=cursor.fetchone()

    is_current_user_sender_of_request=False
    if(friend_status==None):
        print("friend_status is none", friend_status,"sender_id=")
        cursor.execute("select * from friends where (user_id=? and friend_id=?) or (friend_id=? and user_id=?)",(current_user_id, other_user_id, current_user_id, other_user_id))
        tmp = cursor.fetchone()
        if tmp is None:
            friend_status=FriendRequestStatus.NOT_SENT.value
        else:
            friend_status = FriendRequestStatus.ACCEPTED.value
    else:
        cursor.execute("SELECT * FROM friend_requests WHERE sender_id=? AND reciever_id=?", (current_user_id, other_user_id))
        tmp=cursor.fetchone()
        if(tmp is not None):
            is_current_user_sender_of_request=True
        friend_status=FriendRequestStatus.PENDING.value
    conn.close()
    return jsonify({"username":other_username,
                    "people_helped": helped_people,
                    "questions_asked": questions_asked,
                    "joined_on": joined_on,
                    "friend_status":friend_status,
                    "is_current_user_sender_of_request":is_current_user_sender_of_request,
                    })


@user_bp.route("/get_users",methods=["GET"])
@requires_token
def GetUsersByName(username):
    conn=GetConnection()
    cursor=conn.cursor()
    username_search_text=request.args.get("username_search_text")
    cursor.execute("SELECT username FROM users WHERE username LIKE ? AND username!=? ORDER BY username ASC LIMIT ?", ("%"+username_search_text+"%",username,10))
    lst=cursor.fetchall()
    lst=list(dict(row) for row in lst)
    conn.close()
    return jsonify(lst)
@user_bp.route("/tags",methods=["GET"])
def GetAllTags():
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