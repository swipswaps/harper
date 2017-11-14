import os
import sqlite3
import datetime as dt
from flask import (
        Flask,
        request,
        session, g,
        redirect,
        url_for,
        abort,
        render_template,
        flash,
    )

app = Flask(__name__)
app.config.from_object(__name__)

app.config.update(dict(
    DATABASE=os.path.join(app.root_path, 'harper.sq3'),
    SECRET_KEY='development key',
    USERNAME='admin',
    PASSWORD='default'
))
app.config.from_envvar('HARPER_SETTINGS', silent=True)
app.jinja_env.add_extension('pypugjs.ext.jinja.PyPugJSExtension')

def connect_db():
    """Connects to the specific database."""
    rv = sqlite3.connect(app.config['DATABASE'])
    rv.row_factory = sqlite3.Row
    return rv

def get_db():
    """Opens a new database connection if there is none yet for the
    current application context.
    """
    if not hasattr(g, 'sqlite_db'):
        g.sqlite_db = connect_db()
    return g.sqlite_db

@app.teardown_appcontext
def close_db(error):
    """Closes the database again at the end of the request."""
    if hasattr(g, 'sqlite_db'):
        g.sqlite_db.close()

def init_db():
    db = get_db()
    with app.open_resource('schema.sql', mode='r') as f:
        db.cursor().executescript(f.read())
    db.commit()

@app.cli.command('initdb')
def initdb_command():
    """Initializes the database."""
    init_db()
    print('Initialized the database.')

@app.route('/')
def show_log():
    db = get_db()
    cur = db.execute('select measurement, timestamp from moisture order by id desc')
    moistures = cur.fetchall()
    return render_template('show_log.pug', moistures=moistures)

@app.route('/moisture', methods=['POST'])
def add_measurement():
    if request.form['measurement']:
        db = get_db()
        db.execute('insert into moisture (measurement, timestamp) values (?, ?)',
                     [request.form['measurement'], dt.datetime.utcnow()])
        db.commit()
        flash('New measurement was successfully posted')
    else:
        flash('Invalid measurement submitted')

    return redirect(url_for('show_log'))
