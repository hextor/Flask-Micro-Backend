import sqlite3, click, sys
from flask import g, Flask, Response, jsonify, request
from data import db, auth

app = Flask(__name__, instance_relative_config=True)
app.config["DEBUG"] = True
db.init_app(app)
basic_auth = auth.GetAuth()
basic_auth.init_app(app)

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
        'message': 'Error: Conflict at ' + request.url +' Code '+ str(error)
    }
    resp = jsonify(message)
    resp.status_code = 409
    return resp

#get all articles connected to a tag
@app.route('/tags/<name>', methods=['GET'])
def getArticles(name):
    mydb = db.get_db()
    try:
        results = mydb.execute(
            "SELECT * FROM tags WHERE name=?", [name]).fetchall()
    except:
            e=sys.exc_info()[0]
            return conflict(e)        
    if results:
        resp = jsonify(results)
        resp.status_code = 200
        db.close_db()
        return resp
    else:
        db.close_db()
        return not_found()

@app.route('/articles/<id>/tags', methods = ['GET'])
def tags(id):
    #get all tags connected to an article
    if request.method == 'GET':
        mydb = db.get_db()
        try:
            results = mydb.execute(
                "SELECT * FROM tags WHERE article=?", [id]).fetchall()
        except:
            e=sys.exc_info()[0]
            return conflict(e)
        if results:
            resp = jsonify(results)
            resp.status_code = 200
            db.close_db()
            return resp
        else:
            db.close_db()
            return not_found()
    else:
        resp = jsonify({'message': request.url + " contains no such method.",
                    'status':405})
        return resp

@app.route('/articles/<id>/update_tags', methods = ['POST', 'DELETE'])
@basic_auth.required
def update_tag(id):
    #post 1 or more tags to an article
    if request.method == 'POST':
        mydb = db.get_db()
        content = request.get_json()
        tagnames = content.get('TagNames'), None
        print(tagnames)
        if tagnames == None:
            resp = jsonify({"error": "Error: Missing Arguments. Please specify TagName(s) to add."})
            resp.status_code = 400
            return resp
        else:
            for t in tagnames[0]:
                print(t)
                try:
                    mydb.execute('INSERT INTO tags(name, article) VALUES (?,?)', [t, id])
                    mydb.commit()
                except:
                    e=sys.exc_info()[0]
                    return conflict(e)
            try:
                tags = mydb.execute(
                    "SELECT name FROM tags WHERE article=?", [id]).fetchall()
            except:
                e=sys.exc_info()[0]
                return conflict(e)    
            db.close_db()
            article_id = "/articles/"+id
            location = article_id + "/tags/"
            results = {'article_id': article_id,
                       'tags': []}
            for t in tags:
                results['tags'].append(t)
            resp = jsonify(results)
            resp.status_code = 401
            resp.headers['Location']=location
            return resp
    #delete 1 or more tags from an article
    elif request.method == 'DELETE':
        mydb = db.get_db()
        content = request.get_json()
        tagnames = content.get('TagNames'), None
        if tagnames == None:
            resp = jsonify({"error": "Error: Missing Arguments. Please specify TagName(s) to add."})
            resp.status_code = 400
            return resp
        else:
            for t in tagnames[0]:
                print(t)
                try:
                    mydb.execute('DELETE FROM tags WHERE name=? AND article=?', [t, id])
                except:
                    e=sys.exc_info()[0]
                    return conflict(e)
                mydb.commit()
            try:
                tags = mydb.execute(
                    "SELECT name FROM tags WHERE article=?", [id]).fetchall()
            except:
                e=sys.exc_info()[0]
                return conflict(e)
            db.close_db()
            article_id = "/articles/"+id
            results = {'article_id': article_id,
                       'tags': []}
            for t in tags:
                results['tags'].append(t)
            resp = jsonify(results)
            resp.status_code = 200
            return resp
    else:
        resp = jsonify({'message': request.url + " contains no such method.",
                    'status':405})
        return resp

