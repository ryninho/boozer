import psycopg2
from flask import Flask, request, session, g, redirect, url_for, \
     abort, render_template, flash
from contextlib import closing
import os
import urlparse

def connect_db():
	return psycopg2.connect(app.config['DATABASE'])

# configuration
env = os.environ['READ_ONLY_DATABASE_URL']
db_parsed = urlparse.urlparse(env)
database=db_parsed.path[1:]
user=db_parsed.username
password = db_parsed.password
host = db_parsed.hostname
port=db_parsed.port
DATABASE = 'host=%s port=%s user=%s dbname=%s password=%s' % (host, port, user, database, password)
DEBUG = True
USERNAME = user
PASSWORD = password

# create the application
app = Flask(__name__)
app.config.from_object(__name__)


@app.before_request
def before_request():
    g.db = connect_db()

@app.teardown_request
def teardown_request(exception):
    db = getattr(g, 'db', None)
    if db is not None:
        db.close()

@app.route('/')
def show_options():
    return render_template('home.html')

@app.route('/mine', methods=['GET'])
def show_mine():
    cur = g.db.cursor()
    cur.execute("""
        select id, name from blazer_queries
            where creator_id = 22178394
        order by created_at desc
        limit 10
        """)
    queries = [dict(id=row[0], title=row[1]) for row in cur.fetchall()]
    return render_template('show_queries.html', queries=queries, subheader='Queries you created recently')

# TODO: either change or have a similar one that passes the same actual query (as a new one or what??)
@app.route('/recent', methods=['GET'])
def show_recent():
    cur = g.db.cursor()
    cur.execute("""
        select query_id, q.name
        from (select query_id, max(created_at) as last_run
        from blazer_audits
          where user_id = 22178394
          and query_id is not null
        GROUP BY 1
        ORDER BY 2 desc
        limit 10) as last_ten
        LEFT JOIN blazer_queries q on q.id = last_ten.query_id
        where q.name is not null -- only return if it hasn't been deleted
        """)
    queries = [dict(id=row[0], title=row[1]) for row in cur.fetchall()]
    return render_template('show_queries.html', queries=queries, subheader='Queries you ran recently')


@app.route('/search', methods=['GET', 'POST'])
def run_search():
    # if not session.get('logged_in'):
    #     abort(401)
    queries = []
    if request.form:
        flash('you searched for ' + request.form['query'] + ' and ' + request.form['source'])
        cur = g.db.cursor()
        cur.execute("""
            select id, name from blazer_queries
                where creator_id = 22178394
            order by created_at desc
            limit 5
            """)
        queries = [dict(id=row[0], title=row[1]) for row in cur.fetchall()] # this is a list of dictionaries

    return render_template('show_queries.html', queries=queries, user_requested_search=True, subheader='Search results')

@app.route('/test', methods=['GET', 'POST'])
def test():
    return render_template('test.html')

# @app.route('/login', methods=['GET', 'POST'])
# def login():
#     error = None
#     if request.method == 'POST':
#         if request.form['username'] != app.config['USERNAME']:
#             error = 'Invalid username'
#         elif request.form['password'] != app.config['PASSWORD']:
#             error = 'Invalid password'
#         else:
#             session['logged_in'] = True
#             flash('You were logged in')
#             return redirect(url_for('show_queries'))
#     return render_template('login.html', error=error)

# @app.route('/logout')
# def logout():
#     session.pop('logged_in', None)
#     flash('You were logged out')
#     return redirect(url_for('show_queries'))

if __name__ == '__main__':
    app.run()
