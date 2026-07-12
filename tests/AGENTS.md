# Tests guide

- `tests/unit` tests one policy or use case with fakes.
- `tests/integration` tests infrastructure against a real-compatible database.
- `tests/e2e` exercises complete scenarios through the HTTP or WebSocket API.
- `tests/mocks` owns reusable fakes by layer.

Group tests by business concept. Test observable behavior and important
security/transaction boundaries, not implementation trivia.
