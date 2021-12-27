from flask import Flask
from flask import render_template
from flask import send_from_directory
from flask_minify import decorators
from flask_minify import minify
from google.cloud import bigquery
import re

app = Flask(__name__)
minify(app=app, caching_limit=0, passive=True)


def validate_id(id):
    if not id:
        # The ID must be non-empty.
        return False

    # The ID must match a regular expression.
    pattern = re.compile(r'^[0-9a-f]{12}$')
    match = pattern.match(id)
    return bool(match)


def random_proposition():
    return find_proposition(None)


def find_proposition(id):
    # Only allow well-formed IDs in the query.
    if not validate_id(id):
        id = None

    # Compose the query.
    client = bigquery.Client()
    query = ('SELECT id, german, english '
             'FROM tractatus.propositions ')
    if id:
        # Pick the proposition with the provided ID.
        query += "WHERE id = '%s' " % id
    else:
        # Pick a random proposition matching basic requirements.
        query += ("WHERE number = '8' "
                  "ORDER BY RAND() ")
    query += 'LIMIT 1'

    # Make the request.
    job = client.query(query)
    rows = job.result()

    try:
        # Read the first row.
        row = next(rows)
    except StopIteration:
        # The query contained no propositions.
        error = 'Not found'
        return '', error, error

    return row.id, row.german, row.english


def render_json(id, german, english):
    return {
        'id': id,
        'german': german,
        'english': english}


@app.route('/')
@decorators.minify(html=True, js=True, cssless=True)
def random_page():
    # Serve the main page with a random proposition.
    id, german, english = random_proposition()
    return render_template('index.html', id=id, german=german, english=english)


@app.route('/<id>')
@decorators.minify(html=True, js=True, cssless=True)
def proposition_page(id):
    # Serve the main page with a specific proposition (via its ID).
    id, german, english = find_proposition(id)
    return render_template('index.html', id=id, german=german, english=english)


@app.route('/proposition')
def random_json():
    # Serve a random proposition as raw data.
    id, german, english = random_proposition()
    return render_json(id=id, german=german, english=english)


@app.route('/proposition/<id>')
def proposition_json(id):
    # Serve a specific proposition (via its ID) as raw data.
    id, german, english = find_proposition(id)
    return render_json(id=id, german=german, english=english)


@app.route('/robots.txt')
def robots():
    return send_from_directory('static',
                               'robots.txt',
                               mimetype='text/plain')


@app.route('/favicon.ico')
def favicon():
    return send_from_directory('static',
                               'favicon.ico',
                               mimetype='image/x-icon')


@app.route('/ludwig.png')
def ludwig():
    return send_from_directory('static',
                               'ludwig.png',
                               mimetype='image/png')


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)
