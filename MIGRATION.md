# Storage migration
SQLAlchemy is upgraded to 2.0.36. Database code now lives in app.storage.db.
The old and new dependency locks are authoritative. Preserve the target version.
Migration reference: https://docs.sqlalchemy.org/en/20/changelog/migration_20.html
