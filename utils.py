# utils.py
import json
import os
import pygame

SAVE_FILE = "save_data.json"


def clamp(v, lo, hi):
    return max(lo, min(hi, v))


def load_save():
    default_settings = {"fullscreen": False, "vol_master": 100, "vol_music": 100, "vol_sfx": 100}
    default_data = {"players": {}, "settings": default_settings}

    if os.path.exists(SAVE_FILE):
        try:
            with open(SAVE_FILE, 'r') as f:
                data = json.load(f)

                # Migração de saves antigos
                if "high_score" in data and "players" not in data:
                    data = {"players": {"Visitante": {"high_score": data["high_score"]}}}
                if "players" not in data:
                    data["players"] = {}

                if "settings" not in data:
                    data["settings"] = default_settings.copy()
                else:
                    # Garante que todas as novas chaves existam mesmo se o cara já tinha "settings"
                    for k, v in default_settings.items():
                        if k not in data["settings"]:
                            data["settings"][k] = v
                return data
        except:
            pass
    return default_data


def save_game(data):
    try:
        with open(SAVE_FILE, 'w') as f:
            json.dump(data, f)
    except:
        pass


def draw_text_shadow(surface, font, text, color, pos, shadow_color=(0, 0, 0), offset=2, anchor="center"):
    t_shadow = font.render(text, True, shadow_color)
    t_main = font.render(text, True, color)
    rect = t_main.get_rect()
    if anchor == "center":
        rect.center = pos
    elif anchor == "topleft":
        rect.topleft = pos

    surface.blit(t_shadow, (rect.x + offset, rect.y + offset))
    surface.blit(t_main, rect)