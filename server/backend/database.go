package main

import (
	"database/sql"
	"encoding/json"
	"fmt"
	"sync"
	"time"

	"github.com/google/uuid"
	_ "modernc.org/sqlite"
)

type Database struct {
	db *sql.DB
	mu sync.RWMutex
}

func NewDatabase(path string) (*Database, error) {
	db, err := sql.Open("sqlite", path+"?_journal_mode=WAL&_busy_timeout=5000")
	if err != nil {
		return nil, fmt.Errorf("open database: %w", err)
	}

	db.SetMaxOpenConns(1)

	d := &Database{db: db}
	if err := d.migrate(); err != nil {
		db.Close()
		return nil, fmt.Errorf("migrate database: %w", err)
	}

	return d, nil
}

func (d *Database) migrate() error {
	schema := `
	CREATE TABLE IF NOT EXISTS accounts (
		id INTEGER PRIMARY KEY,
		steam_id TEXT UNIQUE NOT NULL,
		session_id TEXT,
		account_data JSON,
		created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
		updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
	);
	CREATE INDEX IF NOT EXISTS idx_accounts_session ON accounts(session_id);
	CREATE INDEX IF NOT EXISTS idx_accounts_steam ON accounts(steam_id);

	CREATE TABLE IF NOT EXISTS servers (
		id TEXT PRIMARY KEY,
		name TEXT,
		address TEXT,
		port INTEGER,
		match_type INTEGER,
		match_size INTEGER,
		build_version TEXT,
		last_heartbeat DATETIME,
		player_count INTEGER DEFAULT 0
	);

	CREATE TABLE IF NOT EXISTS reservations (
		id TEXT PRIMARY KEY,
		server_id TEXT,
		account_id INTEGER,
		team INTEGER,
		expires_at DATETIME
	);
	CREATE INDEX IF NOT EXISTS idx_reservations_account ON reservations(account_id);

	CREATE TABLE IF NOT EXISTS matchmaking_queue (
		id INTEGER PRIMARY KEY AUTOINCREMENT,
		account_id INTEGER UNIQUE,
		session_id TEXT,
		match_type INTEGER,
		match_size INTEGER,
		party TEXT,
		queued_at DATETIME DEFAULT CURRENT_TIMESTAMP
	);
	CREATE INDEX IF NOT EXISTS idx_queue_type_size ON matchmaking_queue(match_type, match_size);
	`
	_, err := d.db.Exec(schema)
	return err
}

func (d *Database) Close() error {
	return d.db.Close()
}

// defaultAccountData creates a new player with ALL ships unlocked,
// including DLC and hidden ships. We go up to type 20 to cover:
//   0-11: Base ships (Scout/Raider/Frigate x Combat/Mining/Production/Research)
//   12+:  DLC ships (Ordo Robots Pack, Kurg Ship Expansion, hidden ships)
// Extra types that don't exist in-game are harmlessly ignored.
func defaultAccountData(accountId uint64) *CCoreAccountData {
	loadouts := make([]Loadout, 20)
	for i := 0; i < 20; i++ {
		loadouts[i] = Loadout{
			ShipType: i,
		}
	}

	// Unlock a generous set of portraits (including hidden ones)
	portraits := make([]int, 30)
	for i := 0; i < 30; i++ {
		portraits[i] = i
	}

	return &CCoreAccountData{
		AccountId:          accountId,
		SessionId:          "",
		CurrentPortraitId:  0,
		PortraitIds:        portraits,
		IsDevAccount:       false,
		Fame:               0,
		FameTotal:          0,
		FameCategoryLimits: []int{},
		FameRatio:          0.0,
		IsDLC:              true, // Enable DLC content
		Loadouts:           loadouts,
	}
}

func (d *Database) GetOrCreateAccount(steamId string) (*CCoreAccountData, error) {
	d.mu.Lock()
	defer d.mu.Unlock()

	var dataJSON sql.NullString
	var id int64
	err := d.db.QueryRow("SELECT id, account_data FROM accounts WHERE steam_id = ?", steamId).Scan(&id, &dataJSON)

	if err == sql.ErrNoRows {
		res, err := d.db.Exec(
			"INSERT INTO accounts (steam_id, created_at, updated_at) VALUES (?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)",
			steamId,
		)
		if err != nil {
			return nil, fmt.Errorf("create account: %w", err)
		}
		id, _ = res.LastInsertId()

		acct := defaultAccountData(uint64(id))
		acctJSON, merr := json.Marshal(acct)
		if merr != nil {
			return nil, fmt.Errorf("marshal default account data: %w", merr)
		}
		_, err = d.db.Exec("UPDATE accounts SET account_data = ? WHERE id = ?", string(acctJSON), id)
		if err != nil {
			return nil, fmt.Errorf("save default account data: %w", err)
		}
		return acct, nil
	}
	if err != nil {
		return nil, fmt.Errorf("query account: %w", err)
	}

	acct := defaultAccountData(uint64(id))
	if dataJSON.Valid && dataJSON.String != "" {
		if err := json.Unmarshal([]byte(dataJSON.String), acct); err != nil {
			return nil, fmt.Errorf("unmarshal account data: %w", err)
		}
	}
	acct.AccountId = uint64(id)
	return acct, nil
}

// GetActiveSession returns the current session for an account, or "" if none.
func (d *Database) GetActiveSession(accountId uint64) string {
	d.mu.RLock()
	defer d.mu.RUnlock()

	var sessionId sql.NullString
	d.db.QueryRow("SELECT session_id FROM accounts WHERE id = ?", accountId).Scan(&sessionId)
	if sessionId.Valid {
		return sessionId.String
	}
	return ""
}

func (d *Database) UpdateSession(accountId uint64, sessionId string) error {
	d.mu.Lock()
	defer d.mu.Unlock()

	_, err := d.db.Exec(
		"UPDATE accounts SET session_id = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
		sessionId, accountId,
	)
	return err
}

func (d *Database) GetAccountBySession(sessionId string) (*CCoreAccountData, error) {
	d.mu.RLock()
	defer d.mu.RUnlock()

	var dataJSON sql.NullString
	var id int64
	err := d.db.QueryRow(
		"SELECT id, account_data FROM accounts WHERE session_id = ?",
		sessionId,
	).Scan(&id, &dataJSON)
	if err != nil {
		return nil, fmt.Errorf("query account by session: %w", err)
	}

	acct := defaultAccountData(uint64(id))
	if dataJSON.Valid && dataJSON.String != "" {
		if err := json.Unmarshal([]byte(dataJSON.String), acct); err != nil {
			return nil, fmt.Errorf("unmarshal account data: %w", err)
		}
	}
	acct.AccountId = uint64(id)
	acct.SessionId = sessionId
	return acct, nil
}

func (d *Database) SaveAccountData(data *CCoreAccountData) error {
	d.mu.Lock()
	defer d.mu.Unlock()

	dataJSON, err := json.Marshal(data)
	if err != nil {
		return fmt.Errorf("marshal account data: %w", err)
	}

	_, err = d.db.Exec(
		"UPDATE accounts SET account_data = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
		string(dataJSON), data.AccountId,
	)
	return err
}

func (d *Database) RegisterServer(server *SServerInstance) error {
	d.mu.Lock()
	defer d.mu.Unlock()

	id := fmt.Sprintf("%s:%d", server.PublicIp, server.Port)
	_, err := d.db.Exec(`
		INSERT INTO servers (id, name, address, port, match_type, match_size, build_version, last_heartbeat, player_count)
		VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, 0)
		ON CONFLICT(id) DO UPDATE SET
			name = excluded.name,
			match_type = excluded.match_type,
			match_size = excluded.match_size,
			build_version = excluded.build_version,
			last_heartbeat = CURRENT_TIMESTAMP
	`, id, server.ServerName, server.PublicIp, server.Port, server.MatchType, server.MatchSize, server.BuildVersion)
	return err
}

func (d *Database) GetAvailableServer(matchType, matchSize int) (*SServerInstance, error) {
	d.mu.RLock()
	defer d.mu.RUnlock()

	var s SServerInstance
	var addr string
	err := d.db.QueryRow(`
		SELECT name, address, port, match_type, match_size, build_version
		FROM servers
		WHERE match_type = ? AND match_size = ?
		  AND last_heartbeat > datetime('now', '-60 seconds')
		ORDER BY player_count ASC
		LIMIT 1
	`, matchType, matchSize).Scan(&s.ServerName, &addr, &s.Port, &s.MatchType, &s.MatchSize, &s.BuildVersion)
	if err != nil {
		return nil, err
	}
	s.PublicIp = addr
	return &s, nil
}

func (d *Database) RemoveStaleServers(timeout time.Duration) error {
	d.mu.Lock()
	defer d.mu.Unlock()

	_, err := d.db.Exec(
		"DELETE FROM servers WHERE last_heartbeat < datetime('now', ?)",
		fmt.Sprintf("-%d seconds", int(timeout.Seconds())),
	)
	return err
}

func (d *Database) CreateReservation(res *Reservation) error {
	d.mu.Lock()
	defer d.mu.Unlock()

	if res.ReservationId == "" {
		res.ReservationId = uuid.New().String()
	}

	_, err := d.db.Exec(
		"INSERT INTO reservations (id, server_id, account_id, team, expires_at) VALUES (?, '', ?, ?, datetime('now', '+5 minutes'))",
		res.ReservationId, res.AccountId, res.Team,
	)
	return err
}

func (d *Database) GetReservation(reservationId string) (*Reservation, error) {
	d.mu.RLock()
	defer d.mu.RUnlock()

	var res Reservation
	var expiresAt string
	err := d.db.QueryRow(
		"SELECT id, account_id, team, expires_at FROM reservations WHERE id = ? AND expires_at > CURRENT_TIMESTAMP",
		reservationId,
	).Scan(&res.ReservationId, &res.AccountId, &res.Team, &expiresAt)
	if err != nil {
		return nil, err
	}

	t, err := time.Parse("2006-01-02 15:04:05", expiresAt)
	if err == nil {
		res.ExpiresAt = t.Unix()
	}
	return &res, nil
}

// RemoveExpiredReservations cleans up reservations past their expiry time.
func (d *Database) RemoveExpiredReservations() error {
	d.mu.Lock()
	defer d.mu.Unlock()

	_, err := d.db.Exec("DELETE FROM reservations WHERE expires_at < CURRENT_TIMESTAMP")
	return err
}

// RemoveStaleQueueEntries removes players who have been in queue for too long
// without being matched (they probably disconnected).
func (d *Database) RemoveStaleQueueEntries(timeout time.Duration) error {
	d.mu.Lock()
	defer d.mu.Unlock()

	_, err := d.db.Exec(
		"DELETE FROM matchmaking_queue WHERE queued_at < datetime('now', ?)",
		fmt.Sprintf("-%d seconds", int(timeout.Seconds())),
	)
	return err
}

func (d *Database) AddToMatchQueue(accountId uint64, sessionId string, matchType, matchSize int, party string) error {
	d.mu.Lock()
	defer d.mu.Unlock()

	// Remove any existing entry for this account first
	d.db.Exec("DELETE FROM matchmaking_queue WHERE account_id = ?", accountId)

	_, err := d.db.Exec(
		"INSERT INTO matchmaking_queue (account_id, session_id, match_type, match_size, party, queued_at) VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)",
		accountId, sessionId, matchType, matchSize, party,
	)
	return err
}

func (d *Database) GetQueuedPlayers(matchType, matchSize int) ([]QueueEntry, error) {
	d.mu.RLock()
	defer d.mu.RUnlock()

	rows, err := d.db.Query(
		"SELECT account_id, session_id, match_type, match_size, party FROM matchmaking_queue WHERE match_type = ? AND match_size = ? ORDER BY queued_at ASC",
		matchType, matchSize,
	)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var entries []QueueEntry
	for rows.Next() {
		var e QueueEntry
		var party sql.NullString
		if err := rows.Scan(&e.AccountId, &e.SessionId, &e.MatchType, &e.MatchSize, &party); err != nil {
			return nil, err
		}
		if party.Valid {
			e.Party = party.String
		}
		entries = append(entries, e)
	}
	return entries, rows.Err()
}

func (d *Database) RemoveFromQueue(accountId uint64) error {
	d.mu.Lock()
	defer d.mu.Unlock()

	_, err := d.db.Exec("DELETE FROM matchmaking_queue WHERE account_id = ?", accountId)
	return err
}
