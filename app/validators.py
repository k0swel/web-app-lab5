import re


def validate_login(login):
    if not login or not login.strip():
        return 'Поле не может быть пустым'
    if not re.match(r'^[a-zA-Z0-9]+$', login):
        return 'Логин должен состоять только из латинских букв и цифр'
    if len(login) < 5:
        return 'Логин должен содержать не менее 5 символов'
    return None


def validate_password(password):
    if not password:
        return 'Поле не может быть пустым'
    if len(password) < 8:
        return 'Пароль должен содержать не менее 8 символов'
    if len(password) > 128:
        return 'Пароль должен содержать не более 128 символов'
    if ' ' in password:
        return 'Пароль не должен содержать пробелы'
    if not re.search(r'[A-ZА-ЯЁ]', password):
        return 'Пароль должен содержать хотя бы одну заглавную букву'
    if not re.search(r'[a-zа-яё]', password):
        return 'Пароль должен содержать хотя бы одну строчную букву'
    if not re.search(r'[0-9]', password):
        return 'Пароль должен содержать хотя бы одну цифру'
    allowed = r"^[a-zA-Zа-яА-ЯёЁ0-9~!?@#$%^&*_\-+()\[\]{}<>/\\|\"'.,;:]+$"
    if not re.match(allowed, password):
        return 'Пароль содержит недопустимые символы'
    return None
