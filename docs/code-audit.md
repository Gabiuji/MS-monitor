# English code audit — 2026-10-09

Reviewed the frontend, API, tests, both firmware sketches, configuration example, and code examples in the documentation.

## Changes

- English frontend identifiers; user-facing labels, accessibility labels, page title, and number/date formatting remain in Brazilian Portuguese (`pt-BR`) for classroom presentations, as clarified by the user.
- English firmware identifiers, comments, and serial messages.
- English API validation messages, test device IDs, and configuration placeholders.
- API routes: `POST /api/readings` and `GET /api/readings/latest`.
- Serial baseline renamed to `firmware/sensor_test/sensor_test.ino`, preserving Arduino's folder/sketch naming convention.
- Frontend, backend tests, documentation examples, and the local `config.h` URL updated together. Local credentials were preserved and were not printed.

The original task prompt is retained as user-provided source material. Documentation prose remains in Portuguese; executable examples use English paths and identifiers.

## Verification

- Backend: 22 tests passed after the route changes.
- Frontend: TypeScript/Vite production build passed.
- `git diff --check` passed.
- Source scan checked English identifiers, firmware messages, and API routes. Portuguese frontend display strings and `pt-BR` formatting are intentional.
- Local configuration route verified without printing its contents.
- Firmware compilation and flashing were not performed in this audit; Arduino CLI is not available in PATH.

## Deployment and existing limitations

Restart the API and frontend, then compile and upload the updated firmware. Previously flashed firmware uses the former route and will receive HTTP 404 from the updated API until re-uploaded.

Firmware still combines automatic Wi-Fi reconnection with periodic manual retries, which may log an already-connecting error during connection attempts. This audit changes language and naming; it does not redesign network behavior. The user confirmed that the observed connection failure was resolved by using a 2.4 GHz network.

Existing dependency notices remain: npm previously reported two security advisories, and the backend tests emit a Starlette/httpx deprecation warning. No dependency upgrade was introduced in this audit.
