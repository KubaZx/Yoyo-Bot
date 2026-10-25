from utils.data import players, settings, get_player_db, save_player, add_item, get_player

for person_key, player_data in players.items():
    parts = person_key.split('_')
    user_id = int(parts[0])
    guild_id = int(parts[1])
    get_player_db(user_id, guild_id)
    player_data = get_player(user_id, guild_id)
    save_player(user_id, guild_id, player_data)
    for item_id in player_data['inventory']:
        add_item(user_id, guild_id, item_id)
