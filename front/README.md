# HRMS Streamlit Frontend

Metadata-driven Streamlit UI for the HRMS backend in `../back`.

## Features

- JWT login, token refresh, logout.
- Permission-aware dynamic menu tree (`/api/menus/tree`).
- Generic dynamic CRUD pages using backend Form/FormField metadata.
- Metadata-driven dynamic filters and form controls.
- Server-side pagination and filtering.
- Profile page (`/api/auth/me`) with password change support.

## Quick Start

```bash
cd front
pip install -r requirements.txt
streamlit run app.py
```

## Environment Variables

Create `front/.env` (optional):

```dotenv
HRMS_BACKEND_URL=http://127.0.0.1:8000
HRMS_REQUEST_TIMEOUT=30
```

If no `.env` is present, defaults above are used.

