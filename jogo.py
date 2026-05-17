import os
import random
import pygame

pygame.init()

ALTURA = 700
LARGURA = 500
window = pygame.display.set_mode((LARGURA, ALTURA))
WINDOW = window
CLOCK = pygame.time.Clock()
pygame.display.set_caption("Cruze a Quatá!")

base = os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else os.getcwd()

costas         = pygame.image.load(os.path.join(base, "pasta_imagens/costas.png"))
frente         = pygame.image.load(os.path.join(base, "pasta_imagens/frente.png"))
direita        = pygame.image.load(os.path.join(base, "pasta_imagens/direita.png"))
esquerda       = pygame.image.load(os.path.join(base, "pasta_imagens/esquerda.png"))
estrada        = pygame.image.load(os.path.join(base, "pasta_imagens/EstradaTeste.png"))
fundo_img      = pygame.image.load(os.path.join(base, "pasta_imagens/fundoGame.png"))
fundo_fim_img  = pygame.image.load(os.path.join(base, "pasta_imagens/gameover.png"))
carro_amarelo  = pygame.image.load(os.path.join(base, "pasta_imagens/amarelo.png"))
carro_vermelho = pygame.image.load(os.path.join(base, "pasta_imagens/vermelho.png"))
carro_rosa     = pygame.image.load(os.path.join(base, "pasta_imagens/rosa.png"))
carro_azul     = pygame.image.load(os.path.join(base, "pasta_imagens/azul.png"))
carro_preto    = pygame.image.load(os.path.join(base, "pasta_imagens/preto.png"))
carro_branco   = pygame.image.load(os.path.join(base, "pasta_imagens/brancop.png"))
tronco_img_raw = pygame.image.load(os.path.join(base, "pasta_imagens/tronco.png"))

TAMANHO_TILE = 48
PLAYER_ALVO_Y = ALTURA * 2 // 3 - 100
TRONCO_SLOTS_OPCOES = [2, 3]


def criar_tile_grama(img, tamanho=TAMANHO_TILE):
    w, h = img.get_size()
    lado = min(w, h)
    x = (w - lado) // 2
    y = (h - lado) // 2
    quadrado = img.subsurface(pygame.Rect(x, y, lado, lado)).copy()
    return pygame.transform.scale(quadrado, (tamanho, tamanho))


def escalar_carro(img):
    nova_altura = TAMANHO_TILE
    orig_w, orig_h = img.get_size()
    nova_largura = int(orig_w * (nova_altura / orig_h))
    return pygame.transform.scale(img, (nova_largura, nova_altura))

def clamp(v, lo, hi):
    return max(lo, min(hi, v))



def desenhar_grama(surface, y, tile_img, bioma="grama"):
    cores = {
        "grama": None,
        "areia": (210, 180, 100),
        "gelo": (200, 230, 255),
    }
    cor = cores.get(bioma)

    if cor:
        pygame.draw.rect(surface, cor, (0, y, LARGURA, TAMANHO_TILE))
        for x in range(0, LARGURA, TAMANHO_TILE):
            if bioma == "areia":
                pygame.draw.circle(surface, (190, 160, 80), (x + 12, y + 18), 3)
                pygame.draw.circle(surface, (190, 160, 80), (x + 36, y + 10), 2)
            elif bioma == "gelo":
                pygame.draw.rect(surface, (100, 130, 110), (0, y, LARGURA, TAMANHO_TILE))
                for x in range(0, LARGURA, TAMANHO_TILE):
                    pygame.draw.ellipse(surface, (210, 230, 220), (x + 3, y + 5, 18, 8))
                    pygame.draw.ellipse(surface, (225, 240, 235), (x + 26, y + 14, 14, 6))
                    pygame.draw.ellipse(surface, (200, 220, 215), (x + 10, y + 28, 20, 7))
                    pygame.draw.polygon(surface, (240, 250, 255), [
                        (x + 38, y + 4), (x + 41, y + 10), (x + 35, y + 10)
                    ])
                    pygame.draw.polygon(surface, (220, 240, 255), [
                        (x + 8, y + 20), (x + 11, y + 26), (x + 5, y + 26)
                    ])
    else:
        for x in range(0, LARGURA, TAMANHO_TILE):
            surface.blit(tile_img, (x, y))


img_cima      = pygame.transform.scale(costas,   (TAMANHO_TILE, TAMANHO_TILE))
img_baixo     = pygame.transform.scale(frente,   (TAMANHO_TILE, TAMANHO_TILE))
img_esquerda  = pygame.transform.scale(esquerda,  (TAMANHO_TILE, TAMANHO_TILE))
img_direita   = pygame.transform.scale(direita,   (TAMANHO_TILE, TAMANHO_TILE))
img_estrada   = pygame.transform.scale(estrada,    (LARGURA, TAMANHO_TILE))
img_fundo     = pygame.transform.scale(fundo_img,  (LARGURA, ALTURA))
img_fundo_fim = pygame.transform.scale(fundo_fim_img, (LARGURA, ALTURA))

grama_original = pygame.image.load(os.path.join(base, "pasta_imagens/Grama.png")).convert()
img_grama = criar_tile_grama(grama_original)

img_rio = pygame.Surface((LARGURA, TAMANHO_TILE))
img_rio.fill((80, 170, 230))
for i in range(0, LARGURA, 30):
    pygame.draw.ellipse(img_rio, (130, 200, 255), (i, TAMANHO_TILE // 2 - 4, 20, 8))

img_rio_gelo = pygame.Surface((LARGURA, TAMANHO_TILE))
img_rio_gelo.fill((210, 238, 255))
pygame.draw.rect(img_rio_gelo, (235, 248, 255), (0, TAMANHO_TILE // 2 - 5, LARGURA, 10))
for i in range(0, LARGURA, 40):
    pygame.draw.line(img_rio_gelo, (170, 210, 235), (i, 6), (i + 15, 22), 1)
    pygame.draw.line(img_rio_gelo, (170, 210, 235), (i + 20, 28), (i + 38, 14), 1)
    pygame.draw.line(img_rio_gelo, (190, 220, 245), (i + 8, 14), (i + 22, 32), 1)
for i in range(10, LARGURA, 55):
    pygame.draw.circle(img_rio_gelo, (255, 255, 255), (i, TAMANHO_TILE // 2), 3)
    pygame.draw.circle(img_rio_gelo, (245, 252, 255), (i, TAMANHO_TILE // 2), 6, 1)

carros_disp_r = [escalar_carro(c) for c in (
    carro_amarelo, carro_rosa, carro_vermelho, carro_azul, carro_branco, carro_preto
)]
carros_disp_l = [pygame.transform.flip(img, True, False) for img in carros_disp_r]


def fazer_img_tronco(num_slots: int) -> pygame.Surface:
    largura = num_slots * TAMANHO_TILE
    return pygame.transform.scale(tronco_img_raw, (largura, TAMANHO_TILE))


troncos_img = {
    2: fazer_img_tronco(2),
    3: fazer_img_tronco(3),
}
troncos_img_flip = {
    k: pygame.transform.flip(v, True, False) for k, v in troncos_img.items()
}


def fazer_img_crocodilo(num_slots: int) -> pygame.Surface:
    w = num_slots * TAMANHO_TILE
    h = TAMANHO_TILE
    surf = pygame.Surface((w, h), pygame.SRCALPHA)

    pygame.draw.rect(surf, (55, 130, 55), (0, h // 4, w, h // 2), border_radius=10)

    for i in range(6, w - 6, 10):
        pygame.draw.ellipse(surf, (40, 105, 40), (i, h // 4 + 2, 8, 6))

    pygame.draw.rect(surf, (160, 200, 120), (0, h // 2, w, h // 4 - 4), border_radius=6)
    pygame.draw.ellipse(surf, (45, 115, 45), (w - 22, h // 4 - 4, 22, h // 2 + 8))

    pygame.draw.circle(surf, (220, 200, 30), (w - 10, h // 4 + 2), 5)
    pygame.draw.circle(surf, (0, 0, 0), (w - 10, h // 4 + 2), 2)

    for i in range(w - 20, w - 2, 5):
        pygame.draw.polygon(
            surf,
            (240, 240, 230),
            [(i, h // 4), (i + 2, h // 4 - 5), (i + 4, h // 4)]
        )

    pygame.draw.polygon(surf, (55, 130, 55), [(0, h // 4 + 4), (0, h // 4 + h // 2 - 4), (10, h // 2)])
    return surf


crocodilos_img = {k: fazer_img_crocodilo(k) for k in TRONCO_SLOTS_OPCOES}
crocodilos_img_flip = {k: pygame.transform.flip(v, True, False) for k, v in crocodilos_img.items()}

LARGURA_CARRO = carros_disp_r[0].get_width()
ALTURA_CARRO = TAMANHO_TILE
SAFE_ZONE_LINHAS = 1

VEL_SCROLL_INICIAL = 0.25
VEL_SCROLL_MAX = 3.0
SCORE_PARA_MAX_VEL = 80

fonte = pygame.font.SysFont("arial", 28, bold=True)
fonte_botao = pygame.font.SysFont("arial", 28, bold=True)
fonte_score = pygame.font.SysFont("arial", 24, bold=True)
fonte_titulo = pygame.font.SysFont("arial", 19)
fonte_hud = pygame.font.SysFont("arial", 20, bold=True)
fonte_kbd = pygame.font.SysFont("arial", 14, bold=True)

BIOMAS = ["grama", "areia", "gelo"]

CICLO_BIOMA_DURACAO = 50
_bioma_cache = {}


def get_bioma_atual(score):
    if score < 50:
        return "grama"
    elif score < 100:
        return "areia"
    else:
        bucket = (score - 100) // CICLO_BIOMA_DURACAO
        if bucket not in _bioma_cache:
            anterior = _bioma_cache.get(bucket - 1, "gelo")
            opcoes = [b for b in BIOMAS if b != anterior]
            _bioma_cache[bucket] = random.choice(opcoes)
        return _bioma_cache[bucket]


def rio_congelado(score):
    return get_bioma_atual(score) == "gelo"


tile_map = {}
lane_data = {}
carros_ativos = []
troncos_ativos = []
arvores_ativas = []
vitorias_ativas = []
fumacas_ativas = []
linhas_arvore_processadas = set()
bioma_por_linha = {}

TIPO_GRAMA = "grama"
TIPO_ESTRADA = "estrada"
TIPO_RIO = "rio"
ARVORE_PREGEN_LINHAS = 10
ARVORE_APARECIMENTO_MS = 500
ARVORE_MARGEM_MANUTENCAO = (ARVORE_PREGEN_LINHAS + 4) * TAMANHO_TILE
ARVORE_CHANCE_BASE = 0.025
ARVORE_CHANCE_EXTRA_MAX = 0.015
ARVORE_CHANCE_EXTRA_SCORE = 20000.0
PREGEN_BIOMA = 5

POWERUP_XP2_DURACAO_MS = 8_000
MAX_POWERUPS_ATIVOS = 1


def criar_img_powerup_escudo():
    size = 36
    surf = pygame.Surface((size, size), pygame.SRCALPHA)

    import math
    cx, cy = size // 2, size // 2
    pontos = []
    for i in range(10):
        angulo = math.pi / 2 + i * math.pi / 5
        r = (size // 2 - 2) if i % 2 == 0 else (size // 4)
        pontos.append((cx + r * math.cos(angulo), cy - r * math.sin(angulo)))

    pygame.draw.polygon(surf, (255, 220, 30), pontos)
    pygame.draw.polygon(surf, (255, 160, 0), pontos, 2)
    pygame.draw.circle(surf, (255, 255, 180), (cx, cy), 6)
    return surf


def criar_img_powerup_xp2():
    size = 36
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    cx, cy = size // 2, size // 2

    pygame.draw.circle(surf, (255, 190, 70), (cx, cy), 15)
    pygame.draw.circle(surf, (70, 35, 10), (cx, cy), 13)
    pygame.draw.circle(surf, (255, 235, 170), (cx, cy), 13, 2)

    f = pygame.font.SysFont("arial", 18, bold=True)
    txt = f.render("x2", True, (255, 240, 220))
    surf.blit(txt, txt.get_rect(center=(cx, cy)))
    return surf


img_powerup_escudo = criar_img_powerup_escudo()
img_powerup_xp2 = criar_img_powerup_xp2()


def resetar_mundo():
    tile_map.clear()
    lane_data.clear()
    carros_ativos.clear()
    troncos_ativos.clear()
    arvores_ativas.clear()
    vitorias_ativas.clear()
    fumacas_ativas.clear()
    linhas_arvore_processadas.clear()
    bioma_por_linha.clear()
    _bioma_cache.clear()


def fixar_bioma_linha(linha: int, score: int) -> str:
    if linha not in bioma_por_linha:
        bioma_por_linha[linha] = get_bioma_atual(score)
    return bioma_por_linha[linha]


def gerar_tile(linha: int):
    if linha not in tile_map:
        linha_base = int(PLAYER_ALVO_Y // TAMANHO_TILE)
        safe_inicio = linha_base - SAFE_ZONE_LINHAS

        if linha >= safe_inicio:
            tile_map[linha] = (img_grama, TIPO_GRAMA)
        else:
            escolha = random.choices(
                [TIPO_GRAMA, TIPO_ESTRADA, TIPO_RIO],
                weights=[3, 4, 1]
            )[0]

            if escolha == TIPO_GRAMA:
                tile_map[linha] = (img_grama, TIPO_GRAMA)
            elif escolha == TIPO_ESTRADA:
                tile_map[linha] = (img_estrada, TIPO_ESTRADA)
            else:
                tile_map[linha] = (img_rio, TIPO_RIO)

    return tile_map[linha]


def calcular_multiplicador_velocidade(score: int) -> float:
    return 1.0 + min(score / 1200.0, 0.25)


def linha_tem_rio_vizinho(linha: int) -> bool:
    for d in (-1, 1):
        nl = linha + d
        if nl < 0:
            continue
        _, tipo_viz = gerar_tile(nl)
        if tipo_viz == TIPO_RIO:
            return True
    return False


def obter_lane_data(linha: int, score: int = 0) -> dict:
    if linha not in lane_data:
        direcao = 1 if linha % 2 == 0 else -1
        tipo = gerar_tile(linha)[1]
        mult = calcular_multiplicador_velocidade(score)

        if tipo == TIPO_RIO:
            tem_rio_vizinho = linha_tem_rio_vizinho(linha)

            if tem_rio_vizinho and random.random() < 0.35:
                modo_rio = "vitoria_regia"
                velocidade = 0.0
                spawn_gap = 0
                num_slots = 0
            else:
                modo_rio = "troncos"
                velocidade = random.uniform(2.0, 4.5) * mult
                spawn_gap = random.randint(int(LARGURA * 0.35), int(LARGURA * 0.6))
                num_slots = random.choice(TRONCO_SLOTS_OPCOES)
        else:
            modo_rio = None
            velocidade = random.uniform(4.5, 9.0) * mult
            spawn_gap = random.randint(int(LARGURA * 0.35), int(LARGURA * 0.65))
            num_slots = 0

        proximo_x = float(-LARGURA_CARRO) if direcao == 1 else float(LARGURA)
        lane_data[linha] = {
            "direcao": direcao,
            "velocidade": velocidade,
            "spawn_gap": spawn_gap,
            "proximo_spawn_x": proximo_x,
            "num_slots": num_slots,
            "modo_rio": modo_rio,
            "vitorias_cols": [],
        }

    return lane_data[linha]


class Carro:
    __slots__ = ("linha", "x", "velocidade", "direcao", "img", "largura")

    def __init__(self, linha, x, velocidade, direcao, img):
        self.linha = linha
        self.x = x
        self.velocidade = velocidade
        self.direcao = direcao
        self.img = img
        self.largura = img.get_width()

    def update(self):
        self.x += self.velocidade * self.direcao

    def fora_da_tela(self):
        if self.direcao == 1:
            return self.x > LARGURA + self.largura
        return self.x < -self.largura * 2

    def screen_y(self, camera_y):
        return int(self.linha * TAMANHO_TILE - camera_y)

    def draw(self, surface, camera_y):
        surface.blit(self.img, (int(self.x), self.screen_y(camera_y)))

    def rect(self, camera_y):
        m = 4
        return pygame.Rect(
            int(self.x) + m,
            self.screen_y(camera_y) + m,
            self.largura - m * 2,
            ALTURA_CARRO - m * 2,
        )


class Tronco:
    def __init__(self, linha, x, velocidade, direcao, num_slots, tipo="tronco"):
        self.linha = linha
        self.x = float(x)
        self.velocidade = velocidade
        self.direcao = direcao
        self.num_slots = num_slots
        self.largura = num_slots * TAMANHO_TILE
        self.tipo = tipo

        banco = troncos_img if tipo == "tronco" else crocodilos_img
        banco_flip = troncos_img_flip if tipo == "tronco" else crocodilos_img_flip

        if direcao == 1:
            self.img = banco[num_slots]
        else:
            self.img = banco_flip[num_slots]

    def update(self):
        self.x += self.velocidade * self.direcao

    def fora_da_tela(self):
        if self.direcao == 1:
            return self.x > LARGURA + self.largura
        return self.x < -self.largura * 2

    def screen_y(self, camera_y):
        return int(self.linha * TAMANHO_TILE - camera_y)

    def draw(self, surface, camera_y):
        sy = self.screen_y(camera_y)
        if -self.largura <= sy <= ALTURA:
            surface.blit(self.img, (int(self.x), sy))

    def rect(self, camera_y):
        m = 4
        return pygame.Rect(
            int(self.x) + m,
            self.screen_y(camera_y) + m,
            self.largura - m * 2,
            TAMANHO_TILE - m * 2,
        )

    def slot_x_mundo(self, slot: int) -> float:
        return self.x + slot * TAMANHO_TILE

    def slot_do_x(self, wx: float) -> int:
        slot = round((wx - self.x) / TAMANHO_TILE)
        return max(0, min(self.num_slots - 1, slot))


class PowerUp:
    TAMANHO = 36

    def __init__(self, wx: float, wy: float, tipo: str):
        self.wx = wx
        self.wy = wy
        self.tipo = tipo
        self.coletado = False

    def screen_pos(self, camera_y):
        return int(self.wx), int(self.wy - camera_y)

    def rect_mundo(self):
        m = 8
        return pygame.Rect(
            int(self.wx) + m,
            int(self.wy) + m,
            self.TAMANHO - m * 2,
            self.TAMANHO - m * 2
        )

    def draw(self, surface, camera_y):
        if self.coletado:
            return

        sx, sy = self.screen_pos(camera_y)
        if -self.TAMANHO <= sy <= ALTURA:
            t = pygame.time.get_ticks()
            alpha = int(120 + 80 * abs((t % 800) / 400.0 - 1))

            if self.tipo == "xp2":
                icon = img_powerup_xp2
                glow_cor = (255, 190, 70, alpha)
            else:
                icon = img_powerup_escudo
                glow_cor = (255, 230, 80, alpha)

            glow = pygame.Surface((self.TAMANHO + 16, self.TAMANHO + 16), pygame.SRCALPHA)
            pygame.draw.circle(
                glow,
                glow_cor,
                (self.TAMANHO // 2 + 8, self.TAMANHO // 2 + 8),
                self.TAMANHO // 2 + 6
            )
            surface.blit(glow, (sx - 8, sy - 8))
            surface.blit(icon, (sx, sy))


class Fumaca:
    def __init__(self, wx, wy, vx, vy, nascida_em):
        self.wx = wx
        self.wy = wy
        self.vx = vx
        self.vy = vy
        self.nascida_em = nascida_em
        self.duracao = random.randint(450, 700)
        self.raio = random.randint(4, 6)

    def expirou(self, agora):
        return agora - self.nascida_em > self.duracao

    def draw(self, surface, camera_y, agora):
        idade = agora - self.nascida_em
        if idade < 0 or idade > self.duracao:
            return

        frac = idade / self.duracao
        wx = self.wx + self.vx * idade
        wy = self.wy + self.vy * idade

        sx = int(wx)
        sy = int(wy - camera_y)

        if sy < -30 or sy > ALTURA + 30:
            return

        raio = int(self.raio + frac * 5)
        alpha = int(140 * (1.0 - frac))

        surf = pygame.Surface((raio * 4, raio * 4), pygame.SRCALPHA)
        pygame.draw.circle(surf, (210, 210, 210, alpha), (raio * 2, raio * 2), raio)
        pygame.draw.circle(surf, (240, 240, 240, max(0, alpha - 40)), (raio * 2 - 2, raio * 2 - 2), max(1, raio - 1))
        surface.blit(surf, (sx - raio * 2, sy - raio * 2))


def spawn_fumaca_carro(carro, agora):
    if random.random() > 0.35:
        return

    if carro.direcao == 1:
        wx = carro.x + 4
        vx = random.uniform(-0.020, -0.010)
    else:
        wx = carro.x + carro.largura - 4
        vx = random.uniform(0.010, 0.020)

    wy = carro.linha * TAMANHO_TILE + TAMANHO_TILE - 8 + random.randint(-2, 2)
    vy = random.uniform(-0.030, -0.018)

    fumacas_ativas.append(Fumaca(wx, wy, vx, vy, agora))


class Arvore:
    def __init__(self, linha, wx, nascida_em=0):
        self.linha = linha
        self.wx = float(wx)
        self.wy = float(linha * TAMANHO_TILE)
        self.nascida_em = nascida_em

    def screen_y(self, camera_y):
        return int(self.wy - camera_y)

    def rect_mundo(self):
        return pygame.Rect(
            int(self.wx) + 12,
            int(self.wy) + 14,
            TAMANHO_TILE - 24,
            TAMANHO_TILE - 14
        )

    def draw(self, surface, camera_y, agora, bioma="grama"):
        sy = self.screen_y(camera_y)
        if -TAMANHO_TILE <= sy <= ALTURA:
            sx = int(self.wx)
            surf = pygame.Surface((TAMANHO_TILE, TAMANHO_TILE + 6), pygame.SRCALPHA)

            tempo = max(0, agora - self.nascida_em)
            alpha = 255
            if tempo < ARVORE_APARECIMENTO_MS:
                alpha = int(255 * (tempo / ARVORE_APARECIMENTO_MS))

            if bioma == "areia":
                pygame.draw.rect(surf, (60, 140, 60), (20, 8, 8, 30), border_radius=4)
                pygame.draw.rect(surf, (60, 140, 60), (10, 16, 10, 6), border_radius=3)
                pygame.draw.rect(surf, (60, 140, 60), (28, 20, 10, 6), border_radius=3)
                pygame.draw.rect(surf, (110, 70, 35), (21, 34, 6, 10), border_radius=2)
            elif bioma == "gelo":
                pygame.draw.polygon(surf, (50, 120, 60), [(24, 6), (8, 32), (40, 32)])
                pygame.draw.polygon(surf, (200, 230, 255), [(24, 6), (10, 22), (38, 22)], 0)
                pygame.draw.polygon(surf, (200, 230, 255), [(24, 6), (14, 16), (34, 16)], 0)
                pygame.draw.rect(surf, (110, 70, 35), (19, 32, 10, 12), border_radius=2)
            else:
                pygame.draw.circle(surf, (40, 150, 50), (24, 16), 16)
                pygame.draw.circle(surf, (55, 180, 65), (16, 18), 13)
                pygame.draw.circle(surf, (35, 120, 40), (31, 20), 12)
                pygame.draw.rect(surf, (110, 70, 35), (19, 22, 10, 22), border_radius=3)

            surf.set_alpha(alpha)
            surface.blit(surf, (sx, sy - 2))


class VitoriaRegia:
    TAMANHO = 28

    def __init__(self, linha, wx):
        self.linha = linha
        self.wx = float(wx)
        self.wy = float(linha * TAMANHO_TILE + (TAMANHO_TILE - self.TAMANHO) // 2)

    def screen_y(self, camera_y):
        return int(self.wy - camera_y)

    def rect_mundo(self):
        return pygame.Rect(
            int(self.wx),
            int(self.wy),
            self.TAMANHO,
            self.TAMANHO
        )

    def draw(self, surface, camera_y):
        sy = self.screen_y(camera_y)
        if -self.TAMANHO <= sy <= ALTURA:
            sx = int(self.wx)
            pygame.draw.rect(surface, (60, 180, 70), (sx, sy, self.TAMANHO, self.TAMANHO), border_radius=5)
            pygame.draw.rect(surface, (25, 110, 35), (sx, sy, self.TAMANHO, self.TAMANHO), 2, border_radius=5)


def desenhar_agua_rio(surface, sy, linha, score=0):
    ld = obter_lane_data(linha, score)
    direcao = ld["direcao"]

    agua = pygame.Surface((LARGURA, TAMANHO_TILE), pygame.SRCALPHA)
    t = pygame.time.get_ticks()
    desloc = (t // 60) % 30

    if direcao == 1:
        xs = range(-30 + desloc, LARGURA + 30, 30)
    else:
        xs = range(LARGURA + 30 - desloc, -30, -30)

    for i, xi in enumerate(xs):
        yoff = 5 if i % 2 == 0 else 0
        pygame.draw.ellipse(
            agua,
            (180, 220, 255, 90),
            (xi, TAMANHO_TILE // 2 - 3 + yoff, 18, 6)
        )
        pygame.draw.ellipse(
            agua,
            (230, 245, 255, 45),
            (xi + 6, TAMANHO_TILE // 2 + 2 + yoff, 10, 3)
        )

    surface.blit(agua, (0, sy))


def tentar_spawnar_carros(linha_ini: int, linha_fim: int, score: int = 0):
    linha_base = int(PLAYER_ALVO_Y // TAMANHO_TILE)
    safe_inicio = linha_base - SAFE_ZONE_LINHAS

    for linha in range(linha_ini, linha_fim + 1):
        if linha >= safe_inicio:
            continue

        _, tipo = gerar_tile(linha)

        if tipo == TIPO_ESTRADA:
            ld = obter_lane_data(linha, score)
            d = ld["direcao"]
            v = ld["velocidade"]
            ja_existem = [c for c in carros_ativos if c.linha == linha]

            if not ja_existem:
                x0 = float(-LARGURA_CARRO) if d == 1 else float(LARGURA)
                img = random.choice(carros_disp_r if d == 1 else carros_disp_l)
                carros_ativos.append(Carro(linha, x0, v, d, img))
                ld["proximo_spawn_x"] = x0 + d * ld["spawn_gap"]
            else:
                ultimo = max(ja_existem, key=lambda c: c.x * d)

                if d == 1 and ultimo.x >= ld["proximo_spawn_x"]:
                    img = random.choice(carros_disp_r)
                    carros_ativos.append(Carro(linha, float(-LARGURA_CARRO), v, d, img))
                    ld["proximo_spawn_x"] += ld["spawn_gap"]
                elif d == -1 and ultimo.x <= ld["proximo_spawn_x"]:
                    img = random.choice(carros_disp_l)
                    carros_ativos.append(Carro(linha, float(LARGURA), v, d, img))
                    ld["proximo_spawn_x"] -= ld["spawn_gap"]

        elif tipo == TIPO_RIO:
            if rio_congelado(score):
                continue

            ld = obter_lane_data(linha, score)

            if ld.get("modo_rio") == "vitoria_regia":
                continue

            d = ld["direcao"]
            v = ld["velocidade"]
            ns = ld["num_slots"]
            largura_t = ns * TAMANHO_TILE

            bioma_linha = bioma_por_linha.get(linha, get_bioma_atual(score))
            tipo_flutuavel = "crocodilo" if bioma_linha == "areia" else "tronco"

            ja_existem = [t for t in troncos_ativos if t.linha == linha]

            if not ja_existem:
                x0 = float(-largura_t) if d == 1 else float(LARGURA)
                troncos_ativos.append(Tronco(linha, x0, v, d, ns, tipo_flutuavel))
                ld["proximo_spawn_x"] = x0 + d * ld["spawn_gap"]
            else:
                ultimo = max(ja_existem, key=lambda c: c.x * d)

                if d == 1 and ultimo.x >= ld["proximo_spawn_x"]:
                    troncos_ativos.append(Tronco(linha, float(-largura_t), v, d, ns, tipo_flutuavel))
                    ld["proximo_spawn_x"] += ld["spawn_gap"]
                elif d == -1 and ultimo.x <= ld["proximo_spawn_x"]:
                    troncos_ativos.append(Tronco(linha, float(LARGURA), v, d, ns, tipo_flutuavel))
                    ld["proximo_spawn_x"] -= ld["spawn_gap"]


def gerar_arvores_para_linhas(linha_ini, linha_fim, linha_visivel_ini, linha_visivel_fim, score=0, agora=0):
    for linha in range(linha_ini, linha_fim + 1):
        if linha in linhas_arvore_processadas:
            continue

        _, tipo = gerar_tile(linha)

        if linha_visivel_ini <= linha <= linha_visivel_fim:
            continue

        if tipo != TIPO_GRAMA:
            linhas_arvore_processadas.add(linha)
            continue

        chance = ARVORE_CHANCE_BASE + min(score / ARVORE_CHANCE_EXTRA_SCORE, ARVORE_CHANCE_EXTRA_MAX)

        if random.random() < chance:
            qtd = 1 if random.random() < 0.9 else 2

            col_total = LARGURA // TAMANHO_TILE
            cols = list(range(1, col_total - 1))
            random.shuffle(cols)

            for col in cols[:qtd]:
                wx = float(col * TAMANHO_TILE + random.randint(-5, 5))
                arvores_ativas.append(Arvore(linha, wx, agora))

        linhas_arvore_processadas.add(linha)


def gerar_vitorias_regias_para_linhas(linha_ini: int, linha_fim: int, score: int = 0):
    if rio_congelado(score):
        return

    linha_base = int(PLAYER_ALVO_Y // TAMANHO_TILE)
    safe_inicio = linha_base - SAFE_ZONE_LINHAS
    pares_processados = set()

    for linha in range(linha_ini, linha_fim + 1):
        if linha >= safe_inicio:
            continue

        _, tipo = gerar_tile(linha)
        if tipo != TIPO_RIO:
            continue

        ld = obter_lane_data(linha, score)
        if ld.get("modo_rio") != "vitoria_regia":
            continue

        par = None
        for d in (-1, 1):
            nl = linha + d
            if nl < 0:
                continue
            _, tipo_viz = gerar_tile(nl)
            if tipo_viz == TIPO_RIO:
                ld_viz = obter_lane_data(nl, score)
                if ld_viz.get("modo_rio") == "vitoria_regia":
                    par = nl
                    break

        chave_par = tuple(sorted((linha, par))) if par is not None else (linha,)
        if chave_par in pares_processados:
            continue
        pares_processados.add(chave_par)

        linhas_do_grupo = [linha, par] if par is not None else [linha]

        if par is not None:
            ld_par = obter_lane_data(par, score)
            cols_compartilhadas = ld["vitorias_cols"] or ld_par["vitorias_cols"]
            if not cols_compartilhadas:
                total_cols = LARGURA // TAMANHO_TILE
                qtd = random.randint(2, 4)
                cols_compartilhadas = sorted(random.sample(range(1, total_cols - 1), qtd))

            ld["vitorias_cols"] = cols_compartilhadas
            ld_par["vitorias_cols"] = cols_compartilhadas

        for ln in linhas_do_grupo:
            ld_ln = obter_lane_data(ln, score)

            if par is None:
                if "vitorias_cols" not in ld_ln or not ld_ln["vitorias_cols"]:
                    total_cols = LARGURA // TAMANHO_TILE
                    qtd = random.randint(2, 4)
                    ld_ln["vitorias_cols"] = sorted(random.sample(range(1, total_cols - 1), qtd))

            for col in ld_ln["vitorias_cols"]:
                wx = float(col * TAMANHO_TILE + (TAMANHO_TILE - VitoriaRegia.TAMANHO) // 2)
                if not any(v.linha == ln and abs(v.wx - wx) < 1 for v in vitorias_ativas):
                    vitorias_ativas.append(VitoriaRegia(ln, wx))


def gerar_powerups_para_linhas(linha_ini, linha_fim, powerups: list, linhas_com_powerup: set, score: int):
    if len([p for p in powerups if not p.coletado]) >= MAX_POWERUPS_ATIVOS:
        return

    linha_base = int(PLAYER_ALVO_Y // TAMANHO_TILE)
    safe_inicio = linha_base - SAFE_ZONE_LINHAS

    for linha in range(linha_ini, linha_fim + 1):
        if linha >= safe_inicio:
            continue
        if linha in linhas_com_powerup:
            continue

        _, tipo = gerar_tile(linha)
        if tipo != TIPO_GRAMA:
            continue

        chance_escudo = 0.007 + min(score / 5000.0, 0.003)
        chance_xp2 = 0.006 + min(score / 5000.0, 0.003)

        roll = random.random()
        tipo_powerup = None

        if roll < chance_escudo:
            tipo_powerup = "escudo"
        elif roll < chance_escudo + chance_xp2:
            tipo_powerup = "xp2"

        if tipo_powerup is None:
            continue

        col_total = LARGURA // TAMANHO_TILE

        colunas_livres = []
        for c in range(1, col_total - 1):
            wx_teste = float(c * TAMANHO_TILE)
            wy_teste = float(linha * TAMANHO_TILE + (TAMANHO_TILE - PowerUp.TAMANHO) // 2)
            rect_teste = pygame.Rect(int(wx_teste), int(wy_teste), PowerUp.TAMANHO, PowerUp.TAMANHO)
            if not any(arv.rect_mundo().colliderect(rect_teste) for arv in arvores_ativas):
                colunas_livres.append(c)

        if not colunas_livres:
            continue

        col = random.choice(colunas_livres)
        wx = float(col * TAMANHO_TILE)
        wy = float(linha * TAMANHO_TILE + (TAMANHO_TILE - PowerUp.TAMANHO) // 2)

        powerups.append(PowerUp(wx, wy, tipo_powerup))
        linhas_com_powerup.add(linha)


def colide_com_arvore(rect_mundo):
    return any(arv.rect_mundo().colliderect(rect_mundo) for arv in arvores_ativas)


def desenhar_botao(surface, rect, label, kbd_hint, hover,
                   cor_normal=(30, 30, 60), cor_hover=(180, 70, 10),
                   cor_borda=(255, 200, 50), cor_texto=(255, 255, 255)):
    cor = cor_hover if hover else cor_normal
    pygame.draw.rect(surface, cor, rect, border_radius=10)
    pygame.draw.rect(surface, cor_borda, rect, 2, border_radius=10)

    t = fonte_botao.render(label, True, cor_texto)
    surface.blit(t, t.get_rect(center=(rect.centerx, rect.centery - 7)))

    hint = fonte_kbd.render(f"[{kbd_hint}]", True, (220, 200, 100))
    surface.blit(hint, hint.get_rect(center=(rect.centerx, rect.centery + 13)))




def draw_button(surface, rect, label, hint, hover,
                normal=(30, 30, 60), hover_cor=(180, 70, 10),
                border=(255, 200, 50), text=(255, 255, 255)):
    return desenhar_botao(surface, rect, label, hint, hover,
                          cor_normal=normal, cor_hover=hover_cor,
                          cor_borda=border, cor_texto=text)


def desenhar_painel_como_jogar():
    overlay = pygame.Surface((LARGURA, ALTURA), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 195))
    window.blit(overlay, (0, 0))

    painel_w, painel_h = 430, 490
    painel_x = (LARGURA - painel_w) // 2
    painel_y = (ALTURA - painel_h) // 2

    painel = pygame.Surface((painel_w, painel_h), pygame.SRCALPHA)
    painel.fill((15, 18, 42, 230))
    pygame.draw.rect(painel, (255, 200, 50), (0, 0, painel_w, painel_h), 3, border_radius=14)
    window.blit(painel, (painel_x, painel_y))

    titulo = fonte_botao.render("COMO JOGAR", True, (255, 210, 50))
    window.blit(titulo, titulo.get_rect(center=(LARGURA // 2, painel_y + 30)))

    pygame.draw.line(
        window, (255, 200, 50),
        (painel_x + 20, painel_y + 50),
        (painel_x + painel_w - 20, painel_y + 50), 1
    )

    secoes = [
        ("MOVIMENTAÇÃO", [
            ("W", "Andar para cima  (+1 ponto)"),
            ("S", "Andar para baixo"),
            ("A", "Andar para esquerda"),
            ("D", "Andar para direita"),
        ]),
        ("CÂMERA", [
            (">>", "Câmera começa parada no início"),
            (">>", "Ao mover, ela rola sozinha para cima"),
            (">>", "Fique pra trás = morte!"),
            (">>", "Quanto mais pontos, mais rápida!"),
        ]),
        ("OBSTÁCULOS", [
            ("!!", "Desvie dos carros na estrada!"),
            ("~~", "Atravesse rios em cima de troncos!"),
            ("A/D", "Mude de slot no tronco (cuidado!)"),
            ("XX", "Cair na água = morte!"),
            ("##", "Árvore = parede, não deixa passar."),
        ]),
        ("POWER-UPS", [
            ("★", "Escudo dourado: absorve 1 golpe fatal."),
            ("x2", "Moeda dourada: vale 2 pontos por 8s."),
        ]),
    ]

    BTN_H = 42
    BTN_MARGIN = 12
    y_ini = painel_y + 60
    y_max = painel_y + painel_h - BTN_H - BTN_MARGIN - 8

    HDR_H = 21
    ITEM_H = 20
    SEC_GAP = 7

    total_linhas = sum(HDR_H + len(itens) * ITEM_H for _, itens in secoes)
    total_gaps = SEC_GAP * (len(secoes) - 1)
    total_h = total_linhas + total_gaps
    espaco = y_max - y_ini
    extra = max(0, (espaco - total_h) // max(1, len(secoes) - 1))

    y_cur = y_ini
    for idx, (titulo_sec, itens) in enumerate(secoes):
        hdr = fonte_hud.render(titulo_sec, True, (255, 180, 40))
        window.blit(hdr, (painel_x + 18, y_cur))
        y_cur += HDR_H

        for icone, texto in itens:
            ic = fonte_titulo.render(icone, True, (130, 200, 255))
            window.blit(ic, (painel_x + 22, y_cur))
            tx = fonte_titulo.render(texto, True, (210, 225, 255))
            window.blit(tx, (painel_x + 52, y_cur))
            y_cur += ITEM_H

        if idx < len(secoes) - 1:
            y_cur += SEC_GAP + extra

    btn_fechar = pygame.Rect(LARGURA // 2 - 75, painel_y + painel_h - BTN_H - BTN_MARGIN, 150, BTN_H)
    mouse = pygame.mouse.get_pos()
    desenhar_botao(
        window, btn_fechar, "FECHAR", "ESC",
        btn_fechar.collidepoint(mouse),
        cor_normal=(50, 20, 70),
        cor_hover=(160, 40, 10)
    )
    return btn_fechar


def tela_inicial():
    clock_menu = pygame.time.Clock()
    btn_w, btn_h = 220, 58
    btn_como_jogar = pygame.Rect(LARGURA // 2 - btn_w // 2, ALTURA // 2 + 30, btn_w, btn_h)
    mostrar_como_jogar = False

    while True:
        mouse = pygame.mouse.get_pos()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                raise SystemExit

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE and not mostrar_como_jogar:
                    return
                if event.key == pygame.K_h and not mostrar_como_jogar:
                    mostrar_como_jogar = True
                if event.key == pygame.K_ESCAPE:
                    mostrar_como_jogar = False

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if mostrar_como_jogar:
                    panel_h = 490
                    btn_fechar_rect = pygame.Rect(
                        LARGURA // 2 - 75,
                        (ALTURA - panel_h) // 2 + panel_h - 42 - 12,
                        150, 42
                    )
                    if btn_fechar_rect.collidepoint(mouse):
                        mostrar_como_jogar = False
                else:
                    if btn_como_jogar.collidepoint(mouse):
                        mostrar_como_jogar = True

        window.blit(img_fundo, (0, 0))

        if pygame.time.get_ticks() % 1000 < 500:
            texto = fonte.render("ESPAÇO para começar", True, (255, 255, 255))
            rect = texto.get_rect(center=(LARGURA // 2, ALTURA // 2 - 20))
            sombra = fonte.render("ESPAÇO para começar", True, (0, 0, 0))
            window.blit(sombra, (rect.x + 2, rect.y + 2))
            window.blit(texto, rect)

        desenhar_botao(window, btn_como_jogar, "Como Jogar", "H",
                       btn_como_jogar.collidepoint(mouse))

        if mostrar_como_jogar:
            desenhar_painel_como_jogar()

        pygame.display.update()
        clock_menu.tick(30)


def tela_game_over(score: int) -> str:
    clock_go = pygame.time.Clock()
    btn_w, btn_h = 170, 58
    btn_retry = pygame.Rect(LARGURA // 2 - btn_w - 15, ALTURA // 2 + 65, btn_w, btn_h)
    btn_menu = pygame.Rect(LARGURA // 2 + 15, ALTURA // 2 + 65, btn_w, btn_h)

    texto_score = fonte.render(f"Pontuação: {score}", True, (255, 220, 50))
    sombra_score = fonte.render(f"Pontuação: {score}", True, (0, 0, 0))

    while True:
        mouse = pygame.mouse.get_pos()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                raise SystemExit

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    return "retry"
                if event.key == pygame.K_m:
                    return "menu"

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if btn_retry.collidepoint(mouse):
                    return "retry"
                if btn_menu.collidepoint(mouse):
                    return "menu"

        window.blit(img_fundo_fim, (0, 0))

        sr = texto_score.get_rect(center=(LARGURA // 2, ALTURA // 2 + 15))
        window.blit(sombra_score, (sr.x + 2, sr.y + 2))
        window.blit(texto_score, sr)

        desenhar_botao(window, btn_retry, "RETRY", "R",
                       btn_retry.collidepoint(mouse),
                       cor_hover=(20, 140, 20))
        desenhar_botao(window, btn_menu, "MENU", "M",
                       btn_menu.collidepoint(mouse),
                       cor_hover=(140, 40, 10))

        pygame.display.update()
        clock_go.tick(30)


def desenhar_hud_status(bx: int, by: int, icon, restante_ms: int, total_ms: int,
                        texto: str, cor_barra, cor_borda=(255, 220, 80)):
    frac = max(0.0, restante_ms / total_ms)

    bw, bh = 130, 18
    window.blit(icon, (bx - 40, by - 8))

    pygame.draw.rect(window, (30, 30, 60), (bx, by, bw, bh), border_radius=5)
    pygame.draw.rect(window, cor_barra, (bx, by, int(bw * frac), bh), border_radius=5)
    pygame.draw.rect(window, cor_borda, (bx, by, bw, bh), 2, border_radius=5)

    t = fonte_kbd.render(texto, True, (255, 255, 255))
    window.blit(t, t.get_rect(center=(bx + bw // 2, by + bh // 2)))


def desenhar_hud_escudo():
    bx = LARGURA - 130 - 10
    by = 10
    bw, bh = 130, 18
    window.blit(img_powerup_escudo, (bx - 40, by - 8))
    pygame.draw.rect(window, (60, 30, 10), (bx, by, bw, bh), border_radius=5)
    pygame.draw.rect(window, (255, 210, 50), (bx, by, bw, bh), border_radius=5)
    pygame.draw.rect(window, (255, 240, 120), (bx, by, bw, bh), 2, border_radius=5)
    t = fonte_kbd.render("ESCUDO ATIVO", True, (60, 30, 0))
    window.blit(t, t.get_rect(center=(bx + bw // 2, by + bh // 2)))


def desenhar_hud_xp2(restante_ms: int):
    secs = max(0, restante_ms // 1000 + 1)
    desenhar_hud_status(
        LARGURA - 130 - 10, 38,
        img_powerup_xp2,
        restante_ms, POWERUP_XP2_DURACAO_MS,
        f"XP x2 {secs}s", (255, 210, 80)
    )


def iniciar_jogo() -> str:
    resetar_mundo()

    player_linha = int(PLAYER_ALVO_Y // TAMANHO_TILE)
    player_wx = float((LARGURA // TAMANHO_TILE // 2) * TAMANHO_TILE)
    player_wy = float(player_linha * TAMANHO_TILE)
    camera_y = player_wy - PLAYER_ALVO_Y
    camera_ativa = False
    imagem = img_baixo
    clock = pygame.time.Clock()
    score = 0

    powerups = []
    linhas_com_powerup = set()

    tem_escudo = False
    graca_ate = 0
    xp2_ate = 0

    tronco_atual = None
    slot_atual = 0
    # Linha mais "acima" (menor índice) que o jogador já pisou.
    # Pontos só são dados quando o jogador bate novo recorde.
    linha_recorde = player_linha

    while True:
        clock.tick(30)
        agora = pygame.time.get_ticks()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                raise SystemExit

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_w:
                    novo_wy = player_wy - TAMANHO_TILE
                    teste_rect = pygame.Rect(
                        int(player_wx) + 4, int(novo_wy) + 4,
                        TAMANHO_TILE - 8, TAMANHO_TILE - 8
                    )

                    if not colide_com_arvore(teste_rect):
                        tronco_atual = None
                        player_wy = novo_wy
                        imagem = img_cima
                        camera_ativa = True
                        nova_linha = int(player_wy // TAMANHO_TILE)
                        if nova_linha < linha_recorde:
                            linha_recorde = nova_linha
                            if agora < xp2_ate:
                                score += 2
                            else:
                                score += 1

                elif event.key == pygame.K_s:
                    novo_wy = player_wy + TAMANHO_TILE
                    teste_rect = pygame.Rect(
                        int(player_wx) + 4, int(novo_wy) + 4,
                        TAMANHO_TILE - 8, TAMANHO_TILE - 8
                    )

                    if not colide_com_arvore(teste_rect):
                        tronco_atual = None
                        player_wy = novo_wy
                        imagem = img_baixo

                elif event.key == pygame.K_a:
                    imagem = img_esquerda
                    if tronco_atual is not None:
                        novo_slot = slot_atual - 1
                        if novo_slot < 0:
                            tronco_atual = None
                        else:
                            slot_atual = novo_slot
                    else:
                        novo_wx = player_wx - TAMANHO_TILE
                        teste_rect = pygame.Rect(
                            int(novo_wx) + 4, int(player_wy) + 4,
                            TAMANHO_TILE - 8, TAMANHO_TILE - 8
                        )
                        if not colide_com_arvore(teste_rect):
                            player_wx = novo_wx

                elif event.key == pygame.K_d:
                    imagem = img_direita
                    if tronco_atual is not None:
                        novo_slot = slot_atual + 1
                        if novo_slot >= tronco_atual.num_slots:
                            tronco_atual = None
                        else:
                            slot_atual = novo_slot
                    else:
                        novo_wx = player_wx + TAMANHO_TILE
                        teste_rect = pygame.Rect(
                            int(novo_wx) + 4, int(player_wy) + 4,
                            TAMANHO_TILE - 8, TAMANHO_TILE - 8
                        )
                        if not colide_com_arvore(teste_rect):
                            player_wx = novo_wx

        vel_scroll = VEL_SCROLL_INICIAL + (VEL_SCROLL_MAX - VEL_SCROLL_INICIAL) * min(
            score / SCORE_PARA_MAX_VEL, 1.0
        )

        if camera_ativa:
            camera_y -= vel_scroll

        target_cam = player_wy - PLAYER_ALVO_Y
        if camera_y > target_cam:
            diff = camera_y - target_cam
            passo = max(vel_scroll + 1.0, diff * 0.22)
            camera_y -= passo
            if camera_y < target_cam:
                camera_y = target_cam

        player_screen_y = player_wy - camera_y
        player_screen_x = int(player_wx)

        if player_screen_y >= ALTURA or player_screen_y < -TAMANHO_TILE:
            return tela_game_over(score)

        linha_ini = int(camera_y // TAMANHO_TILE) - 1
        linha_fim = int((camera_y + ALTURA) // TAMANHO_TILE) + 1

        linha_visivel_ini = int(camera_y // TAMANHO_TILE)
        linha_visivel_fim = int((camera_y + ALTURA) // TAMANHO_TILE)

        for l in range(linha_ini - PREGEN_BIOMA, linha_fim + PREGEN_BIOMA + 1):
            fixar_bioma_linha(l, score)

        tentar_spawnar_carros(linha_ini, linha_fim, score)
        gerar_arvores_para_linhas(
            linha_visivel_ini - ARVORE_PREGEN_LINHAS,
            linha_visivel_fim + ARVORE_PREGEN_LINHAS,
            linha_visivel_ini,
            linha_visivel_fim,
            score,
            agora
        )
        gerar_vitorias_regias_para_linhas(linha_ini, linha_fim, score)
        gerar_powerups_para_linhas(linha_ini, linha_fim, powerups, linhas_com_powerup, score)

        for c in carros_ativos:
            c.update()
            spawn_fumaca_carro(c, agora)

        carros_ativos[:] = [c for c in carros_ativos if not c.fora_da_tela()]
        fumacas_ativas[:] = [f for f in fumacas_ativas if not f.expirou(agora)]

        if not rio_congelado(score):
            for t in troncos_ativos:
                t.update()
            troncos_ativos[:] = [t for t in troncos_ativos if not t.fora_da_tela()]
        else:
            troncos_ativos.clear()

        arvores_ativas[:] = [
            a for a in arvores_ativas
            if -ARVORE_MARGEM_MANUTENCAO <= a.screen_y(camera_y) <= ALTURA + ARVORE_MARGEM_MANUTENCAO
        ]

        vitorias_ativas[:] = [
            v for v in vitorias_ativas
            if -TAMANHO_TILE <= v.screen_y(camera_y) <= ALTURA + TAMANHO_TILE
        ]

        if tronco_atual is not None and tronco_atual not in troncos_ativos:
            tronco_atual = None

        player_linha_atual = int(player_wy // TAMANHO_TILE)
        _, tipo_atual = gerar_tile(player_linha_atual)

        if tipo_atual == TIPO_RIO:
            if rio_congelado(score):
                tronco_atual = None
            else:
                ld_atual = obter_lane_data(player_linha_atual, score)
                em_vitoria_regia_lane = ld_atual.get("modo_rio") == "vitoria_regia"

                if em_vitoria_regia_lane:
                    tronco_atual = None
                elif tronco_atual is not None:
                    player_wx = tronco_atual.slot_x_mundo(slot_atual)
                    player_wx = clamp(player_wx, 0.0, float(LARGURA - TAMANHO_TILE))
                else:
                    troncos_da_linha = [t for t in troncos_ativos if t.linha == player_linha_atual]
                    for t in troncos_da_linha:
                        if t.x <= player_wx < t.x + t.largura:
                            tronco_atual = t
                            slot_atual = t.slot_do_x(player_wx)
                            player_wx = t.slot_x_mundo(slot_atual)
                            break
        else:
            tronco_atual = None

        player_wx = clamp(player_wx, 0.0, float(LARGURA - TAMANHO_TILE))
        player_screen_x = int(player_wx)

        player_rect_mundo = pygame.Rect(
            int(player_wx) + 4, int(player_wy) + 4,
            TAMANHO_TILE - 8, TAMANHO_TILE - 8,
        )
        player_rect = pygame.Rect(
            player_screen_x + 4, int(player_screen_y) + 4,
            TAMANHO_TILE - 8, TAMANHO_TILE - 8,
        )

        for pu in powerups:
            if not pu.coletado and player_rect_mundo.colliderect(pu.rect_mundo()):
                pu.coletado = True
                if pu.tipo == "escudo":
                    tem_escudo = True
                elif pu.tipo == "xp2":
                    if agora >= xp2_ate:
                        xp2_ate = agora + POWERUP_XP2_DURACAO_MS

        powerups[:] = [
            p for p in powerups
            if not p.coletado and -TAMANHO_TILE <= p.wy - camera_y <= ALTURA + TAMANHO_TILE
        ]

        morreu = False

        def checa_morte_real():
            nonlocal morreu
            if tipo_atual == TIPO_ESTRADA:
                for c in carros_ativos:
                    if c.rect(camera_y).colliderect(player_rect):
                        morreu = True
                        return
            elif tipo_atual == TIPO_RIO:
                if not rio_congelado(score):
                    em_vitoria = any(
                        v.rect_mundo().colliderect(player_rect_mundo)
                        for v in vitorias_ativas
                        if v.linha == player_linha_atual
                    )
                    if tronco_atual is None and not em_vitoria:
                        morreu = True

        if not tem_escudo and agora >= graca_ate:
            checa_morte_real()
        elif tem_escudo:
            golpe_fatal = False
            if tipo_atual == TIPO_ESTRADA:
                for c in carros_ativos:
                    if c.rect(camera_y).colliderect(player_rect):
                        golpe_fatal = True
                        break
            elif tipo_atual == TIPO_RIO:
                if not rio_congelado(score):
                    em_vitoria = any(
                        v.rect_mundo().colliderect(player_rect_mundo)
                        for v in vitorias_ativas
                        if v.linha == player_linha_atual
                    )
                    if tronco_atual is None and not em_vitoria:
                        golpe_fatal = True

            if golpe_fatal:
                tem_escudo = False
                graca_ate = agora + 600

        if morreu:
            return tela_game_over(score)

        window.blit(img_fundo, (0, 0))

        for linha in range(linha_ini, linha_fim + 1):
            sy = int(linha * TAMANHO_TILE - camera_y)
            surf, tipo = gerar_tile(linha)
            bioma_linha = fixar_bioma_linha(linha, score)

            if tipo == TIPO_GRAMA:
                desenhar_grama(window, sy, surf, bioma_linha)
            else:
                window.blit(surf, (0, sy))

            if tipo == TIPO_RIO:
                if rio_congelado(score):
                    window.blit(img_rio_gelo, (0, sy))
                else:
                    desenhar_agua_rio(window, sy, linha, score)

        for arv in arvores_ativas:
            arv.draw(window, camera_y, agora, fixar_bioma_linha(arv.linha, score))

        for v in vitorias_ativas:
            v.draw(window, camera_y)

        for pu in powerups:
            pu.draw(window, camera_y)

        for f in fumacas_ativas:
            f.draw(window, camera_y, agora)

        for t in troncos_ativos:
            t.draw(window, camera_y)

        for c in carros_ativos:
            sy = c.screen_y(camera_y)
            if -ALTURA_CARRO <= sy <= ALTURA:
                c.draw(window, camera_y)

        if tronco_atual is not None and tipo_atual == TIPO_RIO:
            sy_t = tronco_atual.screen_y(camera_y)
            for s in range(tronco_atual.num_slots):
                sx_slot = int(tronco_atual.slot_x_mundo(s))
                cor_slot = (255, 255, 100, 160) if s == slot_atual else (255, 255, 255, 60)
                indicador = pygame.Surface((TAMANHO_TILE - 8, 4), pygame.SRCALPHA)
                indicador.fill(cor_slot)
                window.blit(indicador, (sx_slot + 4, sy_t + TAMANHO_TILE - 6))

        if tem_escudo:
            aura = pygame.Surface((TAMANHO_TILE + 16, TAMANHO_TILE + 16), pygame.SRCALPHA)
            pulso = int(120 + 80 * abs((agora % 600) / 300.0 - 1))
            pygame.draw.circle(
                aura,
                (255, 220, 60, pulso),
                (TAMANHO_TILE // 2 + 8, TAMANHO_TILE // 2 + 8),
                TAMANHO_TILE // 2 + 6
            )
            window.blit(aura, (player_screen_x - 8, int(player_screen_y) - 8))
            window.blit(imagem, (player_screen_x, int(player_screen_y)))
        elif agora < graca_ate:
            if (agora // 80) % 2 == 0:
                window.blit(imagem, (player_screen_x, int(player_screen_y)))
        else:
            window.blit(imagem, (player_screen_x, int(player_screen_y)))

        score_texto = fonte_score.render(f"Score: {score}", True, (255, 255, 255))
        score_sombra = fonte_score.render(f"Score: {score}", True, (0, 0, 0))
        window.blit(score_sombra, (12, 12))
        window.blit(score_texto, (10, 10))

        if tem_escudo:
            desenhar_hud_escudo()

        if agora < xp2_ate:
            desenhar_hud_xp2(xp2_ate - agora)

        pygame.display.update()


if __name__ == "__main__":
    tela_inicial()
    while True:
        resultado = iniciar_jogo()
        if resultado == "menu":
            tela_inicial()