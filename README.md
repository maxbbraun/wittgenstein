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

- LaTeX parsing
- Unicode/HTML rendering
- GPT-3 fine-tuning & inference

## Frontend

[App Engine](https://cloud.google.com/appengine/docs/standard/python3/runtime)

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
