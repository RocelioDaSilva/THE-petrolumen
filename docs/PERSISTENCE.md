# Local persistence and saved calculations

The backend exposes account and saved-calculation endpoints under `/api`.
Saved records contain a title, calculation type, request JSON, result JSON,
and creation time; each record is restricted to the account that created it.

## Configuration

Authentication and saved-record endpoints require `PETROLUMEN_SECRET_KEY` to
contain at least 32 characters. For a local PowerShell session, a key can be
generated without printing it:

```powershell
$env:PETROLUMEN_SECRET_KEY = python -c "import secrets; print(secrets.token_urlsafe(32))"
$env:PETROLUMEN_DATABASE_URL = "sqlite:///./petrolumen.db"
```

The default database URL is `sqlite:///./petrolumen.db`; a relative SQLite
path is resolved from the backend process working directory. Set
`PETROLUMEN_DATABASE_URL` to choose another supported SQLAlchemy URL.

## API flow

1. `POST /api/auth/register` with `username`, `email`, and `password`.
   Registration always assigns the ordinary `user` role.
2. `POST /api/auth/token` with `username` and `password`; use the returned
   bearer token in the `Authorization` header.
3. `POST /api/saved-simulations` with `name`, `simulation_type`, `input_data`,
   and `result_data`.
4. `GET /api/saved-simulations` lists the authenticated account's records.
   `GET` and `DELETE /api/saved-simulations/{id}` operate only on that
   account's records.

List responses omit the potentially large input and result payloads. Fetch an
individual record to retrieve them. Accounts and saved calculations are local
application data; configure database backups and protect the database file
appropriately.
