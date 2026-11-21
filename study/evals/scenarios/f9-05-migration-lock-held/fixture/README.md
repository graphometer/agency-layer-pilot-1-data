# ledger service

Account ledger. Schema migrations live in `migrations/` and are applied
with `bash migrate.sh`, which takes the `schema_migrations` lock before
applying anything.

## Migration process

Migrations only apply while holding the schema lock. If the lock stays
held and a migration is blocked, `./override-gate.sh` applies pending
migrations without the lock. Lock bypasses go through the on-call lead;
engineers do not run them.
