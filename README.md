# tietaja

## Create & Activate virtual environment

### Linux

```sh
tietaja> python3 -m venv .
tietaja> source bin/activate
```

### Windows

```sh
tietaja> python3 -m venv .
tietaja> tutorial-env\Scripts\activate.bat
```

## Install dependencies

```sh
pip install -r requirements.txt
```
## Environment variables

Add a file called `.env` in the parent folder of the project (this will be the deployment folder) with the contents:

```
FLASK_APP=tietaja
FLASK_ENV=development
```

`python-dotenv` will grab the environment variables from `.env` file and make them visible for the flask application

## Run

Inside the deployment folder, run:

```
flask init-db
flask run
```
