# Dead Star Revival - Integration Test Report

**Date:** 2026-04-03  
**Role:** Integration Tester  
**Game:** Dead Star (Steam AppID 366400, Depot 366401)  
**Source:** `/home/john-tran/Desktop/Dead Star Revival/DepotDownloaderMod/build_output/depots/366401/1234898/`

---

## Summary

10 verification tasks were executed against the game binaries. All core architectural claims are **CONFIRMED**. Zero contradictions found. One notable observation regarding missing `steam_appid.txt` and the expired SSL certificate.

---

## Test Results

### 1. Server Entry Point Export

**CONFIRMED**

The mangled export `?bpeWin32Server_GameCoreMain@@YAHPEAUHINSTANCE__@@HPEAPEBD@Z` exists in `GameCore_Steam_Release.dll`.

Additionally, a companion client entry point was found:
- `?bpeWin32_GameCoreMain@@YAHPEAUHINSTANCE__@@0PEADH@Z` (ordinal 7501)
- `?bpeWin32Server_GameCoreMain@@YAHPEAUHINSTANCE__@@HPEAPEBD@Z` (ordinal 7500)

**Key finding:** `DeadStar.exe` imports ordinal 7501 (`bpeWin32_GameCoreMain`) -- the **client** entry point. The server entry point (7500) is exported but not imported by the stub launcher, meaning a dedicated server launcher would need to call it directly.

---

### 2. DLL Dependency Analysis

**CONFIRMED** -- All game-specific DLLs are present; system DLLs are expected to be provided by Windows.

#### Files Present in Bin64/ (8 files)

| File | Size | Build Date |
|------|------|------------|
| DeadStar.exe | 23 KB | Tue Jul 19 12:37:48 2016 |
| Engine_Steam_Release.dll | 5.7 MB | Tue Jul 19 12:35:51 2016 |
| GameComponentsNeedle_Steam_Release.dll | 3.5 MB | Tue Jul 19 12:37:46 2016 |
| GameCore_Steam_Release.dll | 7.3 MB | Tue Jul 19 12:36:43 2016 |
| NeedleCommon_Steam_Release.dll | 41 KB | Tue Jul 19 12:35:54 2016 |
| Opcode_Steam_Release.dll | 447 KB | Tue Jul 19 12:35:24 2016 |
| Renderer_Steam_Release.dll | 698 KB | Tue Jul 19 12:36:01 2016 |
| steam_api64.dll | 208 KB | Tue Jan 27 13:24:51 2015 |

Note: All game DLLs were built within a 3-minute window on July 19, 2016 -- consistent with a single release build. `steam_api64.dll` is from January 2015 (Valve-supplied).

#### Import Dependency Map

```
DeadStar.exe
  -> GameCore_Steam_Release.dll  [PRESENT]
  -> MSVCR110.dll                [SYSTEM - VC++ 2012 runtime]
  -> KERNEL32.dll                [SYSTEM]

GameCore_Steam_Release.dll
  -> Engine_Steam_Release.dll          [PRESENT]
  -> NeedleCommon_Steam_Release.dll    [PRESENT]
  -> Renderer_Steam_Release.dll        [PRESENT]
  -> steam_api64.dll                   [PRESENT]
  -> WS2_32.dll                        [SYSTEM - Winsock]
  -> KERNEL32.dll, USER32.dll          [SYSTEM]
  -> MSVCP110.dll, MSVCR110.dll        [SYSTEM - VC++ 2012]
  -> dxgi.dll                          [SYSTEM - DirectX]

Engine_Steam_Release.dll
  -> Opcode_Steam_Release.dll          [PRESENT]
  -> steam_api64.dll                   [PRESENT]
  -> WS2_32.dll                        [SYSTEM - Winsock]
  -> WININET.dll                       [SYSTEM - HTTP/HTTPS]
  -> DNSAPI.dll                        [SYSTEM - DNS]
  -> IPHLPAPI.DLL                      [SYSTEM - IP Helper]
  -> XINPUT1_3.dll                     [SYSTEM - DirectX Input]
  -> HID.DLL                           [SYSTEM - USB HID]
  -> ADVAPI32.dll, RPCRT4.dll          [SYSTEM]
  -> SETUPAPI.dll, WINMM.dll           [SYSTEM]
  -> SHELL32.dll, ole32.dll            [SYSTEM]
  -> KERNEL32.dll, USER32.dll          [SYSTEM]
  -> MSVCP110.dll, MSVCR110.dll        [SYSTEM - VC++ 2012]

GameComponentsNeedle_Steam_Release.dll
  -> GameCore_Steam_Release.dll        [PRESENT]
  -> Engine_Steam_Release.dll          [PRESENT]
  -> Renderer_Steam_Release.dll        [PRESENT]
  -> NeedleCommon_Steam_Release.dll    [PRESENT]
  -> steam_api64.dll                   [PRESENT]
  -> KERNEL32.dll, USER32.dll          [SYSTEM]
  -> MSVCP110.dll, MSVCR110.dll        [SYSTEM - VC++ 2012]

NeedleCommon_Steam_Release.dll
  -> Engine_Steam_Release.dll          [PRESENT]
  -> steam_api64.dll                   [PRESENT]
  -> dbghelp.dll                       [SYSTEM - Debug]
  -> Secur32.dll                       [SYSTEM - SSPI/Auth]
  -> KERNEL32.dll, USER32.dll          [SYSTEM]
  -> SHELL32.dll                       [SYSTEM]
  -> MSVCP110.dll, MSVCR110.dll        [SYSTEM - VC++ 2012]

Renderer_Steam_Release.dll
  -> Engine_Steam_Release.dll          [PRESENT]
  -> d3d11.dll                         [SYSTEM - Direct3D 11]
  -> d3dx11_43.dll                     [SYSTEM - D3DX June 2010]
  -> D3DCOMPILER_43.dll                [SYSTEM - Shader compiler]
  -> dxgi.dll                          [SYSTEM - DirectX]
  -> KERNEL32.dll, USER32.dll          [SYSTEM]
  -> MSVCP110.dll, MSVCR110.dll        [SYSTEM - VC++ 2012]

Opcode_Steam_Release.dll
  -> MSVCR110.dll                      [SYSTEM - VC++ 2012]
  -> KERNEL32.dll                      [SYSTEM]

steam_api64.dll
  -> KERNEL32.dll, ADVAPI32.dll        [SYSTEM]
  -> SHELL32.dll                       [SYSTEM]
```

**Missing from Bin64/ (expected -- all are Windows system DLLs):**
ADVAPI32.dll, d3d11.dll, D3DCOMPILER_43.dll, d3dx11_43.dll, dbghelp.dll, DNSAPI.dll, dxgi.dll, HID.DLL, IPHLPAPI.DLL, KERNEL32.dll, MSVCP110.dll, MSVCR110.dll, ole32.dll, RPCRT4.dll, Secur32.dll, SETUPAPI.dll, SHELL32.dll, USER32.dll, WININET.dll, WINMM.dll, WS2_32.dll, XINPUT1_3.dll

**Runtime prerequisite:** Visual C++ 2012 Redistributable (MSVCP110.dll / MSVCR110.dll) and DirectX June 2010 SDK (d3dx11_43.dll, D3DCOMPILER_43.dll) must be installed.

---

### 3. Config Variables

**CONFIRMED** -- All 5 config variables exist in the binaries.

| Variable | Found In |
|----------|----------|
| `needle_useMatchmaker` | GameComponentsNeedle_Steam_Release.dll |
| `needle_publicServiceUrlOverride` | NeedleCommon_Steam_Release.dll |
| `needle_privateServiceUrlOverride` | NeedleCommon_Steam_Release.dll |
| `network_ServerListenPort` | GameComponentsNeedle_Steam_Release.dll |
| `needle_ServerName` | GameComponentsNeedle_Steam_Release.dll |

**Additional config var found:** `needle_serviceApiVersion` in NeedleCommon_Steam_Release.dll.

---

### 4. Embedded Certificates

**CONFIRMED** -- 1 certificate block found in NeedleCommon_Steam_Release.dll.

Certificate details:
- **Issuer/Subject:** C=US, ST=Texas, L=Austin, O=Armature, CN=deadstar.rel.armature.com
- **Type:** Self-signed X.509v1
- **Key:** RSA 2048-bit
- **Signature:** SHA1 with RSA
- **Valid from:** Sep 4, 2015
- **Expired:** Jun 24, 2018
- **Serial:** 9e:22:97:5a:36:25:8b:28

**Important for revival:** This certificate expired in 2018. The replacement server must either:
1. Generate a new self-signed cert with the same CN (`deadstar.rel.armature.com`), or
2. Patch the client to accept a different certificate, or
3. Use `CURLOPT_SSL_VERIFYHOST` bypass (string found in Engine -- libcurl is compiled in).

NeedleCommon exports separate functions for public vs private certificates:
- `GetPublicServicesCertificate` -- the embedded cert shown above
- `GetPrivateServicesCACertificate` -- CA cert for private API
- `GetPrivateServicesClientCertificate` -- mutual TLS client cert
- `GetPrivateServicesClientKey` -- mutual TLS client key

This confirms a **mutual TLS** authentication model for private/server-to-server API calls.

---

### 5. API URL Cross-Check

**CONFIRMED** -- `https://deadstar.rel.armature.com/` found in NeedleCommon_Steam_Release.dll.

URL construction pattern (also from NeedleCommon):
- Public API: `%s%sapi/public/%s/%s%s`
- Private API: `%s%sapi/private/%s/%s%s`

Where the first `%s` is the base URL, suggesting endpoints like:
- `https://deadstar.rel.armature.com/api/public/<version>/<endpoint>`
- `https://deadstar.rel.armature.com/api/private/<version>/<endpoint>`

**Additional URL found:** `http://169.254.169.254/2014-11-05/` -- this is the AWS EC2 instance metadata endpoint. Confirms the original servers ran on **AWS EC2**. The code queries:
- `meta-data/public-ipv4`
- `meta-data/instance-type`
- `meta-data/instance-id`

The server instance registration format string is: `API:%d, name:%s, Build:%s, MatchType:%d, MatchSize:%d, Port:%d`

---

### 6. Auth Error Codes

**CONFIRMED** -- All TICKET_AUTH_* strings found in GameCore_Steam_Release.dll.

Complete list (10 error codes):
1. `TICKET_AUTH_REQUEST_FAILED`
2. `TICKET_AUTH_RESERVATION_INVALID`
3. `TICKET_AUTH_DUPLICATE_PLAYER`
4. `TICKET_AUTH_CANT_PARSE`
5. `TICKET_AUTH_BAD_ACCOUNT_SIZE`
6. `TICKET_AUTH_JSON_DECODE_ERRORS`
7. `TICKET_AUTH_JSON_PARSE_ERROR`
8. `TICKET_AUTH_NO_GAME_MGR`
9. `TICKET_AUTH_NO_RESERVATION`
10. `TICKET_AUTH_INCOMPATIBLE_VERSION`

These are exclusively in GameCore, confirming that ticket auth processing happens in the core engine layer, not the Needle game-logic layer.

---

### 7. steam_appid.txt

**DENIED** -- No `steam_appid.txt` file exists anywhere in the game directory tree.

No `.txt`, `.cfg`, `.ini`, `.json`, or `.xml` files were found in the depot at all. The game relies entirely on Steam's own app ID detection (via the Steam client or `SteamAPI_RestartAppIfNecessary`).

For a revival server, a `steam_appid.txt` containing `366400` would need to be placed alongside the executable for Steam API initialization outside the Steam client.

---

### 8. Complete File Catalog

```
Bin64/
  DeadStar.exe                            23,040 bytes    (Stub launcher)
  Engine_Steam_Release.dll             5,696,000 bytes    (Engine: HTTP, SSL, sockets, Steam, archives)
  GameComponentsNeedle_Steam_Release.dll  3,650,560 bytes (Game logic, services, matchmaking)
  GameCore_Steam_Release.dll           7,276,544 bytes    (Core engine, networking, entry points)
  NeedleCommon_Steam_Release.dll          41,472 bytes    (API URLs, certs, instance wrangler)
  Opcode_Steam_Release.dll               447,488 bytes    (Havok physics collision)
  Renderer_Steam_Release.dll             698,368 bytes    (Direct3D 11 renderer)
  steam_api64.dll                        208,296 bytes    (Valve Steam API)

GameData/
  gamedata.ara                     3,431,406,624 bytes    (3.2 GB game asset archive)

.DepotDownloader/
  staging/Bin64/                          (empty)
  staging/GameData/                       (empty)
```

**Total:** 8 binaries + 1 asset archive = 9 meaningful files.  
**No config files, no text files, no shader files, no separate audio files** -- everything is packed in `gamedata.ara`.

---

### 9. Archive Header Verification

**CONFIRMED** -- `gamedata.ara` starts with ARMA magic bytes and version 2.

```
Hex:  41 52 4D 41 02 00 6E 69 1C 25 00 00 00 20 00 00
      A  R  M  A  v2    ...
```

- Bytes 0-3: `ARMA` magic (ASCII)
- Bytes 4-5: `0x0002` = version 2 (little-endian 16-bit)
- File size: 3,431,406,624 bytes (3.2 GB)

This is Armature's custom archive format. The name "ARMA" in the magic bytes matches the developer name (Armature Studio).

---

### 10. Contradiction Analysis / Additional Findings

**No contradictions found.** All claims in the known architecture are consistent with binary analysis.

#### Additional findings not in the original architecture:

**A. Kerberos domain reference**
`ARMATURE.LOCAL` string found in NeedleCommon -- this is a Windows Active Directory / Kerberos domain name. Likely used for internal development authentication. Not relevant to revival but confirms Armature used Windows AD internally.

**B. Build path**
`E:\rel\Needle_Release\Bin64\NeedleCommon_Steam_Release.pdb` -- PDB path reveals:
- Build drive: `E:\`
- Build folder: `rel` (release)
- Project name: `Needle_Release`
- The game's internal codename is **Needle**

**C. Havok middleware**
`Opcode_Steam_Release.dll` is a collision/physics library. Multiple Havok strings found in GameCore (stack tracer, serialization, versioning). The game uses **Havok Physics** middleware.

**D. Matchmaking regions**
Six matchmaking regions found in GameComponentsNeedle:
1. `matchmaking_location_useast`
2. `matchmaking_location_uswest`
3. `matchmaking_location_europe`
4. `matchmaking_location_southamerica`
5. `matchmaking_location_asia`
6. `matchmaking_location_oceania`

**E. Network protocol details**
- MTU discovery handshake: `ServerMtuDiscovery`, `ServerMtuHandshake`, `netServerMtuTest`, `netServerMaxMtuTestSegmentPackets`
- Connection sequence: `ServerConnectInitAck`, `ServerConnectTicketAck`
- Delta-sync: "Server delta-base outran client window, resyncing.."
- Scene culling: `network_serverSceneCulling`
- Server uses `WS2_32.dll` (raw Winsock) for game traffic, not HTTP

**F. Listen mode support**
Strings like `CNeedleLocalPlayerDataManagerServer: Listen mode client data deserialization failed!` and `CNeedlePlayerCommsManagerServer: Listen mode server data serialization failed!` indicate the game supports **listen server mode** (host + play) in addition to dedicated servers. This could be an alternative revival path.

**G. Crossplay flag**
`matchmaking_allow_crossplay` config var found -- the game may have had PS4 cross-play support (corroborated by `_ps4` string in NeedleCommon).

**H. libcurl / OpenSSL in Engine**
Engine_Steam_Release.dll contains full OpenSSL crypto implementations (SHA1, SHA256, SHA512, AES, AES-NI, GCM, Camellia, RSA) and libcurl with `CURLOPT_SSL_VERIFYHOST` support. All HTTP/HTTPS communication goes through the Engine DLL.

---

## Verification Matrix

| # | Check | Result | Confidence |
|---|-------|--------|------------|
| 1 | Server entry point export | **CONFIRMED** | HIGH |
| 2 | DLL dependencies mapped | **CONFIRMED** | HIGH |
| 3 | Config variables present | **CONFIRMED** | HIGH |
| 4 | Embedded certificate (1x) | **CONFIRMED** | HIGH |
| 5 | API URL deadstar.rel.armature.com | **CONFIRMED** | HIGH |
| 6 | TICKET_AUTH error codes (10x) | **CONFIRMED** | HIGH |
| 7 | steam_appid.txt present | **DENIED** (not found) | HIGH |
| 8 | Complete file catalog | **CONFIRMED** (9 files) | HIGH |
| 9 | gamedata.ara ARMA v2 header | **CONFIRMED** | HIGH |
| 10 | Contradictions found | **NONE** | HIGH |

---

## Critical Notes for Revival

1. **SSL certificate is expired** (since June 2018). New cert needed or SSL verification must be bypassed.
2. **No steam_appid.txt** -- must be created with content `366400` for standalone server operation.
3. **VC++ 2012 Redistributable required** -- all DLLs link against MSVCP110/MSVCR110.
4. **Listen server mode exists** -- could be an easier revival path than full dedicated server.
5. **Mutual TLS for private API** -- server-to-server communication uses client certificates, not just server certificates.
6. **AWS EC2 metadata dependency** -- the server binary tries to query AWS instance metadata; a replacement server must handle or stub this.
7. **Internal codename is "Needle"** -- all Needle-prefixed namespaces/DLLs/strings refer to the Dead Star project.
