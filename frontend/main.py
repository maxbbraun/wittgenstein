from cachetools import cached
from cachetools import TTLCache
from concurrent.futures import ThreadPoolExecutor
from google.api_core.exceptions import GoogleAPIError
from google.cloud.secretmanager import SecretManagerServiceClient
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
from google.cloud.firestore_v1.base_query import FieldFilter
from google.cloud.firestore_v1.base_vector_query import DistanceMeasure
from google.cloud.firestore_v1.field_path import FieldPath
from google.cloud.firestore_v1.vector import Vector
from openai import OpenAI
import os
import random
import re
from urllib.parse import quote
from urllib.parse import unquote

# The model used and expected for any text embeddings.
EMBEDDING_MODEL = 'text-embedding-3-large'

# The number of dimensions used and expected for any text embeddings.
EMBEDDING_DIMENSIONS = 256

app = Flask(__name__)
minify(app=app, caching_limit=0, passive=True)


def _validate_id(id):
    if not id:
        # The ID must be non-empty.
        return False

    # The ID must match a regular expression.
    pattern = re.compile(r'^[0-9a-zA-Z]{20}$')
    match = pattern.match(id)
    return bool(match)


def _random_proposition(exclude_id=None):
    return _find_proposition(id=None, exclude_id=exclude_id)


@firestore.transactional
def _random_query(transaction, propositions_ref, metadata_ref,
                  exclude_id=None):
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
    query_ref = propositions_ref.where(
        filter=FieldFilter('index', '==', random_index)).limit(1)
    try:
        proposition = next(query_ref.stream())
    except StopIteration:
        # The query returned no results.
        proposition = None

    return proposition


def _find_proposition(id, exclude_id=None):
    # Get the propositions from Firestore.
    db = firestore.Client()
    propositions_ref = db.collection('propositions')

    if id:
        # Only allow well-formed IDs in the query.
        if not _validate_id(id):
            abort(404)  # Not Found
    else:
        # Select a random proposition.
        transaction = db.transaction()
        metadata_ref = db.collection('metadata').document('propositions')
        proposition = _random_query(transaction, propositions_ref,
                                    metadata_ref, exclude_id=exclude_id)

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


def _render_page(id, german, english):
    return render_template('index.html',
                           id=id,
                           german=german,
                           english=english)


def _render_json(id, german, english):
    return {
        'id': id,
        'german': german,
        'english': english}


def _render_static(filename, mimetype):
    return send_from_directory(app.static_folder, filename, mimetype=mimetype)


def _previews_bucket_name():
    google_cloud_project = os.environ['GOOGLE_CLOUD_PROJECT']
    return f'{google_cloud_project}-previews'


def _illustrations_bucket_name():
    google_cloud_project = os.environ['GOOGLE_CLOUD_PROJECT']
    return f'{google_cloud_project}-illustrations'


@cached(cache=TTLCache(maxsize=10, ttl=24*60*60))  # Cache 10 for 1 day.
def _secret(key):
    # Retrieve a value from the Google Cloud Secret Manager.
    try:
        google_cloud_project = os.environ['GOOGLE_CLOUD_PROJECT']
        secretmanager_client = SecretManagerServiceClient()
        secret_path = SecretManagerServiceClient.secret_version_path(
            project=google_cloud_project, secret=key, secret_version='latest')
        return secretmanager_client.access_secret_version(
            name=secret_path).payload.data.decode('UTF-8')
    except (KeyError, GoogleAPIError) as e:
        raise ValueError(f'Failed to retrieve secret: {e}')


def _sanitize(query):
    if not query:
        return None

    # Remove any URL encoding.
    query = unquote(query)

    # Enforce a maximum query length. The hard limit for the model
    # text-embedding-ada-002 is 8191 tokens (~30k characters).
    query = query[:10000]

    return query


@cached(cache=TTLCache(maxsize=100, ttl=24*60*60))  # Cache 100 for 1 day.
def _embedding(text):
    openai_client = OpenAI(api_key=_secret('openai_api_key'))

    # Embed the text using the OpenAI API.
    embedding_result = openai_client.embeddings.create(
        input=text,
        model=EMBEDDING_MODEL,
        dimensions=EMBEDDING_DIMENSIONS)
    return embedding_result.data[0].embedding


@cached(cache=TTLCache(maxsize=1, ttl=24*60*60))  # Cache 1 for 1 day.
def _proposition_count():
    # Count all propositions in the search collection.
    count = firestore.Client().collection('tractatus').count().get()
    return count[0][0].value


def _vector_scores(vector_field, query_embedding, proposition_count):
    # Search one language's proposition embeddings.
    query = firestore.Client().collection('tractatus').select(['score'])
    documents = query.find_nearest(
        vector_field=vector_field,
        query_vector=Vector(query_embedding),
        distance_measure=DistanceMeasure.DOT_PRODUCT,
        limit=proposition_count,
        distance_result_field='score').stream()
    return {document.id: document.get('score') for document in documents}


def _search(query):
    if not query:
        return None

    with ThreadPoolExecutor(max_workers=2) as executor:
        # Embed the query and count the propositions in parallel.
        embedding = executor.submit(_embedding, query)
        count = executor.submit(_proposition_count)
        query_embedding = embedding.result()
        proposition_count = count.result()

        # Search the German and English embeddings in parallel.
        german = executor.submit(
            _vector_scores,
            'german_embedding', query_embedding, proposition_count)
        english = executor.submit(
            _vector_scores,
            'english_embedding', query_embedding, proposition_count)
        german_scores = german.result()
        english_scores = english.result()

    # Both searches must rank the same propositions.
    if german_scores.keys() != english_scores.keys():
        raise ValueError('Mismatched vector search results')

    # Sort by the sum of the German and English similarities.
    return sorted(
        german_scores,
        key=lambda id: german_scores[id] + english_scores[id],
        reverse=True)


@app.route('/')
@decorators.minify(html=True, js=True, cssless=True)
def random_page():
    # Serve the main page with a random proposition.
    id, german, english = _random_proposition()
    return _render_page(id=id, german=german, english=english)


@app.route('/<id>')
@decorators.minify(html=True, js=True, cssless=True)
def id_page(id):
    # Serve the main page with a specific proposition (via its ID).
    id, german, english = _find_proposition(id=id)
    return _render_page(id=id, german=german, english=english)


@app.route('/style.css')
def style_css():
    return _render_static(filename='style.css', mimetype='text/css')


@app.route('/random.json')
def random_json():
    # Optionally exclude a particular proposition by ID.
    exclude_id = request.args.get('exclude')

    # Serve a random proposition as raw data.
    id, german, english = _random_proposition(exclude_id=exclude_id)
    return _render_json(id=id, german=german, english=english)


@app.route('/robots.txt')
def robots_txt():
    return _render_static(filename='robots.txt', mimetype='text/plain')


@app.route('/sitemap.txt')
def sitemap_txt():
    # Get all proposition IDs from Firestore.
    db = firestore.Client()
    propositions_ref = db.collection('propositions')
    query_ref = (propositions_ref
                 .select([])
                 .order_by(FieldPath.document_id()))

    # Create a list of fully qualified proposition URLs.
    urls = []
    for proposition in query_ref.stream():
        url = url_for('id_page', id=proposition.id, _external=True)
        urls.append(url)

    # Add the search page.
    urls.append(url_for('search_page', _external=True))

    # Return the list of URLs as plain text.
    response = make_response('\n'.join(urls) + '\n', 200)
    response.mimetype = 'text/plain'
    return response


@app.route('/favicon.ico')
def favicon_ico():
    return _render_static(filename='favicon.ico', mimetype='image/x-icon')


@app.route('/ludwig.png')
def ludwig_png():
    return _render_static(filename='ludwig.png', mimetype='image/png')


@app.route('/ludwig-vr.png')
def ludwig_vr_png():
    return _render_static(filename='ludwig-vr.png', mimetype='image/png')


@app.route('/search.png')
def search_png():
    return _render_static(filename='search.png', mimetype='image/png')


@app.route('/preview/<id>.html')
def preview_html(id):
    # Look up the proposition to preview.
    id, german, english = _find_proposition(id=id)

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
    if not _validate_id(id):
        abort(404)  # Not Found

    # Create a reference to the preview image in Google Cloud Storage.
    storage_client = storage.Client()
    previews_bucket = storage_client.bucket(_previews_bucket_name())
    preview_blob_name = f'{id}.png'
    preview_blob = previews_bucket.blob(preview_blob_name)

    if not preview_blob.exists():
        abort(404)  # Not Found.

    # Redirect to the preview image URL.
    return redirect(preview_blob.public_url)


@app.route('/illustration.png')
def illustration_png():
    # Expect the proposition ID to be passed as a query parameter.
    id = request.args.get('id')

    # Only allow well-formed IDs in the lookup.
    if not _validate_id(id):
        abort(404)  # Not Found

    # Create a reference to the illustration in Google Cloud Storage.
    storage_client = storage.Client()
    illustrations_bucket = storage_client.bucket(_illustrations_bucket_name())
    illustration_blob_name = f'{id}.png'
    illustration_blob = illustrations_bucket.blob(illustration_blob_name)

    if not illustration_blob.exists():
        abort(404)  # Not Found.

    # Redirect to the illustration URL.
    return redirect(illustration_blob.public_url)


@app.route('/error.png')
def error_png():
    # Retrieve the error image from Google Cloud Storage.
    storage_client = storage.Client()
    illustrations_bucket = storage_client.bucket(_illustrations_bucket_name())
    error_blob = illustrations_bucket.blob('error.png')

    if not error_blob.exists():
        abort(404)  # Not Found.

    # Redirect to the error image URL.
    return redirect(error_blob.public_url)


@app.route('/about')
def about_link():
    return redirect('https://medium.com/data-science/'
                    'i-made-an-ai-read-wittgenstein-'
                    'then-told-it-to-play-philosopher-'
                    'ac730298098')


@app.route('/code')
def code_link():
    return redirect('https://github.com/maxbbraun/wittgenstein')


@app.route('/share')
def share_link():
    # Expect the proposition ID to be passed as a query parameter.
    id = request.args.get('id')

    # Only allow well-formed IDs in the link.
    if not _validate_id(id):
        abort(404)  # Not Found

    # Construct the Twitter URL with text and a link.
    link = url_for('id_page', id=id, _external=True)
    text = quote(f'Thus Spoke @Wittgenstein22 {link}')
    twitter_url = f'https://twitter.com/intent/tweet?text={text}'

    # Redirect to the sharing URL.
    return redirect(twitter_url)


@app.route('/search')
@decorators.minify(html=True, js=True, cssless=True)
def search_page():
    # A search query request parameter is optional.
    query = _sanitize(request.args.get('q'))

    if query:
        ranking = _search(query)
    else:
        ranking = None

    # Serve the search results page.
    return render_template('search.html', query=query, ranking=ranking)


@app.route('/search.json')
def search_json():
    # Expect the search query to be passed as a request parameter.
    query = _sanitize(request.args.get('q'))

    # Perform the proposition search.
    ranking = _search(query)

    # Return the proposition ranking response as JSON.
    if ranking:
        return {
            'query': query,
            'ranking': ranking}
    else:
        return {
            'query': query or None,
            'ranking': None}


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)
