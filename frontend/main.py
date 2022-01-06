from flask import Flask
from flask import render_template
from flask import request
from flask import send_from_directory
from flask_minify import decorators
from flask_minify import minify
from google.cloud import firestore
from google.cloud.firestore_v1.field_path import FieldPath
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


def random_proposition(exclude_id=None):
    return find_proposition(id=None, exclude_id=exclude_id)


@firestore.transactional
def random_query(transaction, propositions_ref, metadata_ref, exclude_id=None):
    # Look up the current total number of propositions.
    metadata = metadata_ref.get(transaction=transaction)
    total = metadata.get('total')

    # Pick an index from a uniform random distribution, optionally excluding
    # one proposition's index.
    random_range = range(total)
    if exclude_id:
        exclude_doc = propositions_ref.document(exclude_id).get()
        if exclude_doc.exists:
            exclude_index = exclude_doc.get('index')
            random_range = list(random_range)
            random_range.remove(exclude_index)
    random_index = random.choice(random_range)

    # Retrieve the proposition with that index.
    query_ref = propositions_ref.where('index', '==', random_index).limit(1)
    try:
        proposition = next(query_ref.stream())
    except StopIteration:
        # The query returned no results.
        proposition = None

    return proposition


def find_proposition(id, exclude_id=None):
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
        proposition = random_query(transaction, propositions_ref, metadata_ref,
                                   exclude_id=exclude_id)

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
    id, german, english = find_proposition(id=id)
    return render_page(id=id, german=german, english=english)


@app.route('/random.json')
def random_json():
    # Optionally exclude a particular proposition by ID.
    exclude_id = request.args.get('exclude')

    # Serve a random proposition as raw data.
    id, german, english = random_proposition(exclude_id=exclude_id)
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


@app.route('/ludwig-vr.png')
def ludwig_vr_png():
    return render_static(filename='ludwig-vr.png', mimetype='image/png')


@app.route('/social.png')
def social_png():
    return render_static(filename='social.png', mimetype='image/png')


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)
