import io
from PIL import Image, ImageDraw, ImageFont

def generate_card(player_data, display_name, avatar_bytes):
    image = Image.new('RGB', (520, 260), (30, 31, 34))
    font_bold = ImageFont.truetype('assets/arialbd.ttf', 28)
    font_regular = ImageFont.truetype('assets/arial.ttf', 16)
    draw = ImageDraw.Draw(image)
    avatar = Image.open(io.BytesIO(avatar_bytes)).convert('RGB').resize((72, 72))
    mask = Image.new('L', (72, 72), 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.ellipse([(0, 0), (72, 72)], fill=255)
    image.paste(avatar, (30, 30), mask)
    draw.text((120, 30), display_name, fill=(255, 255, 255), font=font_bold)
    if player_data['active_title'] is not None:
        draw.text((120, 67), f"{player_data['active_title']}", fill=(255, 200, 50), font=font_regular)
    draw.text((120, 85), f"Level {player_data['level']}", fill=(150, 150, 150), font=font_regular)
    draw.text((30, 120), "XP", fill=(150, 150, 150), font=font_regular)
    draw.text((400, 120), f"{player_data['xp']} / {player_data['level'] * 100}", fill=(150, 150, 150), font=font_regular)
    progress = player_data['xp'] / (player_data['level'] * 100)
    draw.rectangle([(30, 145), (490, 155)], fill=(50, 51, 55))
    draw.rectangle([(30, 145),(int(30 + progress * 460), 155)], fill=(88, 101, 242))
    draw.text((30, 190), "Money", fill=(150, 150, 150), font=font_regular)
    draw.text((30, 210), str(player_data['money']), fill=(255, 255, 255), font=font_bold)
    draw.text((200, 190), "Messages", fill=(150, 150, 150), font=font_regular)
    draw.text((200, 210), f"{player_data['total_messages']}", fill=(255, 255, 255), font=font_bold)
    draw.text((370, 190), "Achievements", fill=(150, 150, 150), font=font_regular)
    draw.text((370, 210), f"{sum(player_data['achievements'].values())} / 3", fill=(255, 255, 255), font=font_bold)
    buffer = io.BytesIO()
    image.save(buffer, format='PNG')
    buffer.seek(0)
    return buffer