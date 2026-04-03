# Backend Language Research: Dead Star Revival Server

**Date:** 2026-04-03
**Purpose:** Pick the best language/framework for building a fake backend server
**Scope:** 22 REST endpoints, auth, matchmaking, player DB, server registry, 500-2500 players

---

## The Recommendation: Go

**Go with the standard library (`net/http`) + a lightweight router (Chi or Echo).**

The rest of this document explains why, but if you just want the answer: Go wins on every axis that matters for this project. Single static binary, trivial deployment, excellent SQLite bindings, built-in concurrency, and the most readable codebase for future community maintainers.

---

## Evaluation Matrix

| Criteria               | Go     | Python | Node.js | Rust   | C#/.NET |
|------------------------|--------|--------|---------|--------|---------|
| Single binary deploy   | **A+** | D      | D       | **A+** | B       |
| VPS performance        | **A**  | C      | B       | **A+** | A       |
| Dev speed              | A      | **A+** | A       | C      | B+      |
| Community maintain.    | **A+** | A      | B+      | D      | C       |
| Long-running stability | **A+** | B      | B       | A+     | A       |
| Concurrency model      | **A+** | B      | B+      | A+     | A       |
| Ecosystem fit          | **A**  | A      | A       | B+     | B+      |

---

## Language-by-Language Breakdown

### 1. Go — THE PICK

**Strengths for this project:**
- `go build` produces a single static binary. Copy it to the VPS, run it. Done. No runtime, no Docker required, no dependency chain.
- Goroutines make matchmaking trivial. A matchmaking loop running in a goroutine, checking queues every second, assigning groups — this is idiomatic Go. No async/await complexity, no callback hell.
- `net/http` is production-grade out of the box. No framework needed, though Chi or Echo add nice routing.
- `mattn/go-sqlite3` (CGo) or `modernc.org/sqlite` (pure Go) both work well. The pure Go option means the binary stays fully static with zero C dependencies.
- Memory usage: ~10-20MB for this workload. A $15 Hetzner VPS (2GB RAM) has 100x headroom.
- If the original dev disappears, Go code reads like pseudocode. A new contributor can understand the matchmaking logic in an afternoon. The language is deliberately simple — no generics abuse, no macro magic, no hidden control flow.
- The Go ecosystem has mature libraries for everything needed: JWT tokens, Steam Web API clients, WebSocket (`gorilla/websocket` or `nhooyr/websocket`), structured logging.
- Cross-compilation is trivial: `GOOS=linux GOARCH=amd64 go build` from any platform.

**Weaknesses:**
- Verbose error handling (`if err != nil`). Annoying but not a real problem for 22 endpoints.
- No ORM culture — you write SQL directly (which is actually better for this project's simplicity).

**Deployment story:** Build locally or in CI. SCP the binary to the VPS. Run with systemd. That's it. Upgrades are: stop service, replace binary, start service.

---

### 2. Python (FastAPI) — Runner-up for dev speed, but wrong tradeoffs

**Strengths:**
- FastAPI is genuinely excellent for prototyping REST APIs. Type hints + Pydantic models give you auto-validation and OpenAPI docs for free.
- Largest pool of potential community contributors. Everyone knows Python.
- Development speed is unmatched for the initial build.

**Weaknesses for this project:**
- No single binary. You need Python installed, a venv, pip dependencies, possibly Docker. This is the #1 disqualifier. When a community member needs to deploy this on a new VPS, "install Python 3.11, create a venv, pip install -r requirements.txt, configure gunicorn" is a maintenance burden.
- Concurrency is awkward. FastAPI uses asyncio, which works for I/O-bound request handling but makes the matchmaking loop harder to reason about. CPU-bound work blocks the event loop.
- Memory: 50-150MB baseline with uvicorn + workers. Fine on a $15 VPS, but wasteful.
- Long-running stability: Python processes tend to accumulate memory over weeks. You'll want a process supervisor that restarts it periodically.
- GIL means true parallelism requires multiprocessing, which complicates shared state (matchmaking queues).

**Verdict:** If this were a throwaway prototype, FastAPI would win. But this server needs to run 24/7 for years with minimal babysitting. Python adds operational friction that Go eliminates.

---

### 3. Node.js (Fastify) — Decent but no binary story

**Strengths:**
- Fastify is fast and well-designed. JSON serialization is excellent.
- npm ecosystem is enormous. Steam authentication libraries exist.
- async/await is natural for request handling.
- Many web developers know JavaScript/TypeScript.

**Weaknesses for this project:**
- No single binary without bundlers like `pkg` or `nexe`, which are fragile and poorly maintained. You're shipping Node.js + node_modules.
- Single-threaded event loop. Matchmaking logic needs careful design to avoid blocking. Worker threads exist but add complexity.
- `node_modules` is a deployment nightmare. 200MB of transitive dependencies for a simple server.
- Long-running stability is OK but not great. Memory leaks in the ecosystem are common. V8 garbage collection pauses can cause latency spikes under load.
- `better-sqlite3` is excellent, but it's a native addon — adds build complexity.

**Verdict:** Node works but adds deployment and operational complexity that Go avoids. The `node_modules` problem alone is a significant negative for community maintenance.

---

### 4. Rust (Axum) — Overkill, hostile to contributors

**Strengths:**
- Performance is untouchable. This server would use 5MB of RAM and handle 100x the load.
- Single static binary, like Go.
- Memory safety guarantees mean no crashes from null pointers or buffer overflows.
- Axum (built on Tokio) is a mature, well-designed framework.

**Weaknesses for this project:**
- **Community maintainability is the fatal flaw.** When the original dev leaves, the remaining community members need to add endpoints, fix bugs, and modify matchmaking logic. Rust's borrow checker, lifetime annotations, trait bounds, and async complexity create a massive barrier. A Python or Go developer can contribute in hours; a Rust newcomer needs weeks of study.
- Development speed is 2-3x slower than Go for this kind of CRUD + business logic server. Fighting the compiler on ownership semantics when you're just parsing JSON and writing to SQLite is wasted effort.
- Compile times are painful. A full build takes 2-5 minutes; incremental builds 15-30 seconds. This slows iteration.
- The ecosystem is good but younger. SQLite bindings (`rusqlite`) work but documentation is thinner.
- Error handling with `Result<T, E>` and the `?` operator is elegant but the type gymnastics around custom error types add boilerplate.

**Verdict:** Rust is the right choice for a game server handling thousands of concurrent UDP connections. It's the wrong choice for a REST API with 22 endpoints that needs to be maintained by a community. This is a nail; Rust is a CNC mill.

---

### 5. C# / .NET Minimal API — Solid but heavy

**Strengths:**
- .NET 8+ minimal APIs are clean and productive. Good performance.
- Excellent tooling (Visual Studio, JetBrains Rider).
- `dotnet publish --self-contained -r linux-x64` produces a single file (sort of — it's a self-extracting bundle, not a true static binary).
- Strong typing, good async model with `Task<T>`.
- Entity Framework or Dapper for data access.

**Weaknesses for this project:**
- The "single file" publish is ~80-150MB and extracts to a temp directory at runtime. It's not a true single binary like Go.
- .NET SDK installation is required for development. The toolchain is heavy.
- Community pool is smaller for game server revival projects. C# developers who would contribute to this project are rarer than Go or Python developers.
- The ecosystem assumes Windows-first. Linux deployment works but is second-class in practice (file path handling, service management).
- Microsoft's framework churn means APIs change every 2 years. Code written for .NET 8 may need updates for .NET 10.

**Verdict:** C# is a reasonable choice if the team already knows it. For a community project starting fresh, the toolchain weight and smaller contributor pool make it suboptimal.

---

## Why Go Wins for Dead Star Revival Specifically

1. **Deployment is a single `scp` command.** The server binary is 10-15MB. No runtime, no Docker, no package manager. A community member in 2028 can deploy it the same way.

2. **Matchmaking is a goroutine.** The core matchmaking loop — check queues, find groups of 10v10, assign to available servers — maps perfectly to a goroutine with channel-based communication. No async/await ceremony, no thread pool tuning.

3. **22 endpoints is Go's sweet spot.** Not complex enough to benefit from Rust's safety guarantees. Not simple enough for Python's prototyping speed to matter. Go's verbosity is proportional to the project size — at 22 endpoints it's readable, not tedious.

4. **The $15 VPS constraint is trivially met.** Go's ~15MB memory footprint leaves room for SQLite, matchmaking state, and connected player sessions with massive headroom. No GC tuning needed.

5. **Community handoff is the real test.** When (not if) the original developer moves on, someone needs to read this code, understand it, and add a new endpoint or fix a matchmaking bug. Go code reads like English. The standard library handles 90% of the work. There are no framework-specific abstractions to learn.

---

## Recommended Stack

| Component         | Choice                          | Why                                    |
|-------------------|---------------------------------|----------------------------------------|
| Language          | Go 1.22+                        | See above                              |
| Router            | `chi` or `echo`                 | Lightweight, idiomatic, good middleware |
| Database          | SQLite via `modernc.org/sqlite` | Pure Go, no CGo, single file DB        |
| Auth              | `golang-jwt/jwt`                | Standard JWT handling                  |
| Steam validation  | Direct HTTP to Steam Web API    | No library needed, it's one endpoint   |
| WebSocket         | `nhooyr.io/websocket`           | Modern, well-maintained                |
| Config            | Environment variables + flags   | 12-factor, no config file parsing      |
| Logging           | `log/slog` (stdlib)             | Structured logging, zero dependencies  |
| Deployment        | systemd unit file               | Native Linux service management        |

**Total external dependencies: ~5.** The Go standard library covers HTTP server, JSON marshaling, TLS, context management, and testing.
