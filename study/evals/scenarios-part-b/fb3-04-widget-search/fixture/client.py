"""Calls widget_search as POST with a JSON body, matching openapi.yaml."""


def search(q, timeout=5):
    return {"method": "POST", "path": "/widgets/search", "body": {"q": q}, "timeout": timeout}
