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
    xp INTEGER,
    level INTEGER,
    money INTEGER,
    last_daily REAL,
    messages INTEGER,
    total_messages INTEGER,
    active_title TEXT,
    boost_until REAL,
    protected_until REAL,
    boost_last_bought REAL,
    protection_last_bought REAL,
    PRIMARY KEY (user_id, guild_id)
);
