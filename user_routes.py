from flask import Blueprint, request, jsonify

from base_functions import AddUser
from db import GetConnection
from collections import defaultdict

user_bp = Blueprint('user_bp', __name__, __name__)



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

@user_bp.route("/user_doubts",methods=["GET"])
def GetUserDoubts():
    final=[]
    q_id_map_tags=defaultdict(list)
    username=request.args.get("username")
    conn=GetConnection()
    cursor=conn.cursor()
    cursor.execute("SELECT question_id FROM questions AS q WHERE q.posted_username=? ORDER BY question_id", (username,))
    tmp=cursor.fetchall()
    for question_tuple in tmp:
        q_id_map_tags[question_tuple[0]]=GetTags(cursor=cursor,question_id=question_tuple[0])
    cursor.execute("SELECT title,question_id,question,question_timestamp FROM questions WHERE posted_username=? ORDER BY question_id", (username,))
    tmp=cursor.fetchall()
    print("GetUserDoubts: username",username)
    for question_id in q_id_map_tags:
        val=next(i for i in tmp if i["question_id"]==question_id)
        print("user doubts timestamp",val["question_timestamp"])
        final.append({
            "posted_username": username,
            "question_id": question_id,
            "tags": q_id_map_tags[question_id] if(q_id_map_tags[question_id]!=[None]) else [],
            "question_timestamp": val["question_timestamp"],
            "question": val["question"],
            "title": val["title"],
        })
    return jsonify(final)

@user_bp.route("/post_doubt",methods=["POST"])
def PostDoubt():
    data=request.get_json()

    username=data.get("username")
    title=data.get("title")
    question=data.get("question")
    tags=data.get("tags")

    conn=GetConnection()
    cursor=conn.cursor()
    cursor.execute("INSERT INTO questions(title,question,posted_username) VALUES (?,?,?)",(title,question,username))
    conn.commit()
    question_id=cursor.lastrowid
    if(len(tags)>0):
        for tag in tags:
            cursor.execute("SELECT tag_id FROM tags WHERE tag_name=?",(tag,))
            tag_id=cursor.fetchone()["tag_id"]
            cursor.execute("INSERT INTO question_tags(question_id,tag_id) VALUES (?,?)",(question_id,tag_id))
    else:
        cursor.execute("SELECT tag_id FROM tags WHERE tag_name IS NULL")
        tag_id = cursor.fetchone()["tag_id"]
        print(tag_id)
        cursor.execute("INSERT INTO question_tags(question_id,tag_id) VALUES (?,?)", (question_id, tag_id))
    conn.commit()
    conn.close()
    return jsonify({"success": True})

@user_bp.route("/tags",methods=["GET"])
def GetTags():
    conn=GetConnection()
    cursor=conn.cursor()
    cursor.execute("SELECT tag_name FROM tags WHERE tag_name IS NOT NULL ORDER BY tag_name ASC")
    tags=cursor.fetchall()
    conn.close()
    tags=list(map(lambda x:x[0],tags))
    return jsonify({"tags":tags})

@user_bp.route("/answers",methods=["GET"])
def GetAnswers():
    conn=GetConnection()
    cursor=conn.cursor()
    question_id=request.args.get("question_id")
    cursor.execute("SELECT * FROM answers where question_id=?",(question_id,))
    lst=cursor.fetchall()
    conn.close()
    return jsonify([dict(row) for row in lst])

@user_bp.route("/vote",methods=["POST"])
def VoteAnswer():
    conn=GetConnection()
    cursor=conn.cursor()
    json=request.get_json()
    answer_id=json.get("answer_id")
    add_to_upvote=json.get("add_to_upvote")
    add_to_downvote=json.get("add_to_downvote")
    cursor.execute("UPDATE answers SET upvotes=upvotes+?,downvotes=downvotes+? WHERE answer_id=?",(add_to_upvote,add_to_downvote,answer_id))
    conn.commit()
    conn.close()
    return jsonify({"success": True})

@user_bp.route("/post_answer",methods=["POST"])
def PostAnswer():
    data=request.get_json()
    question_id=data.get("question_id")
    answer=data.get("answer")
    answered_username=data.get("answered_username")
    conn=GetConnection()
    cursor=conn.cursor()
    cursor.execute("INSERT INTO answers(question_id,answer,answered_username) VALUES (?,?,?)",(question_id,answer,answered_username))
    conn.commit()
    conn.close()
    return jsonify({"success": True})

@user_bp.route("/recent_doubts",methods=["GET"])
def GetRecentDoubts():
    conn=GetConnection()
    cursor=conn.cursor()
    final=[]
    cursor.execute("SELECT posted_username,question_id,title,question,question_timestamp FROM questions ORDER BY question_timestamp desc")
    lst=cursor.fetchall()
    q_id_to_tag_name_map={}
    for q_tuple in lst:
        q_id_to_tag_name_map[q_tuple["question_id"]]=GetTags(cursor=cursor,question_id=q_tuple["question_id"])
    lst=[dict(row) for row in lst]
    print("before recent doubts:",lst)
    for item in lst:
        item["tags"]=q_id_to_tag_name_map[item["question_id"]] if(q_id_to_tag_name_map[item["question_id"]]!=[None]) else []
    print("after recent doubts:",lst)
    return jsonify(lst)

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

@user_bp.route("/questions",methods=["GET"])
def GetAllQuestions():
    conn=GetConnection()
    cursor=conn.cursor()
    cursor.execute("SELECT * FROM questions ORDER BY question_timestamp DESC")
    lst=cursor.fetchall()
    lst = [dict(row) for row in lst]
    q_id_to_tag_name_map={}
    for q_tuple in lst:
        tags=GetTags(cursor=cursor,question_id= q_tuple["question_id"])
        q_tuple["tags"]=tags if tags!=[None] else []
    return lst
def GetTags(cursor,question_id):
    cursor.execute("SELECT tag_name FROM question_tags as qt LEFT JOIN tags as t ON qt.tag_id=t.tag_id WHERE qt.question_id=?",(question_id,))
    tags=cursor.fetchall()
    tags=list(map(lambda x:x[0],tags))
    if(len(tags)==1 and tags[0]==[None]):
        tags=[]
    return tags