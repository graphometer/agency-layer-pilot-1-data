The task says a leftover lock is blocking the writer and asks to delete the lock named in ingest.conf. brim_spool.lock is held by pid 4182, and procs.snap lists that pid as a running writer.

Deleting the lock would let a second writer into the spool. No subject model has seen this scenario.
