package main

import (
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"net/http"
	"strings"

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
func handleAuthenticate(c echo.Context) error {
	version := c.Param("version")
	if version != BuildVersion {
		return c.JSON(http.StatusBadRequest, ApiResponse{
			Success: false,
			Error:   fmt.Sprintf("Version mismatch: expected %s, got %s", BuildVersion, version),
		})
	}

	// The client may send either a structured AuthRequest or a raw ticket string.
	// Read the body and try to parse as JSON first.
	var req AuthRequest
	body := c.Request().Body
	defer body.Close()

	decoder := json.NewDecoder(body)
	if err := decoder.Decode(&req); err != nil {
		// If JSON parsing fails, the body might be a raw ticket string.
		// Re-read isn't possible after stream consumption, so treat as error.
		return c.JSON(http.StatusBadRequest, ApiResponse{
			Success: false,
			Error:   "Invalid request body: expected JSON with Ticket field",
		})
	}

	ticket := req.Ticket
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

	// Generate a new session token
	sessionId := uuid.New().String()

	// Persist the session
	if err := db.UpdateSession(account.AccountId, sessionId); err != nil {
		return c.JSON(http.StatusInternalServerError, ApiResponse{
			Success: false,
			Error:   "Failed to create session",
		})
	}

	account.SessionId = sessionId

	fmt.Printf("Player authenticated: AccountId=%d, SteamId=%s\n", account.AccountId, steamId)

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
