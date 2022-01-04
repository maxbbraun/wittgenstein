from flask import Flask
from flask import render_template
from flask import send_from_directory
from flask_minify import decorators
from flask_minify import minify
from google.cloud import firestore
import random
import re

app = Flask(__name__)
minify(app=app, caching_limit=0, passive=True)


def validate_id(id):
    if not id:
        # The ID must be non-empty.
        return False

    # The ID must match a regular expression.
    pattern = re.compile(r'^[0-9a-zA-Z]{20}$')
    match = pattern.match(id)
    return bool(match)


def random_proposition():
    return find_proposition(None)


@firestore.transactional
def random_query(transaction, propositions_ref, metadata_ref):
    # Look up the current total number of propositions.
    metadata = metadata_ref.get(transaction=transaction)
    total = metadata.get('total')

    # Pick one index from a uniform random distribution.
    random_index = random.randint(0, total)

    # Retrieve the proposition with that index.
    query_ref = propositions_ref.where(
        'index', '==', random_index).limit(1)
    try:
        proposition = next(query_ref.stream())
    except StopIteration:
        # The query returned no results.
        proposition = None

    return proposition


def find_proposition(id):
    # Only allow well-formed IDs in the query.
    if not validate_id(id):
        id = None

    # Get the propositions from Firestore.
    db = firestore.Client()
    propositions_ref = db.collection('propositions')

    if not id:
        # Select a random proposition.
        transaction = db.transaction()
        metadata_ref = db.collection('metadata').document('propositions')
        proposition = random_query(transaction, propositions_ref, metadata_ref)

        if proposition:
            return (proposition.id,
                    proposition.get('german'),
                    proposition.get('english'))
        else:
            error = 'No propositions found'
            return '', error, error

    # Look up a proposition by its ID.
    proposition_ref = propositions_ref.document(id)
    proposition = proposition_ref.get()

    if proposition.exists:
        return (proposition.id,
                proposition.get('german'),
                proposition.get('english'))
    else:
        error = 'Proposition not found'
        return '', error, error


def render_page(id, german, english):
    return render_template('index.html',
                           id=id,
                           german=german,
                           english=english)


def render_json(id, german, english):
    return {
        'id': id,
        'german': german,
        'english': english}


def render_static(filename, mimetype):
    return send_from_directory('static', filename, mimetype=mimetype)


@app.route('/')
@decorators.minify(html=True, js=True, cssless=True)
def random_page():
    # Serve the main page with a random proposition.
    id, german, english = random_proposition()
    return render_page(id=id, german=german, english=english)


@app.route('/<id>')
@decorators.minify(html=True, js=True, cssless=True)
def id_page(id):
    # Serve the main page with a specific proposition (via its ID).
    id, german, english = find_proposition(id)
    return render_page(id=id, german=german, english=english)


@app.route('/proposition')
def random_json():
    # Serve a random proposition as raw data.
    id, german, english = random_proposition()
    return render_json(id=id, german=german, english=english)


@app.route('/robots.txt')
def robots_txt():
    return render_static(filename='robots.txt', mimetype='text/plain')


@app.route('/favicon.ico')
def favicon_ico():
    return render_static(filename='favicon.ico', mimetype='image/x-icon')


@app.route('/ludwig.png')
def ludwig_png():
    return render_static(filename='ludwig.png', mimetype='image/png')


@app.route('/social.png')
def social_png():
    return render_static(filename='social.png', mimetype='image/png')


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)
