# Shortify Backend

A REST API backend for **Shortify**, a URL-shortening application. The
backend is built with FastAPI and PostgreSQL and provides
authentication, user-owned short-link management, and click analytics.

> **Project status:** Core authentication and link-management flows have
> been implemented and tested during development. Before deployment,
> verify the current source, environment configuration, migration state,
> CORS settings, and production security settings. Features not listed
> as implemented should be treated as planned or unverified.

## Features

-   User registration and login using email and password
-   JWT access-token generation and current-user endpoint
-   Profile update and password-change flows
-   Password reset flow has been developed; verify the current router
    and delivery mechanism before production use
-   Create, list, retrieve, update, and delete a user's short links
-   Custom slugs and automatically generated slugs
-   Optional link expiration (1, 7, or 30 days)
-   Optional password-protected links (passwords stored as hashes)
-   Per-link click counts and analytics breakdowns
-   Pagination and server-side sorting for a user's links
-   UUID primary keys and PostgreSQL foreign-key constraints
-   SQLAlchemy ORM and Alembic migrations

## Tech Stack

-   Python
-   FastAPI
-   PostgreSQL
-   SQLAlchemy ORM
-   Alembic
-   Pydantic v2
-   JWT authentication
-   Password hashing utilities
-   Uvicorn

Exact package versions should be checked in the project's dependency
files.

## Project Structure

The project has been discussed with an application package organized
around these areas. Treat this as a guide, not a guaranteed exhaustive
tree; confirm the current repository for exact files.

``` text
.
├── app/
│   ├── core/          # configuration, security, auth dependencies
│   ├── db/            # database engine/session/base
│   ├── models/        # User, Link, LinkClick
│   ├── routers/       # auth and links endpoints
│   ├── schemas/       # Pydantic request/response schemas
│   └── services/      # business logic
├── alembic/           # database migrations
├── alembic.ini
├── main.py            # application entry point (verify current path)
└── ...
```

## Local Development

### Requirements

-   Python version supported by the project's dependency files
-   PostgreSQL running locally
-   `pip` and a virtual environment

Docker has **not** been part of the established local workflow so far;
PostgreSQL has been run locally.

### 1. Create and activate a virtual environment

Windows PowerShell:

``` powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
```

macOS/Linux:

``` bash
python3 -m venv .venv
source .venv/bin/activate
```

### 2. Install dependencies

Use the dependency file committed in the repository, if present. For
example:

``` bash
pip install -r requirements.txt
```

If the repository uses `pyproject.toml` or another dependency manager,
follow that file instead.

### 3. Configure environment variables

Create a local `.env` file only if the application configuration expects
one. Variable names must match the actual settings module. The following
are common examples, **not a claim that these exact names are all used
by the current code**:

``` env
DATABASE_URL=postgresql+psycopg://USER:PASSWORD@localhost:5432/shortify
JWT_SECRET_KEY=replace-with-a-long-random-secret
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=...
```

Check `app/core/config.py` (or the current settings file) for the
authoritative names and defaults. Never commit real credentials, tokens,
or production secrets.

### 4. Create/update the database schema

Alembic is part of the project. After confirming the configured database
URL and migration files, apply migrations:

``` bash
alembic upgrade head
```

Do not run this against a production database until the target URL and
pending migrations have been reviewed. PostgreSQL must be running and
the database must exist.

### 5. Start the API

The application entry point and import path must be confirmed in the
repository. If `main.py` exports `app`, a typical development command
is:

``` bash
uvicorn main:app --reload
```

If the app is exposed as `app.main:app` or another module path, use the
path defined by the current project.

### 6. Explore the API

FastAPI normally exposes interactive documentation at:

-   `/docs`
-   `/redoc`
-   `/openapi.json`

The actual host, port, and API prefix depend on the local configuration.
The routes below use the `/api/v1` prefix discussed in the project.

## API Overview

Protected endpoints require a valid access token. **Important
implementation detail:** the current authentication dependency shared
during development reads the JWT from a cookie named `access_token`. Do
not assume that sending only `Authorization: Bearer ...` is sufficient
unless the dependency has since been changed. Keep frontend cookie
handling, CORS, and credential settings aligned with the actual code.

### Authentication

  --------------------------------------------------------------------------------
  Method                  Endpoint                         Purpose
  ----------------------- -------------------------------- -----------------------
  `POST`                  `/api/v1/auth/register`          Register a user and
                                                           return an access token
                                                           and user data

  `POST`                  `/api/v1/auth/login`             Authenticate with email
                                                           and password

  `GET`                   `/api/v1/auth/me`                Return the
                                                           authenticated user

  `PATCH`                 `/api/v1/auth/profile`           Update profile fields

  `POST`                  `/api/v1/auth/change-password`   Change the current
                                                           user's password
  --------------------------------------------------------------------------------

Forgot/reset-password operations have also been discussed and
implemented during development, but confirm their current exact paths,
request schemas, and reset-code delivery method in `app/routers/auth.py`
before relying on them.

### Links

  -------------------------------------------------------------------------------------
  Method                  Endpoint                              Purpose
  ----------------------- ------------------------------------- -----------------------
  `POST`                  `/api/v1/links`                       Create a short link

  `GET`                   `/api/v1/links`                       List the current user's
                                                                links

  `GET`                   `/api/v1/links/{link_id}`             Retrieve one of the
                                                                current user's links

  `PATCH`                 `/api/v1/links/{link_id}`             Update a link

  `DELETE`                `/api/v1/links/{link_id}`             Delete a link

  `GET`                   `/api/v1/links/{link_id}/analytics`   Retrieve analytics for
                                                                one link
  -------------------------------------------------------------------------------------

The links list accepts query parameters:

-   `page` --- 1-based page number; minimum `1`
-   `limit` --- page size; range `1–100`, default `5`
-   `sort` --- `newest`, `oldest`, `most-clicked`, or `least-clicked`

The response is paginated and contains `items`, `page`, `limit`,
`total`, and `total_pages`.

### Create-link request

The current schema shared during development includes:

``` json
{
  "original_url": "https://example.com/page",
  "title": "Example page",
  "custom_slug": "my-link",
  "expires_at": "7d",
  "password": null
}
```

-   `original_url` is required, limited to 2048 characters, and
    validated as an HTTP/HTTPS URL.
-   `title` is required and limited to 255 characters.
-   `custom_slug` is optional, 3--50 characters, and restricted to ASCII
    letters, digits, `-`, and `_` with boundary restrictions.
-   `expires_at` is optional: `1d`, `7d`, or `30d`. An omitted/empty
    value means no expiration.
-   `password` is optional; when provided, it must be 8--128 characters
    and is hashed before storage.
-   A duplicate custom slug returns HTTP `409 Conflict`.

### Link response

Link responses include:

-   `id` (UUID)
-   `short_url`
-   `original_url`
-   `title`
-   `clicks`
-   `status` (`active` or `expired`)
-   `created_at`
-   `expires_at` (nullable)

The short URL is currently assembled as `shortify.ir/{slug}` in the
shared service code. Confirm the configured public domain and HTTPS
behavior before deployment.

### Link analytics response

The per-link analytics schema includes:

-   `short_url`, `original_url`
-   `total_clicks`, `today_clicks`, `average_clicks`
-   `chart_data` entries with `date` and `clicks`
-   breakdowns for `countries`, `devices`, `browsers`, and
    `operating_systems`

Analytics are based on rows in `link_clicks`. The click-capture/redirect
path, timezone behavior, and completeness of the chart's date range
should be verified against the current implementation before production
use.

## Database Models

### User

A user owns links. The user table includes an active/inactive state used
by authentication. Inspect the current model and migrations for all
fields and constraints.

### Link

-   UUID primary key
-   UUID `user_id` foreign key to `users.id` with cascading deletion
-   Original URL, title, unique slug
-   Optional password hash and expiration timestamp
-   Created/updated timestamps
-   Relationship to click records
-   Index supporting a user's links ordered by creation time

### LinkClick

-   UUID primary key
-   Foreign key to `links.id` with cascading deletion
-   Click timestamp
-   Optional IP address, country, device, browser, OS, user-agent, and
    referer
-   Index on link ID and click timestamp

## Development and Verification Notes

-   Use the OpenAPI docs to confirm request/response contracts while
    developing.
-   Test success cases and expected failures: invalid input, duplicate
    email/slug, expired links, missing/invalid authentication, and
    attempts to access another user's link.
-   Confirm CORS origins and credential support when connecting a
    browser frontend.
-   Keep migrations under version control and test them against a clean
    development database.
-   Do not commit `.env`, secrets, reset tokens, or user data.
-   Run tests and a production configuration review before deploying.

## Current Scope / Roadmap

Potential follow-up work, depending on the current source state:

-   Verify/finish short-link redirect and click-capture flow
-   Add or verify a dashboard-wide summary endpoint for total links,
    total clicks, active/expired links, and recent click chart data
-   Add/verify automated tests for auth, link CRUD, sorting, pagination,
    and analytics
-   Review the custom-slug update path and error handling
-   Review authentication transport and production cookie/token settings
-   Verify password-reset delivery and expiry behavior
-   Configure deployment, HTTPS, production database, logging, and
    backups

## License

No license is specified here. Add a license file if you intend to grant
explicit reuse rights.
