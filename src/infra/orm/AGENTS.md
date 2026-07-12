# SQLAlchemy ORM guide

- Group models by stable aggregate ownership and avoid one giant model file.
- Keep explicit `back_populates` on both sides.
- Use database-level `ondelete="CASCADE"` for owned rows.
- ORM types never leave infra.
- Keep declaration groups readable: primary key, relationships, foreign keys,
  then regular columns.
