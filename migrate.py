from utils.data import players, settings, get_player_db, save_player, add_item, get_player, unlock_achievement, add_memory, set_setting

for person_key, player_data in players.items():
    parts = person_key.split('_')
    user_id = int(parts[0])
    guild_id = int(parts[1])
    get_player_db(user_id, guild_id)
    player_data = get_player(user_id, guild_id)
    save_player(user_id, guild_id, player_data)
    for item_id in player_data['inventory']:
        add_item(user_id, guild_id, item_id)
    for achievement, unlocked in player_data['achievements'].items():
        if unlocked:
            unlock_achievement(user_id, guild_id, achievement)
    for message in player_data['ai_memory']:
        add_memory(user_id, guild_id, message['role'], message['content'])
for guild_key, guild_settings in settings.items():
    guild_id = int(guild_key)
    for setting, enabled in guild_settings.items():
        set_setting(guild_id, setting, enabled)
