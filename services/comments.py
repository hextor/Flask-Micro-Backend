import sqlite3
import click
import sys
from flask import g, Flask, Response, jsonify, request
from .data import db
app = Flask(__name__, instance_relative_config=True)
app.config["DEBUG"] = True
db.init_app(app)

# this function found here: http://blog.luisrei.com/articles/flaskrest.html
@app.errorhandler(404)
def not_found(error=None):
    message = {
        'status': 404,
        'message': 'Not Found: ' + request.url,
    }
    resp = jsonify(message)
    resp.status_code = 404
    return resp

@app.errorhandler(409)
def conflict(error=None):
    message = {
        'status': 409,
        'message': 'Error: Conflict at ' + request.url+' Code '+error,
    }
    resp = jsonify(message)
    resp.status_code = 409
    return resp

@app.route('/articles/<id>/comments/', methods = ['GET', 'POST', 'DELETE'])
def comments(id):
    #get number of comments connected to an article
    if request.method == 'GET':
        mydb = db.get_db()
        try: 
            results = mydb.execute(
                "SELECT COUNT(*) FROM comments WHERE article=?", [id]).fetchall()
        except:
            e=sys.exc_info()[0]
            conflict(e)
        if results>0:
            resp = jsonify(results)
            resp.status_code = 200
            db.close_db()
            return resp
        else:
            db.close_db()
            return not_found()
            
    #post a new comment on an article
    if request.method == 'POST':
        mydb = db.get_db()
        content = request.get_json()
        user= content.get('username'), None
        body= content.get('text'), None
        if user == None or body==None:
            resp = jsonify({"error": "Error: Missing Arguments. Please specify Username and Comment Text"})
            resp.status_code = 400
            return resp
        else:
            try:
                mydb.execute(
                    'INSERT INTO comments(author, content, article)''VALUES (?,?,?)', [user, body, id])
            except:
                e=sys.exc_info()[0]
                conflict(e)
            mydb.commit()
            try:
                comments = mydb.execute(
                    "SELECT * FROM comments WHERE article=? ORDER BY posted ASC", [id]).fetchall()
            except:
                e=sys.exc_info()[0]
                conflict(e)
            db.close_db()
            article_id = "/articles/"+ id
            location = article_id + "/comments/"
            results = {'article_id': article_id,
                       'comments': []}
            for c in comments:
                results['comments'].append(c)
            resp = jsonify(results)
            resp.status_code = 401
            resp.headers['Location']=location
            return resp

    #delete comment from an article
    elif request.method == 'DELETE':
        mydb = db.get_db()
        content = request.get_json()
        comment_id = content.get('CommentId'), None
        if comment_id == None:
            resp = jsonify({"error": "Error: Missing Arguments. Please specify TagName(s) to add."})
            resp.status_code = 400
            return resp
        else:
            try:
                mydb.execute('DELETE FROM comments WHERE id=? AND article=?', [comment_id, id])
            except:
                e=sys.exc_info()[0]
                conflict(e)
            mydb.commit()
            try: 
                comments = mydb.execute(
                    "SELECT * FROM comments WHERE article=? ORDER BY posted ASC", [id]).fetchall()
            except:
                e=sys.exc_info()[0]
                conflict(e)
            db.close_db()
            article_id = "/articles/"+id
            results = {'article_id': article_id,
                       'comments': []}
            for c in comments:
                results['comments'].append(c)
            resp = jsonify(results)
            resp.status_code = 200
            return resp
    else:
        message: {'message': request.url + " contains no such method.",
                  'status': 405}
        resp = jsonify(message)
        resp.status_code = 405
        return resp


#get n most recent article comments.
@app.route('/articles/<id>/comments/<number>', methods=['GET'])
def getComments(id, number):
    mydb = db.get_db()
    try:
        results = mydb.execute(
            "SELECT TOP ? * FROM (SELECT * FROM comments WHERE article=? ORDER BY posted ASC)", [number,id]).fetchall()
    except:
        e=sys.exc_info()[0]
        conflict(e)

    if results:
        resp = jsonify(results)
        resp.status_code = 200
        db.close_db()
        return resp
    else:
        db.close_db()
        return not_found()

if __name__ == '__main__':
    app.run("127.0.0.1", "5003")