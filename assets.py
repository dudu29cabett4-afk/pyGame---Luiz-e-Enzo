# assets.py
import os
import pygame
from config import *

images = {}
sons = {}
fonts = {}


def escalar_carro(img):
    orig_w, orig_h = img.get_size()
    nova_largura = int(orig_w * (TAMANHO_TILE / orig_h))
    return pygame.transform.scale(img, (nova_largura, TAMANHO_TILE))


def _criar_pu_escudo():
    surf = pygame.Surface((36, 36), pygame.SRCALPHA)
    import math
    pontos = []
    for i in range(10):
        angulo = math.pi / 2 + i * math.pi / 5
        r = 16 if i % 2 == 0 else 9
        pontos.append((18 + r * math.cos(angulo), 18 - r * math.sin(angulo)))
    pygame.draw.polygon(surf, (255, 220, 30), pontos)
    pygame.draw.polygon(surf, (255, 160, 0), pontos, 2)
    pygame.draw.circle(surf, (255, 255, 180), (18, 18), 6)
    return surf


def _criar_pu_xp2():
    surf = pygame.Surface((36, 36), pygame.SRCALPHA)
    pygame.draw.circle(surf, (255, 190, 70), (18, 18), 15)
    pygame.draw.circle(surf, (70, 35, 10), (18, 18), 13)
    pygame.draw.circle(surf, (255, 235, 170), (18, 18), 13, 2)
    f = pygame.font.SysFont("arial", 18, bold=True)
    txt = f.render("x2", True, (255, 240, 220))
    surf.blit(txt, txt.get_rect(center=(18, 18)))
    return surf


def load_all_assets():
    base = os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else os.getcwd()

    fonts['botao'] = pygame.font.SysFont("arial", 20, bold=True)
    fonts['botao_grande'] = pygame.font.SysFont("arial", 24, bold=True)
    fonts['score'] = pygame.font.SysFont("arial", 22, bold=True)
    fonts['kbd'] = pygame.font.SysFont("arial", 12, bold=True)
    fonts['hud'] = pygame.font.SysFont("arial", 18, bold=True)
    fonts['titulo'] = pygame.font.SysFont("arial", 16)

    def load_img(path, scale=None):
        try:
            img = pygame.image.load(os.path.join(base, path)).convert_alpha()
            if scale:
                img = pygame.transform.scale(img, scale)
            return img
        except Exception:
            surf = pygame.Surface(scale if scale else (TAMANHO_TILE, TAMANHO_TILE))
            surf.fill((255, 0, 255))
            return surf

    def load_sound(path, volume=0.5):
        try:
            s = pygame.mixer.Sound(os.path.join(base, path))
            s.set_volume(volume)
            return s
        except Exception:
            return None

    def load_folder_as_list(folder_path, scale=None):
        """Carrega todas as imagens PNG de uma pasta em uma lista."""
        full_path = os.path.join(base, folder_path)
        loaded = []
        if os.path.exists(full_path):
            for f in sorted(os.listdir(full_path)):
                if f.lower().endswith('.png'):
                    loaded.append(load_img(os.path.join(folder_path, f), scale))

        # Fallback se a pasta estiver vazia ou não existir
        if not loaded:
            surf = pygame.Surface(scale if scale else (TAMANHO_TILE, TAMANHO_TILE))
            surf.fill((255, 0, 255))
            loaded.append(surf)
        return loaded

    def load_prefix_sounds(folder_path, prefix):
        """Carrega todos os MP3 de uma pasta que começam com o prefixo em uma lista."""
        full_path = os.path.join(base, folder_path)
        loaded = []
        if os.path.exists(full_path):
            for f in sorted(os.listdir(full_path)):
                if f.startswith(prefix) and f.lower().endswith('.mp3'):
                    s = load_sound(os.path.join(folder_path, f))
                    if s: loaded.append(s)
        return loaded

    # =========================================================
    # CARREGAMENTO DOS BIOMAS (IMAGENS)
    # =========================================================
    images['biomas'] = {}
    for bioma in BIOMAS:
        images['biomas'][bioma] = {
            'solos': load_folder_as_list(f"imagens/biomas/{bioma}/solos", (TAMANHO_TILE, TAMANHO_TILE)),
            'aguas': load_folder_as_list(f"imagens/biomas/{bioma}/aguas", (TAMANHO_TILE, TAMANHO_TILE)),
            'obstaculos': load_folder_as_list(f"imagens/biomas/{bioma}/obstaculos", (TAMANHO_TILE, TAMANHO_TILE)),
        }

        # A transição é uma imagem principal de banda inteira
        trans_lista = load_folder_as_list(f"imagens/biomas/{bioma}/transicao")
        images['biomas'][bioma]['transicao'] = trans_lista[0] if trans_lista else None

    # =========================================================
    # CARREGAMENTO DE ENTIDADES GLOBAIS (IMAGENS)
    # =========================================================
    # Estradas (Tamanho LARGURA x TAMANHO_TILE)
    images['estradas'] = load_folder_as_list("imagens/estradas", (LARGURA, TAMANHO_TILE))

    # Lilypads
    images['lilypads'] = load_folder_as_list("imagens/lilypads", (TAMANHO_TILE, TAMANHO_TILE))

    # Carros
    carros_crus = load_folder_as_list("imagens/carros")
    images['carros_r'] = [escalar_carro(c) for c in carros_crus]
    images['carros_l'] = [pygame.transform.flip(c, True, False) for c in images['carros_r']]

    # Personagens
    images['personagens'] = {}
    for cor in ["azul", "verde", "vermelho"]:
        images['personagens'][cor] = {
            'frente': load_img(f"imagens/personagens/{cor}/frente.png", (TAMANHO_TILE, TAMANHO_TILE)),
            'costas': load_img(f"imagens/personagens/{cor}/costas.png", (TAMANHO_TILE, TAMANHO_TILE)),
            'esquerda': load_img(f"imagens/personagens/{cor}/esquerda.png", (TAMANHO_TILE, TAMANHO_TILE)),
            'direita': load_img(f"imagens/personagens/{cor}/direita.png", (TAMANHO_TILE, TAMANHO_TILE)),
        }

    # Elementos do Rio
    images['rios'] = {
        'jacare': load_img("imagens/rios/jacare.png", (86, 65)),
        'jacare_flip': pygame.transform.flip(load_img("imagens/rios/jacare.png", (86, 65)), True, False),
        'tronco': load_img("imagens/rios/tronco.png", (TAMANHO_TILE, TAMANHO_TILE))
    }

    # Telas de Morte e Fundo
    images['telas'] = {
        'fullscreen': load_img("imagens/telas/fullscreen.png", (LARGURA, ALTURA)),
        'morte_afogado': load_img("imagens/telas/mortes/morte_afogado.png", (LARGURA, ALTURA)),
        'morte_borda': load_img("imagens/telas/mortes/morte_borda.png", (LARGURA, ALTURA)),
        'morte_carro': load_img("imagens/telas/mortes/morte_carro.png", (LARGURA, ALTURA))
    }

    # Powerups programáticos (mantidos conforme o design original)
    images['pu_escudo'] = _criar_pu_escudo()
    images['pu_xp2'] = _criar_pu_xp2()

    # =========================================================
    # CARREGAMENTO DE ÁUDIO (SONS)
    # =========================================================
    sons['passos'] = {
        'agua': load_sound("sons/passos/passos_agua.mp3"),
        'rua': load_sound("sons/passos/passos_rua.mp3"),
        'terra': load_sound("sons/passos/passos_terra.mp3"),
        'tronco': load_sound("sons/passos/passos_tronco.mp3"),
        # Listas com múltiplas variações
        'deserto': load_prefix_sounds("sons/passos", "passos_deserto"),
        'floresta': load_prefix_sounds("sons/passos", "passos_floresta"),
    }

    sons['interface'] = {
        'click': load_sound("sons/interface/clickbutton.mp3"),
        'hover': load_sound("sons/interface/hoverbutton.mp3"),
        'recorde': load_sound("sons/interface/recorde_no_meio_da_partida.mp3"),
    }

    sons['ambiente'] = {
        'jogo': load_sound("sons/ambiente/jogo.mp3", 0.4),
        'menu': load_sound("sons/ambiente/menu.mp3", 0.4),
        'passaros_floresta': load_sound("sons/ambiente/passaros_floresta.mp3", 0.3),
        'vento_urbano': load_sound("sons/ambiente/vento_urbano.mp3", 0.3),
    }

    sons['powerups'] = {
        'bonus_2x': load_sound("sons/powerups/bonus_2x.mp3"),
        'escudo': load_sound("sons/powerups/bonus_escudo.mp3"),
    }

    sons['mortes'] = {
        'geral': load_sound("sons/mortes/morte.mp3"),
        'agua': load_sound("sons/mortes/morte_agua.mp3"),
        'borda': load_sound("sons/mortes/morte_borda.mp3"),
        'carro': load_sound("sons/mortes/morte_carro.mp3"),
    }