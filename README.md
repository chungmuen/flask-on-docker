ref: https://testdriven.io/blog/dockerizing-flask-with-postgres-gunicorn-and-nginx/

## Reproduce flask-app in Docker:

`sudo aws s3 cp s3://ez-config-pr-prod/config/nginx-conf/apply_customized_endpoint_configuration.sh - | bash`

`mkdir flask-on-docker && cd flask-on-docker`

`mkdir services && cd services`

`mkdir web && cd web`

`mkdir project`

`python -m venv env`

`source env/bin/activate`

`pip install flask==2.2.2`

`vi project/__init__.py`
```python
from flask import Flask, jsonify
  

app = Flask(__name__)


@app.route("/")
def hello_world():
    return jsonify(hello="world")   

```

`vi manage.py`
```python
from flask.cli import FlaskGroup
  
from project import app


cli = FlaskGroup(app)


if __name__ == "__main__":
    cli()
    
```

`python manage.py run`

`vi requirements.txt`
```
Flask==2.2.2
    
```

`vi Dockerfile`
```dockerfile
# pull official base image
FROM python:3.9-slim-buster

# set work directory
WORKDIR /usr/src/app

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# install dependencies
RUN pip install --upgrade pip
COPY ./requirements.txt /usr/src/app/requirements.txt
RUN pip install -r requirements.txt

# copy project
COPY . /usr/src/app/

```

`cd .. `
`cd ..`
`vi docker-compose.yml`
```docker-compose
version: '3.3'
  
services:
  web:
    build: ./services/web
    command: python manage.py run -h 0.0.0.0
    volumes:
      - ./services/web/:/usr/src/app/
    ports:
      - 8093:5000
    env_file:
      - ./.env.dev
      
```

`vi .env.dev`
```
FLASK_APP=project/__init__.py
FLASK_DEBUG=1
```

`sudo apt install docker-compose`
`sudo docker-compose build`
`sudo docker-compose up -d`
`sudo docker-compose logs -f`
`curl http://172.18.0.2:5000`
`sudo docker-compose stop`

## Reproduce flask-app + PostgresDB in Docker:

`sudo aws s3 cp s3://ez-config-pr-prod/config/nginx-conf/apply_customized_endpoint_configuration.sh - | bash`
`mkdir flask-on-docker && cd flask-on-docker`
`mkdir services && cd services`
`mkdir web && cd web`
`mkdir project`
`python -m venv env`
`source env/bin/activate`
`pip install flask==2.2.2`

`vi project/config.py`
```python
import os
  

basedir = os.path.abspath(os.path.dirname(__file__))


class Config(object):
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite://")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

```

`vi project/__init__.py`
```python
from flask import Flask, jsonify, Response
from flask_sqlalchemy import SQLAlchemy


app = Flask(__name__)
app.config.from_object("project.config.Config")
db = SQLAlchemy(app)


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(128), unique=True, nullable=False)
    active = db.Column(db.Boolean(), default=True, nullable=False)

    def __init__(self, email):
        self.email = email


@app.route("/")
def hello_world():
    return jsonify(hello="world")


@app.route("/usr")
def query_usr():
    res = User.query.all()
    resdic = {}
    for row in res:
        resdic.update({row.id:row.email})
    html_data = f'<pre>{resdic}</pre>'
    response = Response(html_data, content_type='text/html')
    return response

```

`vi manage.py`
```python
from flask.cli import FlaskGroup
  
from project import app, db, User


cli = FlaskGroup(app)


@cli.command("create_db")
def create_db():
    db.drop_all()
    db.create_all()
    db.session.commit()


@cli.command("seed_db")
def seed_db():
    db.session.add(User(email="michael@mherman.org"))
    db.session.commit()


if __name__ == "__main__":
    cli()
    
```

`vi requirements.txt`
```
Flask==2.2.2
Flask-SQLAlchemy==3.0.3
psycopg2-binary==2.9.5
    
```

`vi entrypoint.sh`
```bash
#!/bin/sh
  
if [ "$DATABASE" = "postgres" ]
then
    echo "Waiting for postgres..."

    while ! nc -z $SQL_HOST $SQL_PORT; do
      sleep 0.1
    done

    echo "PostgreSQL started"
fi

python manage.py create_db

exec "$@"

```
`chmod +x services/web/entrypoint.sh`

`vi Dockerfile`
```dockerfile
# pull official base image
FROM python:3.9-slim-buster

# set work directory
WORKDIR /usr/src/app

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# install system dependencies
RUN apt-get update && apt-get install -y netcat

# install dependencies
RUN pip install --upgrade pip
COPY ./requirements.txt /usr/src/app/requirements.txt
RUN pip install -r requirements.txt

# copy project
COPY . /usr/src/app/

# run entrypoint.sh
ENTRYPOINT ["/usr/src/app/entrypoint.sh"]

```

`cd .. `
`cd ..`
`vi docker-compose.yml`
```docker-compose
version: '3.3'
  
services:
  web:
    build: ./services/web
    command: python manage.py run -h 0.0.0.0
    volumes:
      - ./services/web/:/usr/src/app/
    ports:
      - 8093:5000
    env_file:
      - ./.env.dev
  db:
    image: postgres:13-alpine
    volumes:
      - postgres_data:/var/lib/postgresql/data/
    environment:
      - POSTGRES_USER=hello_flask
      - POSTGRES_PASSWORD=hello_flask
      - POSTGRES_DB=hello_flask_dev

volumes:
  postgres_data:
      
```

`vi .env.dev`
```
FLASK_APP=project/__init__.py
FLASK_DEBUG=1
DATABASE_URL=postgresql://hello_flask:hello_flask@db:5432/hello_flask_dev
SQL_HOST=db
SQL_PORT=5432
DATABASE=postgres

```

`sudo apt install docker-compose`
`sudo docker-compose build`
`sudo docker-compose up -d`
`sudo docker-compose logs -f`
`curl http://172.18.0.2:5000`
`sudo docker-compose exec web python manage.py create_db` # Create the table
`sudo docker-compose exec db psql --username=hello_flask --dbname=hello_flask_dev` # Ensure the users table was created
`sudo docker volume inspect flaskondocker_postgres_data` # Check that the volume was created
`sudo docker-compose exec web python manage.py seed_db` # add sample users to the users table
`sudo docker-compose exec db psql --username=hello_flask --dbname=hello_flask_dev` # Ensure the user entry was created
`sudo docker-compose stop`
go to the URL: `https://jupyter.moclodbapi.ez.sats.cloud/custom3/usr`# to check if the app functions with the postgresDB
`sudo docker-compose stop`