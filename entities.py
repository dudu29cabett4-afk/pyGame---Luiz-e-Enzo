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
        sy = int(self.wy - camera_y) + (TAMANHO_TILE - self.TAMANHO) // 2
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
        self.anim_duracao = 100  # Duração da transição em milissegundos
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
            else:
                for t in [tr for tr in self.world.troncos_ativos if tr.linha == player_linha]:
                    if t.x <= self.wx < t.x + t.largura:
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
        banco = assets.images['troncos'] if tipo == "tronco" else assets.images['crocodilos']
        banco_flip = assets.images['troncos_flip'] if tipo == "tronco" else assets.images['crocodilos_flip']
        self.img = banco[num_slots] if direcao == 1 else banco_flip[num_slots]

    def update(self): self.x += self.velocidade * self.direcao

    def slot_x_mundo(self, slot): return self.x + slot * TAMANHO_TILE

    def slot_do_x(self, wx): return max(0, min(self.num_slots - 1, round((wx - self.x) / TAMANHO_TILE)))


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
            cx = TAMANHO_TILE // 2

            if bioma == "areia":
                pygame.draw.rect(surf, (60, 140, 60), (cx - 4, 8, 8, 32), border_radius=4)
                pygame.draw.rect(surf, (60, 140, 60), (cx - 10, 16, 6, 6), border_radius=3)
                pygame.draw.rect(surf, (60, 140, 60), (cx + 4, 20, 6, 6), border_radius=3)
                pygame.draw.rect(surf, (110, 70, 35), (cx - 3, 38, 6, 6), border_radius=2)
            elif bioma == "gelo":
                pygame.draw.polygon(surf, (50, 120, 60), [(cx, 4), (cx - 14, 34), (cx + 14, 34)])
                pygame.draw.rect(surf, (110, 70, 35), (cx - 4, 34, 8, 10), border_radius=2)
            else:
                pygame.draw.circle(surf, (40, 150, 50), (cx, 18), 12)
                pygame.draw.rect(surf, (110, 70, 35), (cx - 4, 24, 8, 20), border_radius=3)

            surf.set_alpha(alpha)
            surface.blit(surf, (int(self.wx), sy))