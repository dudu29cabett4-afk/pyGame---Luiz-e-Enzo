# assets.py
import os
import pygame
from config import *

images = {}
fonts = {}


def criar_tile_grama(img, tamanho=TAMANHO_TILE):
    w, h = img.get_size()
    lado = min(w, h)
    quadrado = img.subsurface(pygame.Rect((w - lado) // 2, (h - lado) // 2, lado, lado)).copy()
    return pygame.transform.scale(quadrado, (tamanho, tamanho))


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


def _px(surf, gx, gy, color, ox=0, oy=0, scale=3):
    surf.fill(color, (ox + gx * scale, oy + gy * scale, scale, scale))


def fazer_img_crocodilo(num_slots: int) -> pygame.Surface:
    """Jacaré em pixel art estilo Stardew Valley (corpo alongado em tronco)."""
    w, h = num_slots * TAMANHO_TILE, TAMANHO_TILE
    surf = pygame.Surface((w, h), pygame.SRCALPHA)
    S = 3

    # Paleta
    DARK = (38, 82, 48)
    MID = (58, 118, 68)
    LIGHT = (96, 158, 88)
    HI = (130, 190, 110)
    BELLY = (168, 198, 118)
    BELLY_HI = (210, 228, 160)
    OUTLINE = (24, 52, 34)
    EYE = (255, 228, 72)
    PUPIL = (18, 22, 18)
    TOOTH = (240, 236, 210)
    WATER = (52, 118, 148)

    # Ondas sutis na água
    for gx in range(w // S):
        if gx % 5 == 0:
            _px(surf, gx, 14, WATER, oy=0, scale=S)
            _px(surf, gx, 15, WATER, oy=0, scale=S)

    body_end = (w // S) - 4
    head_start = body_end - 5

    # Corpo principal (segmentos repetidos)
    for gx in range(2, body_end):
        row_hi = 9 if gx % 3 != 0 else 10
        for gy in range(row_hi, 13):
            col = MID
            if gy >= 11:
                col = BELLY
            elif gy == row_hi:
                col = LIGHT
            _px(surf, gx, gy, col, scale=S)

        # Escamas em losango
        if gx % 2 == 0:
            _px(surf, gx, row_hi - 1, HI, scale=S)
            _px(surf, gx, row_hi - 1, DARK, scale=S)
        _px(surf, gx, 8, DARK, scale=S)
        _px(surf, gx, 13, OUTLINE, scale=S)

    # Barriga com highlight
    for gx in range(4, body_end - 2):
        _px(surf, gx, 11, BELLY_HI if gx % 4 == 0 else BELLY, scale=S)

    # Cauda afilada
    tail_map = [
        (body_end, 10, MID), (body_end, 11, MID),
        (body_end + 1, 10, MID), (body_end + 1, 11, DARK),
        (body_end + 2, 10, DARK), (body_end + 2, 11, DARK),
        (body_end + 3, 10, OUTLINE),
    ]
    for gx, gy, col in tail_map:
        if gx * S < w:
            _px(surf, gx, gy, col, scale=S)

    # Cabeça (lado direito = frente do sprite)
    hx = head_start
    head_pixels = [
        (hx, 7, DARK), (hx + 1, 7, DARK), (hx + 2, 7, MID),
        (hx, 8, MID), (hx + 1, 8, LIGHT), (hx + 2, 8, LIGHT), (hx + 3, 8, LIGHT),
        (hx, 9, MID), (hx + 1, 9, MID), (hx + 2, 9, LIGHT), (hx + 3, 9, LIGHT), (hx + 4, 9, LIGHT),
        (hx, 10, MID), (hx + 1, 10, MID), (hx + 2, 10, MID), (hx + 3, 10, LIGHT), (hx + 4, 10, LIGHT),
        (hx + 1, 11, BELLY), (hx + 2, 11, BELLY), (hx + 3, 11, BELLY),
        (hx + 3, 7, DARK), (hx + 4, 7, DARK), (hx + 4, 8, MID),
        (hx + 5, 8, MID), (hx + 5, 9, MID), (hx + 5, 10, DARK),
        (hx + 6, 9, DARK), (hx + 6, 10, OUTLINE),
    ]
    for gx, gy, col in head_pixels:
        if gx * S < w:
            _px(surf, gx, gy, col, scale=S)

    # Olho
    if (hx + 4) * S < w:
        _px(surf, hx + 4, 8, EYE, scale=S)
        _px(surf, hx + 4, 8, PUPIL, scale=S)

    # Focinho e dentes
    snout = [(hx + 5, 9), (hx + 5, 10), (hx + 6, 9), (hx + 6, 10), (hx + 7, 10)]
    for gx, gy in snout:
        if gx * S < w:
            _px(surf, gx, gy, LIGHT if gy == 9 else MID, scale=S)
    for gx, gy in [(hx + 5, 11), (hx + 6, 11)]:
        if gx * S < w:
            _px(surf, gx, gy, TOOTH, scale=S)

    # Patas
    for gx, gy in [(3, 12), (7, 12), (body_end - 4, 12)]:
        _px(surf, gx, gy, DARK, scale=S)
        _px(surf, gx, 13, OUTLINE, scale=S)

    # Contorno superior do corpo
    for gx in range(2, body_end + 1):
        _px(surf, gx, 7, OUTLINE, scale=S)

    # Nariz na frente
    if (hx + 7) * S < w:
        _px(surf, hx + 7, 10, OUTLINE, scale=S)

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

    images['fundo'] = load_img("pasta_imagens/fundoGame.png", (LARGURA, ALTURA))
    images['fundo_fim'] = load_img("pasta_imagens/gameover.png", (LARGURA, ALTURA))
    images['gameover_afogado'] = load_img("pasta_imagens/afogado.png", (LARGURA, ALTURA))
    images['gameover_borda'] = load_img("pasta_imagens/borda.png", (LARGURA, ALTURA))
    images['estrada'] = load_img("pasta_imagens/EstradaTeste.png", (LARGURA, TAMANHO_TILE))

    images['p_cima'] = load_img("pasta_imagens/costas.png", (TAMANHO_TILE, TAMANHO_TILE))
    images['p_baixo'] = load_img("pasta_imagens/frente.png", (TAMANHO_TILE, TAMANHO_TILE))
    images['p_esq'] = load_img("pasta_imagens/esquerda.png", (TAMANHO_TILE, TAMANHO_TILE))
    images['p_dir'] = load_img("pasta_imagens/direita.png", (TAMANHO_TILE, TAMANHO_TILE))

    images['grama'] = criar_tile_grama(load_img("pasta_imagens/Grama.png"))

    cr_raw = [
        load_img("pasta_imagens/amarelo.png"), load_img("pasta_imagens/rosa.png"),
        load_img("pasta_imagens/vermelho.png"), load_img("pasta_imagens/azul.png"),
        load_img("pasta_imagens/brancop.png"), load_img("pasta_imagens/preto.png")
    ]
    images['carros_r'] = [escalar_carro(c) for c in cr_raw]
    images['carros_l'] = [pygame.transform.flip(c, True, False) for c in images['carros_r']]

    images['pu_escudo'] = _criar_pu_escudo()
    images['pu_xp2'] = _criar_pu_xp2()

    t_raw = load_img("pasta_imagens/tronco.png", (TAMANHO_TILE, TAMANHO_TILE))
    images['troncos'] = {}
    for k in TRONCO_SLOTS_OPCOES:
        surf_tronco = pygame.Surface((k * TAMANHO_TILE, TAMANHO_TILE), pygame.SRCALPHA)
        for i in range(k):
            surf_tronco.blit(t_raw, (i * TAMANHO_TILE, 0))
        images['troncos'][k] = surf_tronco

    images['troncos_flip'] = {k: pygame.transform.flip(v, True, False) for k, v in images['troncos'].items()}
    images['crocodilos'] = {k: fazer_img_crocodilo(k) for k in TRONCO_SLOTS_OPCOES}
    images['crocodilos_flip'] = {k: pygame.transform.flip(v, True, False) for k, v in images['crocodilos'].items()}
