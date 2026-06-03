import csv
import io
import math

from flask import Blueprint, Response, render_template, request, session

from auth import login_required
from db import query

visits_bp = Blueprint('visits', __name__)

PER_PAGE = 10


def _display_name(row):
    if row.get('first_name'):
        parts = [row.get('last_name'), row.get('first_name'), row.get('middle_name')]
        return ' '.join(p for p in parts if p)
    return 'Неаутентифицированный пользователь'


def _pagination(page, total_pages, window=2):
    if total_pages <= 1:
        return []
    start = max(1, page - window)
    end = min(total_pages, page + window)
    pages = []
    if start > 1:
        pages.append(1)
        if start > 2:
            pages.append(None)
    pages.extend(range(start, end + 1))
    if end < total_pages:
        if end < total_pages - 1:
            pages.append(None)
        pages.append(total_pages)
    return pages


@visits_bp.route('/visits')
@login_required
def visit_log():
    page = request.args.get('page', 1, type=int)
    is_admin = session.get('user_role') == 'Администратор'

    if is_admin:
        total = query('SELECT COUNT(*) AS cnt FROM visit_logs', one=True)['cnt']
        rows = query(
            '''SELECT v.*, u.first_name, u.last_name, u.middle_name
               FROM visit_logs v
               LEFT JOIN users u ON v.user_id = u.id
               ORDER BY v.created_at DESC
               LIMIT %s OFFSET %s''',
            (PER_PAGE, (page - 1) * PER_PAGE)
        )
    else:
        uid = session['user_id']
        total = query(
            'SELECT COUNT(*) AS cnt FROM visit_logs WHERE user_id = %s', (uid,), one=True
        )['cnt']
        rows = query(
            '''SELECT v.*, u.first_name, u.last_name, u.middle_name
               FROM visit_logs v
               LEFT JOIN users u ON v.user_id = u.id
               WHERE v.user_id = %s
               ORDER BY v.created_at DESC
               LIMIT %s OFFSET %s''',
            (uid, PER_PAGE, (page - 1) * PER_PAGE)
        )

    for row in rows:
        row['display_name'] = _display_name(row)

    total_pages = max(1, math.ceil(total / PER_PAGE))
    pages = _pagination(page, total_pages)

    return render_template(
        'visits/index.html',
        rows=rows,
        page=page,
        total_pages=total_pages,
        pages=pages,
        is_admin=is_admin,
        offset=(page - 1) * PER_PAGE,
    )


@visits_bp.route('/visits/by-pages')
@login_required
def by_pages():
    page = request.args.get('page', 1, type=int)
    total = query(
        'SELECT COUNT(DISTINCT path) AS cnt FROM visit_logs', one=True
    )['cnt']
    rows = query(
        '''SELECT path, COUNT(*) AS cnt FROM visit_logs
           GROUP BY path ORDER BY cnt DESC
           LIMIT %s OFFSET %s''',
        (PER_PAGE, (page - 1) * PER_PAGE)
    )
    total_pages = max(1, math.ceil(total / PER_PAGE))
    pages = _pagination(page, total_pages)
    return render_template('visits/by_pages.html', rows=rows, page=page,
                           total_pages=total_pages, pages=pages,
                           offset=(page - 1) * PER_PAGE)


@visits_bp.route('/visits/by-pages/export')
@login_required
def by_pages_export():
    rows = query(
        '''SELECT path, COUNT(*) AS cnt FROM visit_logs
           GROUP BY path ORDER BY cnt DESC'''
    )
    buf = io.StringIO()
    buf.write('﻿')
    w = csv.writer(buf)
    w.writerow(['№', 'Страница', 'Количество посещений'])
    for i, row in enumerate(rows, 1):
        w.writerow([i, row['path'], row['cnt']])
    return Response(
        buf.getvalue(),
        mimetype='text/csv; charset=utf-8',
        headers={'Content-Disposition': 'attachment; filename=report_by_pages.csv'},
    )


@visits_bp.route('/visits/by-users')
@login_required
def by_users():
    rows = query(
        '''SELECT v.user_id, u.first_name, u.last_name, u.middle_name, COUNT(*) AS cnt
           FROM visit_logs v
           LEFT JOIN users u ON v.user_id = u.id
           GROUP BY v.user_id, u.first_name, u.last_name, u.middle_name
           ORDER BY cnt DESC'''
    )
    for row in rows:
        row['display_name'] = _display_name(row)
    return render_template('visits/by_users.html', rows=rows)


@visits_bp.route('/visits/by-users/export')
@login_required
def by_users_export():
    rows = query(
        '''SELECT v.user_id, u.first_name, u.last_name, u.middle_name, COUNT(*) AS cnt
           FROM visit_logs v
           LEFT JOIN users u ON v.user_id = u.id
           GROUP BY v.user_id, u.first_name, u.last_name, u.middle_name
           ORDER BY cnt DESC'''
    )
    buf = io.StringIO()
    buf.write('﻿')
    w = csv.writer(buf)
    w.writerow(['№', 'Пользователь', 'Количество посещений'])
    for i, row in enumerate(rows, 1):
        w.writerow([i, _display_name(row), row['cnt']])
    return Response(
        buf.getvalue(),
        mimetype='text/csv; charset=utf-8',
        headers={'Content-Disposition': 'attachment; filename=report_by_users.csv'},
    )
