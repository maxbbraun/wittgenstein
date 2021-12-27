# Wittgenstein 2022

[![](website.png)](https://wittgenstein.app)

> TODO
> - Social share image (Custom per proposition?)
> - Generate more propositions
> - Write Medium story
> - Make GitHub repo public
> - Update 'About' link
> - Publish in Medium publication (Other magazine?)

## Training

[Colab](training.ipynb)

- [Project Gutenberg](https://www.gutenberg.org/ebooks/5740) LaTeX parsing
- Unicode/HTML rendering
- OpenAI GPT-3 [fine-tuning](https://beta.openai.com/docs/guides/fine-tuning) & [inference](https://beta.openai.com/docs/api-reference)

## Frontend

[App Engine](https://cloud.google.com/appengine/docs/standard/python3/runtime) & [BigQuery](https://cloud.google.com/bigquery/docs/quickstarts/quickstart-cloud-console)

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
gcloud app deploy
```
