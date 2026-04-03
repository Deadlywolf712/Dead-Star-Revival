package main

import (
	"fmt"
	"log"
	"net/http"
	"os"
	"sync"
	"time"

	"github.com/google/uuid"
	"github.com/labstack/echo/v4"
)

// MatchResult stores the outcome for a matched player, looked up during progress polling.
type MatchResult struct {
	Address       string
	ReservationId string
	MatchedAt     time.Time
}

// queueMeta tracks per-player queue metadata not stored in the database.
type queueMeta struct {
	JoinedAt  time.Time
	MatchType int
	MatchSize int
}

var (
	// matchedPlayers maps accountId -> MatchResult for players who have been placed.
	matchedPlayers sync.Map

	// queueTracker maps accountId -> queueMeta so we know when each player joined.
	queueTracker sync.Map

	// queueMu serializes queue mutations to prevent double-matching race conditions.
	queueMu sync.Mutex
)

// playersNeeded returns how many players are required to start a match of the given size.
func playersNeeded(matchSize int) int {
	switch matchSize {
	case MatchSizeSmall:
		return 10 // 5v5
	case MatchSizeMedium:
		return 14 // 7v7
	case MatchSizeLarge:
		return 20 // 10v10
	default:
		return 10
	}
}

// matchSizeName returns a human-readable label for logging.
func matchSizeName(matchSize int) string {
	switch matchSize {
	case MatchSizeSmall:
		return "5v5"
	case MatchSizeMedium:
		return "7v7"
	case MatchSizeLarge:
		return "10v10"
	default:
		return "unknown"
	}
}

// matchTypeName returns a human-readable label for the match type.
func matchTypeName(matchType int) string {
	switch matchType {
	case MatchTypeConquest:
		return "Conquest"
	case MatchTypeRecon:
		return "Recon"
	case MatchTypeHunt:
		return "Hunt"
	case MatchTypeFreeplay:
		return "Freeplay"
	case MatchTypeNeedle:
		return "Needle"
	default:
		return fmt.Sprintf("Type%d", matchType)
	}
}

// defaultServerAddress returns the fallback server address from env or a hardcoded default.
func defaultServerAddress() string {
	if addr := os.Getenv("DEFAULT_SERVER"); addr != "" {
		return addr
	}
	return "localhost:27015"
}

// matchWaitTimeout is how long a player can sit in queue before we start with whoever we have.
var matchWaitTimeout = 60 * time.Second

// handleMatchmakeStart handles POST /api/public/:version/matchmake
// Adds the requesting player to the matchmaking queue.
func handleMatchmakeStart(c echo.Context) error {
	sessionId := getSessionFromRequest(c)
	if sessionId == "" {
		return c.JSON(http.StatusUnauthorized, MatchmakeResponse{
			Status: "error",
			Error:  "Missing or invalid session token",
		})
	}

	account, err := db.GetAccountBySession(sessionId)
	if err != nil {
		return c.JSON(http.StatusUnauthorized, MatchmakeResponse{
			Status: "error",
			Error:  "Invalid or expired session",
		})
	}

	var req MatchmakeRequest
	if err := c.Bind(&req); err != nil {
		return c.JSON(http.StatusBadRequest, MatchmakeResponse{
			Status: "error",
			Error:  "Invalid matchmake request",
		})
	}

	// If player was already matched from a previous search, clear it so they can requeue.
	matchedPlayers.Delete(account.AccountId)

	// Remove from queue first to prevent duplicate entries.
	queueMu.Lock()
	_ = db.RemoveFromQueue(account.AccountId)
	if err := db.AddToMatchQueue(account.AccountId, sessionId, req.Type, req.Size, req.Party); err != nil {
		queueMu.Unlock()
		log.Printf("Failed to add player %d to queue: %v", account.AccountId, err)
		return c.JSON(http.StatusInternalServerError, MatchmakeResponse{
			Status: "error",
			Error:  "Failed to join matchmaking queue",
		})
	}
	queueTracker.Store(account.AccountId, queueMeta{
		JoinedAt:  time.Now(),
		MatchType: req.Type,
		MatchSize: req.Size,
	})
	queueMu.Unlock()

	log.Printf("Player %d queued for %s %s", account.AccountId, matchTypeName(req.Type), matchSizeName(req.Size))

	return c.JSON(http.StatusOK, MatchmakeResponse{
		Status: "searching",
	})
}

// handleMatchmakeProgress handles GET /api/public/:version/matchmake
// Player polls this to check if a match has been found.
func handleMatchmakeProgress(c echo.Context) error {
	sessionId := getSessionFromRequest(c)
	if sessionId == "" {
		return c.JSON(http.StatusUnauthorized, MatchmakeResponse{
			Status: "error",
			Error:  "Missing or invalid session token",
		})
	}

	account, err := db.GetAccountBySession(sessionId)
	if err != nil {
		return c.JSON(http.StatusUnauthorized, MatchmakeResponse{
			Status: "error",
			Error:  "Invalid or expired session",
		})
	}

	// Check if this player has been matched.
	if val, ok := matchedPlayers.Load(account.AccountId); ok {
		result := val.(MatchResult)
		// Clean up: remove from matched map after retrieval so it doesn't linger forever.
		// The client will get the address once and connect; subsequent polls after connection
		// aren't expected, but if they happen we'll just return "searching" again.
		matchedPlayers.Delete(account.AccountId)
		queueTracker.Delete(account.AccountId)
		return c.JSON(http.StatusOK, MatchmakeResponse{
			Status:  "found",
			Address: result.Address,
		})
	}

	// Still in queue — check if the player actually is queued (they might have timed out or
	// been removed due to an error).
	if _, ok := queueTracker.Load(account.AccountId); !ok {
		return c.JSON(http.StatusOK, MatchmakeResponse{
			Status: "error",
			Error:  "Not in matchmaking queue",
		})
	}

	return c.JSON(http.StatusOK, MatchmakeResponse{
		Status: "searching",
	})
}

// handleMatchmakeCancel handles DELETE /api/public/:version/matchmake
// Lets a player leave the queue voluntarily.
func handleMatchmakeCancel(c echo.Context) error {
	sessionId := getSessionFromRequest(c)
	if sessionId == "" {
		return c.JSON(http.StatusUnauthorized, MatchmakeResponse{
			Status: "error",
			Error:  "Missing or invalid session token",
		})
	}

	account, err := db.GetAccountBySession(sessionId)
	if err != nil {
		return c.JSON(http.StatusUnauthorized, MatchmakeResponse{
			Status: "error",
			Error:  "Invalid or expired session",
		})
	}

	queueMu.Lock()
	_ = db.RemoveFromQueue(account.AccountId)
	queueTracker.Delete(account.AccountId)
	queueMu.Unlock()

	matchedPlayers.Delete(account.AccountId)

	log.Printf("Player %d left matchmaking queue", account.AccountId)

	return c.JSON(http.StatusOK, MatchmakeResponse{
		Status: "cancelled",
	})
}

// startMatchmaker launches the background matchmaking goroutine.
// Call this once at server startup.
func startMatchmaker() {
	go func() {
		ticker := time.NewTicker(5 * time.Second)
		defer ticker.Stop()

		for range ticker.C {
			runMatchmakingCycle()
		}
	}()
	log.Println("Matchmaker started (polling every 5s)")
}

// runMatchmakingCycle checks every (matchType, matchSize) combination and creates matches.
func runMatchmakingCycle() {
	matchTypes := []int{
		MatchTypeConquest, MatchTypeRecon, MatchTypeHunt,
		MatchTypeFreeplay, MatchTypeNeedle,
	}
	matchSizes := []int{MatchSizeSmall, MatchSizeMedium, MatchSizeLarge}

	for _, mt := range matchTypes {
		for _, ms := range matchSizes {
			tryCreateMatch(mt, ms)
		}
	}

	// Expire stale match results that were never picked up (player disconnected).
	matchedPlayers.Range(func(key, value any) bool {
		result := value.(MatchResult)
		if time.Since(result.MatchedAt) > 2*time.Minute {
			matchedPlayers.Delete(key)
			log.Printf("Expired unclaimed match result for account %v", key)
		}
		return true
	})
}

// tryCreateMatch attempts to form a match for the given type+size.
func tryCreateMatch(matchType, matchSize int) {
	queueMu.Lock()
	defer queueMu.Unlock()

	players, err := db.GetQueuedPlayers(matchType, matchSize)
	if err != nil || len(players) == 0 {
		return
	}

	needed := playersNeeded(matchSize)

	// Check if we have enough players.
	haveEnough := len(players) >= needed

	// If not enough, check if anyone has been waiting past the timeout threshold.
	// For a small revival community, we start with whoever we have rather than
	// making people wait forever — the game server fills remaining slots with bots.
	forceStart := false
	if !haveEnough && len(players) >= 2 {
		for _, p := range players {
			if meta, ok := queueTracker.Load(p.AccountId); ok {
				m := meta.(queueMeta)
				if time.Since(m.JoinedAt) > matchWaitTimeout {
					forceStart = true
					break
				}
			}
		}
	}

	if !haveEnough && !forceStart {
		return
	}

	// Cap to the number needed (take first N if we have more than enough).
	matchPlayers := players
	if len(matchPlayers) > needed {
		matchPlayers = matchPlayers[:needed]
	}

	// Find an available game server for this mode.
	server, err := db.GetAvailableServer(matchType, matchSize)
	var address string
	if err != nil || server == nil {
		// No dedicated server registered — fall back to default address.
		address = defaultServerAddress()
		log.Printf("No registered server for %s %s, using default: %s",
			matchTypeName(matchType), matchSizeName(matchSize), address)
	} else {
		address = fmt.Sprintf("%s:%d", server.PublicIp, server.Port)
	}

	// Split players into two teams as evenly as possible.
	half := len(matchPlayers) / 2

	for i, p := range matchPlayers {
		team := 0
		if i >= half {
			team = 1
		}

		reservationId := uuid.New().String()

		res := &Reservation{
			ReservationId: reservationId,
			AccountId:     p.AccountId,
			Team:          team,
			ExpiresAt:     time.Now().Add(5 * time.Minute).Unix(),
		}

		if err := db.CreateReservation(res); err != nil {
			log.Printf("Failed to create reservation for account %d: %v", p.AccountId, err)
			continue
		}

		// Store match result so the player's next progress poll returns "found".
		matchedPlayers.Store(p.AccountId, MatchResult{
			Address:       address,
			ReservationId: reservationId,
			MatchedAt:     time.Now(),
		})

		// Remove from queue and tracker.
		_ = db.RemoveFromQueue(p.AccountId)
		queueTracker.Delete(p.AccountId)
	}

	label := matchSizeName(matchSize)
	if forceStart {
		log.Printf("Match created (force-start): %s %s %d/%d players on %s",
			matchTypeName(matchType), label, len(matchPlayers), needed, address)
	} else {
		log.Printf("Match created: %s %s %d players on %s",
			matchTypeName(matchType), label, len(matchPlayers), address)
	}
}
