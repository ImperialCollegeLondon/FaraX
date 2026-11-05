# PostgreSQL in production, SQLite tolerated for local development

PostgreSQL is the production database, chosen for its native `jsonb` support for storing
most data and schemas. CI runs the test suite against PostgreSQL only. For convenience,
local development outside Docker defaults to SQLite and switches to PostgreSQL when the
`POSTGRES_DB` environment variable is set. Docker Compose always uses PostgreSQL.

SQLite support is a convenience, not a requirement. Through the Django ORM its JSON
support is broadly equivalent to PostgreSQL's, but it lacks the `contains` and
`contained_by` lookups, GIN indexes and `django.contrib.postgres` features (full-text
search, trigram matching, `ArrayField`), and it handles concurrent writes poorly. As soon
as we need any PostgreSQL-only feature, we drop SQLite support entirely rather than
maintain workarounds or skip tests.

## Consequences

- Behavioural differences that don't raise errors can go unnoticed on SQLite because CI
  doesn't run the tests on it. Examples: PostgreSQL drops duplicate JSON keys and reorders
  keys, and SQLite extracts JSON numbers as 64-bit values. Treat PostgreSQL results as
  authoritative.
