from flask import Flask, request,jsonify

from answer_routes import answers_bp
from base_functions import CreateTableIfNotExist
from db import GetConnection
from doubt_routes import doubts_bp
from user_routes import user_bp

app = Flask(__name__)
app.register_blueprint(user_bp)
app.register_blueprint(doubts_bp)
app.register_blueprint(answers_bp)

if __name__ == '__main__':
    # conn=GetConnection()
    # cursor=conn.cursor()
    #
    #
    # cursor.execute("""DROP TABLE IF EXISTS question_tags""")
    # cursor.execute("""DROP TABLE IF EXISTS tags""")
    # cursor.execute("""DROP TABLE IF EXISTS answers""")
    # cursor.execute("""DROP TABLE IF EXISTS questions""")
    # conn.commit()
    # conn.close()
    CreateTableIfNotExist()
    app.run(host="0.0.0.0",port=5000, debug=True)