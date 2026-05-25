# assets.py
# Este arquivo gerencia o carregamento de todos os recursos do jogo:
# imagens, sons e fontes. O carregamento é feito uma única vez e armazenado em dicionários
# (images, sons, fonts) na memória RAM do computador, garantindo ótima performance na execução do jogo.

import os
import pygame
from config import *

images = {}
sons = {}
fonts = {}


def escalar_carro(img):
    # Pega uma imagem retangular de proporções aleatórias e "força" que sua largura
    # se encaixe na métrica de tamanho "TILE" do jogo sem esticar ou achatar a arte.
    orig_w, orig_h = img.get_size()
    nova_largura = int(orig_w * (TAMANHO_TILE / orig_h))
    return pygame.transform.scale(img, (nova_largura, TAMANHO_TILE))


def _criar_pu_escudo():
    # Uma forma bem avançada de desenhar com Pygame puro: Usamos Polígonos para criar uma
    # estrela amarela na mão ao invés de usar arquivo .png
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
    # Determina dinamicamente em que pasta estamos para abrir arquivos sem "Directory error"
    base = os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else os.getcwd()

    # Criação de objetos de Fonte para textos.
    fonts['botao'] = pygame.font.SysFont("arial", 20, bold=True)
    fonts['botao_grande'] = pygame.font.SysFont("arial", 24, bold=True)
    fonts['score'] = pygame.font.SysFont("arial", 22, bold=True)
    fonts['kbd'] = pygame.font.SysFont("arial", 12, bold=True)
    fonts['hud'] = pygame.font.SysFont("arial", 18, bold=True)

    def load_img(path, scale=None, pixel_art=False):
        # Uma função envelope ("wrapper") para Pygame Load, que trata erros graciosamente com Try-Except.
        # Se você apagar a pasta da imagem sem querer, ela gera um quadrado roxo no lugar
        # e o seu jogo não vai "crashar".
        try:
            img = pygame.image.load(os.path.join(base, path))
            try:
                # convert_alpha otimiza em hardware o processamento de canais de cor
                img = img.convert_alpha()
            except pygame.error:
                img = img.convert()
            if scale:
                if pixel_art:
                    img = pygame.transform.scale(img, scale)
                else:
                    img = pygame.transform.scale(img, scale)
            return img
        except (pygame.error, OSError):
            surf = pygame.Surface(scale if scale else (TAMANHO_TILE, TAMANHO_TILE))
            surf.fill((255, 0, 255)) # Pinta de roxo como alerta visual
            return surf

    def load_sound(path, volume=0.5):
        try:
            s = pygame.mixer.Sound(os.path.join(base, path))
            s.set_volume(volume)
            return s
        except (pygame.error, OSError):
            return None

    def load_folder_as_list(folder_path, scale=None):
        # Abre a pasta e escaneia automaticamente todos as imagens de blocos daquele bioma.
        # Excelente para adicionar artes rapidamente depois!
        full_path = os.path.join(base, folder_path)
        loaded = []
        if os.path.exists(full_path):
            for f in sorted(os.listdir(full_path)):
                if f.lower().endswith('.png'):
                    loaded.append(load_img(os.path.join(folder_path, f), scale, pixel_art=True))
        if not loaded:
            surf = pygame.Surface(scale if scale else (TAMANHO_TILE, TAMANHO_TILE))
            surf.fill((255, 0, 255))
            loaded.append(surf)
        return loaded

    def load_prefix_sounds(folder_path, prefix):
        full_path = os.path.join(base, folder_path)
        loaded = []
        if os.path.exists(full_path):
            for f in sorted(os.listdir(full_path)):
                if f.startswith(prefix) and f.lower().endswith('.mp3'):
                    s = load_sound(os.path.join(folder_path, f))
                    if s:
                        loaded.append(s)
        return loaded

    # Inicialização dos dicionários principais
    images['biomas'] = {}
    for bioma in BIOMAS:
        images['biomas'][bioma] = {
            'solos': load_folder_as_list(f"imagens/biomas/{bioma}/solos", (TAMANHO_TILE, TAMANHO_TILE)),
            'aguas': load_folder_as_list(f"imagens/biomas/{bioma}/aguas", (TAMANHO_TILE, TAMANHO_TILE)),
            'obstaculos': load_folder_as_list(f"imagens/biomas/{bioma}/obstaculos", (TAMANHO_TILE, TAMANHO_TILE)),
        }
        trans_lista = load_folder_as_list(f"imagens/biomas/{bioma}/transicao", (LARGURA, TAMANHO_TILE))
        images['biomas'][bioma]['transicao'] = trans_lista[0] if trans_lista else None

    images['estradas'] = load_folder_as_list("imagens/estradas", (TAMANHO_TILE, TAMANHO_TILE))
    images['lilypads'] = load_folder_as_list("imagens/lilypads", (TAMANHO_TILE, TAMANHO_TILE))

    carros_crus = load_folder_as_list("imagens/carros")
    images['carros_r'] = [escalar_carro(c) for c in carros_crus]
    # Se temos o Sprite apontando pra direita, apenas invertemos com flip para apontar pra esquerda
    images['carros_l'] = [pygame.transform.flip(c, True, False) for c in images['carros_r']]

    images['personagens'] = {}
    for cor in CORES_RAPOSA:
        images['personagens'][cor] = {
            'frente': load_img(f"imagens/personagens/{cor}/frente.png", (TAMANHO_TILE, TAMANHO_TILE), pixel_art=True),
            'costas': load_img(f"imagens/personagens/{cor}/costas.png", (TAMANHO_TILE, TAMANHO_TILE), pixel_art=True),
            'esquerda': load_img(f"imagens/personagens/{cor}/esquerda.png", (TAMANHO_TILE, TAMANHO_TILE), pixel_art=True),
            'direita': load_img(f"imagens/personagens/{cor}/direita.png", (TAMANHO_TILE, TAMANHO_TILE), pixel_art=True),
        }

    jacare_img = load_img("imagens/rios/jacaré.png", None, pixel_art=True)
    jacare_h = TAMANHO_TILE
    jacare_w = max(TAMANHO_TILE, int(jacare_img.get_width() * (jacare_h / jacare_img.get_height())))
    jacare_scaled = pygame.transform.scale(jacare_img, (jacare_w, jacare_h))
    images['rios'] = {
        'jacare': jacare_scaled,
        'jacare_flip': pygame.transform.flip(jacare_scaled, True, False),
        'jacare_w': jacare_w,
        'tronco': load_img("imagens/rios/tronco.png", (TAMANHO_TILE, TAMANHO_TILE), pixel_art=True),
    }

    images['telas'] = {
        'fullscreen': load_img("imagens/telas/fullscreen.png", (LARGURA, ALTURA)),
        'fundomenu': load_img("imagens/telas/fundomenu.png", (LARGURA, ALTURA)),
        'morte_afogado': load_img("imagens/telas/mortes/morte_afogado.png", (LARGURA, ALTURA)),
        'morte_borda': load_img("imagens/telas/mortes/morte_borda.png", (LARGURA, ALTURA)),
        'morte_carro': load_img("imagens/telas/mortes/morte_carro.png", (LARGURA, ALTURA)),
        'morte_jacare': load_img("imagens/telas/mortes/morte_jacare.png", (LARGURA, ALTURA)),
    }

    images['pu_escudo'] = _criar_pu_escudo()
    images['pu_xp2'] = _criar_pu_xp2()

    sons['passos'] = {
        'agua': load_sound("sons/passos/passos_agua.mp3"),
        'rua': load_sound("sons/passos/passos_rua.mp3"),
        'terra': load_sound("sons/passos/passos_terra.mp3"),
        'tronco': load_sound("sons/passos/passos_tronco.mp3"),
        'deserto': load_prefix_sounds("sons/passos", "passos_deserto"),
        'floresta': load_prefix_sounds("sons/passos", "passos_floresta"),
    }

    sons['interface'] = {
        'click': load_sound("sons/interface/clickbutton.mp3"),
        'hover': load_sound("sons/interface/hoverbutton.mp3"),
        'recorde': load_sound("sons/interface/recorde_no_meio_da_partida.mp3"),
    }

    sons['ambiente'] = {
        'jogo_path': os.path.join(base, "sons/ambiente/jogo.mp3"),
        'menu_path': os.path.join(base, "sons/ambiente/menu.mp3"),
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
        'carro': load_sound("sons/mortes/morte_carro.mp3", 0.1),
        'jacare': load_sound("sons/mortes/morte_jacare.mp3"),
    }