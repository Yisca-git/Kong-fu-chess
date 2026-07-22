"""Shared configuration for all client modules."""
SERVER_URI = "ws://localhost:8765"

# Server message keys
MSG_ERROR                  = "error"
MSG_ASSIGNED               = "assigned"
MSG_WAITING                = "waiting"
MSG_PIECES                 = "pieces"
MSG_ELO_UPDATE             = "elo_update"
MSG_MATCHMAKING_TIMEOUT    = "matchmaking_timeout"
MSG_OPPONENT_DISCONNECTED  = "opponent_disconnected"
MSG_OPPONENT_FORFEITED     = "opponent_forfeited"
MSG_RECONNECTED            = "reconnected"
MSG_GAMES                  = "games"
MSG_LEADERBOARD            = "leaderboard"
MSG_COUNTDOWN              = "countdown"

REQUEST_TIMEOUT = 5  # seconds for one-shot WS requests
