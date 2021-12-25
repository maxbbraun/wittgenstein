# Wittgenstein 2022

## Frontend

```bash
cd frontend
```

### Test

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

### Deploy

```bash
gcloud app deploy
```

## Backend

https://colab.research.google.com/drive/1MW4av42BfNP_24lcV99Zi3SqBd4WH5O1?usp=chrome_ntp#scrollTo=RcYFHdyhd23H

# TODO
- Permalink to generated proposition
- Social share image with proposition and link to website
- Cloud Function to generate and add to database
- Generate more propositions
- Clean up Colab and check in (keys!)
