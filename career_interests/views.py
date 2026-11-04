"""Django port of the PHP career-interest questionnaire.

Uses the existing MySQL schema without migrations to legacy tables.
Accounts are resolved from the authenticated Django user.
"""
import json
import logging
import re
from django.db import connection, transaction
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponseForbidden
from django.shortcuts import redirect, render
from django.views.decorators.http import require_GET, require_POST
from django.contrib.auth.decorators import login_required

log = logging.getLogger(__name__)
GENERAL_PARENT = '03000079'
MAX_INTERESTS = 100


def get_career_account_id(request):
    if not request.user.is_authenticated:
        return None

    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT acc_id
            FROM account
            WHERE auth_user_id = %s
              AND acc_status = 'active'
            LIMIT 1
            """,
            [request.user.pk]
        )

        row = cursor.fetchone()

    return row[0] if row else None

def rows(sql, params=()):
    with connection.cursor() as cursor:
        cursor.execute(sql, params)
        names = [c[0] for c in cursor.description]
        return [dict(zip(names, item)) for item in cursor.fetchall()]


def selected_account(request):
    if request.user.is_authenticated:
        # Map Django users to legacy account IDs via your project's profile model.
        account_id = get_career_account_id(request)
    else:
        account_id = None
    if not account_id:
        return None
    found = rows("SELECT acc_id, acc_fname, acc_lname FROM account WHERE acc_id=%s AND acc_status='active'", [account_id])
    return found[0] if found else None


def categories():
    return {kind: rows("SELECT category_id, category_name FROM category WHERE category_type=%s AND is_active='Y' ORDER BY category_name", [kind]) for kind in ('degree program', 'career field', 'skill')}


def interests(user_id):
    return rows("""SELECT c.category_id,c.category_name,c.category_type,ui.intr_score
        FROM user_interests ui JOIN category c ON c.category_id=ui.category_id
        WHERE ui.user_id=%s ORDER BY c.category_type,c.category_name""", [user_id])


def recommendations(parent_ids, degree_id, existing_ids):
    general = rows("""SELECT c.category_id,c.category_name FROM category_parent cp
        JOIN category c ON c.category_id=cp.skill_id
        WHERE cp.parent_id=%s AND c.category_type='skill' AND c.is_active='Y'
        ORDER BY c.category_name""", [GENERAL_PARENT])
    general = [r for r in general if r['category_id'] not in existing_ids]
    parents = list(dict.fromkeys(p for p in parent_ids if re.fullmatch(r'[0-9]{8}', str(p))))
    specific = []
    if parents:
        placeholders = ','.join(['%s'] * len(parents))
        specific = rows(f"""SELECT c.category_id,c.category_name,
            SUM(CASE WHEN cp.parent_id=%s THEN 2 ELSE 1 END) AS relevance
            FROM category_parent cp JOIN category c ON c.category_id=cp.skill_id
            WHERE cp.parent_id IN ({placeholders}) AND c.category_type='skill' AND c.is_active='Y'
            AND NOT EXISTS (SELECT 1 FROM category_parent g WHERE g.skill_id=cp.skill_id AND g.parent_id=%s)
            GROUP BY c.category_id,c.category_name
            ORDER BY relevance DESC,c.category_name LIMIT 3""", [degree_id or parents[0], *parents, GENERAL_PARENT])
        specific = [r for r in specific if r['category_id'] not in existing_ids]
    return {'specific': specific, 'general': general}



@require_GET
@login_required
def suggestions(request):
    user = selected_account(request)
    if not user:
        return JsonResponse({'error': 'Select an account first.'}, status=403)
    cats = categories()
    valid = {kind: {r['category_id'] for r in vals} for kind, vals in cats.items()}
    existing = interests(user['acc_id'])
    parent_rows = [r for r in existing if r['category_type'] in ('degree program', 'career field')]
    degree = request.GET.get('degree', '')
    career = request.GET.get('career', '')
    parents = [r['category_id'] for r in parent_rows]
    if degree in valid['degree program']:
        parents.insert(0, degree)
    if career in valid['career field']:
        parents.append(career)
    degree_id = degree if degree in valid['degree program'] else next((r['category_id'] for r in parent_rows if r['category_type']=='degree program'), '')
    return JsonResponse(recommendations(parents, degree_id, {r['category_id'] for r in existing}))

@login_required
def questionnaire(request):
    user = selected_account(request)
    if not user:
        return render(request, 'career_interests/questionnaire.html', {
            'account': None,
        })
    cats = categories()
    existing = interests(user['acc_id'])
    parents = [r for r in existing if r['category_type'] in ('degree program', 'career field')]
    return render(request, 'career_interests/questionnaire.html', {
        'account': user,
        'has_profile': bool(parents), 'profile_parents': parents,
        'degrees': cats['degree program'], 'careers': cats['career field'], 'skills': cats['skill'],
        'existing_ids': [r['category_id'] for r in existing],
        'saved': request.GET.get('saved') == '1',
    })


@require_POST
@login_required
def save_interests(request):
    user = selected_account(request)
    if not user:
        return HttpResponseForbidden('Select an account first.')
    try:
        data = json.loads(request.POST.get('payload', '{}'))
        if not isinstance(data, dict):
            raise ValueError('Invalid form data')
    except (ValueError, TypeError):
        return HttpResponseBadRequest('Invalid form payload.')
    cats = categories()
    valid = {kind: {r['category_id'] for r in vals} for kind, vals in cats.items()}
    existing = interests(user['acc_id'])
    existing_ids = {r['category_id'] for r in existing}
    parents = [r for r in existing if r['category_type'] in ('degree program', 'career field')]
    has_profile = bool(parents)
    if has_profile and data.get('update_profile') != 'yes':
        return redirect('career_interests:questionnaire')
    pending = {}
    errors = []

    def add(category_id, kind, score, label):
        if not category_id:
            return
        if category_id not in valid[kind]:
            errors.append(f'Invalid {label} selection.')
            return
        if type(score) is not int or not 1 <= score <= 5:
            errors.append(f'{label} interest score must be between 1 and 5.')
            return
        if category_id in existing_ids:
            return
        if category_id in pending:
            errors.append(f'Duplicate selection: {label}.')
            return
        pending[category_id] = score

    degree_id = ''
    career_id = ''
    if not has_profile:
        degree_id = data.get('major', '')
        career_id = data.get('career', '')
        add(degree_id, 'degree program', 5, 'degree')
        add(career_id, 'career field', 5, 'career')
    else:
        if data.get('add_new_degree') == 'yes':
            degree_id = data.get('new_degree', '')
            add(degree_id, 'degree program', 5, 'new degree')
        if data.get('add_new_career') == 'yes':
            career_id = data.get('new_career', '')
            add(career_id, 'career field', 5, 'new career')

    for field, kind in [('extra_career', 'career field'), ('extra_skill', 'skill')]:
        entries = data.get(field, [])
        if not isinstance(entries, list) or len(entries) > MAX_INTERESTS:
            errors.append(f'Invalid {field} entries.')
            continue
        for entry in entries:
            if not isinstance(entry, dict):
                errors.append('Invalid entry.')
                continue
            add(entry.get('id', ''), kind, entry.get('score'), kind)

    selected_parents = [r['category_id'] for r in parents]
    if degree_id in valid['degree program']:
        selected_parents.insert(0, degree_id)
    if career_id in valid['career field']:
        selected_parents.append(career_id)
    primary_degree = degree_id if degree_id in valid['degree program'] else next((r['category_id'] for r in parents if r['category_type']=='degree program'), '')
    allowed = {r['category_id'] for group in recommendations(selected_parents, primary_degree, existing_ids).values() for r in group}
    suggested = data.get('suggested', [])
    if not isinstance(suggested, list) or len(suggested) > MAX_INTERESTS:
        errors.append('Invalid recommended skills.')
    else:
        for entry in suggested:
            if not isinstance(entry, dict):
                errors.append('Invalid recommended skill entry.')
                continue
            if entry.get('selected') is True:
                if entry.get('id') not in allowed:
                    errors.append('Invalid recommended skill.')
                else:
                    add(entry['id'], 'skill', entry.get('score'), 'recommended skill')
    if errors:
        return render(request, 'career_interests/error.html', {'errors': errors}, status=400)
    if pending:
        try:
            with transaction.atomic():
                with connection.cursor() as cursor:
                    for category_id, score in pending.items():
                        cursor.execute("""INSERT INTO user_interests(user_id,category_id,intr_score)
                            VALUES (%s,%s,%s) ON DUPLICATE KEY UPDATE intr_score=VALUES(intr_score),intr_date=NOW()""",
                            [user['acc_id'], category_id, score])
        except Exception:
            log.exception('Unable to save questionnaire interests')
            return render(request, 'career_interests/error.html', {'errors': ['Unable to save interests. Check the Django server log.']}, status=500)
    return redirect('career_interests:questionnaire_saved')


@require_GET
def questionnaire_saved(request):
    from django.urls import reverse
    return redirect(reverse('career_interests:questionnaire') + '?saved=1')
