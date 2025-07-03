from collections import defaultdict
from importlib.metadata import requires

from flask import Blueprint, request, jsonify

from base_functions import requires_token, QuestionStatus
from db import GetConnection
from user_routes import GetTagsByQuestionId

doubts_bp=Blueprint('doubts_bp', __name__)

@doubts_bp.route("/user_doubts",methods=["GET"])
def GetUserDoubts():
    username=request.args.get('username')
    conn=GetConnection()
    main_cursor=conn.cursor()
    main_cursor.execute("SELECT title,question_id,question,question_timestamp,status FROM questions WHERE posted_username=? ORDER BY question_id",(username,))
    lst=main_cursor.fetchall()
    lst=list(dict(row) for row in lst)
    for q_tuple in lst:
        tag_cursor=conn.cursor()
        q_tuple["posted_username"]=username
        q_tuple["tags"] =GetTagsByQuestionId(cursor=tag_cursor,question_id=q_tuple["question_id"])
        tag_cursor.close()
    conn.close()
    return jsonify(lst)

@doubts_bp.route("/recent_doubts",methods=["GET"])
def GetRecentDoubts():
    conn=GetConnection()
    main_cursor=conn.cursor()
    main_cursor.execute("SELECT posted_username,question_id,title,question,question_timestamp,status FROM questions ORDER BY question_timestamp desc LIMIT 5")
    lst=main_cursor.fetchall()
    lst = [dict(row) for row in lst]
    for q_tuple in lst:
        tag_cursor=conn.cursor()
        q_tuple["tags"]=GetTagsByQuestionId(cursor=tag_cursor,question_id=q_tuple["question_id"])
        tag_cursor.close()
    conn.close()
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
    cursor.execute("INSERT INTO questions(title,question,posted_username,status) VALUES (?,?,?,?)",(title,question,username,QuestionStatus.PENDING.value))
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

@doubts_bp.route("/questions_filter",methods=["GET"])
def GetDoubtsByFilter():
    conn=GetConnection()
    cursor=conn.cursor()
    search_text=request.args.get("search_text")
    tags=request.args.getlist("tags")
    from_date=request.args.get("from_date")
    to_date=request.args.get("to_date")
    status=request.args.get("status")
    print(from_date,to_date)
    if(status==QuestionStatus.ANY.value):
        print("yes any question status","search_text",search_text,"tags",tags,"from_date",from_date,"to_date",to_date)
        cursor.execute("SELECT * FROM questions WHERE question LIKE ? OR title LIKE ? AND question_timestamp BETWEEN ? AND ?",("%"+search_text+"%","%"+search_text+"%",from_date,to_date))
    else:
        print("no any question status","search_text",search_text,"tags",tags,"from_date",from_date,"to_date",to_date)
        cursor.execute("SELECT * FROM questions WHERE question LIKE ? OR title LIKE ? AND question_timestamp BETWEEN ? AND ? AND status=?",("%" + search_text + "%", "%" + search_text + "%", from_date, to_date,status))
    lst=cursor.fetchall()
    lst=list(dict(row) for row in lst)

    print("all questions of that type",lst)
    q_to_remove=[]
    for q_tuple in lst:
        actual_tags=GetTagsByQuestionId(cursor=cursor,question_id=q_tuple["question_id"])
        print("tags",tags,"actual_tags",actual_tags,"set(tags)",set(tags),"set(actual_tags)",set(actual_tags))
        if(len(set(tags)-set(actual_tags))==0):
            q_tuple["tags"]=actual_tags
        else:
            q_to_remove.append(q_tuple)
    lst=[q_tuple for q_tuple in lst if q_tuple not in q_to_remove]
    conn.close()
    return lst

@doubts_bp.route("/mark_doubt_solved",methods=["POST"])
@requires_token
def MarkDoubtSolved(username):
    conn=GetConnection()
    cursor=conn.cursor()
    data=request.get_json()
    question_id=data.get("question_id")
    cursor.execute("UPDATE questions SET status=? WHERE question_id=?",(QuestionStatus.SOLVED.value,question_id))
    conn.commit()
    conn.close()
    return jsonify({"success": True})