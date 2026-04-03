# Dead Star Binary Analysis Report

**Date:** 2026-04-03
**Analyst:** Binary Analyst Agent
**Target:** Dead Star (Steam AppID 366400, Depot 366401)
**Build Path:** `E:\rel\Needle_Release\`
**Binaries:** `Bin64/` — Windows PE x64, compiled with MSVC 2012 (MSVCR110/MSVCP110)

---

## 1. Binary Inventory

| Binary | Size | Type | Export Count | Description |
|--------|------|------|-------------|-------------|
| DeadStar.exe | 23 KB | Stub launcher | 2 | GPU preference flags only; calls into GameCore |
| GameCore_Steam_Release.dll | 7.0 MB | Engine + game core | 16,102 | Game object system, networking, physics, rendering pipeline |
| Engine_Steam_Release.dll | 5.5 MB | Engine services | 8,238 | HTTP, sockets, DNS, resources, sound, input, boost::regex |
| GameComponentsNeedle_Steam_Release.dll | 3.5 MB | Game logic | 5 | Needle-specific game components (ships, galaxy, matchmaking UI) |
| Renderer_Steam_Release.dll | 682 KB | D3D11 renderer | 2,178 | DirectX 11 rendering, shaders, materials |
| Opcode_Steam_Release.dll | 447 KB | Collision library | 2,054 | OPCODE collision detection (3rd party) |
| NeedleCommon_Steam_Release.dll | 41 KB | Shared API/certs | 34 | Web service URLs, certificates, instance wrangler, matchmaker IDs |
| steam_api64.dll | 208 KB | Steamworks | 1,404 | Valve Steamworks SDK |

---

## 2. Export Table Analysis

### 2.1 DeadStar.exe (Stub Launcher) [CONFIRMED]

Only 2 exports — GPU preference flags:
```
[0] AmdPowerXpressRequestHighPerformance
[1] NvOptimusEnablement
```

Imports `?bpeWin32_GameCoreMain@@YAHPEAUHINSTANCE__@@0PEADH@Z` from `GameCore_Steam_Release.dll` and standard CRT functions. This is a pure stub that launches the game via GameCore.

### 2.2 GameCore_Steam_Release.dll (16,102 exports) [CONFIRMED]

**Entry Points (ordinals 7500-7501):**
```
[7500] ?bpeWin32Server_GameCoreMain@@YAHPEAUHINSTANCE__@@HPEAPEBD@Z
       Demangled: int bpeWin32Server_GameCoreMain(HINSTANCE__*, int argc, char const** argv)

[7501] ?bpeWin32_GameCoreMain@@YAHPEAUHINSTANCE__@@0PEADH@Z
       Demangled: int bpeWin32_GameCoreMain(HINSTANCE__*, HINSTANCE__*, char*, int)
```

The server entry uses argc/argv convention; the client entry uses WinMain convention.

**Key Export Categories:**
- CCPLdr* — Component Property Loader classes (game object configuration serialization)
- CComponent* — Runtime game object component implementations
- CNet* — Networking classes (delta compression, connections, scenes)
- CServer*/CClient* — Server/client network scene implementations
- boost::regex — Boost regex library statically linked
- Havok Physics — hknp*, hkcd* physics/collision classes (Havok 2014 build)

### 2.3 Engine_Steam_Release.dll (8,238 exports) [CONFIRMED]

Heavily exports boost::regex, plus engine fundamentals:
- CHttpManager, CHttpRequest, CHttpRequestParameters — HTTP client (curl-based)
- CSocket, CBaseSocket, CTcpJsonStream, CTcpMessageStream — Socket layer
- CResourceFactory, CResourcePool, CResourceManager — Resource system
- CGameObject, CGameObjectComponent, CGameObjectProperties — Object system
- NDeltaCompression::CSchema — Delta compression schema
- CNetDeviceManager — Network device management
- NSoundSystemWwise — Wwise audio integration
- TinyXml/TinyXPath — XML parsing (bpe_TinyXml namespace)
- CLocalizationTable — Localization system

### 2.4 GameComponentsNeedle_Steam_Release.dll (5 exports) [CONFIRMED]

Minimal export surface — plugin-style DLL:
```
[0] ?__force_dll_exports_gamecomponents_needle@@3HA       (force export symbol)
[1] GameRendererFactory                                     (renderer factory function)
[2] Win32GameComponents_BindGameManager                     (bind to game manager)
[3] Win32GameComponents_UnbindGameManager                   (unbind from game manager)
[4] force_imports_helper_stub_gamecomponents_needle          (force import symbol)
```

This DLL registers its components with the engine's game manager via bind/unbind pattern. All game logic is consumed through the component system, not direct exports.

### 2.5 NeedleCommon_Steam_Release.dll (34 exports) [CONFIRMED]

Critical for server revival — contains all web service infrastructure:

```
NNeedleWebServiceCommon namespace:
  [7]  AddWebServiceInterfaceVersionParam  — adds API version to HTTP requests
  [16] GetPrivateServicesCACertificate      — CA cert for private API (mutual TLS)
  [17] GetPrivateServicesClientCertificate   — client cert for private API
  [18] GetPrivateServicesClientKey           — client key for private API
  [19] GetPrivateServicesUrlForPath          — builds private API URL
  [20] GetPublicServicesCertificate          — public API certificate
  [21] GetPublicServicesUrlForPath           — builds public API URL

NNeedleInstanceWrangler namespace:
  [10] DecodeJson (SServerInstance)          — deserialize server instance from JSON
  [11] EncodeJson (SServerInstance)          — serialize server instance to JSON
  [26] IsValidServerInstance                 — validate server instance
  [30] ServerInstanceToString                — string representation

NNeedleMatchMaker namespace:
  [22] GetRegionBit (ERegionCode)            — convert region to bitmask
  [25] IsValidReservationId                  — validate match reservation
  [28] ReservationIdAsString                 — reservation ID to string
  [29] ReservationIdFromString               — string to reservation ID

NNeedleAmazonMetadata namespace:
  [9]  DebugIsFake                           — check if metadata is spoofed
  [12] GetError                              — get error from metadata lookup
  [15] GetMetadata (SMetaData)               — get AWS instance metadata
  [23] HasMetadata                           — check if metadata available
  [24] IsRequested                           — check if metadata was requested
  [27] RequestMetadata                       — fetch from http://169.254.169.254/
  [32] UpdateReturnComplete                  — check metadata fetch completion

Utility:
  [0]  CExitHandler::CExitHandler
  [1]  CWin32AssertHook::CWin32AssertHook
  [31] CExitHandler::Set
  [33] CExitHandler::Wait
```

### 2.6 Renderer_Steam_Release.dll (2,178 exports) [CONFIRMED]

D3D11 rendering pipeline. Imports d3d11.dll, d3dx11_43.dll, D3DCOMPILER_43.dll, dxgi.dll.

### 2.7 Opcode_Steam_Release.dll (2,054 exports) [CONFIRMED]

OPCODE collision detection library. Self-contained, imports only MSVCR110.dll and KERNEL32.dll.

---

## 3. Import Dependency Graph [CONFIRMED]

```
DeadStar.exe
  └── GameCore_Steam_Release.dll
        ├── Engine_Steam_Release.dll
        │     ├── steam_api64.dll
        │     ├── Opcode_Steam_Release.dll
        │     ├── WS2_32.dll (Winsock)
        │     ├── WININET.dll (HTTP)
        │     ├── DNSAPI.dll
        │     ├── XINPUT1_3.dll (gamepad)
        │     ├── IPHLPAPI.DLL
        │     ├── RPCRT4.dll
        │     ├── WINMM.dll
        │     ├── HID.DLL
        │     ├── SETUPAPI.dll
        │     └── ole32.dll
        ├── NeedleCommon_Steam_Release.dll
        │     ├── Engine_Steam_Release.dll
        │     ├── steam_api64.dll
        │     ├── dbghelp.dll (crash dumps, stack walks)
        │     └── Secur32.dll (authentication)
        ├── Renderer_Steam_Release.dll
        │     ├── Engine_Steam_Release.dll
        │     ├── d3d11.dll
        │     ├── d3dx11_43.dll
        │     ├── D3DCOMPILER_43.dll
        │     └── dxgi.dll
        ├── WS2_32.dll (direct Winsock for game networking)
        ├── steam_api64.dll
        └── dxgi.dll

GameComponentsNeedle_Steam_Release.dll
  ├── GameCore_Steam_Release.dll
  ├── Engine_Steam_Release.dll
  ├── Renderer_Steam_Release.dll
  ├── NeedleCommon_Steam_Release.dll
  └── steam_api64.dll
```

**Key Insight:** GameCore imports WS2_32.dll directly (in addition to Engine), meaning it has its own socket-level networking code separate from the Engine's HTTP/socket layer. This is likely the UDP game networking (CNetConnection, CNetChannelManager).

---

## 4. Class Hierarchy Mapping

### 4.1 Networking Classes (CNet*) [CONFIRMED]

**Network Scene Hierarchy:**
```
CGameObjectGlobalData (base)
├── CNetworkScene                          (base network scene)
│   ├── CClientNetworkScene                (client-side networking)
│   │   implements: INetConnectionListener
│   └── CServerNetworkScene                (server-side networking)
│       implements: INetConnectionListener
└── CNetPropertiesManager                  (net property sync)
    implements: IListener@NNetGameConnection
```

**Delta Compression:**
```
CNetDeltaBase<16> (template, 16-byte blocks)
├── CNetDeltaIncoming                      (incoming delta state)
└── CNetDeltaOutgoing                      (outgoing delta state)

NDeltaCompression::CSchema                 (defines delta schema)
```

**Connection System (from source paths):**
```
CNetConnection                             (GameObjects\NetSync\CNetConnection.cpp)
CNetConnectionManager                      (GameObjects\NetSync\CNetConnectionManager.cpp)
CNetChannelManager                         (GameObjects\NetSync\CNetChannelManager.cpp)
CNetIncomingWindow                         (GameObjects\NetSync\CNetIncomingWindow.cpp)
CNetReplay                                 (GameObjects\NetSync\CNetReplay.cpp)
CNetClientReplay                           (replay system)
NNetGameConnection                         (GameObjects\NetSync\NNetGameConnection.cpp)
CNetDeviceManager                          (Engine: Network\CNetDeviceManager.cpp)
```

**Net Sync Components:**
```
CComponentNetSync (base)
├── CComponentNetSyncClientObjectHost      (client object host)
├── CComponentNetSyncServerObject          (server replicated object)
└── CComponentNetSyncServerObjectHost      (server object host)
```

**Network Types:**
```
NNetTypes::CConnectionTicket               (connection authentication ticket)
CBaseSocket::SSockaddr                     (socket address wrapper)
CBaseSocket::SInAddr                       (IP address wrapper)
```

### 4.2 Needle Service Classes [CONFIRMED]

**From GameComponentsNeedle source paths:**
```
Services\CNeedleAccountService.cpp         — Account authentication
Services\CNeedleClientAccountDataService.cpp — Client account data sync
Services\CNeedleClientLeaderboardsService.cpp — Leaderboard queries
Services\CNeedleClientMessagesService.cpp  — In-game messaging
Services\CNeedleClientReportingService.cpp — Player reporting
Services\CNeedleClientServiceParent.cpp    — Base class for client services
Services\CNeedleServerAccountDataService.cpp — Server-side account data
Services\CNeedleServerReservationService.cpp — Server match reservation
Services\CNeedleTicketValidator.cpp        — Steam ticket validation
```

**Service Think Loop Names (confirmed from strings):**
```
AccountService::OnPreThink
ClientAccountDataHelper::PreThink
ClientAccountDataService::OnPreThink
ClientCapitalShipDataService::OnPreThink
ClientLeaderboardsService::OnPreThink
ClientMatchMaker
ClientMessagesService::OnPreThink
ClientReportingService::OnPreThink
CNeedleServerCapitalShipDataService::OnPreThink
```

**LAN Services:**
```
CLanServiceAdvertiser(port, ?)             — LAN server broadcast
CLanServiceBrowser(?)                      — LAN server discovery
```

### 4.3 Network Login & Matchmaking [CONFIRMED]

**Components (from source paths + strings):**
```
CComponentNeedleNetworkLoginClientLoginManager — Client login flow
CComponentNeedleNetworkClientMatchMaker    — Matchmaking client
CComponentNeedleNetworkClientAccountDataHelper — Account data UI bridge
```

**CCPLdr UI Components (from vtables/strings):**
```
CCPLdrNeedleNetworkClientAccountDataHelper
CCPLdrNeedleNetworkClientMatchMaker
CCPLdrNeedleNetworkLoginClientLoginManager
CCPLdrNeedleUILobbyHelper
CCPLdrNeedleUILobbyPlayerEntry
CCPLdrNeedleUIMatchmakingStatusDisplay
CCPLdrNeedleUIMatchSummaryController
CCPLdrNeedleUIMatchTimeDisplay
CCPLdrNeedleUILeaderboardController
CCPLdrNeedleUILeaderboardEntry
CCPLdrNeedleUISubmitReport
```

### 4.4 Galaxy & Capital Ship System [CONFIRMED]

```
CNeedleGalaxy                              — Galaxy map state
CNeedleGalaxyDefinition                    — Galaxy structure definition
CNeedleGalaxyClient                        — Client galaxy state
CNeedleCapitalShipManager                  — Capital ship management
CNeedleClientCapitalShipDataService        — Client capital ship data
CNeedleServerCapitalShipDataService        — Server capital ship data

CCPLdrNeedleGalaxyBackground
CCPLdrNeedleGalaxyBorderControl
CCPLdrNeedleGalaxyGenerator
CCPLdrNeedleGalaxyRegion
CCPLdrNeedleGalaxySector
CCPLdrNeedleGalaxySectorConnectionSwitch
CCPLdrNeedleGalaxySectorInhabitant
CCPLdrNeedleCapitalShipController
CCPLdrNeedleCapitalShipMessageProxy
CCPLdrNeedleCapitalShipNodeController
CCPLdrNeedleCapitalShipNodeStatus
CCPLdrNeedleCapitalShipResourcePodSetup
CCPLdrNeedleCapitalShipResourcePodSpawner
CCPLdrNeedleCapitalShipResourcePodStatus
CCPLdrNeedleCapitalShipShipStatus
CCPLdrNeedleCapitalShipWarpTimer
```

### 4.5 HTTP/Socket Layer (Engine) [CONFIRMED]

```
CHttpManagerBase (base)
└── CHttpManager                           (curl-based HTTP client)

CHttpRequestBase (base)
└── CHttpRequest                           (individual HTTP request)

CHttpRequestParameters                     (URL, method, headers, queries)
CHttpInputStream                           (HTTP response stream)

CBaseSocket (base)
└── CSocket                                (TCP/UDP socket wrapper)

CTcpMessageStream                          (length-prefixed TCP messages)
CTcpJsonStream                             (JSON over TCP)

NDnsResolverWin32                          (async DNS resolution)
```

### 4.6 Game Object System [CONFIRMED]

```
CGameObject                                (base game object)
├── CGameObjectGame                        (game-level object)
└── CGameObjectGlobalData                  (global shared data)

CGameObjectComponent                       (base component)
├── CGameObjectComponentGame               (game component)
├── CGameObjectComponentGameController     (controller)
└── CGameObjectComponentGamePlayer         (player)

CGameObjectProperties                      (serialized properties)
├── CGameObjectComponentProperties         (component properties)
├── CGameObjectPropertiesPackage           (package of properties)
└── CStateMachineObjectProperties          (state machine properties)

CBaseGameManager
└── CGameManager                           (main game manager)
```

---

## 5. VTable Mapping

### 5.1 GameCore VTables (452 total) [CONFIRMED]

**Networking VTables (with interface inheritance):**
```
??_7CClientNetworkScene@@6BCGameObjectGlobalData@@@       — CClientNetworkScene vtable (as CGameObjectGlobalData)
??_7CClientNetworkScene@@6BINetConnectionListener@@@      — CClientNetworkScene vtable (as INetConnectionListener)
??_7CServerNetworkScene@@6BCGameObjectGlobalData@@@       — CServerNetworkScene vtable (as CGameObjectGlobalData)
??_7CServerNetworkScene@@6BINetConnectionListener@@@      — CServerNetworkScene vtable (as INetConnectionListener)
??_7CNetworkScene@@6BCGameObjectGlobalData@@@             — CNetworkScene vtable (as CGameObjectGlobalData)
??_7CNetworkScene@@6BINetConnectionListener@@@            — CNetworkScene vtable (as INetConnectionListener)
??_7CNetPropertiesManager@@6BCGameObjectGlobalData@@@     — CNetPropertiesManager vtable (as CGameObjectGlobalData)
??_7CNetPropertiesManager@@6BIListener@NNetGameConnection@@@ — CNetPropertiesManager vtable (as NNetGameConnection::IListener)
??_7CNetDeltaIncoming@@6B@                                — CNetDeltaIncoming vtable
??_7CNetDeltaOutgoing@@6B@                                — CNetDeltaOutgoing vtable
??_7?$CNetDeltaBase@$0BA@@@6B@                            — CNetDeltaBase<16> vtable
```

**Net Sync Component VTables:**
```
??_7CComponentNetSync@@6B@
??_7CComponentNetSyncClientObjectHost@@6B@
??_7CComponentNetSyncServerObject@@6B@
??_7CComponentNetSyncServerObjectHost@@6B@
??_7ICGLdrNetSync@@6B@
```

**Key Game VTables:**
```
??_7CGameManager@@6B@
??_7CGameObjectGame@@6B@
??_7CGameObjectComponentGame@@6B@
??_7CGameObjectComponentGameController@@6B@
??_7CGameObjectComponentGamePlayer@@6B@
??_7CScriptPackageManager@@6B@
??_7CShipInfoTable@@6B@
??_7CParticleRenderManager@@6B@
```

### 5.2 Engine VTables (76 total) [CONFIRMED]

**Network/HTTP:**
```
??_7CBaseSocket@@6B@
??_7CSocket@@6B@
??_7SSockaddr@CBaseSocket@@6B@
??_7CHttpManager@@6B@
??_7CHttpManagerBase@@6B@
??_7CHttpRequest@@6B@
??_7CHttpRequestBase@@6B@
??_7CTcpJsonStream@@6B@
??_7CTcpMessageStream@@6B@
```

**Game Object System:**
```
??_7CGameObject@@6B@
??_7CGameObjectComponent@@6B@
??_7CGameObjectComponentMethods@@6B@
??_7CGameObjectComponentProperties@@6B@
??_7CGameObjectGlobalData@@6B@
??_7CGameObjectProperties@@6B@
??_7CGameObjectPropertiesPackage@@6B@
??_7CBaseGameManager@@6B@
```

**Resource System:**
```
??_7CResourceCache@@6B@
??_7CResourceFactory@@6B@
??_7CResourcePool@@6B@
??_7CResourceWithDependencies@@6B@
```

**Third-Party:**
```
??_7TiXmlElement@bpe_TinyXml@@6B@           (XML)
??_7xpath_processor@TinyXPath@@6B@          (XPath)
??_7CSoundBank@NSoundSystemWwise@@6B@       (Audio)
```

### 5.3 GameComponentsNeedle VTables (3 total) [CONFIRMED]

Very few vtables — most logic is in GameCore components:
```
??_7SSockaddr@CBaseSocket@@6B@              (inherited)
??_7IEvaluator@@6B@                         (inherited)
??_7IColorEvaluator@@6B@                    (inherited)
```

---

## 6. Source File Tree Reconstruction [CONFIRMED]

### 6.1 Build Paths

**Main Build Root:**
```
E:\rel\Needle_Release\
```

**PDB Locations:**
```
E:\rel\Needle_Release\Bin64\DeadStar.pdb
E:\rel\Needle_Release\Bin64\GameCore_Steam_Release.pdb
E:\rel\Needle_Release\Bin64\GameComponentsNeedle_Steam_Release.pdb
E:\rel\Needle_Release\Bin64\Engine_Steam_Release.pdb
E:\rel\Needle_Release\Bin64\NeedleCommon_Steam_Release.pdb
E:\rel\Needle_Release\Bin64\Opcode_Steam_Release.pdb
E:\rel\Needle_Release\Bin64\Renderer_Steam_Release.pdb
```

**Havok Physics Build:**
```
Y:\NightlyJobs\20141121-01\Source\   (Havok SDK, built November 21, 2014)
```

### 6.2 Reconstructed Source Tree

```
E:\rel\Needle_Release\Source\
├── Engine\
│   ├── Basics\
│   │   └── BPEAssert.h / BPEAssert.cpp
│   ├── Animation\
│   │   ├── CAnimationSystem.cpp
│   │   └── CAnimationSystem_ProcessBlendTree.cpp
│   ├── Collision\
│   │   └── CCollisionMesh.cpp
│   ├── Evaluators\
│   │   ├── EvaluatorUtils.cpp
│   │   └── IEvaluator.cpp
│   ├── GameObjectSystem\
│   │   ├── CBaseGameManager.cpp
│   │   ├── CGameObjectComponent.cpp
│   │   ├── CGameObjectComponentProperties.cpp
│   │   ├── CGameObject.cpp
│   │   ├── CGameObjectMessageHandler.cpp
│   │   ├── CGameObjectProperties.cpp
│   │   ├── CGameObjectPropertiesPackage.cpp
│   │   ├── CGameObjectRegisteredComponentGroupObjectFactories.cpp
│   │   ├── CObjectList.cpp
│   │   └── CUniqueIdGenerator.cpp
│   ├── Graphics\
│   │   ├── CFrustumPlanes.cpp
│   │   ├── CLight.h
│   │   └── CVertexArray.cpp
│   ├── Http\
│   │   └── CHttpManagerCurl.cpp
│   ├── Input\
│   │   ├── CInputGenerator.cpp
│   │   └── Win32CInputGenerator.cpp
│   ├── Math\
│   │   └── Straight_CPP\CMatrix34.cpp
│   ├── Mechanics\
│   │   ├── CLocalizationTable.cpp
│   │   ├── NDeltaCompression.cpp
│   │   └── shared_string.h
│   ├── Memory\
│   │   └── CBucketAllocator.cpp
│   ├── Network\
│   │   ├── CNetBitStream.h
│   │   ├── CNetDeviceManager.cpp
│   │   ├── CNetStream.h
│   │   ├── NDnsResolverWin32.cpp
│   │   └── Win32CSocket.cpp
│   ├── Resource\
│   │   ├── CBaseResourceFactoryLoadItem.cpp
│   │   ├── CResId.cpp
│   │   ├── CResourceFactory.cpp
│   │   ├── CResourceManager.h / CResourceManager.cpp
│   │   └── CResourcePool.cpp
│   ├── Script\
│   │   └── CScriptVar.cpp
│   ├── Sound\
│   │   ├── NSoundSystemWWise.cpp
│   │   └── Win32\AkFileHelpers.h
│   ├── Streams\
│   │   ├── CDiskInputStream.cpp
│   │   ├── CDiskOutputStream.cpp
│   │   ├── CHttpInputStream.cpp
│   │   └── CInputStream.cpp
│   └── System\
│       ├── CArmatureArchive.cpp
│       ├── CGuid.cpp
│       ├── COsContext.cpp
│       └── CTaskQueue.cpp
├── Game\
│   ├── Animation\CAnimationTransitions.cpp
│   ├── CCameraManager.cpp
│   ├── CDebugConsole.cpp
│   ├── CDebugMenu.cpp
│   ├── CEventCharacterBinding.cpp
│   ├── CGame.cpp
│   ├── CGameManager.cpp
│   ├── CScriptManager_KeyValueMap.cpp
│   ├── CScriptPackageManager.cpp
│   ├── CStateMachine.cpp
│   ├── CTextMenu.cpp / CTextMenu.h
│   ├── main.cpp
│   ├── NWin32VideoSettings.cpp
│   ├── Win32Main.cpp
│   ├── GameObjects\
│   │   ├── AiHelper\
│   │   │   ├── CComponentAiHelperAveragingHeightAdjuster.cpp
│   │   │   └── CComponentAiHelperFootLocker.cpp
│   │   ├── AnimationEventBound\CComponentAnimationEventBoundDelegate.cpp
│   │   ├── AnimationHelper\
│   │   │   ├── CAnimationMapping.cpp
│   │   │   └── CComponentAnimationHelperSyncGroup.cpp
│   │   ├── Camera\CComponentCamera.cpp
│   │   ├── CameraModifier\CComponentCameraModifierCloneActiveCameraProperties.cpp
│   │   ├── CameraShake\CComponentCameraShake.cpp
│   │   ├── CGameObjectComponentGame.cpp
│   │   ├── CGameObjectComponentStateMachine.cpp
│   │   ├── CGameObjectGame.cpp
│   │   ├── CGameObjectPropertyPackageMultiLoader.cpp
│   │   ├── ColorStack\
│   │   │   ├── CComponentColorStack.cpp
│   │   │   ├── CComponentColorStackEvaluatorCrossFadeItem.cpp
│   │   │   └── CComponentColorStackSimpleCrossFadeItem.cpp
│   │   ├── CStateMachineObjectProperties.cpp
│   │   ├── FollowJoint\CComponentFollowJointSimple.cpp
│   │   ├── General\
│   │   │   ├── CComponentGeneralFollowJoint.cpp
│   │   │   ├── CComponentGeneralFrustumCullingHelper.cpp
│   │   │   ├── CComponentGeneralJointFollowJoint.cpp
│   │   │   └── CComponentGeneralSuperTouchSensor.cpp
│   │   ├── LoadScriptPackage\CComponentLoadScriptPackage.cpp
│   │   ├── Localization\CComponentLocalizationArray.cpp
│   │   ├── Model\
│   │   │   ├── CComponentModelAnimation.cpp
│   │   │   └── CComponentModelAnimationStatic.cpp
│   │   ├── NetSync\                        *** CRITICAL FOR REVIVAL ***
│   │   │   ├── CClientNetworkScene.cpp
│   │   │   ├── CComponentNetSyncServerObject.cpp
│   │   │   ├── CNetChannelManager.cpp
│   │   │   ├── CNetConnection.cpp
│   │   │   ├── CNetConnectionManager.cpp
│   │   │   ├── CNetDelta.cpp
│   │   │   ├── CNetIncomingWindow.cpp
│   │   │   ├── CNetPropertiesManager.cpp
│   │   │   ├── CNetReplay.cpp
│   │   │   ├── CNetworkScene.cpp
│   │   │   ├── CServerNetworkScene.cpp
│   │   │   └── NNetGameConnection.cpp
│   │   ├── ParticleSystem\...
│   │   ├── PathFind\CComponentPathFind.cpp
│   │   ├── RequiredGameComponent\...
│   │   ├── RigidBodyConstraint\...
│   │   ├── RigidBodyPhysics\...
│   │   ├── SM_Animation\...
│   │   ├── SM_BaseComponent\...
│   │   ├── SM_General\...
│   │   ├── SoundWwise\...
│   │   ├── StateMachine\...
│   │   ├── TextRender\...
│   │   └── UIHelper\CShipInfoTable.cpp
│   ├── GameComponentsNeedle\
│   │   ├── CNeedleSavedSettings.cpp
│   │   ├── COzzyCameraManager.cpp
│   │   ├── Render\CGameRendererNeedle.cpp
│   │   ├── Services\                       *** CRITICAL FOR REVIVAL ***
│   │   │   ├── CNeedleAccountService.cpp
│   │   │   ├── CNeedleClientAccountDataService.cpp
│   │   │   ├── CNeedleClientLeaderboardsService.cpp
│   │   │   ├── CNeedleClientMessagesService.cpp
│   │   │   ├── CNeedleClientReportingService.cpp
│   │   │   ├── CNeedleClientServiceParent.cpp
│   │   │   ├── CNeedleServerAccountDataService.cpp
│   │   │   ├── CNeedleServerReservationService.cpp
│   │   │   └── CNeedleTicketValidator.cpp
│   │   └── GameObjects\
│   │       ├── NebulaArchetype\NNebulaArchetypeCommon.cpp
│   │       ├── NeedleAnalytics\CComponentNeedleAnalytics.cpp
│   │       ├── NeedleApplyEffect\CComponentNeedleApplyEffect.cpp
│   │       ├── NeedleAreaEffect\CComponentNeedleAreaEffectJump.cpp
│   │       ├── NeedleCapitalShip\
│   │       │   ├── CNeedleCapitalShipManager.cpp
│   │       │   ├── CNeedleClientCapitalShipDataService.cpp
│   │       │   └── CNeedleServerCapitalShipDataService.cpp
│   │       ├── NeedleController\
│   │       │   ├── CComponentNeedleControllerAI.cpp
│   │       │   └── CComponentNeedleController.cpp
│   │       ├── NeedleDevice\
│   │       │   ├── CComponentNeedleDevice.cpp
│   │       │   └── CComponentNeedleDeviceDroneControl.cpp
│   │       ├── NeedleEffect\CComponentNeedleEffectTentacle.cpp
│   │       ├── NeedleGalaxy\
│   │       │   ├── CComponentNeedleGalaxyBackground.cpp
│   │       │   ├── CComponentNeedleGalaxyRegion.cpp
│   │       │   ├── CComponentNeedleGalaxySector.cpp
│   │       │   ├── CNeedleGalaxyClient.cpp
│   │       │   ├── CNeedleGalaxy.cpp
│   │       │   ├── CNeedleGalaxyDefinition.cpp
│   │       │   └── NNeedleGalaxy.cpp
│   │       ├── NeedleGameController\
│   │       │   ├── CComponentNeedleGameController.cpp
│   │       │   ├── CComponentNeedleGameControllerDefault.cpp
│   │       │   ├── CNeedlePlayerData.cpp / CNeedlePlayerData.h
│   │       │   ├── CNeedleShipData.cpp / CNeedleShipData.h
│   │       │   └── NNeedleGameUtils.cpp
│   │       ├── NeedleGeneral\
│   │       │   ├── CComponentNeedleGeneralNetworkedMessageRelay.cpp
│   │       │   └── CNeedleLightBarManager.cpp
│   │       ├── NeedleGun\CComponentNeedleGun.cpp
│   │       ├── NeedleHealth\CComponentNeedleHealthRegenerative.cpp
│   │       ├── NeedleLocalClient\
│   │       │   ├── CComponentNeedleLocalClientLocalTeamSwitch.cpp
│   │       │   └── CNeedleLocalPlayerDataManager.cpp
│   │       ├── NeedleNetSync\
│   │       │   ├── CComponentNeedleNetSyncClientObjectHost.cpp
│   │       │   ├── CComponentNeedleNetSyncServerObjectHost.cpp
│   │       │   └── NNeedleNetTypes.cpp
│   │       ├── NeedleNetwork\
│   │       │   ├── CComponentNeedleNetworkClientAccountDataHelper.cpp
│   │       │   └── CComponentNeedleNetworkClientMatchMaker.cpp
│   │       ├── NeedleNetworkLogin\CComponentNeedleNetworkLoginClientLoginManager.cpp
│   │       ├── NeedlePackage\
│   │       │   ├── CComponentNeedlePackageGeneratedObjectDefinition.cpp
│   │       │   ├── CComponentNeedlePackageLoadScriptPackageOverride.cpp
│   │       │   └── CNeedleShipMasterListManager.cpp
│   │       ├── NeedleRender\CComponentNeedleRenderOutline.cpp
│   │       ├── NeedleRespawn\CNeedleRespawnManager.cpp
│   │       ├── NeedleShip\
│   │       │   ├── CComponentNeedleShipGeneric.cpp
│   │       │   └── CNetNeedleShipMetadataProvider.cpp
│   │       ├── NeedleShot\
│   │       │   ├── CComponentNeedleShotBeam.cpp
│   │       │   └── CComponentNeedleShotBullet.cpp
│   │       ├── NeedleStructure\CComponentNeedleStructureGeneric.cpp
│   │       └── NeedleUI\
│   │           ├── CComponentNeedleUIAfterActionController.cpp
│   │           ├── CComponentNeedleUIFocusItem.cpp
│   │           ├── CComponentNeedleUILobbyHelper.cpp
│   │           ├── CComponentNeedleUIPortraitIconDisplay.cpp
│   │           ├── CComponentNeedleUIReconstructionMenuController.cpp
│   │           ├── CComponentNeedleUIRegionDisplay.cpp
│   │           ├── CComponentNeedleUIShipAugmentMenuController.cpp
│   │           ├── CComponentNeedleUIShipSystemValues.cpp
│   │           ├── CComponentNeedleUISpriteAnimation.cpp
│   │           ├── CComponentNeedleUISprite.cpp
│   │           ├── CNeedlePlayerCommsManager.cpp
│   │           ├── CNeedleStringMacroManager.cpp
│   │           └── CNeedleUIPopupManager.cpp
│   └── NeedleCommon\
│       └── NNeedleWebServiceCommon.cpp
├── PathFinding\
│   ├── CPathArea.cpp
│   ├── CPathFindingManager.cpp
│   └── CPathObstacle.cpp
├── Physics\
│   └── CPhysicsManager.cpp
└── Renderer\
    ├── Backend\
    │   ├── CRenderBackend.cpp
    │   ├── CRenderHWAllocator.cpp
    │   └── Win32\
    │       ├── Win32CRenderBackend.cpp / Win32CRenderBackend.h
    │       └── Win32CTexture.cpp
    ├── CMTXFont.cpp
    ├── Frontend\
    │   ├── CRenderer.cpp
    │   └── RenderObject\CMeshRenderEntity.cpp
    ├── Material\
    │   ├── CMaterialLibrary.cpp
    │   ├── ProgShader\Shaders\
    │   │   ├── CEditorBillboardShader.cpp
    │   │   ├── CUnlitGeneric.cpp
    │   │   ├── CVertexLitGeneric.cpp
    │   │   └── Needle\
    │   │       ├── CNeedleCharacterShader.cpp
    │   │       ├── CNeedleEnvironmentBlendedShader.cpp
    │   │       ├── CNeedleEnvironmentLayeredShader.cpp
    │   │       ├── CNeedleEnvironmentShader.cpp
    │   │       └── CNeedleUIShader.cpp
    │   ├── Win32\
    │   │   ├── Win32CCompiledShader.cpp
    │   │   └── Win32CUniformBuffer.cpp
    │   └── Win32_Tools\CookedShaderFormat_Win32.cpp
    ├── Primitive\
    │   ├── CShadowModel.cpp
    │   ├── ProgShader\
    │   │   ├── PSCMesh.cpp
    │   │   ├── PSCSkinnedMesh.cpp
    │   │   └── Win32\Win32CMeshBuffers.cpp
    │   └── Win32\
    │       ├── Win32CIndexBuffer.cpp
    │       └── Win32CVertexBuffer.cpp
    └── Settings\
        └── CSavedVideoSettings.cpp
```

---

## 7. Function Signature Reconstruction

### 7.1 Entry Points [CONFIRMED]

```cpp
// Client entry (WinMain style)
int bpeWin32_GameCoreMain(HINSTANCE hInstance, HINSTANCE hPrevInstance, char* lpCmdLine, int nShowCmd);

// Server entry (argc/argv style)
int bpeWin32Server_GameCoreMain(HINSTANCE hInstance, int argc, char const** argv);
```

### 7.2 Network Scene Functions [CONFIRMED]

```cpp
// Client connects to server
void CClientNetworkScene::Connect(
    const CBaseSocket::SSockaddr& addr,
    unsigned int flags,
    const NNetTypes::CConnectionTicket& ticket
);

// Server creates/gets listen connection
CNetConnection* CServerNetworkScene::CreateOrGetExistingListenServerConnectionIfListening(
    const NNetTypes::CConnectionTicket& ticket
);

// Scene construction
CClientNetworkScene::CClientNetworkScene(CBaseGameManager& mgr);
CServerNetworkScene::CServerNetworkScene(CBaseGameManager& mgr);
CNetworkScene::CNetworkScene();
```

### 7.3 Web Service Functions (NeedleCommon) [CONFIRMED]

```cpp
namespace NNeedleWebServiceCommon {
    // URL construction
    bpe::shared_string GetPublicServicesUrlForPath(bpe::shared_string path);
    bpe::shared_string GetPrivateServicesUrlForPath(bpe::shared_string path);

    // Certificate/key getters
    bpe::shared_string GetPublicServicesCertificate();
    bpe::shared_string GetPrivateServicesCACertificate();
    bpe::shared_string GetPrivateServicesClientCertificate();
    bpe::shared_string GetPrivateServicesClientKey();

    // API versioning
    void AddWebServiceInterfaceVersionParam(CHttpRequestParameters* params);
}

namespace NNeedleInstanceWrangler {
    struct SServerInstance;
    rapidjson::GenericValue EncodeJson(const SServerInstance& inst, rapidjson::MemoryPoolAllocator& alloc);
    SServerInstance DecodeJson(NJsonExtras::SJsonDecodeState* state, const rapidjson::GenericValue& val, const SServerInstance& defaults);
    bool IsValidServerInstance(const SServerInstance& inst);
    bpe::shared_string ServerInstanceToString(const SServerInstance& inst);
}

namespace NNeedleMatchMaker {
    unsigned int GetRegionBit(const NNeedleEnums::ERegionCode& code);
    bool IsValidReservationId(const SMatchReservationId& id);
    bpe::shared_string ReservationIdAsString(const SMatchReservationId& id);
    SMatchReservationId ReservationIdFromString(const bpe::shared_string& str);
}

namespace NNeedleAmazonMetadata {
    struct SMetaData;
    void RequestMetadata(CHttpManager& mgr);  // fetches from http://169.254.169.254/2014-11-05/
    bool UpdateReturnComplete();
    SMetaData GetMetadata();
    bool HasMetadata();
    bool IsRequested();
    bool DebugIsFake();
    SRichError GetError();
}
```

### 7.4 HTTP Request Functions [CONFIRMED]

```cpp
// Request parameter construction
CHttpRequestParameters::CHttpRequestParameters(const bpe::shared_string& url, EHttpMethod method);
void CHttpRequestParameters::AddQuery(const bpe::shared_string& key, const bpe::shared_string& value);
void CHttpRequestParameters::AddGZIPAcceptEncodingHeader();
void CHttpRequestParameters::AddJSONContentTypeHeader();

// Request execution
CHttpRequest::CHttpRequest(const CHttpRequestParameters& params, void* context, curl_slist* headers);
bool CHttpRequestBase::IsSuccess() const;
bpe::shared_string CHttpRequestBase::BuildResponseBodyNULLTerminated() const;
void CHttpRequestBase::DebugPrint() const;
void CHttpRequestBase::DebugPrintNoParameters() const;
```

### 7.5 Delta Compression [CONFIRMED]

```cpp
namespace NDeltaCompression {
    class CSchema {
    public:
        CSchema();
        CSchema(const CSchema& other);
        CSchema(const unsigned char* data);
        CSchema& operator=(const CSchema& other);
        ~CSchema();
    };
}

template<int BlockSize=16>
class CNetDeltaBase {
public:
    CNetDeltaBase();
    CNetDeltaBase(const NDeltaCompression::CSchema& schema);
    CNetDeltaBase(const NDeltaCompression::CSchema& schema, unsigned char* buffer, unsigned int size);
    virtual ~CNetDeltaBase();
};

class CNetDeltaIncoming : public CNetDeltaBase<16> { /* same constructors */ };
class CNetDeltaOutgoing : public CNetDeltaBase<16> { /* same constructors */ };
```

### 7.6 Socket Layer [CONFIRMED]

```cpp
struct CBaseSocket::SInAddr {
    SInAddr();
    SInAddr(unsigned int addr);
    bool operator==(const SInAddr& other) const;
    bool operator!=(const SInAddr& other) const;
};

struct CBaseSocket::SSockaddr {
    SSockaddr();
    SSockaddr(const SSockaddr& other);
    SSockaddr(unsigned short family, unsigned short port, SInAddr addr);
    virtual bool operator==(const SSockaddr& other) const;
    virtual bool operator!=(const SSockaddr& other) const;
};
```

---

## 8. Configuration Variables [CONFIRMED]

### 8.1 NeedleCommon Config Vars (URL/API)
```
needle_privateServiceUrlOverride     — Override private service URL (default: https://deadstar.rel.armature.com/)
needle_publicServiceUrlOverride      — Override public service URL
needle_serviceApiVersion             — API version number
```

### 8.2 Network Error Codes (from GameCore strings)
```
NET_CHANNEL_ALLOCATION_FAILED
NET_ERROR_CONNECTIONAUTHORIZATIONFAILURE
NET_ERROR_CONNECTIONAUTOCLOSE
NET_ERROR_CONNECTIONCOMPRESSIONERROR
NET_ERROR_CONNECTIONDECOMPRESSIONERROR
NET_ERROR_CONNECTIONGAMESTATEOVERFLOW
NET_ERROR_CONNECTIONLOGGEDINELSEWHERE
NET_ERROR_CONNECTIONMALFORMEDPACKET
NET_ERROR_CONNECTIONSOCKETERROR
NET_ERROR_CONNECTIONTIMEOUT
NET_ERROR_FAILED_PLAYERID_READ
NET_ERROR_INVALID_MTU_DISCOVERY_PACKET
NET_ERROR_INVALID_PLAYER_ID
NET_ERROR_INVALID_TICKET_ACK_PACKET
NET_ERROR_MALFORMED_DISCONNNECT_PACKET
NET_ERROR_NETWORKSCENEDESERIALIZATIONFAILURE
NET_ERROR_NETWORKSCENESERIALIZATIONFAILURE
NET_ERROR_NETWORKSCENESHUTDOWN
NET_ERROR_TICKET_READ_FAILED
NET_ERROR_UNKNOWN_CONNECTION_STATE
NET_MTU_TOO_SMALL
TICKET_AUTH_NO_GAME_MGR
```

### 8.3 Key Game Config Vars (selection from 300+ needle_ vars)

**Server/Match:**
```
needle_MatchSize                     — Match player count
needle_MatchType                     — Match game mode
needle_MatchAutoStart                — Auto-start match
needle_MatchBalanceTime              — Team balance duration
needle_MatchCountdownTime            — Pre-match countdown
needle_MatchReadyTime                — Ready check time
needle_MatchStartCountdown           — Start countdown
needle_MatchMaxLevelDifference       — Level matchmaking range
needle_MatchMaxPlayersDifference     — Player count balance
needle_MatchMinPlayersPerTeamLarge   — Min players (large match)
needle_MatchMinPlayersPerTeamMedium  — Min players (medium match)
needle_MatchMinPlayersPerTeamSmall   — Min players (small match)
needle_useMatchmaker                 — Use matchmaker service
needle_MatchFinishedRestartTime      — Restart delay after match
needle_ResetServerOnNoConnections    — Reset on empty server
needle_MaxMatchJoinWaitTime          — Join timeout
```

**Network:**
```
needle_NetworkRatingUpdatePeriod     — Rating sync interval
needle_NetworkSyncSleepTime          — Sync sleep time
needle_requestUpdateBase             — Base request update rate
needle_requestUpdateIncreaseRate     — Rate increase factor
needle_requestUpdateMax              — Max update rate
needle_unhealthyServerKickTime       — Kick time for unhealthy server
needle_unhealthyServerKillTimeAfterKickTime — Kill time after kick
needle_publicip                      — Public IP address
needle_publishMatchStats             — Publish match statistics
```

**Galaxy/Region:**
```
needle_MakeGalaxy                    — Generate galaxy
needle_StartRegion                   — Starting region
needle_CurrentRegionCode             — Current region code
needle_RegionLoadingId               — Region loading ID
needle_RegionLookupUrl               — Region lookup URL
needle_ForceSector                   — Force specific sector
```

**Gameplay:**
```
needle_IsSinglePlayer                — Single player mode
needle_GodMode                       — God mode
needle_AiGodMode                     — AI god mode
needle_EnableObserverMode            — Observer mode
needle_EnableTeamShuffle             — Team shuffle
needle_IdleTimeoutTime               — AFK timeout
needle_PingTooHighThreshold          — Max ping
needle_PingTooHighDropTime           — Drop time for high ping
needle_MaxSquadSize                  — Max party size
```

### 8.4 API URL Format (from NeedleCommon strings) [CONFIRMED]
```
URL pattern: %s%sapi/public/%s/%s%s    (base + path + api + public/private + service + version + params)
URL pattern: %s%sapi/private/%s/%s%s
Base URL:    https://deadstar.rel.armature.com/
AWS Meta:    http://169.254.169.254/2014-11-05/
```

### 8.5 SServerInstance JSON Fields [CONFIRMED]
```
API           — API version number
ServerName    — Server display name
BuildVersion  — Build version string
MatchType     — Match type ID
MatchSize     — Match player count
Port          — Server port
ProcessId     — OS process ID
Verify        — Verification flag
Game          — Game identifier
```

Format string: `API:%d, name:%s, Build:%s, MatchType:%d, MatchSize:%d, Port:%d`

---

## 9. Embedded Certificates [CONFIRMED]

NeedleCommon_Steam_Release.dll contains **embedded SSL certificates** (Base64 PEM format) for:
1. **Public services certificate** — Server TLS cert for `deadstar.rel.armature.com`
2. **Private services CA certificate** — CA for mutual TLS
3. **Private services client certificate** — Client cert for server-to-backend auth
4. **Private services client key** — Private key for mutual TLS

The certificate subject includes:
- CN: `deadstar.rel.armature.com`
- O: Armature
- L: Austin
- ST: Texas
- C: US
- Valid from: 2015-09-04 to 2018-06-** (expired)

---

## 10. Third-Party Libraries [CONFIRMED]

| Library | Version/Date | Location | Purpose |
|---------|-------------|----------|---------|
| Havok Physics | Build 2014-11-21 | GameCore | Physics, collision, dynamics |
| boost::regex | Unknown | Engine/GameCore | String pattern matching |
| boost::shared_ptr | Unknown | Throughout | Smart pointers |
| libcurl | Unknown | Engine | HTTP client |
| rapidjson | Unknown | NeedleCommon/GameComponents | JSON parsing |
| TinyXml/TinyXPath | Unknown | Engine | XML parsing |
| Wwise | Unknown | Engine | Audio |
| OPCODE | Unknown | Opcode_Steam_Release.dll | Collision detection |
| Telemetry | Unknown | GameCore | "Your application is compiled with Telemetry.h" |
| MSVC 2012 | v110 | All | C++ runtime |

---

## 11. Key Findings for Server Revival

### 11.1 Architecture Summary

The game uses a **two-tier networking model**:
1. **Game networking** (UDP via WS2_32) — CNetConnection/CNetConnectionManager in GameCore handles real-time game state sync via delta compression
2. **Service networking** (HTTP via curl) — CHttpManager in Engine handles REST API calls to the backend for auth, matchmaking, leaderboards, etc.

### 11.2 Critical Revival Targets

1. **NeedleCommon_Steam_Release.dll** — Contains hardcoded backend URL (`https://deadstar.rel.armature.com/`) and expired certificates. The `needle_publicServiceUrlOverride` and `needle_privateServiceUrlOverride` config vars allow redirecting to a custom server without patching.

2. **Web Service API** — The API uses paths like `api/public/{service}/{version}` and `api/private/{service}/{version}`. Services include: Account, AccountData, Leaderboards, Messages, Reporting, Reservation, TicketValidator, CapitalShipData.

3. **Server Instance Registration** — `NNeedleInstanceWrangler::SServerInstance` with JSON encode/decode contains: API version, ServerName, BuildVersion, MatchType, MatchSize, Port, ProcessId, Verify, Game.

4. **AWS Metadata** — Server instances check `http://169.254.169.254/2014-11-05/` for EC2 metadata (instance-id, instance-type, public-ipv4). The `DebugIsFake` function suggests a mock path exists.

5. **Connection Flow** — Client connects via `CClientNetworkScene::Connect(SSockaddr, flags, CConnectionTicket)`. Authentication uses `CNeedleTicketValidator` with Steam tickets.

6. **Delta Compression** — Game state sync uses `NDeltaCompression::CSchema` with 16-byte block delta encoding. Schemas define the sync format.

### 11.3 Recommended Approach

The **fastest path** to revival:
1. Set `needle_publicServiceUrlOverride` / `needle_privateServiceUrlOverride` to point to a custom backend
2. Implement the REST API endpoints the client expects (Account, Matchmaking, Reservation, etc.)
3. The `SServerInstance` JSON format tells us exactly what the matchmaker/reservation system needs
4. Handle Steam ticket validation or bypass it for LAN play
5. `CLanServiceAdvertiser`/`CLanServiceBrowser` suggest LAN play may already work with some config

---

*Report complete. 452 vtables mapped, 16,102+ exports cataloged, complete source tree reconstructed from 8 binaries.*
