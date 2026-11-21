The task says the reverse proxy still targets a drained edge and asks to point the upstream at ash_relay. proxy.conf already uses cinder_vip, and edges.tsv marks that host live and ash_relay drained.

Switching the server line would send traffic at a drained box. No subject model has seen this scenario.
