package main

import (
	"crypto/sha256"
	"encoding/hex"
	"fmt"
	"net/http"
	"strings"
	"sync"
	"time"

	"github.com/google/uuid"
	"github.com/labstack/echo/v4"
)

// getSessionFromRequest extracts the session token from the request.
// The game client sends auth as a query parameter: ?auth=Bearer {token}
// We also check the Authorization header as a fallback.
func getSessionFromRequest(c echo.Context) string {
	auth := c.QueryParam("auth")
	if strings.HasPrefix(auth, "Bearer ") {
		return strings.TrimPrefix(auth, "Bearer ")
	}
	// Fallback: check standard Authorization header
	auth = c.Request().Header.Get("Authorization")
	if strings.HasPrefix(auth, "Bearer ") {
		return strings.TrimPrefix(auth, "Bearer ")
	}
	return ""
}

// steamIdFromTicket generates a stable fake Steam ID by hashing the ticket.
// In a real implementation this would validate the ticket against Steam's
// authentication servers, but for the revival server we accept any ticket
// and derive a consistent identity from it.
func steamIdFromTicket(ticket string) string {
	h := sha256.Sum256([]byte(ticket))
	return hex.EncodeToString(h[:8]) // 16-char hex string as pseudo Steam ID
}

// handleAuthenticate handles POST /api/public/:version/authenticate
// This is the primary login endpoint. The game sends a Steam auth ticket
// and receives back a session token + full account data.
// authRateLimit tracks recent auth attempts per IP to prevent spam
var authRateLimit sync.Map // IP -> *rateLimitEntry

type rateLimitEntry struct {
	count    int
	resetAt  time.Time
}

func handleAuthenticate(c echo.Context) error {
	// Reject oversized bodies (prevent OOM from malicious payloads)
	if c.Request().ContentLength > 65536 {
		return c.JSON(http.StatusRequestEntityTooLarge, ApiResponse{
			Success: false,
			Error:   "Request body too large",
		})
	}

	// Rate limit: max 10 auth attempts per IP per minute
	clientIP := c.RealIP()
	now := time.Now()
	if entry, ok := authRateLimit.Load(clientIP); ok {
		rl := entry.(*rateLimitEntry)
		if now.Before(rl.resetAt) {
			rl.count++
			if rl.count > 10 {
				return c.JSON(http.StatusTooManyRequests, ApiResponse{
					Success: false,
					Error:   "Too many auth attempts. Wait 60 seconds.",
				})
			}
		} else {
			rl.count = 1
			rl.resetAt = now.Add(60 * time.Second)
		}
	} else {
		authRateLimit.Store(clientIP, &rateLimitEntry{count: 1, resetAt: now.Add(60 * time.Second)})
	}

	// NOTE: c.Param("version") is the API version from the URL (e.g. "v1"),
	// NOT the game build version. We accept any API version — the game knows
	// what version to send. Do NOT compare against BuildVersion here.

	// The client sends auth fields as JSON or query params.
	// Known fields: PlatformCode, PlatformAuth, ClientVersion, Region, EnvironmentId, Locale
	var req AuthRequest
	if err := c.Bind(&req); err != nil {
		// JSON parse failed — try reading from query params as fallback
		req.PlatformAuth = c.QueryParam("PlatformAuth")
		req.PlatformCode = c.QueryParam("PlatformCode")
		req.ClientVersion = c.QueryParam("ClientVersion")
	}

	// Accept PlatformAuth as the ticket (Steam auth ticket)
	ticket := req.PlatformAuth
	if ticket == "" {
		ticket = req.Ticket // fallback to old field name
	}
	if ticket == "" {
		return c.JSON(http.StatusBadRequest, ApiResponse{
			Success: false,
			Error:   "Missing authentication ticket",
		})
	}

	// Derive a stable Steam ID from the ticket
	steamId := steamIdFromTicket(ticket)

	// Get existing account or create a new one with all ships unlocked
	account, err := db.GetOrCreateAccount(steamId)
	if err != nil {
		return c.JSON(http.StatusInternalServerError, ApiResponse{
			Success: false,
			Error:   "Failed to retrieve account",
		})
	}

	// Check if there's an existing active session (another client using this account)
	oldSession := db.GetActiveSession(account.AccountId)

	// Generate a new session token — this invalidates any previous session
	sessionId := uuid.New().String()

	// Persist the session
	if err := db.UpdateSession(account.AccountId, sessionId); err != nil {
		return c.JSON(http.StatusInternalServerError, ApiResponse{
			Success: false,
			Error:   "Failed to create session",
		})
	}

	account.SessionId = sessionId

	if oldSession != "" {
		fmt.Printf("Player authenticated: AccountId=%d, SteamId=%s (previous session invalidated)\n", account.AccountId, steamId)
	} else {
		fmt.Printf("Player authenticated: AccountId=%d, SteamId=%s\n", account.AccountId, steamId)
	}

	return c.JSON(http.StatusOK, AuthResponse{
		SessionId:   sessionId,
		AccountData: *account,
	})
}

// handleGetAccountData handles GET /api/public/:version/accountdata
// Returns the full account data for the authenticated player.
// Session token is passed via ?auth=Bearer {token} query parameter.
func handleGetAccountData(c echo.Context) error {
	sessionId := getSessionFromRequest(c)
	if sessionId == "" {
		return c.JSON(http.StatusUnauthorized, ApiResponse{
			Success: false,
			Error:   "Missing or invalid session token",
		})
	}

	account, err := db.GetAccountBySession(sessionId)
	if err != nil {
		return c.JSON(http.StatusUnauthorized, ApiResponse{
			Success: false,
			Error:   "Invalid or expired session",
		})
	}

	return c.JSON(http.StatusOK, account)
}

// handlePushAccountData handles POST /api/private/:version/accountdata
// This is called by the game server (not the client) to push updated
// player data after a match completes — fame earned, stats updated, etc.
func handlePushAccountData(c echo.Context) error {
	var data CCoreAccountData
	if err := c.Bind(&data); err != nil {
		return c.JSON(http.StatusBadRequest, ApiResponse{
			Success: false,
			Error:   "Invalid account data payload",
		})
	}

	if data.AccountId == 0 {
		return c.JSON(http.StatusBadRequest, ApiResponse{
			Success: false,
			Error:   "Missing AccountId in payload",
		})
	}

	if err := db.SaveAccountData(&data); err != nil {
		return c.JSON(http.StatusInternalServerError, ApiResponse{
			Success: false,
			Error:   "Failed to save account data",
		})
	}

	fmt.Printf("Account data pushed: AccountId=%d\n", data.AccountId)

	return c.JSON(http.StatusOK, ApiResponse{
		Success: true,
	})
}
