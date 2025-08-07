import sqlite3
from flask import Flask, render_template, g

DATABASE = 'scans.db'

app = Flask(__name__)

def get_db():
    """Opens a new database connection if there is none yet for the current application context."""
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        # This makes the rows returned by fetchall() behave like dictionaries
        db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_connection(exception):
    """Closes the database again at the end of the request."""
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

@app.route('/')
def index():
    """Main dashboard route. Fetches and displays scan history."""
    try:
        db = get_db()
        cursor = db.cursor()
        # Fetch all records, ordering by the most recent scan first
        cursor.execute("SELECT * FROM scan_history ORDER BY scan_time DESC")
        scans = cursor.fetchall()
        return render_template('index.html', scans=scans)
    except sqlite3.OperationalError:
        # This can happen if the database or table doesn't exist yet.
        # We'll return an empty list and a message.
        return render_template('index.html', scans=[], error="Database or table not found. Run the main scanner script first.")
    except Exception as e:
        # Catch other potential errors
        return render_template('index.html', scans=[], error=f"An error occurred: {e}")

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8080)
