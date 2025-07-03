from flask import Blueprint, request, jsonify

from base_functions import requires_token, FriendRequestStatus
from db import GetConnection

friend_bp=Blueprint("friend_bp",__name__)

@friend_bp.route("/send_friend_request",methods=["POST"])
@requires_token
def SendFriendRequest(username):
    conn=GetConnection()
    cursor=conn.cursor()
    data=request.get_json()
    reciever_username=data["username"]
    cursor.execute("select user_id from users where username=?",(username,))
    sender_id=cursor.fetchone()["user_id"]
    cursor.execute("select user_id from users where username=?",(reciever_username,))
    reciever_id=cursor.fetchone()["user_id"]
    cursor.execute("insert into friend_requests values (?,?,?)",(sender_id,reciever_id,FriendRequestStatus.PENDING.value))
    conn.commit()
    conn.close()
    return jsonify({"success": True})

@friend_bp.route("/accept_friend_request",methods=["POST"])
@requires_token
def AcceptFriendRequest(username):
    conn=GetConnection()
    cursor=conn.cursor()
    data=request.get_json()
    reciever_username=data["username"]
    cursor.execute("select user_id from users where username=?",(reciever_username,))
    reciever_id=cursor.fetchone()["user_id"]
    cursor.execute("select user_id from users where username=?",(username,))
    sender_id=cursor.fetchone()["user_id"]

    cursor.execute("delete from friend_requests where (sender_id=? and reciever_id=?) or (reciever_id=? and sender_id=?)",(sender_id,reciever_id,sender_id,reciever_id))
    cursor.execute("insert into friends(user_id,friend_id) values (?,?)",(reciever_id,sender_id))
    conn.commit()
    conn.close()
    return jsonify({"success": True})

@friend_bp.route("/decline_friend_request",methods=["POST"])
@requires_token
def DeclineFriendRequest(username):
    conn=GetConnection()
    cursor=conn.cursor()
    data=request.get_json()
    reciever_username=data["username"]
    cursor.execute("select user_id from users where username=?",(reciever_username,))
    reciever_id=cursor.fetchone()["user_id"]
    cursor.execute("select user_id from users where username=?",(username,))
    sender_id=cursor.fetchone()["user_id"]
    cursor.execute("delete from friend_requests where (sender_id=? and reciever_id=?) or (reciever_id=? and sender_id=?)",(sender_id, reciever_id, sender_id, reciever_id))
    conn.commit()
    conn.close()
    return jsonify({"success": True})


@friend_bp.route("/users_friends",methods=["GET"])
@requires_token
def GetUsersFriends(username):
    conn=GetConnection()
    cursor=conn.cursor()
    cursor.execute("select user_id from users where username=?",(username,))
    user_id=cursor.fetchone()["user_id"]
    cursor.execute("select username from friends join users on users.user_id=friends.friend_id where friends.user_id=? union select username from friends join users on users.user_id=friends.user_id where friends.friend_id=?",(user_id,user_id))
    lst=cursor.fetchall()
    conn.close()
    if(lst==None):
        lst=[]
    else:
        lst=list(dict(row) for row in lst)
    print(lst)
    return jsonify(lst)

@friend_bp.route("/user_friend_request_recieved",methods=["GET"])
@requires_token
def GetUserFriendRequestsRecieved(username):
    conn=GetConnection()
    cursor=conn.cursor()
    cursor.execute("select user_id from users where username=?",(username,))
    user_id=cursor.fetchone()["user_id"]
    cursor.execute("select username from users as u join friend_requests as fr on u.user_id=fr.sender_id where fr.reciever_id=?",(user_id,))
    lst=cursor.fetchall()
    conn.close()
    if(lst==None):
        lst=[]
    else:
        lst=list(dict(row) for row in lst)
    return jsonify(lst)
@friend_bp.route("/user_friend_request_sent",methods=["GET"])
@requires_token
def GetUserFriendRequestsSent(username):
    conn=GetConnection()
    cursor=conn.cursor()
    cursor.execute("select user_id from users where username=?", (username,))
    user_id = cursor.fetchone()["user_id"]
    cursor.execute("select username from users as u join friend_requests as fr on u.user_id=fr.reciever_id where fr.sender_id=?",(user_id,))
    lst = cursor.fetchall()
    conn.close()
    if (lst == None):
        lst = []
    else:
        lst = list(dict(row) for row in lst)
    return jsonify(lst)