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
gcloud app deploy
```
