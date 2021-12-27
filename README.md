# Wittgenstein 2022

[![](website.png)](https://wittgenstein.app)

> TODO
> - Social share image (dynamic?)
> - Generate more propositions
> - Clean up Colab and check in (keys!)
> - Medium story

## Training

- LaTeX parsing
- Unicode/HTML rendering
- GPT-3 fine-tuning & inference

[Colab](training.ipynb)

## Frontend

[App Engine Standard Python 3](https://cloud.google.com/appengine/docs/standard/python3/runtime)

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
