from flask import Flask
from flask import render_template
from flask import send_from_directory
from flask_minify import decorators
from flask_minify import minify

from google.cloud import bigquery

app = Flask(__name__)
minify(app=app, caching_limit=0, passive=True)


def random_proposition():
    return find_proposition(None)


def find_proposition(id):
    client = bigquery.Client()

    query = ('SELECT id, german, english '
             'FROM tractatus.propositions ')

    if id:
        query += "WHERE id = '%s' " % id
    else:
        query += ("WHERE number = '8' "
                  "ORDER BY RAND() ")

    query += 'LIMIT 1'
    job = client.query(query)
    rows = job.result()

    try:
        row = next(rows)
        return row.id, row.german, row.english
    except StopIteration:
        # TODO
        return '0', '?', '?'


@app.route('/')
@decorators.minify(html=True, js=True, cssless=True)
def index():
    id, german, english = random_proposition()
    return render_template('index.html', id=id, german=german, english=english)


@app.route('/proposition')
def proposition():
    id, german, english = random_proposition()
    return {
        'id': id,
        'german': german,
        'english': english}


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
