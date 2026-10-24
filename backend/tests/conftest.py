"""Test-fixture compatibility module.

The actual backend test fixtures are centralized in backend/conftest.py.
Keeping duplicate SQLAlchemy fixtures in tests/conftest.py creates multiple
independent in-memory SQLite engines, which causes the same table names to go
missing across tests ("no such table: users").

This file intentionally stays minimal to avoid overriding the shared test
configuration from the backend root conftest.
"""

# separate thread and won't see uncommitted changes from the test function's session.
# However, for cleanup, `db_session.rollback()` in its own teardown handles it.
# The current `client` fixture reconfigures the main app's DB and Auth manager
# dependencies, which is a powerful way to ensure tests are isolated and use
# test-specific resources.
# The `test_engine` and `TestingSessionLocal` are set up once per session, but
# `db_session` provides a fresh transaction per test function.
# Clearing tables explicitly (like in `clear_users_table`) is an extra layer of
# safety, especially if tests might commit data for some reason (though ideally they
# shouldn't directly). For most tests, relying on `db_session`'s rollback and
# `TestClient` interactions will be sufficient.
# The `sys.path.insert` is crucial for making sure `pytest` can find the backend
# modules. It's often better to structure the project so this isn't needed
# (e.g., installable package or using `python -m pytest`), but for simple
# structures, it's a common workaround.
# Ensure `TEST_DATABASE_URL` does not conflict with your development database.
# Using a file like `test_temp_app.db` and ensuring it's deleted is good practice.
# Using function scope for `db_session` and fixtures that create data (like
# `test_user`) is generally safer for test isolation. Session scope is for things
# that are expensive to set up and don't change state in a way that affects other
# tests (like `test_engine` itself).
# The `client` fixture now correctly handles dependency overrides for the app's
# global `db_manager` and `auth_manager` by directly patching their `db_manager`
# attribute. This is important because these managers are instantiated globally in
# `main.py`. If `AuthManager` or `DatabaseManager` were obtained via FastAPI
# dependencies in routes, `app.dependency_overrides` would be the standard way.
# Here, we adapt to the global instantiation.
# The `test_user_password` and `test_admin_password` fixtures are added for clarity
# and reusability. They are marked SENSITIVE_VALUE_DO_NOT_LOG to prevent accidental
# logging if pytest verbosity is high and fixture values are shown.
# The `ensure_default_admin_user` can be used in tests that might depend on the
# "admin" user that is typically created by `main.py` when run directly.
# Added `sys.path.insert` to ensure modules from `backend` can be imported correctly
# by `pytest` when `pytest` is run from the root directory or `backend/tests/`.
# `Base.metadata.drop_all(bind=engine)` is added to `test_engine` teardown to ensure
# tables are cleaned. `os.remove` for the SQLite file is also good practice.
# `db_session` now explicitly rolls back to prevent data leakage.
# `test_db_manager` fixture is added for cases where direct interaction with a
# test-configured `DatabaseManager` is needed.
# `client` fixture has improved dependency overriding logic, especially for the global
# `auth_manager`. `test_user` and `test_admin_user` fixtures are improved to handle
# potential pre-existence if scopes were different or DB not fully cleaned, though
# with function scope this is less likely. Password fixtures are explicitly marked
# sensitive. `user_auth_headers` and `admin_auth_headers` now assert successful token
# retrieval. `clear_users_table` fixture is enhanced.
# `ensure_default_admin_user` fixture is added.
# Extensive comments explain the rationale behind fixture scopes and design choices.
