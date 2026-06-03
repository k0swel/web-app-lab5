from flask import Flask, request, session

from auth import auth_bp
from db import close_db, init_db, log_visit
from users import users_bp
from visits import visits_bp
import os

app = Flask(__name__, template_folder='../templates')
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret')

app.teardown_appcontext(close_db)
app.register_blueprint(auth_bp)
app.register_blueprint(users_bp)
app.register_blueprint(visits_bp)


@app.before_request
def record_visit():
    if (not request.path.startswith('/static')
            and '.' not in request.path
            and request.method == 'GET'):
        log_visit(session.get('user_id'), request.path)


if __name__ == '__main__':
    with app.app_context():
        init_db()
    app.run(host='localhost', port=5001)
