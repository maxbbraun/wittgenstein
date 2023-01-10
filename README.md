# Wittgenstein 2022

Try it out at [wittgenstein.app](https://wittgenstein.app) and read more on [Medium](https://towardsdatascience.com/i-made-an-ai-read-wittgenstein-then-told-it-to-play-philosopher-ac730298098?sk=17f0f6830659a5d6b5521662cff8a463).

[![](website.png)](https://wittgenstein.app)

## Data

[Colab](data.ipynb) ([interactive](https://colab.research.google.com/github/maxbbraun/wittgenstein/blob/main/data.ipynb))

- [Project Gutenberg](https://www.gutenberg.org/ebooks/5740) LaTeX parsing
- Unicode/HTML rendering
- OpenAI GPT-3 [fine-tuning](https://beta.openai.com/docs/guides/fine-tuning) & [inference](https://beta.openai.com/docs/api-reference)

## Website

[App Engine](https://cloud.google.com/appengine/docs/standard/python3/runtime) & [Firestore](https://firebase.google.com/docs/firestore)

```bash
cd frontend
```

```bash
python3 -m venv venv
. venv/bin/activate
pip install -r requirements.txt
```

```bash
export GOOGLE_CLOUD_PROJECT=$(gcloud config get-value project)
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/service-account.json"
python main.py
```

```bash
gcloud app deploy --project=${GOOGLE_CLOUD_PROJECT}
```

## Bot

[Cloud Run](https://cloud.google.com/run/docs) & [Cloud Scheduler](https://cloud.google.com/scheduler/docs)

```bash
cd bot
```

```bash
python3 -m venv venv
. venv/bin/activate
pip install -r requirements.txt

export GOOGLE_CLOUD_PROJECT=$(gcloud config get-value project)
export GOOGLE_APPLICATION_CREDENTIALS="path/to/service-account.json"

python bot.py  # https://localhost:8080
```

```bash
export GOOGLE_CLOUD_PROJECT=$(gcloud config get-value project)
export SERVICE_NAME=bot-service
export REGION=us-central1

gcloud builds submit \
  --project=${GOOGLE_CLOUD_PROJECT} \
  --region=${REGION} \
  --tag=gcr.io/${GOOGLE_CLOUD_PROJECT}/${SERVICE_NAME}
gcloud run deploy ${SERVICE_NAME} \
  --project=${GOOGLE_CLOUD_PROJECT} \
  --region=${REGION} \
  --image=gcr.io/${GOOGLE_CLOUD_PROJECT}/${SERVICE_NAME} \
  --set-env-vars=GOOGLE_CLOUD_PROJECT=${GOOGLE_CLOUD_PROJECT} \
  --allow-unauthenticated
```

```bash
export JOB_NAME=bot-job
export JOB_URI="$(gcloud run services describe ${SERVICE_NAME} --project=${GOOGLE_CLOUD_PROJECT} --region=${REGION} --format 'value(status.url)')/tweet"

gcloud scheduler jobs create http ${JOB_NAME} \
  --project=${GOOGLE_CLOUD_PROJECT} \
  --location=${REGION} \
  --schedule="0 9 * * 1" \
  --time-zone="America/Los_Angeles" \
  --uri=${JOB_URI} \
  --http-method=post
```
