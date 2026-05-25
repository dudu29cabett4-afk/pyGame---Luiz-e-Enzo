import json
import os
import pygame

SAVE_FILE = "save_data.json"


def clamp(v, lo, hi):
    # Função auxiliar matemática.
    # Ela garante que um valor numérico 'v' não ultrapasse um limite mínimo 'lo' nem um máximo 'hi'.
    # Usado vastamente para travar posições de tela, mouse, câmera.
    return max(lo, min(hi, v))


def load_save():
    # Função responsável por gerenciar a Persistência de Dados via arquivo local (JSON).
    default_settings = {
        "fullscreen": False,
        "fundomenu": False,
        "vol_master": 100,
        "vol_music": 100,
        "vol_sfx": 100,
    }
    default_data = {"players": {}, "settings": default_settings}

    if os.path.exists(SAVE_FILE):
        # Tenta ler o arquivo se ele já existir no sistema.
        try:
            with open(SAVE_FILE, 'r') as f:
                data = json.load(f)

                # Migração de saves antigos (Backwards Compatibility)
                # Garante que pessoas que baixaram a versão velha não percam seus saves na nova.
                if "high_score" in data and "players" not in data:
                    data = {"players": {"Visitante": {"high_score": data["high_score"]}}}
                if "players" not in data:
                    data["players"] = {}

                if "settings" not in data:
                    data["settings"] = default_settings.copy()
                else:
                    for k, v in default_settings.items():
                        if k not in data["settings"]:
                            data["settings"][k] = v
                for pdata in data["players"].values():
                    if "cor" not in pdata:
                        pdata["cor"] = "verde"
                return data
        except (json.JSONDecodeError, OSError, KeyError, TypeError):
            # Se der ruim (Ex: JSON corrompido ou modificado errado pelo usuário), passa adiante criando um save em branco
            pass
    return default_data


def save_game(data):
    # Serializa e salva o estado da memória atual gravando num arquivo de texto puro (JSON).
    try:
        with open(SAVE_FILE, 'w') as f:
            json.dump(data, f)
    except OSError:
        pass


def draw_text_shadow(surface, font, text, color, pos, shadow_color=(0, 0, 0), offset=2, anchor="center"):
    # Função puramente estética para desenhar as fontes do jogo.
    # Renderiza o texto primeiramente preto ("shadow") e depois, com um pequeno distanciamento (offset),
    # desenha o texto com a cor primária, o que produz um efeito 3D visual de sobreposição.
    t_shadow = font.render(text, True, shadow_color)
    t_main = font.render(text, True, color)
    rect = t_main.get_rect()
    if anchor == "center":
        rect.center = pos
    elif anchor == "topleft":
        rect.topleft = pos

    surface.blit(t_shadow, (rect.x + offset, rect.y + offset))
    surface.blit(t_main, rect)