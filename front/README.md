# HRMS Dash Frontend

Metadata-driven Dash + Dash Mantine Components frontend for the HRMS backend in `../back`.

## Features

- JWT login, refresh, and logout.
- Permission-aware menu tree (`/api/menus/tree`) with ETag-aware refresh.
- Metadata-driven dynamic pages via Form/FormField schema.
- Dynamic filters and Dash AG Grid table rendering.
- Profile page (`/api/auth/me`) with password change support.

## Quick Start

```bash
cd front
pip install -r requirements.txt
python app.py
```

## Environment Variables

Create `front/.env` (optional):

```dotenv
HRMS_BACKEND_URL=http://127.0.0.1:8000
HRMS_REQUEST_TIMEOUT=30
```

If no `.env` is present, defaults above are used.

## Architecture

- `app.py`: Dash app bootstrap and callback registration.
- `pages/`: Login, profile, dynamic route-backed pages.
- `layouts/`: Shell, navbar, and sidebar layout builders.
- `callbacks/`: Authentication, navigation, menu, profile, and CRUD callback graph.
- `components/`: Reusable dynamic form/table/filter/modal UI blocks.
- `services/`: API clients, cache service, auth/metadata helpers.
- `assets/`: Global styles and Mantine visual overrides.

