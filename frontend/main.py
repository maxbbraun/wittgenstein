from flask import abort
from flask import Flask
from flask import make_response
from flask import render_template
from flask import redirect
from flask import request
from flask import send_from_directory
from flask import url_for
from flask_minify import decorators
from flask_minify import minify
from google.cloud import firestore
from google.cloud import storage
from google.cloud.firestore_v1.field_path import FieldPath
import os
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
    random.seed()
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
    # Get the propositions from Firestore.
    db = firestore.Client()
    propositions_ref = db.collection('propositions')

    if id:
        # Only allow well-formed IDs in the query.
        if not validate_id(id):
            abort(404)  # Not Found
    else:
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
            abort(500)  # Internal Server Error

    # Look up a proposition by its ID.
    proposition_ref = propositions_ref.document(id)
    proposition = proposition_ref.get()

    if proposition.exists:
        return (proposition.id,
                proposition.get('german'),
                proposition.get('english'))
    else:
        abort(404)  # Not Found


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


def previews_bucket_name():
    google_cloud_project = os.environ['GOOGLE_CLOUD_PROJECT']
    return f'{google_cloud_project}-previews'


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


@app.route('/sitemap.txt')
def sitemap_txt():
    # Get all propositions from Firestore.
    db = firestore.Client()
    propositions_ref = db.collection('propositions')
    query_ref = propositions_ref.order_by(FieldPath.document_id())

    # Create a list of fully qualified proposition URLs.
    urls = []
    for proposition in query_ref.stream():
        url = url_for('id_page', id=proposition.id, _external=True)
        urls.append(url)

    # Return the list of URLs as plain text.
    response = make_response('\n'.join(urls), 200)
    response.mimetype = 'text/plain'
    return response


@app.route('/favicon.ico')
def favicon_ico():
    return render_static(filename='favicon.ico', mimetype='image/x-icon')


@app.route('/ludwig.png')
def ludwig_png():
    return render_static(filename='ludwig.png', mimetype='image/png')


@app.route('/ludwig-vr.png')
def ludwig_vr_png():
    return render_static(filename='ludwig-vr.png', mimetype='image/png')


@app.route('/preview/<id>.html')
def preview_html(id):
    # Look up the proposition to preview.
    id, german, english = find_proposition(id=id)

    # Pick randomly (but consistently per ID) between the two picture versions.
    random.seed(id)
    if random.getrandbits(1):
        ludwig_url = url_for('ludwig_png')
    else:
        ludwig_url = url_for('ludwig_vr_png')

    # Render the preview page.
    return render_template('preview.html',
                           id=id,
                           german=german,
                           english=english,
                           ludwig_url=ludwig_url)


@app.route('/preview/<id>.png')
def preview_png(id):
    # Only allow well-formed IDs in the lookup.
    if not validate_id(id):
        abort(404)  # Not Found

    # Create a reference to the preview image in Google Cloud Storage.
    storage_client = storage.Client()
    previews_bucket = storage_client.bucket(previews_bucket_name())
    preview_blob_name = f'{id}.png'
    preview_blob = previews_bucket.blob(preview_blob_name)

    if not preview_blob.exists():
        abort(404)  # Not Found.

    # Redirect to the preview image URL.
    return redirect(preview_blob.public_url)


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)
