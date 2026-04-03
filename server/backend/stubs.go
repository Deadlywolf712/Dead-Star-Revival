package main

import (
	"fmt"
	"net/http"
	"time"

	"github.com/labstack/echo/v4"
)

// handleGetMessages handles GET /api/public/:version/messages
// Returns login message and MOTD for the client splash screen.
func handleGetMessages(c echo.Context) error {
	return c.JSON(http.StatusOK, MessagesResponse{
		LoginMessage:    "Welcome to Dead Star Revival!",
		MessageOfTheDay: "Community-run servers. Join the Discord!",
		Date:            time.Now().Format("2006-01-02"),
	})
}

// handleGetLeaderboards handles GET /api/public/:version/leaderboards
func handleGetLeaderboards(c echo.Context) error {
	return c.JSON(http.StatusOK, []struct{}{})
}

// handleGetLocalLeaderboard handles GET /api/public/:version/leaderboards/local
func handleGetLocalLeaderboard(c echo.Context) error {
	return c.JSON(http.StatusOK, echo.Map{})
}

// handleReport handles POST /api/public/:version/report
func handleReport(c echo.Context) error {
	var body map[string]interface{}
	if err := c.Bind(&body); err != nil {
		return c.JSON(http.StatusBadRequest, ApiResponse{
			Success: false,
			Error:   "Invalid report payload",
		})
	}

	fmt.Printf("Report received: %v\n", body)

	return c.JSON(http.StatusOK, ApiResponse{Success: true})
}

// handleCapitalShipStatus handles GET /api/public/:version/capitalship/status
func handleCapitalShipStatus(c echo.Context) error {
	return c.JSON(http.StatusOK, echo.Map{
		"CapitalShipMatchState": 0,
	})
}

// handleStartRun handles POST /api/public/:version/capitalship/run
func handleStartRun(c echo.Context) error {
	return c.JSON(http.StatusOK, ApiResponse{Success: true})
}

// handleDeleteContract handles DELETE /api/public/:version/contract
func handleDeleteContract(c echo.Context) error {
	return c.JSON(http.StatusOK, ApiResponse{Success: true})
}

// handleAugmentShip handles POST /api/public/:version/augment
func handleAugmentShip(c echo.Context) error {
	return c.JSON(http.StatusOK, ApiResponse{Success: true})
}

// handleReconstructAugment handles POST /api/public/:version/reconstruct
func handleReconstructAugment(c echo.Context) error {
	return c.JSON(http.StatusOK, ApiResponse{Success: true})
}

// handleGetRewards handles GET /api/public/:version/rewards
func handleGetRewards(c echo.Context) error {
	return c.JSON(http.StatusOK, echo.Map{
		"rewards": []struct{}{},
	})
}

// handleGetTrophies handles GET /api/public/:version/trophies
func handleGetTrophies(c echo.Context) error {
	return c.JSON(http.StatusOK, echo.Map{
		"trophies": []struct{}{},
	})
}

// handleGetDLC handles GET /api/public/:version/dlc
func handleGetDLC(c echo.Context) error {
	return c.JSON(http.StatusOK, echo.Map{
		"dlc": []struct{}{},
	})
}
