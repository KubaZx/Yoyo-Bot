import json
import os

def load_data():
    if os.path.exists('players.json'):
        with open('players.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_data(data):
    with open('players.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def get_person_key(user_id, guild_id):
    return f"{user_id}_{guild_id}"

players = load_data()
DEFAULT_PROFILE = {'xp': 0, 'level': 1, 'money': 0, 'last_daily': 0, 'messages': 0, 'total_messages': 0, 'achievements': {'500_messages': False, 'level_5': False, '500_money': False}, 'ai_memory': []}
