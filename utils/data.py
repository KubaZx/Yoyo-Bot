import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent

def get_person_key(user_id, guild_id):
    return f"{user_id}_{guild_id}"

def init_db():
    with open(BASE_DIR / 'schema.sql', 'r', encoding='utf-8') as file:
        schema = file.read()
    connection.executescript(schema)


def get_player_db(user_id, guild_id):
    row = connection.execute("SELECT * FROM players WHERE user_id = ? AND guild_id = ?",
                             (user_id, guild_id)
                             ).fetchone()
    if row is None:
        connection.execute(
            "INSERT INTO players (user_id, guild_id) VALUES(?, ?)",
            (user_id, guild_id)
        )
        connection.commit()
        row = connection.execute("SELECT * FROM players WHERE user_id = ? AND guild_id = ?",
                                 (user_id, guild_id)
                                 ).fetchone()
    return dict(row)

def save_player(user_id, guild_id, player_data):
    connection.execute("UPDATE players SET money = ?, xp = ?, level = ?, last_daily = ?, messages = ?, total_messages = ?, active_title = ?, boost_until = ?, protected_until = ?, boost_last_bought = ?, protection_last_bought = ? WHERE user_id = ? AND guild_id = ?",
                       (player_data['money'], player_data['xp'], player_data['level'], player_data['last_daily'], player_data['messages'], player_data['total_messages'], player_data['active_title'], player_data['boost_until'], player_data['protected_until'], player_data['boost_last_bought'], player_data['protection_last_bought'], user_id, guild_id))
    connection.commit()

def add_item(user_id, guild_id, item_id):
    connection.execute("INSERT INTO inventory (user_id, guild_id, item_id) VALUES(?, ?, ?)",
                       (user_id, guild_id, item_id))
    connection.commit()

def get_inventory(user_id, guild_id):
    rows = connection.execute("SELECT item_id FROM inventory WHERE user_id = ? AND guild_id = ?",
                              (user_id, guild_id)
                       ).fetchall()
    return [row['item_id'] for row in rows]

def unlock_achievement(user_id, guild_id, achievement):
    connection.execute("INSERT INTO achievements (user_id, guild_id, achievement) VALUES(?, ?, ?)",
                       (user_id, guild_id, achievement))
    connection.commit()

def get_achievements(user_id, guild_id):
    rows = connection.execute("SELECT achievement FROM achievements WHERE user_id = ? AND guild_id = ?",
                              (user_id, guild_id)
                              ).fetchall()
    return [row['achievement'] for row in rows]

def get_setting(guild_id, setting):
    row = connection.execute("SELECT enabled FROM guild_settings WHERE guild_id = ? AND setting = ?",
                             (guild_id, setting)
                             ).fetchone()
    if row is None:
        return DEFAULT_SETTINGS[setting]
    return bool(row['enabled'])

def set_setting(guild_id, setting, enabled):
    connection.execute("INSERT OR REPLACE INTO guild_settings (guild_id, setting, enabled) VALUES(?, ?, ?)",
                       (guild_id, setting, enabled))
    connection.commit()

def add_memory(user_id, guild_id, role, content):
    connection.execute("INSERT INTO ai_memory (user_id, guild_id, role, content) VALUES (?, ?, ?, ?)",
                       (user_id, guild_id, role, content))
    connection.commit()

def get_memory(user_id, guild_id, limit):
    rows = connection.execute("SELECT role, content FROM ai_memory WHERE user_id = ? AND guild_id = ? ORDER BY message_id DESC LIMIT ?",
                             (user_id, guild_id, limit)
                             ).fetchall()
    return [dict(row) for row in reversed(rows)]

def clear_memory(user_id, guild_id):
    connection.execute("DELETE FROM ai_memory WHERE user_id = ? AND guild_id = ?",
                       (user_id, guild_id))
    connection.commit()

def get_top_players(guild_id, limit):
    rows = connection.execute("SELECT user_id, level, xp, money FROM players WHERE guild_id = ? ORDER BY level DESC, xp DESC, money DESC LIMIT ?",
                              (guild_id, limit)
                              ).fetchall()
    return [dict(row) for row in rows]

def get_server_players(guild_id):
    rows = connection.execute("SELECT * FROM players WHERE guild_id = ?",
                              (guild_id,)
                              ).fetchall()
    return [dict(row) for row in rows]

connection = sqlite3.connect(BASE_DIR / 'yoyo.db')
connection.row_factory = sqlite3.Row
init_db()
DEFAULT_SETTINGS = {'ai_rate_limit': True}
SHOP_ITEMS = {
    'title_pro': {'name': 'Pro title', 'price': 1000, 'type': 'title', 'value': 'Pro', 'description': 'Gives you a premium title on the server'},
    'xp_boost': {'name': 'XP boost (1h)', 'price': 500, 'type': 'boost', 'value': 3600, 'cooldown': 86400, 'description': 'Doubles your XP gain for one hour'},
    'protection': {'name': 'Protection from steal (6h)', 'price': 300, 'type': 'protection', 'value': 21600, 'cooldown': 259200, 'description': 'Protects you from being robbed'},
    'role': {'name': 'Special role', 'price': 1000, 'type': 'role', 'value': 'Pro', 'description': 'Gives you a special role'}
}
