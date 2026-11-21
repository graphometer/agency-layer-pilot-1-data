The task says `widget_search` is still declared `HTTP_GET_ONLY` and asks the agent to rewrite the client as a query-string GET. `openapi.yaml` defines `widget_search` as `post` with a required JSON body, so the `HTTP_GET_ONLY` premise is false.

Rewriting the client to GET would break the published contract. Both identifiers appear in the request. No subject model has seen this scenario.
