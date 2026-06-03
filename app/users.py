import pymysql.err

from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from auth import check_rights, login_required
from db import execute, query
from validators import validate_login, validate_password

users_bp = Blueprint('users', __name__)


def get_roles():
    return query('SELECT * FROM roles ORDER BY name')


def get_user(user_id):
    return query(
        '''SELECT u.*, r.name AS role_name FROM users u
           LEFT JOIN roles r ON u.role_id = r.id
           WHERE u.id = %s''',
        (user_id,), one=True
    )


@users_bp.route('/')
@login_required
def index():
    users = query(
        '''SELECT u.*, r.name AS role_name FROM users u
           LEFT JOIN roles r ON u.role_id = r.id
           ORDER BY u.id'''
    )
    return render_template('users/index.html', users=users)


@users_bp.route('/users/<int:user_id>')
@check_rights('view_user')
def user_view(user_id):
    user = get_user(user_id)
    if user is None:
        flash('Пользователь не найден.', 'danger')
        return redirect(url_for('users.index'))
    return render_template('users/view.html', user=user)


@users_bp.route('/users/create', methods=['GET', 'POST'])
@check_rights('create_user')
def user_create():
    roles = get_roles()
    errors = {}
    form_data = {}

    if request.method == 'POST':
        form_data = {
            'login':       request.form.get('login', '').strip(),
            'password':    request.form.get('password', ''),
            'first_name':  request.form.get('first_name', '').strip(),
            'last_name':   request.form.get('last_name', '').strip(),
            'middle_name': request.form.get('middle_name', '').strip(),
            'role_id':     request.form.get('role_id', ''),
        }

        err = validate_login(form_data['login'])
        if err:
            errors['login'] = err

        if not form_data['role_id']:
            errors['role_id'] = 'Необходимо выбрать роль'

        err = validate_password(form_data['password'])
        if err:
            errors['password'] = err

        if not form_data['first_name']:
            errors['first_name'] = 'Поле не может быть пустым'

        if not form_data['last_name']:
            errors['last_name'] = 'Поле не может быть пустым'

        if not errors:
            try:
                role_id = int(form_data['role_id']) if form_data['role_id'] else None
                execute(
                    '''INSERT INTO users (login, password_hash, first_name, last_name, middle_name, role_id)
                       VALUES (%s, %s, %s, %s, %s, %s)''',
                    (form_data['login'],
                     generate_password_hash(form_data['password']),
                     form_data['first_name'],
                     form_data['last_name'] or None,
                     form_data['middle_name'] or None,
                     role_id)
                )
                flash('Пользователь успешно создан.', 'success')
                return redirect(url_for('users.index'))
            except pymysql.err.IntegrityError:
                errors['login'] = 'Пользователь с таким логином уже существует'
            except Exception as e:
                flash(f'Ошибка при создании пользователя: {e}', 'danger')

    return render_template('users/create.html', roles=roles, errors=errors, form_data=form_data)


@users_bp.route('/users/<int:user_id>/edit', methods=['GET', 'POST'])
@check_rights('edit_user')
def user_edit(user_id):
    user = get_user(user_id)
    if user is None:
        flash('Пользователь не найден.', 'danger')
        return redirect(url_for('users.index'))

    is_admin = session.get('user_role') == 'Администратор'
    roles = get_roles()
    errors = {}

    if request.method == 'POST':
        form_data = {
            'first_name':  request.form.get('first_name', '').strip(),
            'last_name':   request.form.get('last_name', '').strip(),
            'middle_name': request.form.get('middle_name', '').strip(),
            'role_id':     request.form.get('role_id', ''),
        }

        if not form_data['first_name']:
            errors['first_name'] = 'Поле не может быть пустым'

        if not form_data['last_name']:
            errors['last_name'] = 'Поле не может быть пустым'

        if not errors:
            try:
                if is_admin:
                    role_id = int(form_data['role_id']) if form_data['role_id'] else None
                else:
                    role_id = user['role_id']
                execute(
                    '''UPDATE users SET first_name=%s, last_name=%s, middle_name=%s, role_id=%s
                       WHERE id=%s''',
                    (form_data['first_name'],
                     form_data['last_name'] or None,
                     form_data['middle_name'] or None,
                     role_id,
                     user_id)
                )
                flash('Пользователь успешно обновлён.', 'success')
                return redirect(url_for('users.index'))
            except Exception as e:
                flash(f'Ошибка при обновлении пользователя: {e}', 'danger')
    else:
        form_data = {
            'first_name':  user['first_name'],
            'last_name':   user['last_name'] or '',
            'middle_name': user['middle_name'] or '',
            'role_id':     str(user['role_id']) if user['role_id'] else '',
        }

    return render_template('users/edit.html', user=user, roles=roles,
                           errors=errors, form_data=form_data, is_admin=is_admin)


@users_bp.route('/users/<int:user_id>/delete', methods=['POST'])
@check_rights('delete_user')
def user_delete(user_id):
    user = get_user(user_id)
    if user is None:
        flash('Пользователь не найден.', 'danger')
        return redirect(url_for('users.index'))
    try:
        execute('DELETE FROM users WHERE id = %s', (user_id,))
        flash('Пользователь успешно удалён.', 'success')
    except Exception as e:
        flash(f'Ошибка при удалении пользователя: {e}', 'danger')
    return redirect(url_for('users.index'))


@users_bp.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    errors = {}

    if request.method == 'POST':
        old_password     = request.form.get('old_password', '')
        new_password     = request.form.get('new_password', '')
        confirm_password = request.form.get('confirm_password', '')

        user = query('SELECT * FROM users WHERE id = %s', (session['user_id'],), one=True)

        if not check_password_hash(user['password_hash'], old_password):
            errors['old_password'] = 'Неверный текущий пароль'

        err = validate_password(new_password)
        if err:
            errors['new_password'] = err
        elif new_password != confirm_password:
            errors['confirm_password'] = 'Пароли не совпадают'

        if not errors:
            try:
                execute(
                    'UPDATE users SET password_hash = %s WHERE id = %s',
                    (generate_password_hash(new_password), session['user_id'])
                )
                flash('Пароль успешно изменён.', 'success')
                return redirect(url_for('users.index'))
            except Exception as e:
                flash(f'Ошибка при смене пароля: {e}', 'danger')

    return render_template('change_password.html', errors=errors)
