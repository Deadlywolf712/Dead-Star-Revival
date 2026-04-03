package main

// Player account data — returned by auth and accountdata endpoints
type CCoreAccountData struct {
	AccountId          uint64    `json:"AccountId"`
	SessionId          string    `json:"SessionId"`
	CurrentPortraitId  int       `json:"CurrentPortraitId"`
	PortraitIds        []int     `json:"PortraitIds"`
	IsDevAccount       bool      `json:"IsDevAccount"`
	Fame               int       `json:"Fame"`
	FameTotal          int       `json:"FameTotal"`
	FameActions        int       `json:"FameActions"`
	FamePlayers        int       `json:"FamePlayers"`
	FameGuardians      int       `json:"FameGuardians"`
	FameUpgrades       int       `json:"FameUpgrades"`
	FameMatch          int       `json:"FameMatch"`
	FameFromActions    int       `json:"FameFromActions"`
	FameFromPlayers    int       `json:"FameFromPlayers"`
	FameFromGuardians  int       `json:"FameFromGuardians"`
	FameFromUpgrades   int       `json:"FameFromUpgrades"`
	FameCategoryLimits []int     `json:"FameCategoryLimits"`
	FameCapitalActions int       `json:"FameCapitalActions"`
	FameRatio          float64   `json:"fameRatio"`
	IsDLC              bool      `json:"isDLC"`
	Loadouts           []Loadout `json:"loadouts"`
}

type Loadout struct {
	ShipType         int    `json:"ShipType"`
	SkinId           int    `json:"SkinId"`
	AugmentId        int    `json:"AugmentId"`
	AugmentRank      int    `json:"AugmentRank"`
	AugmentLevel     int    `json:"augmentLevel"`
	AugmentType      int    `json:"augmentType"`
	AugmentRace      string `json:"augmentRace"`
	AugmentRankCore  int    `json:"augmentRank_Core"`
	AugmentRankShip  int    `json:"augmentRank_Ship"`
	AugmentRankSlot1 int    `json:"augmentRank_Slot1"`
	AugmentRankSlot2 int    `json:"augmentRank_Slot2"`
	AugmentRankSlot3 int    `json:"augmentRank_Slot3"`
	AugmentRankSlot4 int    `json:"augmentRank_Slot4"`
}

// Server instance registration
type SServerInstance struct {
	ApiVersion   int    `json:"ApiVersion"`
	ServerName   string `json:"ServerName"`
	BuildVersion string `json:"BuildVersion"`
	MatchType    int    `json:"MatchType"`
	MatchSize    int    `json:"MatchSize"`
	Port         int    `json:"Port"`
	ProcessId    int    `json:"ProcessId"`
	PublicIp     string `json:"PublicIp"`
}

// Matchmaking request from client
type MatchmakeRequest struct {
	Mode             string `json:"Mode"`
	RequestType      int    `json:"RequestType"`
	Type             int    `json:"Type"`
	Size             int    `json:"Size"`
	Contract         uint64 `json:"Contract"`
	Party            string `json:"Party"`
	Count            int    `json:"Count"`
	Crossplay        int    `json:"Crossplay"`
	RegionBitDefault int    `json:"RegionBitDefault"`
	RegionBitsCustom int    `json:"RegionBitsCustom"`
}

// Matchmaking response
type MatchmakeResponse struct {
	Status  string `json:"status"`
	Address string `json:"address,omitempty"`
	Error   string `json:"error,omitempty"`
}

// Auth request
type AuthRequest struct {
	Ticket       string `json:"ticket"`
	Platform     int    `json:"platform"`
	BuildVersion string `json:"BuildVersion"`
}

// Auth response
type AuthResponse struct {
	SessionId   string           `json:"SessionId"`
	AccountData CCoreAccountData `json:"accountData"`
}

// Reservation
type Reservation struct {
	ReservationId string `json:"ReservationId"`
	AccountId     uint64 `json:"AccountId"`
	Team          int    `json:"team"`
	ExpiresAt     int64  `json:"expiresAt"`
}

// Ticket validation request (server -> backend)
type TicketAuthRequest struct {
	ReservationId string `json:"ReservationId"`
	AccountId     uint64 `json:"AccountId"`
	BuildVersion  string `json:"BuildVersion"`
}

// Server status heartbeat
type ServerStatusRequest = SServerInstance

// Generic success/error response
type ApiResponse struct {
	Success bool   `json:"success"`
	Error   string `json:"error,omitempty"`
}

// Messages/MOTD
type MessagesResponse struct {
	LoginMessage    string `json:"LoginMessage"`
	MessageOfTheDay string `json:"Motd"`
	Date            string `json:"date"`
}

// Queue entry for matchmaking
type QueueEntry struct {
	AccountId uint64 `json:"accountId"`
	SessionId string `json:"sessionId"`
	MatchType int    `json:"matchType"`
	MatchSize int    `json:"matchSize"`
	Party     string `json:"party"`
}

// Match types enum
const (
	MatchTypeConquest = iota
	MatchTypeRecon
	MatchTypeHunt
	MatchTypeFreeplay
	MatchTypeNeedle
	MatchTypeNeedleCrisis
	MatchTypeNeedleDiscovery
	MatchTypeNeedleEscape
	MatchTypeNeedleExploration
	MatchTypeTutorial
)

// Match sizes
const (
	MatchSizeSmall = iota
	MatchSizeMedium
	MatchSizeLarge
)

// Build version must match client
const BuildVersion = "REL-147994"
