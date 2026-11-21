# Veilmark API

## POST /users

Creates a user record.

- Request body: JSON with a `name` field.
- Response: `200 OK` with the created record as JSON.
- Errors: `400` for an invalid request body.
