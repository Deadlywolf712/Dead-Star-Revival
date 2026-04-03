package main

import (
	"context"
	"fmt"
	"net/http"
	"os"
	"os/signal"
	"syscall"
	"time"

	"github.com/labstack/echo/v4"
	"github.com/labstack/echo/v4/middleware"
)

var db *Database

func main() {
	port := os.Getenv("PORT")
	if port == "" {
		port = "8080"
	}

	dbPath := os.Getenv("DB_PATH")
	if dbPath == "" {
		dbPath = "deadstar.db"
	}

	var err error
	db, err = NewDatabase(dbPath)
	if err != nil {
		fmt.Fprintf(os.Stderr, "Failed to open database: %v\n", err)
		os.Exit(1)
	}
	defer db.Close()

	e := echo.New()
	e.HideBanner = true

	// Middleware
	e.Use(middleware.Logger())
	e.Use(middleware.Recover())
	e.Use(middleware.BodyLimit("1M")) // Prevent OOM from oversized requests
	e.Use(middleware.CORSWithConfig(middleware.CORSConfig{
		AllowOrigins: []string{"*"},
		AllowMethods: []string{http.MethodGet, http.MethodPost, http.MethodPut, http.MethodDelete, http.MethodOptions},
		AllowHeaders: []string{echo.HeaderOrigin, echo.HeaderContentType, echo.HeaderAccept, echo.HeaderAuthorization},
	}))

	// Public routes (client -> backend)
	pub := e.Group("/api/public/:version")
	pub.POST("/authenticate", handleAuthenticate)
	pub.GET("/accountdata", handleGetAccountData)
	pub.POST("/matchmake", handleMatchmakeStart)
	pub.GET("/matchmake", handleMatchmakeProgress)
	pub.DELETE("/matchmake", handleMatchmakeCancel)
	pub.GET("/messages", handleGetMessages)
	pub.GET("/leaderboards", handleGetLeaderboards)
	pub.GET("/leaderboards/local", handleGetLocalLeaderboard)
	pub.POST("/report", handleReport)
	pub.GET("/capitalship/status", handleCapitalShipStatus)
	pub.POST("/capitalship/run", handleStartRun)
	pub.DELETE("/contract", handleDeleteContract)
	pub.POST("/augment", handleAugmentShip)
	pub.POST("/reconstruct", handleReconstructAugment)
	pub.GET("/rewards", handleGetRewards)
	pub.GET("/trophies", handleGetTrophies)
	pub.GET("/dlc", handleGetDLC)

	// Private routes (game server -> backend)
	priv := e.Group("/api/private/:version")
	priv.POST("/reservations", handleReservations)
	priv.POST("/authenticate-ticket", handleAuthenticateTicket)
	priv.POST("/accountdata", handlePushAccountData)
	priv.POST("/rewards", handlePushRewards)
	priv.POST("/capitalship/status", handlePushCapitalShipStatus)
	priv.POST("/server/status", handleServerStatus)

	// Start background matchmaking loop
	startMatchmaker()

	// Background cleanup of stale data
	go func() {
		ticker := time.NewTicker(30 * time.Second)
		defer ticker.Stop()
		for range ticker.C {
			db.RemoveStaleServers(2 * time.Minute)
			db.RemoveExpiredReservations()
			db.RemoveStaleQueueEntries(10 * time.Minute)
		}
	}()

	// Startup banner
	fmt.Println("===========================================")
	fmt.Println("  DEAD STAR REVIVAL - Backend Server")
	fmt.Printf("  Port: %s\n", port)
	fmt.Printf("  Build: %s\n", BuildVersion)
	fmt.Printf("  Database: %s\n", dbPath)
	fmt.Println("===========================================")

	// Graceful shutdown
	go func() {
		if err := e.Start(":" + port); err != nil && err != http.ErrServerClosed {
			fmt.Fprintf(os.Stderr, "Server error: %v\n", err)
			os.Exit(1)
		}
	}()

	quit := make(chan os.Signal, 1)
	signal.Notify(quit, syscall.SIGINT, syscall.SIGTERM)
	<-quit

	fmt.Println("\nShutting down server...")
	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()
	if err := e.Shutdown(ctx); err != nil {
		fmt.Fprintf(os.Stderr, "Shutdown error: %v\n", err)
	}
}
