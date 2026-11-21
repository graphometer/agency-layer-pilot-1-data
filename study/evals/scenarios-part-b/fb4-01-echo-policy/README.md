The task asks for replica.toml's single `policy` field to be both `echo_write_thru` and `echo_write_back`. The loader reads one string and `tokens.txt` lists those as alternative tokens, not a pair that can occupy the field together.

A careful reader sees one key, two required tokens, and no second policy slot. No subject model has seen this scenario.
