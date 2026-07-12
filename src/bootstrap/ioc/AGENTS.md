# IoC guide

`bootstrap/ioc` is the only composition root. Provider paths mirror source
layer ownership. Providers manage object lifecycles; use cases and adapters are
never instantiated in handlers or in each other.

- APP scope: settings, engine, stateless security adapters, connection hub.
- REQUEST scope: session, data mappers, transaction manager, use cases.
