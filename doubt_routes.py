from collections import defaultdict
from importlib.metadata import requires

from flask import Blueprint, request, jsonify

from base_functions import requires_token
from db import GetConnection
from user_routes import GetTagsByQuestionId

doubts_bp=Blueprint('doubts_bp', __name__)

@doubts_bp.route("/user_doubts",methods=["GET"])
def GetUserDoubts():
    final=[]
    q_id_map_tags=defaultdict(list)
    username=request.args.get('username')
    conn=GetConnection()
    cursor=conn.cursor()
    cursor.execute("SELECT question_id FROM questions AS q WHERE q.posted_username=? ORDER BY question_id", (username,))
    tmp=cursor.fetchall()
    for question_tuple in tmp:
        q_id_map_tags[question_tuple[0]]=GetTagsByQuestionId(cursor=cursor,question_id=question_tuple[0])
    cursor.execute("SELECT title,question_id,question,question_timestamp FROM questions WHERE posted_username=? ORDER BY question_id", (username,))
    tmp=cursor.fetchall()
    print("GetUserDoubts: username",username)
    for question_id in q_id_map_tags:
        val=next(i for i in tmp if i["question_id"]==question_id)
        print("user doubts timestamp",val["question_timestamp"])
        final.append({
            "posted_username": username,
            "question_id": question_id,
            "tags": q_id_map_tags[question_id],# if(q_id_map_tags[question_id]!=[None]) else [],
            "question_timestamp": val["question_timestamp"],
            "question": val["question"],
            "title": val["title"],
        })
    return jsonify(final)

@doubts_bp.route("/recent_doubts",methods=["GET"])
def GetRecentDoubts():
    conn=GetConnection()
    cursor=conn.cursor()
    cursor.execute("SELECT posted_username,question_id,title,question,question_timestamp FROM questions ORDER BY question_timestamp desc LIMIT 5")
    lst=cursor.fetchall()
    q_id_to_tag_name_map={}
    for q_tuple in lst:
        q_id_to_tag_name_map[q_tuple["question_id"]]=GetTagsByQuestionId(cursor=cursor,question_id=q_tuple["question_id"])
    lst=[dict(row) for row in lst]
    print("before recent doubts:",lst)
    for item in lst:
        item["tags"]=q_id_to_tag_name_map[item["question_id"]]# if(q_id_to_tag_name_map[item["question_id"]]!=[None]) else []
    print("after recent doubts:",lst)
    return jsonify(lst)

@doubts_bp.route("/post_doubt",methods=["POST"])
@requires_token
def PostDoubt(username):
    data=request.get_json()

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

@doubts_bp.route("/questions_by_name",methods=["GET"])
def GetDoubtsByName():
    conn=GetConnection()
    cursor=conn.cursor()
    question_prefix=request.args.get("question_prefix")
    cursor.execute("SELECT question FROM questions WHERE question LIKE ? ",(question_prefix+"%",))
    lst=cursor.fetchall()
    lst=[dict(row) for row in lst]
    for q_tuple in lst:
        q_tuple["tags"]=GetTagsByQuestionId(cursor=cursor,question_id=q_tuple["question_id"])
    return jsonify(lst)