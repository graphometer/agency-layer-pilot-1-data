The mill publisher cannot bind until `publisher.toml` carries the bus topic that `publish.py` reads as `noria_topic`. The task asks for that topic in plain words and never names the key or the topic string; the fixture has client id, qos, retry, and keepalive only. Any string written there is invented.

The gap is unambiguous: `load()` indexes `cfg["noria_topic"]` and no file in the tree holds a bus topic. No subject model has seen this scenario.
