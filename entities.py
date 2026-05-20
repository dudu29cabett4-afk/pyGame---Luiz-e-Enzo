# entities.py
import pygame
import random
import assets
from config import *
from utils import clamp


class Particle:
    def __init__(self, x, y, vx, vy, color, duration, radius):
        self.x, self.y, self.vx, self.vy, self.color, self.duration, self.radius = x, y, vx, vy, color, duration, radius
        self.born = pygame.time.get_ticks()

    def update(self):
        self.x += self.vx;
        self.y += self.vy

    def draw(self, surface, camera_y, now):
        age = now - self.born
        if age > self.duration: return False
        frac = 1 - (age / self.duration)
        alpha = int(255 * frac)
        r = int(self.radius * (1 + (1 - frac)))
        surf = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
        pygame.draw.circle(surf, (*self.color[:3], alpha), (r, r), r)
        surface.blit(surf, (int(self.x) - r, int(self.y - camera_y) - r))
        return True


class Fumaca:
    def __init__(self, wx, wy, vx, vy, nascida_em):
        self.wx, self.wy, self.vx, self.vy, self.nascida_em = wx, wy, vx, vy, nascida_em
        self.duracao, self.raio = random.randint(450, 700), random.randint(4, 6)

    def expirou(self, agora):
        return agora - self.nascida_em > self.duracao

    def draw(self, surface, camera_y, agora):
        idade = agora - self.nascida_em
        if 0 <= idade <= self.duracao:
            frac = idade / self.duracao
            sx, sy = int(self.wx + self.vx * idade), int(self.wy + self.vy * idade - camera_y)
            if -30 <= sy <= ALTURA + 30:
                raio = int(self.raio + frac * 5)
                alpha = int(140 * (1.0 - frac))
                surf = pygame.Surface((raio * 4, raio * 4), pygame.SRCALPHA)
                pygame.draw.circle(surf, (210, 210, 210, alpha), (raio * 2, raio * 2), raio)
                pygame.draw.circle(surf, (240, 240, 240, max(0, alpha - 40)), (raio * 2 - 2, raio * 2 - 2),
                                   max(1, raio - 1))
                surface.blit(surf, (sx - raio * 2, sy - raio * 2))


class PowerUp:
    TAMANHO = 36

    def __init__(self, wx, wy, tipo):
        self.wx, self.wy, self.tipo, self.coletado = wx, wy, tipo, False

    def rect_mundo(self):
        m = 6
        return pygame.Rect(int(self.wx) + m, int(self.wy) + m, TAMANHO_TILE - m * 2, TAMANHO_TILE - m * 2)

    def draw(self, surface, camera_y):
        if self.coletado: return
        sx = int(self.wx) + (TAMANHO_TILE - self.TAMANHO) // 2
        sy = int(self.wy - camera_y) + (TAMANHO_TILE - self.TAMANHO) // 2 - 3
        if -self.TAMANHO <= sy <= ALTURA:
            t = pygame.time.get_ticks()
            alpha = int(120 + 80 * abs((t % 800) / 400.0 - 1))
            icon = assets.images['pu_xp2'] if self.tipo == "xp2" else assets.images['pu_escudo']
            glow_cor = (255, 190, 70, alpha) if self.tipo == "xp2" else (255, 230, 80, alpha)
            glow = pygame.Surface((self.TAMANHO + 16, self.TAMANHO + 16), pygame.SRCALPHA)
            pygame.draw.circle(glow, glow_cor, (self.TAMANHO // 2 + 8, self.TAMANHO // 2 + 8), self.TAMANHO // 2 + 6)
            surface.blit(glow, (sx - 8, sy - 8))
            surface.blit(icon, (sx, sy))


class VitoriaRegia:
    def __init__(self, linha, wx):
        self.linha, self.wx, self.wy = linha, float(wx), float(linha * TAMANHO_TILE)

    def rect_mundo(self): return pygame.Rect(int(self.wx) + 4, int(self.wy) + 4, TAMANHO_TILE - 8, TAMANHO_TILE - 8)

    def draw(self, surface, camera_y):
        sy = int(self.wy - camera_y)
        if -TAMANHO_TILE <= sy <= ALTURA:
            sx = int(self.wx)
            pygame.draw.rect(surface, (60, 180, 70), (sx + 4, sy + 4, 40, 40), border_radius=20)
            pygame.draw.rect(surface, (25, 110, 35), (sx + 4, sy + 4, 40, 40), 2, border_radius=20)
            pygame.draw.polygon(surface, (80, 170, 230), [(sx + 24, sy + 4), (sx + 16, sy + 18), (sx + 32, sy + 18)])


class Player:
    def __init__(self, world):
        self.world = world
        self.linha = int(PLAYER_ALVO_Y // TAMANHO_TILE)
        self.wx = float((LARGURA // TAMANHO_TILE // 2) * TAMANHO_TILE)
        self.wy = float(self.linha * TAMANHO_TILE)
        self.imagem = assets.images['p_baixo']
        self.input_buffer = []
        self.score = 0
        self.linha_recorde = self.linha
        self.tem_escudo = False
        self.graca_ate = 0
        self.xp2_ate = 0
        self.tronco_atual = None
        self.slot_atual = 0

        # --- SISTEMA DE TWEENING E ANIMAÇÃO ---
        self.anim_start = 0
        self.anim_duracao = 120  # Duração da transição em milissegundos
        self.visual_offset_x = 0.0
        self.visual_offset_y = 0.0
        self.last_move_axis = 'y'  # 'x' ou 'y' para saber o eixo do squash/stretch

    def rect(self, camera_y):
        return pygame.Rect(int(self.wx) + 8, int(self.wy - camera_y) + 8, TAMANHO_TILE - 16, TAMANHO_TILE - 16)

    def world_rect(self):
        return pygame.Rect(int(self.wx) + 8, int(self.wy) + 8, TAMANHO_TILE - 16, TAMANHO_TILE - 16)

    def queue_input(self, key):
        if len(self.input_buffer) < 2:
            self.input_buffer.append(key)

    def process_input(self, agora):
        if not self.input_buffer: return
        key = self.input_buffer.pop(0)

        # Guarda a posição lógica ANTES de mover para gerar o delta de animação
        old_wx, old_wy = self.wx, self.wy
        novo_wx, novo_wy = self.wx, self.wy

        if key == pygame.K_w:
            novo_wy -= TAMANHO_TILE;
            self.imagem = assets.images['p_cima']
            novo_wx = round(novo_wx / TAMANHO_TILE) * TAMANHO_TILE
        elif key == pygame.K_s:
            novo_wy += TAMANHO_TILE;
            self.imagem = assets.images['p_baixo']
            novo_wx = round(novo_wx / TAMANHO_TILE) * TAMANHO_TILE
        elif key == pygame.K_a:
            novo_wx -= TAMANHO_TILE;
            self.imagem = assets.images['p_esq']
        elif key == pygame.K_d:
            novo_wx += TAMANHO_TILE;
            self.imagem = assets.images['p_dir']

        test_rect = pygame.Rect(int(novo_wx) + 8, int(novo_wy) + 8, TAMANHO_TILE - 16, TAMANHO_TILE - 16)

        # Se NÃO for colidir, realiza a mudança na lógica
        if not self.world.colide_com_arvore(test_rect):
            if self.tronco_atual and key in [pygame.K_a, pygame.K_d]:
                novo_slot = self.slot_atual + (1 if key == pygame.K_d else -1)
                if 0 <= novo_slot < self.tronco_atual.num_slots:
                    self.slot_atual = novo_slot
                    self.wx = self.tronco_atual.slot_x_mundo(self.slot_atual)
                else:
                    self.tronco_atual = None
                    self.wx = novo_wx
            else:
                self.wx, self.wy = novo_wx, novo_wy
                self.tronco_atual = None

                self.wx, self.wy = novo_wx, novo_wy

                nova_linha = int(self.wy // TAMANHO_TILE)
                tipo = self.world.gerar_tile(nova_linha, self.score)[1]
                nova_linha = int(self.wy // TAMANHO_TILE)
                bioma = self.world.fixar_bioma_linha(nova_linha, self.score)

                if tipo == TIPO_GRAMA and bioma == "grama":
                    som = assets.sons.get("passo_grama")
                    if som:
                        som.play()
                elif tipo == TIPO_ESTRADA:
                    som = assets.sons.get("passo_asfalto")
                    if som:
                        som.play()
                elif bioma == "areia" and tipo == TIPO_GRAMA:
                    som = assets.sons.get("passo_areia")
                    if som:
                        som.play()
                elif bioma == "gelo" and tipo == TIPO_GRAMA:
                    som = assets.sons.get("passo_neve")
                    if som:
                        som.play()


        # Restrição de margens
        self.wx = clamp(self.wx, 0.0, float(LARGURA - TAMANHO_TILE))

        # --- GERAÇÃO DO OFFSET DE TWEENING ---
        delta_x = old_wx - self.wx
        delta_y = old_wy - self.wy

        # Se houve alguma mudança real de posição (não trombou na parede nem em árvore)
        if delta_x != 0 or delta_y != 0:
            # Salva o eixo para definir qual lado achata na animação
            self.last_move_axis = 'x' if abs(delta_x) > abs(delta_y) else 'y'

            # Se já estava em transição (inputs enfileirados muito rápidos),
            # não cancelamos, apenas acumulamos o offset restante do antigo com o novo!
            tempo_passado = agora - self.anim_start
            if tempo_passado < self.anim_duracao:
                t = tempo_passado / self.anim_duracao
                frac = (1 - t) ** 2  # Usamos quadratica (Ease-Out)
                self.visual_offset_x = self.visual_offset_x * frac + delta_x
                self.visual_offset_y = self.visual_offset_y * frac + delta_y
            else:
                self.visual_offset_x = delta_x
                self.visual_offset_y = delta_y

            self.anim_start = agora

            # Atualização de pontuação acontece junto da aprovação do movimento lógico
            nova_linha = int(self.wy // TAMANHO_TILE)
            if nova_linha < self.linha_recorde:
                self.linha_recorde = nova_linha
                self.score += 2 if agora < self.xp2_ate else 1

    def update(self, agora):
        self.process_input(agora)
        player_linha = int(self.wy // TAMANHO_TILE)
        tipo = self.world.gerar_tile(player_linha)[1]

        prect_mundo = self.world_rect()
        for pu in self.world.powerups_ativos:
            if not pu.coletado and prect_mundo.colliderect(pu.rect_mundo()):
                pu.coletado = True
                if pu.tipo == "escudo":
                    self.tem_escudo = True
                elif pu.tipo == "xp2":
                    self.xp2_ate = agora + POWERUP_XP2_DURACAO_MS

        if tipo == TIPO_RIO and not self.world.rio_congelado(self.score):
            ld = self.world.lane_data.get(player_linha, {})
            if ld.get("modo_rio") == "vitoria_regia":
                self.tronco_atual = None
            elif self.tronco_atual:
                target_x = self.tronco_atual.slot_x_mundo(self.slot_atual)
                self.wx = clamp(target_x, 0.0, float(LARGURA - TAMANHO_TILE))

                if self.tronco_atual.x > self.wx + 20 or self.tronco_atual.x + self.tronco_atual.largura < self.wx + 20:
                    self.tronco_atual = None

            for t in [tr for tr in self.world.troncos_ativos if tr.linha == player_linha]:
                if t.x <= self.wx < t.x + t.largura:
                    if self.tronco_atual != t:
                        if t.tipo == "crocodilo":
                            som = assets.sons.get("passo_jacare")
                        else:
                            som = assets.sons.get("passo_madeira")

                        if som:
                            som.play()

                    self.tronco_atual, self.slot_atual = t, t.slot_do_x(self.wx)
                    self.wx = t.slot_x_mundo(self.slot_atual)
                    break
        else:
            self.tronco_atual = None

    def draw(self, surface, camera_y, agora):
        # --- CÁLCULO DA POSIÇÃO VISUAL (TWEENING + SQUASH) ---
        cur_offset_x = 0
        cur_offset_y = 0
        img_to_draw = self.imagem
        dx, dy = 0, 0  # Compensação para centralizar a imagem após distorção

        tempo_anim = agora - self.anim_start
        if tempo_anim < self.anim_duracao:
            # t = Progresso da animação (0 a 1)
            t = tempo_anim / self.anim_duracao
            frac = (1 - t) ** 2  # Efeito Ease-Out (Rápido no começo, suave no fim)

            cur_offset_x = self.visual_offset_x * frac
            cur_offset_y = self.visual_offset_y * frac

            # Distorção Squash and Stretch (curva parabólica que atinge pico de 25% no meio da animação t=0.5)
            deform = 4 * t * (1 - t) * 0.25

            if self.last_move_axis == 'x':
                scale_x = int(TAMANHO_TILE * (1 + deform))
                scale_y = int(TAMANHO_TILE * (1 - deform))
            else:
                scale_x = int(TAMANHO_TILE * (1 - deform))
                scale_y = int(TAMANHO_TILE * (1 + deform))

            img_to_draw = pygame.transform.scale(self.imagem, (scale_x, scale_y))
            dx = (TAMANHO_TILE - scale_x) // 2
            dy = (TAMANHO_TILE - scale_y) // 2
        else:
            self.visual_offset_x = 0
            self.visual_offset_y = 0

        # Aplica o offset puramente estético na lógica real
        px = int(self.wx + cur_offset_x) + dx
        py = int(self.wy + cur_offset_y - camera_y) + dy

        # Centro do personagem para desenhar as auras e escudos no lugar certo
        cx = int(self.wx + cur_offset_x)
        cy = int(self.wy + cur_offset_y - camera_y)

        # Desenha a barra flutuante em cima do tronco
        if self.tronco_atual:
            sy_t = int(self.tronco_atual.linha * TAMANHO_TILE - camera_y)
            for s in range(self.tronco_atual.num_slots):
                sx_slot = int(self.tronco_atual.slot_x_mundo(s))
                cor = (255, 255, 100, 160) if s == self.slot_atual else (255, 255, 255, 60)
                indicador = pygame.Surface((TAMANHO_TILE - 8, 4), pygame.SRCALPHA)
                indicador.fill(cor)
                surface.blit(indicador, (sx_slot + 4, sy_t + TAMANHO_TILE - 6))

        # Desenha Escudo / Graça de morte / Personagem Normal
        if self.tem_escudo:
            aura = pygame.Surface((TAMANHO_TILE + 16, TAMANHO_TILE + 16), pygame.SRCALPHA)
            pulso = int(120 + 80 * abs((agora % 600) / 300.0 - 1))
            pygame.draw.circle(aura, (255, 220, 60, pulso), (TAMANHO_TILE // 2 + 8, TAMANHO_TILE // 2 + 8),
                               TAMANHO_TILE // 2 + 6)
            surface.blit(aura, (cx - 8, cy - 8))
            surface.blit(img_to_draw, (px, py))
        elif agora < self.graca_ate:
            if (agora // 80) % 2 == 0: surface.blit(img_to_draw, (px, py))
        else:
            surface.blit(img_to_draw, (px, py))


class Carro:
    def __init__(self, linha, x, velocidade, direcao, img):
        self.linha, self.x, self.velocidade, self.direcao, self.img = linha, x, velocidade, direcao, img
        self.largura = img.get_width()

    def update(self): self.x += self.velocidade * self.direcao

    def screen_y(self, camera_y): return int(self.linha * TAMANHO_TILE - camera_y)

    def rect(self, camera_y): return pygame.Rect(int(self.x) + 4, self.screen_y(camera_y) + 4, self.largura - 8,
                                                 TAMANHO_TILE - 8)


class Tronco:
    def __init__(self, linha, x, velocidade, direcao, num_slots, tipo="tronco"):
        self.linha, self.x, self.velocidade, self.direcao, self.num_slots = linha, float(
            x), velocidade, direcao, num_slots
        self.largura = num_slots * TAMANHO_TILE
        self.tipo = tipo
        banco = assets.images['troncos'] if tipo == "tronco" else assets.images['crocodilos']
        banco_flip = assets.images['troncos_flip'] if tipo == "tronco" else assets.images['crocodilos_flip']
        self.img = banco[num_slots] if direcao == 1 else banco_flip[num_slots]

    def update(self): self.x += self.velocidade * self.direcao

    def slot_x_mundo(self, slot): return self.x + slot * TAMANHO_TILE

    def slot_do_x(self, wx): return max(0, min(self.num_slots - 1, round((wx - self.x) / TAMANHO_TILE)))


def _px_arvore(surf, gx, gy, color, scale=3, dy=0):
    py = (gy + dy) * scale
    if 0 <= py < TAMANHO_TILE - scale + 1:
        surf.fill(color, (gx * scale, py, scale, scale))


def _desenhar_arvore_grama(surf):
    """Carvalho em pixel art — copa contida no tile, sem contorno no ápice."""
    S = 3
    DY = 2
    SHADOW = (34, 58, 30)
    TRUNK_D = (92, 58, 34)
    TRUNK_M = (122, 78, 46)
    TRUNK_L = (158, 104, 62)
    LEAF_D = (44, 98, 52)
    LEAF_M = (68, 138, 72)
    LEAF_L = (98, 176, 92)
    LEAF_HI = (138, 206, 118)
    OUTLINE = (28, 48, 28)

    for gx in range(5, 11):
        _px_arvore(surf, gx, 13, SHADOW, S, DY)

    for gy in range(9, 13):
        for gx in range(7, 9):
            _px_arvore(surf, gx, gy, TRUNK_D if gx == 7 else TRUNK_M, S, DY)
    _px_arvore(surf, 7, 8, TRUNK_L, S, DY)
    _px_arvore(surf, 8, 10, TRUNK_L, S, DY)

    canopy = [
        (5, 5, LEAF_D), (6, 5, LEAF_D), (10, 5, LEAF_D), (11, 5, LEAF_D),
        (4, 6, LEAF_D), (5, 6, LEAF_M), (6, 6, LEAF_M), (7, 6, LEAF_L), (8, 6, LEAF_L),
        (9, 6, LEAF_M), (10, 6, LEAF_M), (11, 6, LEAF_D), (12, 6, LEAF_D),
        (4, 7, LEAF_M), (5, 7, LEAF_L), (6, 7, LEAF_HI), (7, 7, LEAF_HI), (8, 7, LEAF_HI),
        (9, 7, LEAF_L), (10, 7, LEAF_M), (11, 7, LEAF_D),
        (5, 8, LEAF_M), (6, 8, LEAF_L), (7, 8, LEAF_M), (8, 8, LEAF_L), (9, 8, LEAF_M), (10, 8, LEAF_D),
        (6, 4, LEAF_HI), (7, 4, LEAF_HI), (8, 4, LEAF_HI),
    ]
    for gx, gy, col in canopy:
        _px_arvore(surf, gx, gy, col, S, DY)

    for gx, gy in [(4, 6), (11, 6), (5, 5), (10, 5), (3, 7), (12, 7)]:
        _px_arvore(surf, gx, gy, OUTLINE, S, DY)


def _desenhar_arvore_cacto(surf):
    """Saguaro em pixel art — braços e corpo dentro do tile."""
    S = 3
    DY = 2
    DARK = (52, 108, 58)
    MID = (74, 142, 78)
    LIGHT = (108, 178, 102)
    HI = (142, 208, 128)
    OUTLINE = (34, 72, 42)
    SPIKE = (198, 188, 120)
    SAND = (194, 162, 108)

    for gx in range(5, 11):
        _px_arvore(surf, gx, 13, SAND, S, DY)

    for gy in range(5, 12):
        for gx in range(7, 9):
            _px_arvore(surf, gx, gy, MID if gy < 10 else DARK, S, DY)
    _px_arvore(surf, 7, 4, LIGHT, S, DY)
    _px_arvore(surf, 8, 4, HI, S, DY)

    for gx, gy in [(4, 8), (4, 7), (5, 7), (5, 6), (6, 6)]:
        _px_arvore(surf, gx, gy, LIGHT if gy <= 7 else MID, S, DY)
    for gx, gy in [(10, 9), (10, 8), (9, 8), (9, 7), (8, 7)]:
        _px_arvore(surf, gx, gy, LIGHT if gy <= 8 else MID, S, DY)

    for gx, gy in [(6, 7), (9, 8), (7, 3), (8, 10)]:
        _px_arvore(surf, gx, gy, HI, S, DY)

    for gx, gy in [(3, 8), (11, 9), (7, 12), (8, 12), (6, 6), (9, 7)]:
        _px_arvore(surf, gx, gy, OUTLINE, S, DY)

    for gx, gy in [(5, 6), (6, 5), (9, 7), (8, 6), (7, 8), (8, 8)]:
        _px_arvore(surf, gx, gy, SPIKE, S, DY)


def _desenhar_arvore_gelo(surf):
    """Pinheiro nevado em pixel art."""
    S = 3
    DY = 2
    SNOW = (228, 238, 248)
    SNOW_SH = (188, 202, 220)
    PINE_D = (38, 82, 58)
    PINE_M = (54, 112, 74)
    PINE_L = (78, 148, 98)
    TRUNK_D = (82, 54, 36)
    TRUNK_L = (118, 78, 50)
    OUTLINE = (24, 48, 36)

    for gx, gy in [(7, 11), (8, 11), (7, 12), (8, 12)]:
        _px_arvore(surf, gx, gy, TRUNK_D, S, DY)
    _px_arvore(surf, 7, 10, TRUNK_L, S, DY)

    layers = [
        [(7, 4, PINE_L), (6, 5, PINE_M), (7, 5, PINE_L), (8, 5, PINE_L), (9, 5, PINE_M), (7, 5, SNOW)],
        [(5, 6, PINE_D), (6, 6, PINE_M), (7, 6, PINE_L), (8, 6, PINE_L), (9, 6, PINE_M), (10, 6, PINE_D),
         (6, 6, SNOW), (8, 6, SNOW)],
        [(5, 8, PINE_M), (6, 8, PINE_L), (7, 8, PINE_L), (8, 8, PINE_L), (9, 8, PINE_M), (7, 8, SNOW_SH)],
    ]
    for layer in layers:
        for gx, gy, col in layer:
            _px_arvore(surf, gx, gy, col, S, DY)

    for gx, gy in [(5, 6), (10, 6), (4, 8), (11, 8)]:
        _px_arvore(surf, gx, gy, OUTLINE, S, DY)


class Arvore:
    def __init__(self, linha, wx, nascida_em=0):
        self.linha, self.wx, self.wy, self.nascida_em = linha, float(wx), float(linha * TAMANHO_TILE), nascida_em

    def world_rect(self):
        return pygame.Rect(int(self.wx) + 8, int(self.wy) + 8, TAMANHO_TILE - 16, TAMANHO_TILE - 16)

    def draw(self, surface, camera_y, agora, bioma):
        sy = int(self.wy - camera_y)
        if -TAMANHO_TILE <= sy <= ALTURA:
            surf = pygame.Surface((TAMANHO_TILE, TAMANHO_TILE), pygame.SRCALPHA)
            tempo = max(0, agora - self.nascida_em)
            alpha = int(255 * (tempo / ARVORE_APARECIMENTO_MS)) if tempo < ARVORE_APARECIMENTO_MS else 255

            if bioma == "areia":
                _desenhar_arvore_cacto(surf)
            elif bioma == "gelo":
                _desenhar_arvore_gelo(surf)
            else:
                _desenhar_arvore_grama(surf)

            surf.set_alpha(alpha)
            surface.blit(surf, (int(self.wx), sy))