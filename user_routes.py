from flask import Blueprint, request, jsonify

from base_functions import AddUser
from db import GetConnection
from collections import defaultdict

user_bp = Blueprint('user_bp', __name__)



@user_bp.route("/register_user",methods=["POST"])
def RegisterUser():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")
    AddUser(username, password)
    return jsonify({"success": True})

@user_bp.route("/check_credentials")
def CheckUsernameAndPassword():  # checks if username and password is there
    user = request.args.get("username")
    passw = request.args.get("password")
    conn = GetConnection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username=?", (user,))
    row = cursor.fetchone()
    conn.close()

    if row is None:
        return jsonify({"user_exists": False, "error_msg": "User not found"})
    elif row["password"] == passw:
        return jsonify({"user_exists": True, "error_msg": ""})
    else:
        return jsonify({"user_exists": True, "error_msg": "Incorrect password"})

@user_bp.route("/user_info",methods=["GET"])
def GetUserInfo():
    username=request.args.get("username")
    conn=GetConnection()
    cursor=conn.cursor()
    cursor.execute("SELECT COUNT(answer_id) FROM answers WHERE answered_username=?",(username,))
    helped_people=cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(question_id) FROM questions WHERE posted_username=?", (username,))
    questions_asked=cursor.fetchone()[0]
    return jsonify({"username":username, "people_helped":helped_people,"questions_asked":questions_asked})

@user_bp.route("/tags",methods=["GET"])
def GetTags():
    conn=GetConnection()
    cursor=conn.cursor()
    cursor.execute("SELECT tag_name FROM tags WHERE tag_name IS NOT NULL ORDER BY tag_name ASC")
    tags=cursor.fetchall()
    conn.close()
    tags=list(map(lambda x:x[0],tags))
    return jsonify({"tags":tags})

def GetTags(cursor,question_id):
    cursor.execute("SELECT tag_name FROM question_tags as qt LEFT JOIN tags as t ON qt.tag_id=t.tag_id WHERE qt.question_id=?",(question_id,))
    tags=cursor.fetchall()
    tags=list(map(lambda x:x[0],tags))
    if(len(tags)==1 and tags[0]==[None]):
        tags=[]
    return tags