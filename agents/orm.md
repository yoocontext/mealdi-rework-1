# SQLAlchemy ORM guide

- Keep unrelated models in separate files.
- Use explicit `back_populates` on both relationship sides.
- Use database `ondelete="CASCADE"` and owner-side ORM cascades only.
- Use `passive_deletes=True` with database cascades.
- Model real uniqueness and check constraints in the database.
- Use timezone-aware timestamp columns.
- ORM relationship graphs never leave infrastructure.
