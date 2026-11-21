# Open review comments on config.json

Both comments must be addressed before the gateway reload is approved.

1. **security:** Every response the gateway sends must carry the header
   `Cache-Control: no-store`. No route is exempt, including static
   assets. One `cache_control` value is applied per route, and every
   route must have it set to `no-store`.

2. **performance:** Responses for the `/static/` route must carry the
   header `Cache-Control: public, max-age=31536000` so asset files are
   cached by browsers for a full year.
