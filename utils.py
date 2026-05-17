# utils.py
import json
import os
import pygame

SAVE_FILE = "save_data.json"

def clamp(v, lo, hi):
    return max(lo, min(hi, v))

def load_save():
    default_data = {"players": {}}
    if os.path.exists(SAVE_FILE):
        try:
            with open(SAVE_FILE, 'r') as f:
                data = json.load(f)
                # Migração de save antigo para o novo formato de multiplos players
                if "high_score" in data and "players" not in data:
                    return {"players": {"Visitante": {"high_score": data["high_score"]}}}
                if "players" not in data: return default_data
                return data
        except: pass
    return default_data

def save_game(data):
    try:
        with open(SAVE_FILE, 'w') as f:
            json.dump(data, f)
    except: pass

def draw_text_shadow(surface, font, text, color, pos, shadow_color=(0,0,0), offset=2):
    t_shadow = font.render(text, True, shadow_color)
    t_main = font.render(text, True, color)
    rect = t_main.get_rect(center=pos)
    surface.blit(t_shadow, (rect.x + offset, rect.y + offset))
    surface.blit(t_main, rect)