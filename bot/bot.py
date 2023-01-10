from flask import abort
from flask import Flask
from google.api_core.exceptions import GoogleAPIError
from google.cloud.secretmanager import SecretManagerServiceClient
import logging
import os
import re
import requests
from requests.exceptions import RequestException
from requests_oauthlib import OAuth1Session

app = Flask(__name__)


def _secret(key):
    """Retrieves a value from the Google Cloud Secret Manager."""

    try:
        google_cloud_project = os.environ['GOOGLE_CLOUD_PROJECT']
        secretmanager_client = SecretManagerServiceClient()
        secret_path = SecretManagerServiceClient.secret_version_path(
            project=google_cloud_project, secret=key, secret_version='latest')
        return secretmanager_client.access_secret_version(
            name=secret_path).payload.data.decode('UTF-8')
    except (KeyError, GoogleAPIError) as e:
        raise ValueError(f'Failed to retrieve secret: {e}')


def _twitter_oauth():
    """Creates a new Twitter OAuth session."""

    try:
        consumer_key = _secret('twitter_consumer_key')
        consumer_secret = _secret('twitter_consumer_secret')
        access_token = _secret('twitter_access_token')
        access_token_secret = _secret('twitter_access_token_secret')
    except ValueError as e:
        abort(500, description=str(e))

    return OAuth1Session(
        consumer_key,
        client_secret=consumer_secret,
        resource_owner_key=access_token,
        resource_owner_secret=access_token_secret)


def _send_tweet(text):
    """Sends a tweet with the specified text."""

    try:
        oauth = _twitter_oauth()
        response = oauth.post(
            'https://api.twitter.com/2/tweets',
            json={'text': text})

        if response.status_code != 201:
            abort(500, description=f'{response.status_code} {response.text}')

        json_response = response.json()
        return json_response['data']['id']
    except (RequestException, TypeError, ValueError, KeyError) as e:
        abort(500, description=str(e))


def _random_proposition(exclude_id):
    """Creates a link to a random proposition, optionally excluding an ID."""

    # Retrieve a random Wittgenstein 2022 proposition ID.
    try:
        response = requests.get('https://wittgenstein.app/random.json',
                                params={'exclude': exclude_id})
        json_response = response.json()
        proposition_id = json_response['id']
        return f'https://wittgenstein.app/{proposition_id}'
    except (RequestException, TypeError, ValueError, KeyError) as e:
        abort(500, description=str(e))


def _latest_proposition():
    """Looks up the latest tweeted proposition ID."""

    try:
        oauth = _twitter_oauth()
        user_id = '1477366642992730112'  # @Wittgenstein22
        response = oauth.get(
            f'https://api.twitter.com/2/users/{user_id}/tweets',
            params={'max_results': 5,
                    'exclude': 'retweets,replies',
                    'tweet.fields': 'entities'})

        if response.status_code != 200:
            abort(500, description=f'{response.status_code} {response.text}')

        # Extract the URL from the tweet.
        json_response = response.json()
        url = json_response['data'][0]['entities']['urls'][0]['expanded_url']

        # Parse the ID from the URL.
        match = re.search(r'https?://wittgenstein\.app/([0-9a-zA-Z]{20})', url)
        if not match:
            raise ValueError(f'Failed to parse ID from URL: {url}')
        return match.group(1)
    except (RequestException, TypeError, ValueError, KeyError,
            IndexError) as e:
        logging.warning(f'Error finding latest tweeted proposition: {e}')
        return None


@app.route('/tweet', methods=['POST'])
def tweet():
    # Tweet a random proposition, excluding the most recently tweeted.
    exclude_id = _latest_proposition()
    proposition_link = _random_proposition(exclude_id)
    tweet_id = _send_tweet(proposition_link)

    return tweet_id


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(debug=True, host='0.0.0.0', port=port)
