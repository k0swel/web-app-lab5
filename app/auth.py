from functools import wraps

from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash

from db import query

auth_bp = Blueprint('auth', __name__)

ADMIN_ROLE = 'Администратор'


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            flash('Для доступа к этой странице необходимо войти в систему.', 'warning')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated


def check_rights(action):
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if 'user_id' not in session:
                flash('Для доступа к этой странице необходимо войти в систему.', 'warning')
                return redirect(url_for('auth.login'))

            role = session.get('user_role')
            uid  = session.get('user_id')
            allowed = False

            if role == ADMIN_ROLE:
                allowed = action in ('create_user', 'edit_user', 'view_user',
                                     'delete_user', 'view_visits')
            else:
                if action == 'edit_user':
                    allowed = kwargs.get('user_id') == uid
                elif action == 'view_user':
                    allowed = kwargs.get('user_id') == uid
                elif action == 'view_visits':
                    allowed = True

            if not allowed:
                flash('У вас недостаточно прав для доступа к данной странице.', 'danger')
                return redirect(url_for('users.index'))

            return f(*args, **kwargs)
        return decorated
    return decorator


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('users.index'))

    error = None
    if request.method == 'POST':
        login_val = request.form.get('login', '').strip()
        password  = request.form.get('password', '')

        user = query(
            '''SELECT u.*, r.name AS role_name FROM users u
               LEFT JOIN roles r ON u.role_id = r.id
               WHERE u.login = %s''',
            (login_val,), one=True
        )

        if user is None or not check_password_hash(user['password_hash'], password):
            error = 'Неверный логин или пароль'
        else:
            session.clear()
            session['user_id']    = user['id']
            session['user_login'] = user['login']
            session['user_role']  = user['role_name']
            return redirect(url_for('users.index'))

    return render_template('login.html', error=error)


@auth_bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('auth.login'))
