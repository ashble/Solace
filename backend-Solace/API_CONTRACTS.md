# Solace API contracts

This document describes the API routes currently registered by `backend-Solace`. It is a snapshot of the implementation, including current limitations; it is not a promise that unfinished UI flows already work end to end.

All examples use the Flask app origin. JSON requests should send `Content-Type: application/json`. Endpoints marked **Session required** read the signed Flask session cookie and return `401` if there is no active session user. State-changing routes marked **CSRF required** also require the session's token in `X-CSRF-Token`.

## Session and CSRF

### `GET /api/csrf`

Creates a CSRF token in the current session if one does not already exist.

**Response `200`**

```json
{"csrf_token":"<token>"}
```

Send that token in `X-CSRF-Token` on state-changing API calls, and keep the same session cookie. Login and registration routes are not currently implemented in this backend snapshot; another part of the application must establish the session.

### `GET /api/auth/me` — Session optional

Returns the active session user.

**Response `200`**

```json
{"user":{"id":12,"name":"A Client","email":"client@example.com","role":"client"}}
```

**Response `401`** when there is no current user: `{"user":null}`.

## Therapist directory

### `GET /api/therapists`

Returns therapist profiles that are listed and belong to active users with the `therapist` role. No session is required.

**Response `200`**

```json
{"therapists":[{
  "id":12,
  "name":"Dr. Example",
  "email":"therapist@example.com",
  "title":"Therapist",
  "bio":"",
  "specialties":["Anxiety","CBT"],
  "languages":"English",
  "location":"Online",
  "session_fee":null
}]}
```

The `therapists` array is empty when no profiles meet those conditions.

## Bookings

Bookings now use the existing `appointments` table as the single source of truth. Relational user IDs and an ISO 8601 `scheduled_at` value live alongside the legacy display columns so the current therapist dashboards can continue to render the same records. Existing `booking_appointments` rows are copied once into `appointments`; the old table is retained as an archive. Status values are `pending`, `confirmed`, `cancelled`, or `completed` in the JSON API (stored title-cased for compatibility with current pages).

### `GET /api/bookings` — Session required

Returns bookings for the current user. A client sees bookings where they are the client; other active roles are queried as the therapist side.

**Response `200`**

```json
{"bookings":[{
  "id":31,
  "client_id":8,
  "therapist_id":12,
  "scheduled_at":"2026-12-01T09:30:00",
  "duration_minutes":50,
  "status":"pending",
  "session_type":"online",
  "notes":""
}]}
```

### `POST /api/bookings` — Client session and CSRF required

Creates a pending booking. The therapist must be an active therapist with a listed profile.

**Request**

```json
{
  "therapist_id":12,
  "scheduled_at":"2026-12-01T09:30:00",
  "duration_minutes":50,
  "session_type":"online",
  "notes":"Optional note"
}
```

`therapist_id` and `scheduled_at` are required. `scheduled_at` must be ISO 8601. `duration_minutes` defaults to `50` and must be from `15` through `240`. `session_type` defaults to `online` and is truncated to 20 characters; `notes` defaults to an empty string and is truncated to 2,000 characters.

**Response `201`**: `{"booking":{...booking fields...}}`.

### `PATCH /api/bookings/{booking_id}/status` — Client or therapist session and CSRF required

Only the booking participant may change status. A client may cancel a pending or confirmed booking. A therapist may confirm/cancel a pending booking, or complete/cancel a confirmed booking.

**Request**

```json
{"status":"confirmed"}
```

Use `cancelled` to cancel. Therapists may also use `completed` after confirmation. A successful response is `200`: `{"booking":{...booking fields...}}`.

### `PATCH /api/appointments/{booking_id}` — Compatibility route

Older booking pages still call this path and may send title-cased status strings (for example, `{"status":"Confirmed"}`). It uses the same participant and transition rules as the canonical booking status route and requires CSRF. New frontend work should use `/api/bookings/{booking_id}/status`.

## Conversations and messages

### `GET /api/conversations` — Session required

Lists conversations involving the current user, newest conversation first. Each entry contains the other participant and the latest message, or `null` if the conversation is empty.

**Response `200`**

```json
{"conversations":[{
  "id":4,
  "participant":{"id":12,"name":"Dr. Example"},
  "last_message":{
    "id":19,
    "conversation_id":4,
    "sender_id":8,
    "body":"Hello",
    "created_at":"2026-11-24T10:00:00"
  }
}]}
```

### `POST /api/conversations` — Session and CSRF required

Creates or returns a conversation between a client and an active therapist. Clients send `therapist_id`; therapists send `client_id`. The therapist must have a listed profile.

**Request (client)**

```json
{"therapist_id":12}
```

**Request (therapist)**

```json
{"client_id":8}
```

**Response `201`**: `{"id":4,"client_id":8,"therapist_id":12}`. Existing conversations are returned with the same response shape.

### `GET /api/conversations/{conversation_id}/messages` — Participant session required

Fetches messages in ascending ID order. Optional query parameters: `limit` (default `50`, clamped to `1..100`) and `before` (message ID; returns messages with a smaller ID).

**Response `200`**

```json
{"messages":[{
  "id":19,
  "conversation_id":4,
  "sender_id":8,
  "body":"Hello",
  "created_at":"2026-11-24T10:00:00"
}]}
```

### `POST /api/conversations/{conversation_id}/messages` — Participant session and CSRF required

**Request**: `{"body":"Message text"}`. The trimmed body must contain 1–5,000 characters.

**Response `201`**: `{"message":{...message fields...}}`.

## Profiles and reports

### `PUT /api/profile/{role}` — Matching active account and CSRF required

`role` is `client`, `therapist`, or `admin`, and must match the active session user's role. Accepts a JSON object; only keys present in that role's profile defaults are stored. Email is read from the account and is not editable through this endpoint. Returns the complete account-specific profile object with status `200`.

### `POST /api/reports` — Multipart form and CSRF required

Required form fields: `concern`, `description`, `reported_user_identifier`. Optional fields: `anonymous` (`true`, `1`, `yes`, or `on` means true), `reporter_identifier`, `reporter_role` (`client` or `therapist`), and repeated `files` attachments. If `anonymous` is false, `reporter_identifier` is required. Concern and identifiers are limited to 120 characters. Accepted extensions are PNG, JPG/JPEG, WEBP, and PDF; each file is limited to 10 MB, with a 25 MB total request limit.

**Response `201`**: `{"id":5,"log_id":"RPT-000005","status":"pending"}`.

### `PATCH /admin/reports/{report_id}/status` — Admin session and CSRF required

Accepts `{"status":"pending"}` or `{"status":"resolved"}` and returns the report ID, status, and `resolved_at`.

### `GET /admin/reports/{report_id}/attachments/{attachment_id}` — Admin session required

Downloads a report attachment.

### `POST /admin/therapist/verify/{verification_id}` — Admin session and CSRF required

Approves a pending application, records the review time, activates the therapist account, and lists the therapist profile. Returns the verification ID and resulting statuses.

### `POST /admin/therapist/reject/{verification_id}` — Admin session and CSRF required

Requires `{"reason":"Reason for rejection"}`. Rejects a pending application, records the reason and review time, suspends the therapist account, and unlists their profile. Non-pending applications return `409`.

## Error responses

Most JSON endpoints use `{"error":"..."}` for application errors. Common status codes are `400` for invalid input/state, `401` for missing active session on protected endpoints, `403` for role/ownership denial or invalid CSRF token, `404` for a missing resource, and `409` for a verification that is no longer pending. Conversation message access intentionally returns `404` when the conversation does not exist or the user is not a participant.

## Known frontend integration gaps

- Existing booking status controls retain a compatibility `PATCH /api/appointments/{id}` endpoint. New booking requests use `POST /api/bookings` with the therapist user ID and ISO date-time; the schedule page and therapist directory now pass a real therapist ID into that flow.
- Existing profile and booking controls fetch a CSRF token and send `X-CSRF-Token`. The admin report status control uses `PATCH` and the same CSRF mechanism.
- The app currently exposes CSRF/session inspection, booking, chat, profile, and report routes, but does not implement login or registration. Session-dependent APIs need the group's authentication work to create the session user.
- Therapist verification and the admin user list now read database records rather than demo rows. Therapist approval/rejection updates verification, user, and profile state.
- Profile data is stored per account. Users can update only their own profile, and admin screens/actions require an active admin session.
- Booking is connected from therapist search through the schedule form. The chat endpoints are available, but `/chats` is not yet an interactive chat UI.
- The current therapist registration flow does not upload verification documents, so the review screen reports when a credential document is not attached.
