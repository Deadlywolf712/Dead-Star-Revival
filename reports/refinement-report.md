# Backend Refinement Report

**Date:** 2026-04-03
**Scope:** Full audit of all 8 Go source files

## Critical Issues Fixed

### 1. AUTH COMPLETELY BROKEN (auth.go)
**Severity: CRITICAL — would block ALL players from logging in**
- `handleAuthenticate` compared `c.Param("version")` (URL path = "v1") against `BuildVersion` ("REL-147994") — these never match
- Every auth request would fail with "Version mismatch"
- **Fix:** Removed the incorrect version check. API version in the URL is not the build version.

### 2. Request body OOM vulnerability (main.go)
**Severity: HIGH — server crashable by any client**
- No body size limit — POST a 1GB payload and the server runs out of memory
- **Fix:** Added `middleware.BodyLimit("1M")` and per-endpoint ContentLength check on auth

### 3. Match result lost on client retry (matchmaking.go)
**Severity: MEDIUM — player loses server address if network hiccups**
- `handleMatchmakeProgress` deleted the match result on first poll
- If client retried (network glitch), second poll returned "not in queue" instead of the server address
- **Fix:** Keep match results until the 2-minute expiry cleanup handles them

### 4. Reservation/queue data never cleaned up (database.go, main.go)
**Severity: MEDIUM — database grows indefinitely**
- Expired reservations accumulated forever
- Disconnected players left orphan queue entries
- **Fix:** Added `RemoveExpiredReservations()` and `RemoveStaleQueueEntries(10min)` to the 30-second cleanup loop

### 5. JSON marshal error silently ignored (database.go)
**Severity: LOW — could write empty data to DB on marshal failure**
- `json.Marshal(acct)` error was discarded with `_`
- **Fix:** Now returns error properly

### 6. Hardcoded date in messages (stubs.go)
**Severity: LOW — cosmetic, wrong date after today**
- `Date: "2026-04-03"` hardcoded
- **Fix:** Uses `time.Now().Format("2006-01-02")`

### 7. Reservation endpoint only accepted arrays (private.go)
**Severity: MEDIUM — game server might send single object**
- `handleReservations` only parsed `[]Reservation`, not a single `Reservation`
- **Fix:** Now tries array first, then single object fallback

### 8. Body handling in auth (auth.go)
**Severity: LOW — redundant body.Close() + manual JSON decoder**
- Used `json.NewDecoder` manually instead of Echo's `Bind`
- Manual `body.Close()` was redundant (Echo handles it)
- **Fix:** Switched to `c.Bind(&req)` for consistency with all other endpoints

## Verification

All fixes compile cleanly. Integration tested 6 endpoints:

| Test | Endpoint | Result |
|------|----------|--------|
| Auth with valid ticket | POST /api/public/v1/authenticate | 200 OK, returns SessionId + 20 ships + 30 portraits |
| Auth with malformed JSON | POST /api/public/v1/authenticate | 400, "Missing authentication ticket" |
| Auth with empty body | POST /api/public/v1/authenticate | 400, "Missing authentication ticket" |
| Messages | GET /api/public/v1/messages | 200, MOTD with dynamic date |
| Leaderboards | GET /api/public/v1/leaderboards | 200, empty array |
| Server heartbeat | POST /api/private/v1/server/status | 200, success |

## Previously Added (earlier in session)

- Database indexes on session_id, steam_id, account_id, queue type+size
- UNIQUE constraint on matchmaking_queue.account_id
- Rate limiting on auth (10/min per IP)
- Session invalidation on re-auth (kicks previous session)
- DLC and hidden content unlocked by default (20 ships, 30 portraits, isDLC=true)
- needle_publicip in config (prevents AWS metadata crash)

## Remaining Known Risks

| Risk | Severity | Notes |
|------|----------|-------|
| Exact JSON field naming | MEDIUM | We inferred field names from strings. Game might expect slightly different structure. Will know on first Windows test. |
| API endpoint paths | MEDIUM | Paths like "/authenticate" are inferred. Real paths constructed at runtime. |
| Rate limit entries never expire | LOW | sync.Map grows with unique IPs. For <2500 players this is negligible. |
| No HTTPS | LOW | Running HTTP, not HTTPS. The game originally used HTTPS with cert pinning. With our URL override it expects HTTP. |
