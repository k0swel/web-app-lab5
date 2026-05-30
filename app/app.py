from flask import Flask

from auth import auth_bp
from db import close_db
from users import users_bp
import os
app = Flask(__name__, template_folder='../templates')
app.secret_key = f'{os.environ.get('SECRET_KEY')}'

app.teardown_appcontext(close_db)
app.register_blueprint(auth_bp)
app.register_blueprint(users_bp)

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000, debug=True)
