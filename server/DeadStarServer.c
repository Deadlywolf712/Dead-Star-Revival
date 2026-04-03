/*
 * DeadStarServer.c - Dedicated Server Launcher for Dead Star
 *
 * Loads GameCore_Steam_Release.dll and calls the server entry point:
 *   bpeWin32Server_GameCoreMain(HINSTANCE, int argc, const char** argv)
 *
 * Build (MinGW cross-compile from Linux):
 *   x86_64-w64-mingw32-gcc -o DeadStarServer.exe DeadStarServer.c -mconsole
 *
 * Build (MSVC):
 *   cl /Fe:DeadStarServer.exe DeadStarServer.c /link /SUBSYSTEM:CONSOLE user32.lib
 *
 * Usage:
 *   DeadStarServer.exe -i GameData/needle_server.sgpr [additional args]
 *
 * The launcher must be placed in (or run from) the Bin64 directory alongside
 * all game DLLs. Alternatively, set the working directory to Bin64.
 */

#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <stdio.h>
#include <stdlib.h>

/* Mangled name for the server entry point in GameCore_Steam_Release.dll */
#define SERVER_ENTRY_MANGLED "?bpeWin32Server_GameCoreMain@@YAHPEAUHINSTANCE__@@HPEAPEBD@Z"
#define GAMECORE_DLL         "GameCore_Steam_Release.dll"
#define STEAM_APPID          "366400"
#define STEAM_APPID_FILE     "steam_appid.txt"

/* Server entry point function signature */
typedef int (__cdecl *pfnServerMain)(HINSTANCE hInstance, int argc, const char** argv);

/*
 * Ensure steam_appid.txt exists in the working directory.
 * This bypasses SteamAPI_RestartAppIfNecessary() so the server
 * can launch without going through the Steam client's app launch.
 */
static void ensure_steam_appid(void)
{
    FILE* f;
    DWORD attr = GetFileAttributesA(STEAM_APPID_FILE);
    if (attr != INVALID_FILE_ATTRIBUTES)
        return;

    f = fopen(STEAM_APPID_FILE, "w");
    if (f) {
        fprintf(f, "%s\n", STEAM_APPID);
        fclose(f);
        printf("[DeadStarServer] Created %s with AppID %s\n", STEAM_APPID_FILE, STEAM_APPID);
    } else {
        fprintf(stderr, "[DeadStarServer] WARNING: Could not create %s\n", STEAM_APPID_FILE);
    }
}

int main(int argc, char* argv[])
{
    HINSTANCE hInstance;
    HMODULE hGameCore;
    pfnServerMain serverMain;
    int result;

    printf("=== Dead Star Revival - Dedicated Server Launcher ===\n");
    printf("Build: " __DATE__ " " __TIME__ "\n\n");

    /* Get our module handle (serves as HINSTANCE for the server) */
    hInstance = GetModuleHandle(NULL);

    /* Ensure steam_appid.txt exists */
    ensure_steam_appid();

    /* Load GameCore DLL */
    printf("[DeadStarServer] Loading %s...\n", GAMECORE_DLL);
    hGameCore = LoadLibraryA(GAMECORE_DLL);
    if (!hGameCore) {
        DWORD err = GetLastError();
        fprintf(stderr, "[DeadStarServer] FATAL: Failed to load %s (error %lu)\n", GAMECORE_DLL, err);
        fprintf(stderr, "[DeadStarServer] Make sure all game DLLs are in the working directory.\n");
        fprintf(stderr, "[DeadStarServer] Required: GameCore, Engine, GameComponentsNeedle,\n");
        fprintf(stderr, "[DeadStarServer]          NeedleCommon, Renderer, Opcode, steam_api64\n");
        return 1;
    }
    printf("[DeadStarServer] Loaded %s successfully.\n", GAMECORE_DLL);

    /* Resolve server entry point */
    printf("[DeadStarServer] Resolving server entry point...\n");
    serverMain = (pfnServerMain)GetProcAddress(hGameCore, SERVER_ENTRY_MANGLED);
    if (!serverMain) {
        DWORD err = GetLastError();
        fprintf(stderr, "[DeadStarServer] FATAL: Could not find server entry point (error %lu)\n", err);
        fprintf(stderr, "[DeadStarServer] Expected export: %s\n", SERVER_ENTRY_MANGLED);
        FreeLibrary(hGameCore);
        return 1;
    }
    printf("[DeadStarServer] Server entry point resolved at %p\n", (void*)serverMain);

    /* Log the arguments we're passing */
    printf("[DeadStarServer] Launching server with %d args:\n", argc);
    for (int i = 0; i < argc; i++) {
        printf("  argv[%d] = \"%s\"\n", i, argv[i]);
    }
    printf("\n");

    /* Call the server entry point */
    printf("[DeadStarServer] === Entering bpeWin32Server_GameCoreMain ===\n\n");
    result = serverMain(hInstance, argc, (const char**)argv);

    printf("\n[DeadStarServer] Server exited with code %d\n", result);

    FreeLibrary(hGameCore);
    return result;
}
