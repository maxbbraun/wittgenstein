# Wittgenstein 2022

[![](website.png)](https://wittgenstein.app)

> TODO
> - Write Medium story
> - Generate more propositions
> - Make GitHub repo public
> - Update 'About' link
> - Publish in Medium publication (Other magazine?)
> - Post Twitter thread
> - Add to braun.design
> - Try Google LaMDA, DeepMind Gopher

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
