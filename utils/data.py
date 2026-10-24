import json
import os
import copy
import sqlite3

def load_data():
    if os.path.exists('players.json'):
        with open('players.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_data(data):
    with open('players.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_settings():
    if os.path.exists('settings.json'):
        with open('settings.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_settings(data):
    with open('settings.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def get_person_key(user_id, guild_id):
    return f"{user_id}_{guild_id}"

def get_guild_settings(guild_id):
    key = str(guild_id)
    if key not in settings:
        settings[key] = {}
    for name, value in DEFAULT_SETTINGS.items():
        if name not in settings[key]:
            settings[key][name] = value
    return settings[key]

def get_player(user_id, guild_id):
    person_key = get_person_key(user_id, guild_id)
    if person_key not in players:
        players[person_key] = {}
    for key, value in DEFAULT_PROFILE.items():
        if key not in players[person_key]:
            players[person_key][key] = copy.deepcopy(value)
    return players[person_key]

def init_db():
    with open('schema.sql', 'r', encoding='utf-8') as file:
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
    connection.execute("UPDATE players SET money = ?, xp = ? WHERE user_id = ? AND guild_id = ?",
                       (player_data['money'], player_data['xp'], user_id, guild_id))
    connection.commit()

connection = sqlite3.connect('yoyo.db')
connection.row_factory = sqlite3.Row
init_db()
players = load_data()
settings = load_settings()
DEFAULT_PROFILE = {'xp': 0, 'level': 1, 'money': 0, 'last_daily': 0, 'messages': 0, 'total_messages': 0, 'achievements': {'500_messages': False, 'level_5': False, '500_money': False}, 'ai_memory': [], 'inventory': [], 'active_title': None, 'boost_until': 0, 'protected_until': 0, 'boost_last_bought': 0, 'protection_last_bought': 0}
DEFAULT_SETTINGS = {'ai_rate_limit': True}
SHOP_ITEMS = {
    'title_pro': {'name': 'Pro title', 'price': 1000, 'type': 'title', 'value': 'Pro', 'description': 'Gives you a premium title on the server'},
    'xp_boost': {'name': 'XP boost (1h)', 'price': 500, 'type': 'boost', 'value': 3600, 'cooldown': 86400, 'description': 'Doubles your XP gain for one hour'},
    'protection': {'name': 'Protection from steal (6h)', 'price': 300, 'type': 'protection', 'value': 21600, 'cooldown': 259200, 'description': 'Protects you from being robbed'},
    'role': {'name': 'Special role', 'price': 1000, 'type': 'role', 'value': 'Pro', 'description': 'Gives you a special role'}
}
