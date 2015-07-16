import psycopg2
from flask import Flask, request, session, g, redirect, url_for, \
     abort, render_template, flash
from contextlib import closing
from flask.ext.cache import Cache
import os
import urlparse
import argparse
from flask_bootstrap import Bootstrap
from flask_nav import Nav
from flask_nav.elements import Navbar, View

print "Note: Please pass either 'local' or 'replica' when starting boozer from the command line to select the db connection"
# print "Also, please pass your blazer or admin username (without the @domain.com)"
# print "For example, python boozer.py replica eric"
print "Also, please pass your blazer id"
print "For example, python boozer.py replica 22178394"
print "Lastly you'll need the following environment variables set: READ_ONLY_DATABASE_URL, LOCAL_DATABASE_URL, BOOZER_SECRET_KEY"
parser = argparse.ArgumentParser(description='Select the database connection.')
parser.add_argument('db_target')
# parser.add_argument('blazer_user')
parser.add_argument('blazer_id')
args = parser.parse_args()

def connect_db():
    return psycopg2.connect(app.config['DATABASE'])

# configuration
if args.db_target == 'replica':
    env = os.environ['READ_ONLY_DATABASE_URL']
elif args.db_target == 'local':
    env = os.environ['LOCAL_DATABASE_URL']
else:
    env = "postgres://localhost:5432/instacart_dev"
    print "please pass either 'local' or 'replica' after the command to select a database connection" # TODO raise exception

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
SECRET_KEY = os.environ['BOOZER_SECRET_KEY'] # only running the flask server locally


# create the application
app = Flask(__name__)
app.config.from_object(__name__)
Bootstrap(app)

nav = Nav()

@nav.navigation
def mynavbar():
    return Navbar(
        'mysite',
        View("Home",
            "Search",
            "Recent",
            "Yours",
            "New"),
    )

# @nav.navigation
# def mynavbar():
#     return Navbar(
#         'mysite',
#         View('Home', 'index'),
#     )


# @app.before_first_request
# def before_first_request(blazer_user=args.blazer_user):
#     pass # TODO: lookup user id with user name and send it back to the module somehow
#     # g.db = connect_db()
#     # cur = g.db.cursor()
#     # cur.execute("""
#     #     select id from users
#     #         where email = '%s@instacart.com'
#     #     order by created_at desc
#     #     limit 1
#     # """ % blazer_user)
#     # print cur.fetchone()
#     # blazer_id = cur.fetchone()
#     # print blazer_id
#     # b.blazer_id = blazer_id # stores the global.  but for one request only?? how to save to the session?

@app.before_request
def before_request(blazer_id=int(args.blazer_id)):
    g.db = connect_db()
    g.blazer_id = blazer_id

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
            where creator_id = %d
        order by created_at desc
        limit 10
        """ % g.blazer_id)
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
          where user_id = %d
          and query_id is not null
        GROUP BY 1
        ORDER BY 2 desc
        limit 10) as last_ten
        LEFT JOIN blazer_queries q on q.id = last_ten.query_id
        where q.name is not null -- only return if it hasn't been deleted
        """ % g.blazer_id)
    queries = [dict(id=row[0], title=row[1]) for row in cur.fetchall()]
    return render_template('show_queries.html', queries=queries, subheader='Queries you ran recently')


@app.route('/search', methods=['GET', 'POST'])
def run_search():
    cur = g.db.cursor()
    cur.execute("""
        SELECT table_name FROM information_schema.tables
        WHERE table_schema = 'public'
        ORDER BY table_name
        """)
    tables = [dict(name=row[0]) for row in cur.fetchall()]

    queries = []
    if request.args:
        qry_table = request.args.get('query-table')
        flash('you searched for ' + qry_table)
        cur.execute("""
            SELECT q.id
              , q.name
              , q.creator_id
              , u.first_name || ' ' || u.last_name as creator_name
              , q.created_at
              , q.updated_at
              , regexp_replace(q.statement, '(extract[\s\n\t]*\([\s\n\t]*\w+[\s\n\t]+from)', 'i','g') as without_extract_from
              , substring(regexp_replace(lower(q.statement), '(extract[\s\n\t]*\([\s\n\t]*\w+[\s\n\t]+from)', 'i','g') from '(?i)from[\s\n\t]+"?(\w+)') as from_table
            FROM blazer_queries q
              INNER JOIN users u on u.id = q.creator_id
            where substring(regexp_replace(lower(q.statement), '(extract[\s\n\t]*\([\s\n\t]*\w+[\s\n\t]+from)', 'i','g') from '(?i)from[\s\n\t]+"?(\w+)') = '%s'
            order by q.updated_at desc
            limit 100""" % qry_table)
        queries = [dict(id=row[0], title=row[1]) for row in cur.fetchall()] # this is a list of dictionaries

    return render_template('show_queries.html', queries=queries, tables=tables, user_requested_search=True, subheader='Search results')

@app.route('/popular', methods=['GET', 'POST'])
def popular():
    return render_template('under_construction.html')

@app.route('/test', methods=['GET', 'POST'])
def test():
    cur = g.db.cursor()
    cur.execute("""
        SELECT table_name FROM information_schema.tables
        WHERE table_schema = 'public'
        ORDER BY table_name
        """)
    tables = [dict(name=row[0]) for row in cur.fetchall()]
    return render_template('test.html', tables=tables, subheader='Tables', nav=nav)

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
    nav.init_app(app)

