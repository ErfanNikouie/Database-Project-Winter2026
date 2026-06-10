# HRMS Backend (Configurable Dynamic Schema)

This backend implements a hybrid HRMS architecture:

- Fixed system metadata tables via Django ORM
- Runtime business tables via SQLAlchemy Core
- Generic CRUD endpoints (`/api/data/*`) for both categories
- JWT authentication with refresh and blacklist logout

## Core Apps

- `apps/users`: `User`, `UserGroup`
- `apps/menus`: `Menu`, `Permission`
- `apps/forms`: `Form`, `FormField`, generic CRUD, validation, filtering, schema services
- `apps/lookups`: `Lookup`, `LookupValue`
- `apps/common`: exception handling, SQLAlchemy engine, permission service, bootstrap signals

## Runtime Bootstrap

On `post_migrate`, system metadata is auto-created:

- system forms (`user`, `user_group`, `menu`, `form`, `form_field`, `permission`, `lookup`, `lookup_value`)
- form fields for each system form
- menu entry for each form
- root admin group + root user
- full root permissions

## API Contract

### Authentication

- `POST /api/auth/login`
- `POST /api/auth/refresh`
- `POST /api/auth/logout`

### Generic Data APIs

- `POST /api/data/insert`
- `POST /api/data/update`
- `POST /api/data/delete`
- `POST /api/data/detail`
- `POST /api/data/list`

## Request Examples

### Insert Dynamic Record

```json
{
  "table": "employee",
  "data": {
    "first_name": "John",
    "last_name": "Doe",
    "salary": 1500.50
  }
}
```

### List With Filters

```json
{
  "table": "employee",
  "limit": 50,
  "offset": 0,
  "sort_by": "id",
  "sort_direction": "asc",
  "filters": {
    "salary": "(>=1000 & <5000) | !=3000",
    "first_name": "John|Ali",
    "is_active": "True"
  }
}
```

### Validation Error Format

```json
{
  "success": false,
  "error": {
    "field": "salary",
    "message": "Invalid filter syntax"
  }
}
```

## Local Run

```bash
pip install -r requirements.txt
python manage.py makemigrations
python manage.py migrate
python manage.py runserver
```

## Production Notes

- set `DJANGO_DEBUG=False`
- use strong `DJANGO_SECRET_KEY`
- route through reverse proxy (Nginx/Traefik)
- enforce HTTPS and secure headers
- run with gunicorn/uvicorn workers
- centralize logs and monitor DB slow queries
- back up PostgreSQL regularly

