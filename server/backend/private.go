package main

import (
	"fmt"
	"net/http"

	"github.com/labstack/echo/v4"
)

// handleReservations handles POST /api/private/:version/reservations
// Game servers send reservation requests when matchmaking assigns players to a server.
func handleReservations(c echo.Context) error {
	var reservations []Reservation
	if err := c.Bind(&reservations); err != nil {
		return c.JSON(http.StatusBadRequest, ApiResponse{
			Success: false,
			Error:   "Invalid reservation payload",
		})
	}

	for i := range reservations {
		if err := db.CreateReservation(&reservations[i]); err != nil {
			return c.JSON(http.StatusInternalServerError, ApiResponse{
				Success: false,
				Error:   fmt.Sprintf("Failed to create reservation %s: %v", reservations[i].ReservationId, err),
			})
		}
		fmt.Printf("Reservation created: %s for account %d on team %d\n",
			reservations[i].ReservationId, reservations[i].AccountId, reservations[i].Team)
	}

	return c.JSON(http.StatusOK, ApiResponse{Success: true})
}

// handleAuthenticateTicket handles POST /api/private/:version/authenticate-ticket
// Game server validates whether a connecting player is allowed in.
// This is the key bypass — we always return success if the build version matches.
func handleAuthenticateTicket(c echo.Context) error {
	var req TicketAuthRequest
	if err := c.Bind(&req); err != nil {
		return c.JSON(http.StatusBadRequest, ApiResponse{
			Success: false,
			Error:   "Invalid ticket auth payload",
		})
	}

	if req.BuildVersion != BuildVersion {
		return c.JSON(http.StatusOK, echo.Map{
			"success": false,
			"error":   "TICKET_AUTH_INCOMPATIBLE_VERSION",
		})
	}

	fmt.Printf("Ticket validated for account %d\n", req.AccountId)

	return c.JSON(http.StatusOK, echo.Map{
		"success":   true,
		"AccountId": req.AccountId,
	})
}

// handleServerStatus handles POST /api/private/:version/server/status
// Game server heartbeat — registers/updates itself as alive.
func handleServerStatus(c echo.Context) error {
	var server SServerInstance
	if err := c.Bind(&server); err != nil {
		return c.JSON(http.StatusBadRequest, ApiResponse{
			Success: false,
			Error:   "Invalid server status payload",
		})
	}

	if err := db.RegisterServer(&server); err != nil {
		return c.JSON(http.StatusInternalServerError, ApiResponse{
			Success: false,
			Error:   "Failed to register server",
		})
	}

	fmt.Printf("Server heartbeat: %s (%s:%d) MatchType=%d\n",
		server.ServerName, server.PublicIp, server.Port, server.MatchType)

	return c.JSON(http.StatusOK, ApiResponse{Success: true})
}

// handlePushRewards handles POST /api/private/:version/rewards
// Server pushes match rewards for players after a match ends.
func handlePushRewards(c echo.Context) error {
	var body map[string]interface{}
	if err := c.Bind(&body); err != nil {
		return c.JSON(http.StatusBadRequest, ApiResponse{
			Success: false,
			Error:   "Invalid rewards payload",
		})
	}

	fmt.Printf("Rewards pushed: %v\n", body)

	return c.JSON(http.StatusOK, ApiResponse{Success: true})
}

// handlePushCapitalShipStatus handles POST /api/private/:version/capitalship/status
// Capital ship match state update from the game server.
func handlePushCapitalShipStatus(c echo.Context) error {
	var body map[string]interface{}
	if err := c.Bind(&body); err != nil {
		return c.JSON(http.StatusBadRequest, ApiResponse{
			Success: false,
			Error:   "Invalid capital ship status payload",
		})
	}

	fmt.Printf("Capital ship status update: %v\n", body)

	return c.JSON(http.StatusOK, ApiResponse{Success: true})
}
