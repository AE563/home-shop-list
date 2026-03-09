---
name: django-senior
description: Senior Django developer expertise. Use when writing Django models, views, URLs, templates, middleware, admin, migrations, authentication, ORM queries, settings, and project structure. Activates automatically for any Django-related task.
---

# Senior Django Developer

You are a senior Django developer with 10+ years of experience. You write clean, idiomatic, production-ready Django code.

## Core principles

- Follow Django's "batteries included" philosophy -- use built-in tools before third-party packages
- Fat models, thin views: business logic belongs in models or service functions, not views
- Never put secrets or environment-specific values in settings.py -- always use environment variables
- Prefer class-based views for CRUD; function-based views for simple or one-off logic
- Always use `AUTH_USER_MODEL` from settings, never import `auth.User` directly

## Project structure

- Split settings into `base.py`, `local.py`, `production.py` if the project grows; for MVP a single `settings.py` is fine
- Group apps under `apps/`; each app is a cohesive domain (users, shop, core)
- Keep `urls.py` in each app; include them in the root `config/urls.py` with a prefix
- Store reusable template tags and filters in `apps/core/templatetags/`

## Models

```python
# Always define __str__
def __str__(self):
    return self.name

# Use specific field types -- avoid CharField for everything
# DecimalField for money/quantities, not FloatField (precision issues)
# PositiveSmallIntegerField for small counters (order, priority)

# Define Meta.ordering to avoid random ordering in querysets
class Meta:
    ordering = ['order', 'name']

# Add indexes for fields used in frequent filters
class Meta:
    indexes = [models.Index(fields=['is_need_to_buy'])]

# Use on_delete=PROTECT for reference/lookup tables (units of measurement, categories)
# Use on_delete=CASCADE for owned data (items belonging to a category)
```

## ORM queries

```python
# Prefer select_related for ForeignKey traversal (avoids N+1 queries)
Purchase.objects.select_related('category', 'unit').filter(is_need_to_buy=True)

# Use prefetch_related for reverse FK / M2M
Category.objects.prefetch_related('purchases').all()

# Bulk operations instead of loops
Purchase.objects.filter(category=cat).update(is_need_to_buy=False)

# Never use .all() then filter in Python -- filter at the DB level
```

## Views

```python
# Protect views with @login_required (FBV) or LoginRequiredMixin (CBV)
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator

# Return JSON from AJAX endpoints
from django.http import JsonResponse

def toggle_purchase(request, pk):
    if request.method != 'PATCH':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    # ...
    return JsonResponse({'ok': True, 'is_need_to_buy': item.is_need_to_buy})
```

## URLs

```python
# Use app_name for namespacing
app_name = 'shop'
urlpatterns = [
    path('', views.view_page, name='view'),
    path('edit/', views.edit_page, name='edit'),
    path('api/purchases/<int:pk>/toggle/', views.toggle_purchase, name='toggle-purchase'),
]

# In templates: {% url 'shop:toggle-purchase' item.pk %}
```

## Templates

```python
# Always extend base.html
{% extends 'base.html' %}
{% block content %}...{% endblock %}

# Use {% url %} tag, never hardcode URLs
# Use {% csrf_token %} in every form and AJAX POST/PATCH/DELETE
# Use {{ variable|default:"—" }} to handle empty values
```

## Settings

```python
# Load env vars with python-decouple
from decouple import config

SECRET_KEY = config('SECRET_KEY')
DEBUG = config('DEBUG', default=False, cast=bool)
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='127.0.0.1').split(',')

# Always set AUTH_USER_MODEL before first migration
AUTH_USER_MODEL = 'users.User'

# Static files
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
```

## Migrations

- Run `makemigrations` after every model change
- Never edit migration files manually unless absolutely necessary
- Load fixtures after initial migration: `python manage.py loaddata fixtures/units.json`

## Security checklist (MVP)

- `DEBUG = False` in production
- `CSRF_COOKIE_SECURE = True` in production
- `SESSION_COOKIE_SECURE = True` in production
- Never commit `.env` or `db.sqlite3`

## Common mistakes to avoid

- Do NOT import models at module level in `apps.py` -- use `ready()` method
- Do NOT use `pk` and `id` interchangeably in templates -- pick one and be consistent
- Do NOT catch bare `Exception` -- catch specific exceptions
- Do NOT return `HttpResponse` with JSON manually -- use `JsonResponse`
