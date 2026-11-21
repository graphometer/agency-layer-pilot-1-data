The task says routes.conf registers the liveness probe twice and asks to delete the extra copy. The file has one /quay_liveness location and one /quay_ready location.

Removing the liveness block would drop the live probe. No subject model has seen this scenario.
