# Videoflix Backend

The backend for Videoflix – a Netflix-style streaming platform. Built with Python, Django, and the Django REST Framework (DRF), running entirely in Docker.

The API covers user registration with email verification, JWT authentication via HttpOnly cookies, password reset, and adaptive video streaming. Uploaded videos are automatically transcoded into three resolutions with FFmpeg in background tasks and delivered as HLS streams.

---

## Table of Contents

- [Features & Tech Stack](#features--tech-stack)
- [Local Development Setup](#local-development-setup)
- [Environment Variables](#environment-variables)
- [Running Tests](#running-tests)
- [API Endpoints](#api-endpoints-documentation)
- [Project Structure](#project-structure)
- [Implementation Notes](#implementation-notes)
- [Credits](#credits)

## Features & Tech Stack

- **Framework:** Django & Django REST Framework (DRF)
- **Authentication:** JWT (SimpleJWT) stored in HttpOnly cookies, with token blacklisting on logout
- **Custom User Model:** Email is the login field; accounts stay inactive until verified by email
- **Email:** Activation and password reset mails with responsive HTML templates, sent asynchronously
- **Background Tasks:** Django RQ with Redis as the broker, split across priority queues
- **Video Processing:** FFmpeg generates a thumbnail and HLS renditions in 480p, 720p and 1080p
- **Streaming:** HLS manifests (`.m3u8`) and segments (`.ts`) served through authenticated endpoints
- **Caching:** Redis as a main-memory caching layer
- **Database:** PostgreSQL
- **Testing:** pytest & pytest-django, 76 tests covering all endpoints
- **Containerization:** Docker Compose with separate services for web, database and Redis

---

## Local Development Setup

This project runs entirely in Docker. You do not need Python, PostgreSQL, Redis or FFmpeg installed locally.

### 1. Clone the repository & enter the directory

```bash
git clone https://github.com/KKrntzk/videoflix_backend.git
cd videoflix_backend
```

### 2. Configure environment variables

The project requires a `.env` file for local configuration and secrets. Copy the provided template and fill in your values:

**Windows (PowerShell)**

```powershell
Copy-Item .env.template .env
```

**macOS / Linux**

```bash
cp .env.template .env
```

Open the newly created `.env` file and set the variables described in the section below.

### 3. Start the containers

```bash
docker compose up --build
```

The first build takes a few minutes. On startup the entrypoint automatically waits for PostgreSQL, runs `collectstatic`, applies migrations, creates the superuser from your `.env`, and starts Gunicorn along with two RQ workers.

The API will be available at: `http://localhost:8000/`

### 4. Access the admin interface

Open `http://localhost:8000/admin/` and log in with `DJANGO_SUPERUSER_EMAIL` and `DJANGO_SUPERUSER_PASSWORD` from your `.env`.

**Note:** Log in with the email address, not the username. The username field still exists on the model, but email is the authentication field.

### 5. Upload a video

Videos are uploaded through the Django admin. Once saved, four background jobs are queued automatically: one for the thumbnail and one for each resolution. You can watch their progress at `http://localhost:8000/django-rq/`.

### 6. Connect the frontend

The frontend is provided by the Developer Akademie and is not part of this repository. Clone it separately:

```bash
git clone https://github.com/Developer-Akademie-Backendkurs/project.Videoflix
```

Open its `index.html` with the VS Code Live Server extension. It expects the backend at `http://127.0.0.1:8000/api/`.

If your Live Server runs on a port other than `5500`, add that origin to `CORS_ALLOWED_ORIGINS` in `core/settings.py`.

---

## Environment Variables

| Variable                                  | Description                                             |
| ----------------------------------------- | ------------------------------------------------------- |
| `SECRET_KEY`                              | Django secret key                                       |
| `DEBUG`                                   | `True` for local development                            |
| `ALLOWED_HOSTS`                           | Comma-separated list of allowed hosts                   |
| `CSRF_TRUSTED_ORIGINS`                    | Comma-separated list of trusted origins                 |
| `DJANGO_SUPERUSER_USERNAME`               | Username of the superuser created on startup            |
| `DJANGO_SUPERUSER_EMAIL`                  | Email used to log into the admin                        |
| `DJANGO_SUPERUSER_PASSWORD`               | Superuser password                                      |
| `DB_NAME` / `DB_USER` / `DB_PASSWORD`     | PostgreSQL credentials (created on first start)         |
| `DB_HOST` / `DB_PORT`                     | `db` and `5432` inside the Docker network               |
| `REDIS_HOST` / `REDIS_PORT` / `REDIS_DB`  | Redis connection for the task queue                     |
| `REDIS_LOCATION`                          | Redis URL for the cache layer                           |
| `EMAIL_HOST` / `EMAIL_PORT`               | SMTP server and port                                    |
| `EMAIL_HOST_USER` / `EMAIL_HOST_PASSWORD` | SMTP credentials                                        |
| `EMAIL_USE_TLS` / `EMAIL_USE_SSL`         | Encryption method – enable exactly one                  |
| `DEFAULT_FROM_EMAIL`                      | Sender address for outgoing mails                       |
| `FRONTEND_URL`                            | Base URL of the frontend, used to build links in emails |

**Note on email:** A working SMTP account is required for activation and password reset mails. When using Gmail, you need an app password – regular account passwords are rejected.

---

## Running Tests

Tests run inside the container, since the database and Redis are only reachable from within the Docker network.

```bash
docker compose exec web pytest

docker compose exec web pytest -v

docker compose exec web pytest auth_app

docker compose exec web pytest --cov=. --cov-report=term-missing
```

---

## API Endpoints (Documentation)

All endpoints are prefixed with `/api/`. Authentication happens through the `access_token` cookie, which is set automatically on login.

### Authentication

- `POST /api/register/` – Registers a new user and sends an activation email. The account stays inactive until verified.
- `GET /api/activate/<uidb64>/<token>/` – Activates the account. The link can only be used once.
- `POST /api/login/` – Validates credentials and sets `access_token` and `refresh_token` as HttpOnly cookies.
- `POST /api/logout/` – Blacklists the refresh token and clears both cookies.
- `POST /api/token/refresh/` – Issues a new access token based on the refresh cookie.
- `POST /api/password_reset/` – Sends a reset link. Always returns 200, regardless of whether the account exists.
- `POST /api/password_confirm/<uidb64>/<token>/` – Sets a new password. The link becomes invalid afterwards.

### Videos

- `GET /api/video/` – Lists all videos with metadata, sorted by creation date descending. Requires authentication.
- `GET /api/video/<movie_id>/<resolution>/index.m3u8` – Returns the HLS manifest for one resolution. Requires authentication.
- `GET /api/video/<movie_id>/<resolution>/<segment>/` – Returns a single HLS segment. Requires authentication.

Supported resolutions are `480p`, `720p` and `1080p`.

### Status Codes

| Endpoint                                  | Action | Expected Status Codes                                          |
| ----------------------------------------- | ------ | -------------------------------------------------------------- |
| `/api/register/`                          | POST   | 201 (Created), 400 (Invalid input)                             |
| `/api/activate/<uidb64>/<token>/`         | GET    | 200 (Activated), 400 (Invalid or used link)                    |
| `/api/login/`                             | POST   | 200 (Logged in), 400 (Invalid credentials or inactive account) |
| `/api/logout/`                            | POST   | 200 (Logged out), 400 (Refresh cookie missing)                 |
| `/api/token/refresh/`                     | POST   | 200 (Refreshed), 400 (Cookie missing), 401 (Invalid token)     |
| `/api/password_reset/`                    | POST   | 200 (Always), 400 (Invalid email format)                       |
| `/api/password_confirm/<uidb64>/<token>/` | POST   | 200 (Reset), 400 (Invalid link or password)                    |
| `/api/video/`                             | GET    | 200 (Listed), 401 (Not authenticated)                          |
| `/api/video/<id>/<resolution>/index.m3u8` | GET    | 200 (Delivered), 401 (Not authenticated), 404 (Not found)      |
| `/api/video/<id>/<resolution>/<segment>/` | GET    | 200 (Delivered), 401 (Not authenticated), 404 (Not found)      |

---

## Project Structure

- `core/` – Project configuration: settings, root URLs, WSGI entry point
- `auth_app/` – Custom user model, authentication, email delivery and token generation
  - `api/` – Serializers, views and URLs for all auth endpoints
  - `authentication.py` – Reads JWTs from HttpOnly cookies instead of the Authorization header
  - `tokens.py` – Custom generator for single-use activation tokens
  - `tasks.py` – Background jobs for sending emails
  - `templates/emails/` – Responsive HTML templates for activation and password reset
- `video_app/` – Video model, processing pipeline and streaming endpoints
  - `api/` – Serializers, views and URLs for the video endpoints
  - `utils.py` – FFmpeg commands and file path helpers
  - `tasks.py` – Background jobs for thumbnail and HLS generation
  - `signals.py` – Queues jobs on upload, removes files on deletion

---

## Implementation Notes

Several decisions in this project deviate from the most obvious approach. They are documented here so the reasoning stays visible.

**Emails are sent asynchronously.** Registration and password reset only enqueue a job and return immediately. A slow or unreachable SMTP server therefore never delays the API response.

**Activation tokens use a custom generator.** Django's `default_token_generator` does not include `is_active` in its hash, which means an activation link would remain valid after the account was already activated. `AccountActivationTokenGenerator` adds that field, making each link single-use. The password reset flow uses Django's default generator, since changing the password invalidates the token automatically.

**Error messages are deliberately generic.** Registration, login and password reset never reveal whether an account exists. The default unique validator on the email field was replaced for this reason, and the behaviour is covered by tests.

**The `username` field is kept on the user model.** The provided Docker entrypoint queries and creates the superuser by username, so removing the field would break container startup. Authentication still happens via email through `USERNAME_FIELD`.

**One job per resolution.** Video conversion is split into four separate jobs instead of one. This keeps every job well below the queue's 900 second timeout, even for longer videos.

**Jobs are split across priority queues.** Email delivery runs on `high`, video conversion on `low`. Two workers are started: one listening only on `high`, the other on `default` and `low`. Without this separation a running conversion would block activation and password reset mails until it finishes.

**HLS files are served through Django.** The frontend's player sends credentials with every segment request, so the files cannot be served by a static file server. Both streaming endpoints validate the requested resolution and file extension before touching the filesystem, which prevents path traversal.

**`STORAGES` replaces `STATICFILES_STORAGE`.** The latter was removed in Django 5.1 and would be silently ignored on this project's Django version.

**`AUTH_COOKIE_SECURE` is `False`.** This is required for local development over HTTP. In production this must be set to `True`.

**Tests use a temporary media root.** The `post_delete` signal removes files from disk, so tests that delete video objects would otherwise wipe real media files. Each video test class writes into its own temporary directory.

**Changes to background tasks require a container restart.** Gunicorn reloads automatically, the RQ worker does not. After editing any `tasks.py`, run `docker compose restart web` so the worker picks up the new code.

---

## Credits

The frontend used to test this backend was provided by the Developer Akademie and is not part of this repository: https://github.com/Developer-Akademie-Backendkurs/project.Videoflix
