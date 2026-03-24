Run
```bash
pybabel compile -d web/translations
```
before executing code to get the translations.
Furthermore, create an .env file
To execute code:
```bash
cd web  # move into web directory
python -m venv .venv  # create venv
source .venv/bin/activate  # activate venv. you might need to use other activate variant
pip install -r ../requirements.txt  # install packages
python app.py  # run website
```
Go to http://localhost:8080
