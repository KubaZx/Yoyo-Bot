CREATE TABLE IF NOT EXISTS guild_settings (
    guild_id INTEGER,
    setting TEXT,
    enabled INTEGER,
    PRIMARY KEY (guild_id, setting)
);

CREATE TABLE IF NOT EXISTS inventory (
    user_id INTEGER,
    guild_id INTEGER,
    item_id TEXT,
    PRIMARY KEY (user_id, guild_id, item_id)
);

CREATE TABLE IF NOT EXISTS achievements (
    user_id INTEGER,
    guild_id INTEGER,
    achievement TEXT,
    PRIMARY KEY (user_id, guild_id, achievement)
);

CREATE TABLE IF NOT EXISTS ai_memory (
    message_id INTEGER PRIMARY KEY,
    user_id INTEGER,
    guild_id INTEGER,
    role TEXT,
    content TEXT
);

CREATE TABLE IF NOT EXISTS players (
    user_id INTEGER,
    guild_id INTEGER,
    xp INTEGER DEFAULT 0,
    level INTEGER DEFAULT 1,
    money INTEGER DEFAULT 0,
    last_daily REAL DEFAULT 0,
    messages INTEGER DEFAULT 0,
    total_messages INTEGER DEFAULT 0,
    active_title TEXT,
    boost_until REAL DEFAULT 0,
    protected_until REAL DEFAULT 0,
    boost_last_bought REAL DEFAULT 0,
    protection_last_bought REAL DEFAULT 0,
    PRIMARY KEY (user_id, guild_id)
);
