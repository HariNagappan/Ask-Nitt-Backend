from importlib.metadata import requires

from flask import Blueprint, request, jsonify

from base_functions import requires_token
from db import GetConnection
from collections import defaultdict

answers_bp=Blueprint("answer",__name__)

@answers_bp.route("/answers",methods=["GET"])
def GetAnswersByQuestionId():
    conn=GetConnection()
    cursor=conn.cursor()
    question_id=request.args.get("question_id")
    cursor.execute("SELECT * FROM answers where question_id=?",(question_id,))
    lst=cursor.fetchall()
    conn.close()
    return jsonify([dict(row) for row in lst])

@answers_bp.route("/vote",methods=["POST"])
@requires_token
def VoteAnswer(username):
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

@answers_bp.route("/post_answer",methods=["POST"])
@requires_token
def PostAnswer(answered_username):
    data=request.get_json()
    question_id=data.get("question_id")
    answer=data.get("answer")
    conn=GetConnection()
    cursor=conn.cursor()
    cursor.execute("INSERT INTO answers(question_id,answer,answered_username) VALUES (?,?,?)",(question_id,answer,answered_username))
    conn.commit()
    conn.close()
    return jsonify({"success": True})
