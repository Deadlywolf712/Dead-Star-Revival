# Dead Star Revival Assets

Reverse engineering artifacts for reviving **Dead Star** (Steam AppID 366400), a delisted 10v10 multiplayer space combat game by Armature Studio.

## Structure

| Directory | Contents |
|-----------|----------|
| `reports/` | Binary analysis, protocol RE, auth flow, game logic, server analysis |
| `configs/` | Extracted game config files and SSL certificates |
| `server/` | Dedicated server launcher source code |
| `api/` | Fake backend API (WIP) |
| `assets/` | Extracted asset listings from gamedata.ara |

## Status

Active reverse engineering effort to rebuild the multiplayer server infrastructure. See reports for current findings.

## Key Findings So Far

- Custom UDP protocol with Snappy compression and delta-compressed bit streams
- 7-step connection handshake mapped
- Auth flow: Steam ticket -> backend -> SessionId (Bearer token)
- INetTicketValidator interface identified as clean bypass point
- Server entry point confirmed at DLL ordinal 7500
- ARMA v2 archive format partially documented
- Config override vars allow redirecting API to self-hosted backend

## Legal

This project is for preservation and educational purposes. No copyrighted game assets are distributed.
