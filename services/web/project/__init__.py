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
