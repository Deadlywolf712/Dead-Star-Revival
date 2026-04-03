# Dead Star Network Protocol Analysis

**Date:** 2026-04-03
**Analyst:** Protocol Engineer (Agent)
**Sources:** GameCore_Steam_Release.dll (7MB), GameComponentsNeedle_Steam_Release.dll (3.5MB), Engine_Steam_Release.dll
**Method:** Static string extraction, symbol demangling, DLL import analysis

---

## 1. Network Error Codes

### NET_ERROR_* (Transport Layer) [CONFIRMED]

All extracted from `GameCore_Steam_Release.dll`. Each has a corresponding `NNetTypes::skConnectionError_*` SRichError constant.

| Error String | SRichError Constant | Category |
|---|---|---|
| `NET_ERROR_CONNECTIONAUTHORIZATIONFAILURE` | `skConnectionError_ConnectionAuthorizationFailure` | Auth |
| `NET_ERROR_CONNECTIONAUTOCLOSE` | `skConnectionError_ConnectionAutoClose` | Lifecycle |
| `NET_ERROR_CONNECTIONCOMPRESSIONERROR` | `skConnectionError_ConnectionCompressionError` | Data |
| `NET_ERROR_CONNECTIONDECOMPRESSIONERROR` | `skConnectionError_ConnectionDecompressionError` | Data |
| `NET_ERROR_CONNECTIONGAMESTATEOVERFLOW` | `skConnectionError_ConnectionGameStateOverflow` | Data |
| `NET_ERROR_CONNECTIONLOGGEDINELSEWHERE` | `skConnectionError_ConnectionLoggedInElsewhere` | Auth |
| `NET_ERROR_CONNECTIONMALFORMEDPACKET` | `skConnectionError_ConnectionMalformedPacket` | Data |
| `NET_ERROR_CONNECTIONSOCKETERROR` | `skConnectionError_ConnectionSocketError` | Transport |
| `NET_ERROR_CONNECTIONTIMEOUT` | `skConnectionError_ConnectionTimeout` | Timeout |
| `NET_ERROR_FAILED_PLAYERID_READ` | — | Data |
| `NET_ERROR_INVALID_MTU_DISCOVERY_PACKET` | — | MTU |
| `NET_ERROR_INVALID_PLAYER_ID` | — | Data |
| `NET_ERROR_INVALID_TICKET_ACK_PACKET` | — | Handshake |
| `NET_ERROR_MALFORMED_DISCONNNECT_PACKET` | — | Data (note: typo in original — triple N) |
| `NET_ERROR_NETWORKSCENEDESERIALIZATIONFAILURE` | `skConnectionError_NetworkSceneDeserializationFailure` | Scene |
| `NET_ERROR_NETWORKSCENESERIALIZATIONFAILURE` | `skConnectionError_NetworkSceneSerializationFailure` | Scene |
| `NET_ERROR_NETWORKSCENESHUTDOWN` | `skConnectionError_NetworkSceneShutdown` | Lifecycle |
| `NET_ERROR_TICKET_READ_FAILED` | — | Handshake |
| `NET_ERROR_UNKNOWN_CONNECTION_STATE` | — | State Machine |
| `NET_CHANNEL_ALLOCATION_FAILED` | — | Channel |
| `NET_MTU_TOO_SMALL` | — | MTU |

### NET_APP_ERROR_* (Application Layer) [CONFIRMED]

Extracted from `GameComponentsNeedle_Steam_Release.dll`:

| Error String | Description |
|---|---|
| `NET_APP_ERROR_CAPITAL_SHIP_DATA_ERROR` | Capital ship game state error |
| `NET_APP_ERROR_CAPITAL_SHIP_MATCH_FINISHED` | Match ended (capital ship destroyed) |
| `NET_APP_ERROR_IDLE_TIMEOUT` | Player idle too long |
| `NET_APP_ERROR_NETWORKDEVICEDISCONNECTED` | Network adapter disconnected |
| `NET_APP_ERROR_PING_TOO_HIGH` | Latency exceeded threshold |
| `NET_APP_ERROR_SERVERCONNECTIONTIMEOUT` | Server-side connection timeout |
| `NET_APP_ERROR_STATSREADFAILURE` | Stats system read failure |
| `NET_APP_ERROR_UNHEALTHY_SERVER_KICKOUT` | Server health check failed |

### Ticket Auth Errors [CONFIRMED]

Each has a `NNetTypes::skConnectionError_TicketAuth*` SRichError constant:

| Error String | Meaning |
|---|---|
| `TICKET_AUTH_BAD_ACCOUNT_SIZE` | Account data size invalid |
| `TICKET_AUTH_CANT_PARSE` | Ticket unparseable |
| `TICKET_AUTH_DUPLICATE_PLAYER` | Player already connected |
| `TICKET_AUTH_INCOMPATIBLE_VERSION` | Build version mismatch |
| `TICKET_AUTH_JSON_DECODE_ERRORS` | JSON decode failure |
| `TICKET_AUTH_JSON_PARSE_ERROR` | JSON parse failure |
| `TICKET_AUTH_NO_GAME_MGR` | Game manager not initialized |
| `TICKET_AUTH_NO_RESERVATION` | No matchmaking reservation found |
| `TICKET_AUTH_REQUEST_FAILED` | Auth service request failed |
| `TICKET_AUTH_RESERVATION_INVALID` | Reservation expired/invalid |
| `TICKET_CONNECTIONS_DISALLOWED` | Server refusing new connections |
| `TICKET_REVOKED` | Ticket revoked post-connect |

---

## 2. Packet Types & Message Structure

### Transport Packet [CONFIRMED]

The replay system reveals the core packet types. `CNetClientReplay` reads/writes three distinct data types in sequence:

```
enum EDataType {
    UserInfo,           // Player ID + Connection Ticket
    TransportPacket,    // Game state / network data
    ControllerPacket    // Player input
};
```

**Evidence:**
- `ReadUserInfo` / `WriteUserInfo` — takes `CStrongId<uint8>` (player ID) + `CConnectionTicket`
- `ReadTransportPacket` / `WriteTransportPacket` — takes `uint32` (size) + `STransportPacket` from `NNetTypes`
- `ReadControllerPacket` / `WriteControllerPacket` — takes `CUserInput`
- `ReadSequenceNumbers` / `WriteSequenceNumbers` — takes two `uint16` values (sequence pair)

### STransportPacket [CONFIRMED]

Structure: `NNetTypes::STransportPacket` — appears in replay read/write functions.

### SGameStatePacket [CONFIRMED]

Structure: `NNetTypes::SGameStatePacket` — has `skMaxDataSize` constant.
- Assertion: `NNetTypes::SGameStatePacket::skMaxDataSize >= uncompressedSize`
- This caps the maximum game state payload per packet.

### Editor Network Packets [CONFIRMED]

Used for development tools only (not relevant to game protocol):
- `ProcessEditorNetworkPacket` on Animation, CameraController, MaterialEditorPlaceholder components
- Dispatched via `gEditorNetworkPacketDelegate` (FastDelegate list)

### Networked Message Relay [CONFIRMED]

`CComponentNeedleGeneralNetworkedMessageRelay` — forwards game object messages over network.
- Source: `GameObjects\NeedleGeneral\CComponentNeedleGeneralNetworkedMessageRelay.cpp`
- "CComponentNeedleGeneralNetworkedMessageRelay should only Think() on clients."

---

## 3. Serialization & Delta Compression

### Delta Compression System [CONFIRMED]

**Namespace:** `NDeltaCompression`
**Source file:** `GameObjects\NetSync\CNetDelta.cpp`

#### Core Classes

| Class | Role |
|---|---|
| `NDeltaCompression::CSchema` | Defines field layout for delta encoding |
| `CNetDeltaBase<16>` | Base class with 16-state sliding window |
| `CNetDeltaIncoming` | Client-side: applies incoming deltas |
| `CNetDeltaOutgoing` | Server-side: generates outgoing deltas |

#### CSchema Operations [CONFIRMED]

```cpp
// Serialization (server -> client)
CSchema::Serialize(
    uint32* stateIndex,           // state slot
    CNetOutputBitStream& stream,  // output bit stream
    uint8* scratchBuffer,         // temp buffer
    uint32 scratchSize,           // temp size
    uint32 someParam,             // [UNCERTAIN] possibly flags
    const uint8* prevState,       // previous state for delta
    const uint8* prevState2       // [UNCERTAIN] second reference state
) -> bool

// Deserialization (client <- server)
CSchema::Deserialize(
    uint32* stateIndex,
    uint8* outputState,
    uint32 outputSize,
    const uint8* prevState,
    CNetInputBitStream& stream,
    CNetInputBitStream& stream2   // [UNCERTAIN] second stream
) -> bool
```

#### Delta Generation [CONFIRMED]

```cpp
// Two overloads for delta generation:
CNetDeltaOutgoing::GenerateDelta(
    CNetOutputBitStream& stream,
    uint8* scratchBuffer,
    uint32* scratchIndex,
    uint32 scratchSize,
    uint16 baseSequence,        // reference sequence number
    uint16 currentSequence      // current sequence number
) -> bool

// Second overload adds a const reference state:
CNetDeltaOutgoing::GenerateDelta(
    CNetOutputBitStream& stream,
    uint8* scratchBuffer,
    uint32* scratchIndex,
    uint32 scratchSize,
    const uint8* referenceState,
    uint32 referenceSize,
    uint16 baseSequence,
    uint16 currentSequence
) -> bool
```

#### Delta Application [CONFIRMED]

```cpp
CNetDeltaIncoming::ApplyDelta(
    const uint8** stateBuffers,   // array of state pointers
    uint32* stateIndex,           // current state index
    CNetInputBitStream& stream,
    const uint8* baseState,       // base state for delta
    uint16 baseSequence,
    uint16 currentSequence
) -> bool
```

#### Schema Creation [CONFIRMED]

- `NDeltaCompression::CreateCompositeSchema(const CSchema*, size_t)` — merges multiple component schemas
- `CSchema::GenerateDefaultSchema(uint32 stateSize)` — creates schema for flat state
- `CNetworkScene::GatherNetworkComponentListAndCompositeSchema(...)` — builds per-object composite schema

#### Per-Component Delta Schema [CONFIRMED]

Each networked component can provide its own schema:
- `CGameObjectComponentGame::GetDeltaSchema()` — virtual, returns `const CSchema*`
- `CComponentModel::GetDeltaSchema()` — model component override
- `CComponentRequiredGameComponentBaseGameProperties::GetDeltaSchema()` — base game properties
- `CNetPropertiesManager::GetIncomingDeltaSchema()` / `GetOutgoingDeltaSchema()`

#### State Sizes [CONFIRMED]

- `CNetworkScene::skScratchDeltaBitsSize` — scratch buffer size for bit-level delta operations
- `CNetworkScene::skScratchDeltaStateSize` — scratch buffer size for state-level operations
- `CNetPropertiesManager::skSerializedSize` — fixed serialized size for properties manager
- Constraint: `scratchBitStream.GetSize() <= gkUint16Max` (max 65535 bits = ~8KB for scratch bit stream)
- Constraint: `newStateSize == GetSchema().GetPaddedStateSize()` — states must be exact schema size
- `kListenerStateSize == kSchemaStateSize` — listener and schema sizes must match

#### Delta Window [CONFIRMED]

- Template parameter `$0BA@` = 16 (hex 0x10) — **the delta window holds 16 states**
- Error messages:
  - `"Delta window is not initialized"`
  - `"Delta window memory already allocated"`
  - `"Delta window memory failed allocation"`
  - `"Delta window size mismatch. Must be %d bytes."`
  - `"Client %d delta-base outran client window, resyncing.."`
  - `"Server delta-base outran client window, resyncing.."`
- Resync occurs when base sequence falls outside 16-state window

### Bit Stream Classes [CONFIRMED]

**Source:** `E:\rel\Needle_Release\Source\Engine/Network/CNetBitStream.h`

| Class | Direction |
|---|---|
| `CNetInputBitStream` | Reading bits from network data |
| `CNetOutputBitStream` | Writing bits to network data |
| `CNetInputStream` | Higher-level input stream (wraps bit stream) |
| `CNetOutputStream` | Higher-level output stream (wraps bit stream) |

The `CInputStream` base class provides:
- `ReadBool()` → `bool`
- `ReadInt32()` → `int32`
- `ReadUint16()` → `uint16`
- `ReadUint32()` → `uint32`
- `ReadReal32()` → `float`
- `ReadString()` → `shared_string`
- `GetBytes(void*, size_t)` — raw byte read
- `AllocAlignedMemoryStream(size_t, size_t)` — aligned allocation
- `SkipBytes(size_t)` — skip forward

### Network Scene Serialization [CONFIRMED]

#### Server-Side (Write Path)

```
CServerNetworkScene::OnNetGameStateSerialize(CNetConnection&, CNetOutputStream&, uint16 sequence)
  └─> WriteCurrentGameState(CNetConnection&, CNetOutputBitStream&, CNetOutputStream&, uint16)
        └─> WriteComponentDelta(CNetConnection&, CNetOutputBitStream&, CNetOutputStream&,
                                CServerPlayerData&, SServerObjectState&, uint16)
```

#### Client-Side (Read Path)

```
CClientNetworkScene::OnNetGameStateDeserialize(CNetConnection&, CNetInputStream&, uint16 sequence)
  └─> ApplyServerGameState(CNetInputBitStream&, CNetInputStream&, uint16 baseSeq, uint16 curSeq)
        └─> UpdateComponents(SClientGameObject*, CNetInputBitStream&, CNetInputStream&,
                             double timestamp, uint16 baseSeq, uint16 curSeq)
```

---

## 4. Connection Handshake

### Connection State Machine [CONFIRMED]

The handshake follows this sequence based on extracted strings:

```
[Client]                                        [Server]
    |                                               |
    |--- ClientConnectTicket ---------------------->|  (1) Client sends ticket
    |                                               |  (2) Server validates via CNeedleConnectionAuthenticator
    |                                               |      - Checks build version compatibility
    |                                               |      - Validates reservation ID
    |                                               |      - Calls StartAuthenticateTicketForPlayer
    |<-- ServerConnectTicketAck --------------------|  (3) Server sends ticket acknowledgment
    |                                               |
    |--- ClientMtuDiscovery ----------------------->|  (4) Client starts MTU discovery
    |<-- ServerMtuHandshake ------------------------|  (5) Server responds to MTU probe
    |    (multiple MTU test segment packets)        |
    |--- "Mtu test complete" ---------------------->|  (6) MTU established
    |                                               |
    |<-- OnNetConnection (player assigned) ---------|  (7) Connection established
    |    Game state sync begins                     |
```

**Key log messages confirming this flow:**
- `"CNetConnection[0x%016llX] Attempting connection to %.64s"` — connection start
- `"CNetConnectionManager: Listening on port %d"` — server listen
- `"CNetConnectionManager: Connection created 0x%016llX"` — connection allocated
- `"Starting MTU test"` — MTU discovery begins
- `"Mtu test complete, Calling listener OnNetConnection for connection"` — MTU done, connection ready
- `"CNetConnection[0x%016llX] info-1 id:%d, RemoteAddr: %.64s, Discovered MTU:%d"` — final MTU
- `"CNetConnection[0x%016llX] info-2 state:%.64s, errorCode:%.64s, socketerr:%d"` — state dump
- `"CNetConnection[0x%016llX] info-3 receive-timeout:%f, disconnect-timeout:%f"` — timeout config

### Disconnect Sequence [CONFIRMED]

- `"CNetConnection[0x%016llX]: Disconnect - Setting to disconnecting state. Will disconnect in %f seconds."` — graceful disconnect with delay
- `DisconnectAll(const SRichError&)` — server kicks all players with reason
- `Disconnect(CStrongId<uint8> playerId, const SRichError&)` — server kicks specific player

### Connection State Error [CONFIRMED]

- `"Unhandled connection state %d!"` — from GameComponentsNeedle — proves the state machine uses integer enum values
- `"NET_ERROR_UNKNOWN_CONNECTION_STATE"` — state machine reached unexpected state

### Client-Side Connection API [CONFIRMED]

```cpp
CClientNetworkScene::Connect(
    const CBaseSocket::SSockaddr& serverAddr,
    uint32 someParam,               // [UNCERTAIN] possibly timeout or flags
    const NNetTypes::CConnectionTicket& ticket
)
```

### Server-Side Listen API [CONFIRMED]

```cpp
CServerNetworkScene::Listen(
    uint16 port,                                    // listen port
    boost::shared_ptr<INetTicketValidator> validator // ticket validation callback
) -> bool
```

Also: `FakeListenForSinglePlayer(boost::shared_ptr<INetTicketValidator>)` — for local/tutorial mode.

### INetConnectionListener Interface [CONFIRMED]

Both `CClientNetworkScene` and `CServerNetworkScene` implement `INetConnectionListener`:
- `OnNetConnection(CNetConnection&)` — new connection established
- `OnNetDisconnection(CNetConnection&)` — connection lost
- `OnNetError(CNetConnection&)` — connection error
- `OnNetGameStateSerialize(CNetConnection&, CNetOutputStream&, uint16)` — send game state
- `OnNetGameStateDeserialize(CNetConnection&, CNetInputStream&, uint16)` — receive game state
- `OnUpdateListenServerData(const CNetConnection&)` — listen server state update

---

## 5. Port Numbers

### Server Listen Port [CONFIRMED]

- Config variable: `network_ServerListenPort` (from GameComponentsNeedle)
- Config variable: `ServerPort` (from GameComponentsNeedle)
- Format string: `"API:%d, name:%s, Build:%s, MatchType:%d, MatchSize:%d, Port:%d"` — port reported to matchmaking
- Server listens via: `CServerNetworkScene::Listen(uint16 port, ...)` — uint16 port parameter
- Query port: `CServerNetworkScene::GetListenPort() -> uint16`

**Default port value:** [UNCERTAIN] — Not embedded as a visible string constant. The port is likely configured via `network_ServerListenPort` console variable at runtime, or passed from the matchmaking/reservation service. Common Armature Studio engine defaults are in the 7000-8000 range but this is speculative.

### Server Address [CONFIRMED]

- Config variable: `network_ServerAddress` — target server IP for clients
- Format: `"Matchmaker: StartRequest - Attempting direct connection to %s."` — address as string

---

## 6. MTU Discovery

### MTU Discovery Mechanism [CONFIRMED]

**Phases:**
1. `ClientMtuDiscovery` — client-initiated probe
2. `ServerMtuHandshake` — server responds
3. `ServerMtuDiscovery` — server-side discovery
4. Segment packets sent for measurement

**Config variables:**
- `netServerMtuTest` — enable/disable MTU testing
- `netServerMaxMtuTestSegmentPackets` — max segment packets for MTU probe

**Error handling:**
- `NET_ERROR_INVALID_MTU_DISCOVERY_PACKET` — malformed MTU probe
- `NET_MTU_TOO_SMALL` — discovered MTU below minimum threshold

**Result logging:**
- `"CNetConnection[0x%016llX] info-1 id:%d, RemoteAddr: %.64s, Discovered MTU:%d"` — final discovered MTU

### Fragment Ring Buffer [CONFIRMED]

For packets exceeding MTU, fragmentation is used:
- `"Fragment RB Peak Size:  %d"` — ring buffer peak usage (RB = Ring Buffer)
- `"Fragment RB Stall:      %.3f ms"` — stall time when ring buffer is full

---

## 7. Compression

### Snappy Compression [CONFIRMED]

The engine uses **Snappy** (Google's fast compression library) for network data:

```cpp
snappy::RawCompress(const char* input, size_t input_length, char* compressed, size_t* compressed_length)
snappy::RawUncompress(const char* compressed, size_t compressed_length, char* uncompressed) -> bool
snappy::GetUncompressedLength(const char* compressed, size_t compressed_length, size_t* result) -> bool
snappy::IsValidCompressedBuffer(const char* compressed, size_t compressed_length) -> bool
```

### Compression Modes [CONFIRMED]

Three compression modes found in delta compression output:
- `CM_GLOBAL` — global compression across all fields
- `CM_LOCAL_2` — local compression with 2-byte granularity
- `CM_LOCAL_4` — local compression with 4-byte granularity

Format string: `"Compression 'CM_GLOBAL' : %d (%d%%)"` — logs compression ratio per mode.

### Compression Statistics [CONFIRMED]

Performance counters:
- `"Net connection: compression time"` — time spent compressing
- `"Net connection: decompression time"` — time spent decompressing
- `"Net connection: rx bytes (compressed)"` — received compressed bytes
- `"Net connection: rx bytes (decompressed)"` — received decompressed bytes
- `"Net connection: tx bytes (compressed)"` — sent compressed bytes
- `"Net connection: tx bytes (decompressed)"` — sent decompressed bytes
- `"Net connection: serialize time"` — serialization time
- `"Net connection: deserialize time"` — deserialization time

### Game State Compression [CONFIRMED]

- `NNetTypes::SGameStatePacket::skMaxDataSize >= uncompressedSize` — max payload assertion
- `"Decompress %d"` — logs decompressed size
- `"skMaxDataSize is not huge enough to store result"` — overflow error

**Note:** Despite the task briefing mentioning zlib, the actual compression uses **Snappy**, not zlib. The DLL imports show no zlib symbols but does contain full Snappy function exports. [CONFIRMED different from initial assumption]

---

## 8. Reliable vs Unreliable Messages

### Channel System [CONFIRMED]

**Source:** `GameObjects\NetSync\CNetChannelManager.cpp`

The protocol uses a **channel-based** reliability system via `CNetChannelManager`:

- `CNetChannelManager RX` — receive-side channel manager (perf counter label)
- `CNetChannelManager TX` — transmit-side channel manager (perf counter label)
- `mpListenChannel != NULL` — listening channel must exist
- `pChannel->GetChannelIndex() < mChannels.size()` — channels are indexed
- `"CNetConnection[0x%016llX] Failed to create channel to %.64s"` — channel creation failure
- `"NET_CHANNEL_ALLOCATION_FAILED"` — channel allocation error

### Sequence Numbers [CONFIRMED]

- `CNetClientReplay::ReadSequenceNumbers(uint16* seq1, uint16* seq2)` — two uint16 sequence numbers per frame
- `CNetClientReplay::WriteSequenceNumbers(uint16 seq1, uint16 seq2)` — dual sequence tracking
- `pNetObject->mSequenceLastReceived != currentSequence` — per-object sequence tracking
- `"WARNING: Too many sequence items (%d/%d) for %s"` — sequence overflow warning

### Interpretation [UNCERTAIN]

The dual-sequence system (base + current) strongly suggests:
- One sequence for **reliable ordered** messages (acknowledged, retransmitted)
- One sequence for **unreliable** messages (latest-only, used for game state)
- The delta compression window (16 states) acts as the reliable ack window — if the server's base sequence is older than 16 frames, it resyncs: `"Server delta-base outran client window, resyncing.."`

---

## 9. Connection Ticket

### CConnectionTicket Structure [CONFIRMED]

**Namespace:** `NNetTypes::CConnectionTicket`
**Source:** Constructed/compared/assigned in GameCore

```cpp
class CConnectionTicket {
public:
    CConnectionTicket();                               // default constructor
    CConnectionTicket& operator=(const CConnectionTicket&);  // copy
    bool operator==(const CConnectionTicket&) const;   // equality comparison
    bool operator!=(const CConnectionTicket&) const;   // inequality comparison

    static const uint32 skMaxSize;                     // maximum ticket data size
};
```

### Ticket Content [CONFIRMED from GameComponentsNeedle]

The ticket contains JSON-encoded data validated by `CNeedleConnectionAuthenticator`:

**Fields parsed from ticket:**
- Build version string (compared for compatibility)
- Reservation ID (matchmaking session reference)
- Account data (player identity)
- Platform-specific auth (Steam auth ticket via `AS_Online_GetPlatformSpecificAuth()`)

**Validation flow:**
1. `CNeedleConnectionAuthenticator::StartAuthenticateTicketForPlayer` — begins async validation
2. Checks: connections allowed, reservation ID valid, build version match
3. `CNeedleConnectionAuthenticator::OnRequestComplete` — auth service callback
4. On success: connection proceeds to MTU discovery
5. On failure: one of the `TICKET_AUTH_*` errors sent

### INetTicketValidator Interface [CONFIRMED]

```cpp
class INetTicketValidator {
    // Implemented by CNeedleTicketValidator
    // Validates incoming connection tickets against reservation service
};
```

`NeedleTicketValidator` — the concrete implementation (from `Services\CNeedleTicketValidator.cpp`).

---

## 10. Network Constants

### Player Limits [CONFIRMED]

- `NNetTypes::skMaxNetworkPlayers` — maximum players (used in multiple size assertions)
  - Player IDs are `CStrongId<uint8, tag>` — uint8-based, max theoretical value 255
  - `NNetTypes::GetMaxPlayerId()` → const `CStrongId<uint8>`
  - `NNetTypes::GetFirstPlayerId()` → const `CStrongId<uint8>`
  - `NNetTypes::GetInvalidPlayerId()` → const `CStrongId<uint8>`
  - **Likely value: 20** [UNCERTAIN] — the game is 10v10, so 20 players. The assertion `NNetTypes::skMaxNetworkPlayers == mPlayerKillCountPerPlayer.size()` etc. sizes arrays to this count.

### Object Limits [CONFIRMED]

- `NNetTypes::skMaxObjectId` — maximum network object ID
  - Assertion: `networkId <= NNetTypes::skMaxObjectId`
- `NNetTypes::skInvalidObjectId` — sentinel value for no object
  - Assertion: `uniqueId != NNetTypes::skInvalidObjectId`
- `NNetTypes::skNetPackageSourceInvalidId` — invalid package source sentinel

### Match Configuration [CONFIRMED]

Match sizes:
- `MatchSize_Small` 
- `MatchSize_Medium`
- `MatchSize_Large`

Match types:
- `MatchType_Conquest`
- `MatchType_Recon`
- `MatchType_Hunt`
- `MatchType_Freeplay`
- `MatchType_Needle`
- `MatchType_NeedleCrisis`
- `MatchType_NeedleDiscovery`
- `MatchType_NeedleEscape`
- `MatchType_NeedleExploration`
- `MatchType_Tutorial`

### Timeout & Ping Configuration [CONFIRMED]

| Config Variable | Purpose |
|---|---|
| `needle_IdleTimeoutTime` | Idle kick timer |
| `needle_IdleTimeoutTimeWarning` | Warning before idle kick |
| `needle_PingTooHighThreshold` | Ping threshold (ms) for too-high warning |
| `needle_PingTooHighDropTime` | Duration (seconds) before kicking high-ping player |
| `needle_HighPingValue` | High ping display threshold |
| `needle_LowPingValue` | Low ping display threshold |
| `needle_unhealthyServerKickTime` | Time before unhealthy server kicks players |
| `needle_unhealthyServerKillTimeAfterKickTime` | Time after kick before server terminates |
| `needle_ResetServerOnNoConnections` | Reset server when all players disconnect |

### Throttle / Bandwidth Config [CONFIRMED]

| Config Variable | Purpose |
|---|---|
| `network_ThrottleLimit` | Maximum throttle level |
| `network_ThrottleStep` | Throttle adjustment step size |
| `network_ThrottleThreshold` | Threshold to trigger throttling |
| `network_ShowObjectBandwidth` | Debug: show per-object bandwidth |
| `network_ShowObjectCount` | Debug: show networked object count |

### Other Network Config [CONFIRMED]

| Config Variable | Purpose |
|---|---|
| `network_ServerAddress` | Server IP address |
| `network_ServerListenPort` | Server UDP listen port |
| `network_LocalPlayerId` | Local player ID (debug) |
| `network_PlayerName` | Local player name |
| `network_AllowCrossPlatformPlay` | Cross-platform toggle |
| `network_BlendTransform` | Network transform interpolation |
| `network_BlendVelocity` | Network velocity interpolation |
| `network_DebugBounds` | Debug: show network bounds |
| `network_DebugConnection` | Debug: connection diagnostics |
| `network_serverSceneCulling` | Server-side visibility culling |
| `network_printHierarchy` | Debug: print object hierarchy |
| `network_WarnAboutServerObjectsOnClient` | Warn if server objects exist on client |
| `needle_NetworkSyncSleepTime` | Network sync sleep interval |
| `needle_NetworkRatingUpdatePeriod` | Rating update frequency |
| `needle_DebugPingValue` | Debug: override ping value |
| `needle_ShowClientPingTimes` | Debug: show all client pings |
| `needle_serviceApiVersion` | Backend API version |

---

## Appendix A: Source File Map

### Network Source Files [CONFIRMED]

All paths relative to `E:\rel\Needle_Release\Source\`:

| File | Purpose |
|---|---|
| `Engine/Network/CNetBitStream.h` | Bit stream read/write primitives |
| `GameObjects/NetSync/CClientNetworkScene.cpp` | Client-side network scene |
| `GameObjects/NetSync/CServerNetworkScene.cpp` | Server-side network scene |
| `GameObjects/NetSync/CNetConnection.cpp` | Individual connection management |
| `GameObjects/NetSync/CNetConnectionManager.cpp` | Connection pool / listener |
| `GameObjects/NetSync/CNetChannelManager.cpp` | Channel-based reliability |
| `GameObjects/NetSync/CNetDelta.cpp` | Delta compression implementation |
| `GameObjects/NetSync/CNetIncomingWindow.cpp` | Incoming state window (sliding buffer) |
| `GameObjects/NetSync/CNetPropertiesManager.cpp` | Network properties sync |
| `GameObjects/NetSync/CNetReplay.cpp` | Network replay recording/playback |
| `GameObjects/NetSync/CNetworkScene.cpp` | Base network scene class |
| `GameObjects/NetSync/NNetGameConnection.cpp` | Connection interfaces/types |
| `GameObjects/NetSync/CComponentNetSyncServerObject.cpp` | Server object sync component |
| `Network/Win32CSocket.cpp` | Win32 socket wrapper (in Engine) |
| `System/Io/Platform/Bsd/hkBsdSocket.cpp` | Havok BSD socket layer |
| `Services/CNeedleTicketValidator.cpp` | Ticket validation service |
| `Services/CNeedleServerReservationService.cpp` | Server reservation service |
| `GameObjects/NeedleNetSync/NNeedleNetTypes.cpp` | Game-specific net types |
| `GameObjects/NeedleNetwork/CComponentNeedleNetworkClientMatchMaker.cpp` | Matchmaking |
| `GameObjects/NeedleNetworkLogin/CComponentNeedleNetworkLoginClientLoginManager.cpp` | Login |
| `GameObjects/NeedleShip/CNetNeedleShipMetadataProvider.cpp` | Ship metadata for network |

---

## Appendix B: Socket Layer

### CSocket [CONFIRMED]

From `Engine_Steam_Release.dll`:

```cpp
class CSocket : public CBaseSocket {
public:
    bool Open(int family, int type, int protocol);  // socket()
    bool Bind(const SSockaddr& addr);               // bind()
    bool Connect(const SSockaddr& addr);             // connect()
    bool Listen(int backlog);                        // listen()
    bool Accept(CSocket* out, SSockaddr* addr);      // accept()
    bool Close();                                     // closesocket()
    int Send(const char* data, int len, int flags);   // send()
    int Recv(char* buf, int len, int flags);          // recv()
    int SendTo(const SSockaddr& addr, const char* data, int len, int flags);  // sendto()
    int RecvFrom(SSockaddr* addr, char* buf, int len, int flags);  // recvfrom()
    bool GetBoundPort(uint16* port);
    bool GetBytesAvailable(uint32* bytes);
    int BlockingSend(const char* data, int len, int flags);
    int BlockingRecv(char* buf, int len, int flags);
    EWaitResult Wait(EWaitOperation op, int timeoutMs);

    static const int16 skAddressFamilyInet;     // AF_INET
    static const int skProtocolUDP;              // IPPROTO_UDP
    static const int skProtocolTCP;              // IPPROTO_TCP
    static const int skProtocolIP;               // IPPROTO_IP
    static const int skSockDatagram;             // SOCK_DGRAM
    static const int skSockStream;               // SOCK_STREAM
    static const int skOptionLevelSocket;        // SOL_SOCKET
    static const int skOptionLevelIP;            // IPPROTO_IP
    static const int skOptionLevelTCP;           // IPPROTO_TCP
    static const int skOptionLevelUDP;           // IPPROTO_UDP
    static const int skSocketOptionReuseAddr;    // SO_REUSEADDR
    static const int skSocketOptionBroadcast;    // SO_BROADCAST
    static const int skSocketOptionKeepAlive;    // SO_KEEPALIVE
    static const int skSocketOptionLinger;       // SO_LINGER
    static const int skSocketOptionReceiveBuffer; // SO_RCVBUF
    static const int skSocketOptionSendBuffer;    // SO_SNDBUF
    static const int skSocketOptionError;         // SO_ERROR
    static const int skSocketOptionNonBlockingIO; // FIONBIO
    static const int skTcpOptionNoDelay;          // TCP_NODELAY
    static const int skMsgPeek;                   // MSG_PEEK
    static const int skMsgWaitAll;                // MSG_WAITALL
    // ... plus all skError_* constants mapping to WSAE* error codes
};
```

**DLL Import:** `WS2_32.dll` — Windows Sockets 2 (confirmed via import table)

**Key detail:** `"Socket option SIO_UDP_CONNRESET failed with error %d."` — the engine sets `SIO_UDP_CONNRESET` to prevent WSAECONNRESET errors on UDP sockets when the remote port is unreachable. This is Windows-specific.

### SSockaddr [CONFIRMED]

```cpp
struct CBaseSocket::SSockaddr {
    SSockaddr();
    SSockaddr(uint16 family, uint16 port, SInAddr addr);
    void SetFamily(uint16);
    uint16 GetFamily();
    void SetPort(uint16);
    uint16 GetPort();
    shared_string ToString() const;
    bool operator==(const SSockaddr&) const;
    bool operator!=(const SSockaddr&) const;
};

struct CBaseSocket::SInAddr {
    SInAddr();
    SInAddr(uint32 addr);
    uint32 GetAddr() const;
    uint8 GetNet() const;
    uint8 GetHost() const;
    uint8 GetLogicalHost() const;
    uint8 GetImpNumber() const;
    uint16 GetImp() const;
    shared_string ToString() const;
};
```

### TCP Message Streams [CONFIRMED]

For non-game traffic (matchmaking, auth, backend services):
- `CTcpMessageStream` — raw TCP message framing
- `CTcpJsonStream` — JSON over TCP (uses RapidJSON)
- `CHttpManager` / `CHttpRequest` — HTTP via libcurl (with SSL support via OpenSSL)

---

## Appendix C: Voice Chat

### Steam Voice [CONFIRMED]

- Voice uses Steam's built-in voice API (not custom UDP):
  - `"DecompressVoice: result=%s"`
  - `"GetAvailableVoice: result=%s bytes=%d"`
  - `"GetVoice: result=%s"`
- Uses `SteamNetworking` for voice relay
- Config: `needle_VoiceChatPushToTalkMode`, `needle_VoiceChatLoopback`, `needle_VoiceChatSpeakerVolume`

---

## Appendix D: Key Architectural Insights for Server Revival

1. **The game protocol is NOT pure raw UDP.** It uses CSocket with skProtocolUDP for game traffic, but the connection layer adds: ticket auth, MTU discovery, channel-based reliability, sequence numbers, delta compression with 16-state sliding window, and Snappy compression.

2. **A replacement server needs to implement:**
   - UDP socket listener
   - `ServerConnectTicketAck` response to `ClientConnectTicket` 
   - `ServerMtuHandshake` response to `ClientMtuDiscovery`
   - MTU test segment handling
   - Channel creation and management
   - Delta state generation using `NDeltaCompression::CSchema` format
   - Snappy compression of game state packets
   - Sequence number tracking (dual uint16)
   - Per-object delta tracking with 16-state window

3. **The ticket validation can be replaced.** The `INetTicketValidator` interface is a clean abstraction — a custom server can implement its own validator that bypasses the now-defunct CNeedleConnectionAuthenticator and reservation service.

4. **Build version checking must be handled.** The authenticator checks: `"Incompatible build: %.*s, Expected: %.*s"` — the server must either report a matching build version or the check must be bypassed.

5. **The backend services (HTTP) are separate from gameplay.** Matchmaking, reservations, account auth all use HTTP/JSON via CTcpJsonStream and CHttpManager. The actual game state flows over UDP. These are independent systems that can be replaced independently.
