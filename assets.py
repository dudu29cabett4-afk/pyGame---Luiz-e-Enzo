# assets.py
import os
import pygame
from config import *

images = {}
fonts = {}


# ... (Mesmas funcoes de antes: criar_tile_grama, escalar_carro, etc)
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


def fazer_img_crocodilo(num_slots: int) -> pygame.Surface:
    w, h = num_slots * TAMANHO_TILE, TAMANHO_TILE
    surf = pygame.Surface((w, h), pygame.SRCALPHA)
    pygame.draw.rect(surf, (55, 130, 55), (0, h // 4, w, h // 2), border_radius=10)
    for i in range(6, w - 6, 10): pygame.draw.ellipse(surf, (40, 105, 40), (i, h // 4 + 2, 8, 6))
    pygame.draw.rect(surf, (160, 200, 120), (0, h // 2, w, h // 4 - 4), border_radius=6)
    pygame.draw.ellipse(surf, (45, 115, 45), (w - 22, h // 4 - 4, 22, h // 2 + 8))
    pygame.draw.circle(surf, (220, 200, 30), (w - 10, h // 4 + 2), 5)
    pygame.draw.circle(surf, (0, 0, 0), (w - 10, h // 4 + 2), 2)
    for i in range(w - 20, w - 2, 5): pygame.draw.polygon(surf, (240, 240, 230),
                                                          [(i, h // 4), (i + 2, h // 4 - 5), (i + 4, h // 4)])
    pygame.draw.polygon(surf, (55, 130, 55), [(0, h // 4 + 4), (0, h // 4 + h // 2 - 4), (10, h // 2)])
    return surf


def load_all_assets():
    base = os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else os.getcwd()

    # Fontes Menores para Menu
    fonts['botao'] = pygame.font.SysFont("arial", 20, bold=True)
    fonts['botao_grande'] = pygame.font.SysFont("arial", 24, bold=True)
    fonts['score'] = pygame.font.SysFont("arial", 22, bold=True)
    fonts['kbd'] = pygame.font.SysFont("arial", 12, bold=True)
    fonts['hud'] = pygame.font.SysFont("arial", 18, bold=True)
    fonts['titulo'] = pygame.font.SysFont("arial", 16)

    def load_img(path, scale=None):
        try:
            img = pygame.image.load(os.path.join(base, path)).convert_alpha()
            if scale: img = pygame.transform.scale(img, scale)
            return img
        except:
            surf = pygame.Surface(scale if scale else (TAMANHO_TILE, TAMANHO_TILE))
            surf.fill((255, 0, 255))
            return surf

    images['fundo'] = load_img("pasta_imagens/fundoGame.png", (LARGURA, ALTURA))
    images['fundo_fim'] = load_img("pasta_imagens/gameover.png", (LARGURA, ALTURA))
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

    t_raw = load_img("pasta_imagens/tronco.png")
    images['troncos'] = {k: pygame.transform.scale(t_raw, (k * TAMANHO_TILE, TAMANHO_TILE)) for k in
                         TRONCO_SLOTS_OPCOES}
    images['troncos_flip'] = {k: pygame.transform.flip(v, True, False) for k, v in images['troncos'].items()}

    images['crocodilos'] = {k: fazer_img_crocodilo(k) for k in TRONCO_SLOTS_OPCOES}
    images['crocodilos_flip'] = {k: pygame.transform.flip(v, True, False) for k, v in images['crocodilos'].items()}