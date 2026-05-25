# entities.py
# Aqui ficam isoladas as classes das Entidades: Jogador, Inimigos, Partículas, PowerUps.
# Cada entidade é um objeto (POO) com estado (posição x, y, velocidade, etc) e comportamento (draw, update).

import pygame
import random
import assets
from config import *
from utils import clamp


class Particle:
    # Simples objeto que cria um "círculo que desaparece", usado em colisões ou efeitos visuais.
    def __init__(self, x, y, vx, vy, color, duration, radius):
        self.x, self.y, self.vx, self.vy, self.color, self.duration, self.radius = x, y, vx, vy, color, duration, radius
        self.born = pygame.time.get_ticks()  # Registra o exato milissegundo de nascimento
        max_r = int(self.radius * 2)
        # SRCALPHA permite criar superfícies (imagens virtuais) que suportam transparência PNG (Alpha Channel).
        self.surf = pygame.Surface((max_r * 2, max_r * 2), pygame.SRCALPHA)

    def update(self, dt):
        # A movimentação multiplica pela velocidade da partícula "vx" e "vy" vezes o dt (Delta Time).
        self.x += self.vx * dt
        self.y += self.vy * dt

    def draw(self, surface, camera_y, agora):
        age = agora - self.born
        if age > self.duration:
            return False  # Morreu, retorna Falso pra lista principal limpar ele

        # O alpha começa em 255 (sólido) e chega a 0 (invisível) progressivamente conforme a partícula envelhece.
        frac = 1 - (age / self.duration)
        alpha = int(255 * frac)
        r = int(self.radius * (1 + (1 - frac)))
        self.surf.fill((0, 0, 0, 0))  # Limpa o frame anterior da Surface interna
        pygame.draw.circle(self.surf, (*self.color[:3], alpha), (r, r), r)
        surface.blit(self.surf, (int(self.x) - r, int(self.y - camera_y) - r))
        return True


class Fumaca:
    # Mesma ideia de Partícula, mas programada especificamente para parecer Fumaça de escapamento dos carros.
    def __init__(self, wx, wy, vx, vy, nascida_em):
        self.wx, self.wy, self.vx, self.vy, self.nascida_em = wx, wy, vx, vy, nascida_em
        self.duracao, self.raio = random.randint(450, 700), random.randint(4, 6)
        max_r = self.raio + 5
        self.surf = pygame.Surface((max_r * 4, max_r * 4), pygame.SRCALPHA)

    def expirou(self, agora):
        return agora - self.nascida_em > self.duracao

    def draw(self, surface, camera_y, agora):
        idade = agora - self.nascida_em
        if 0 <= idade <= self.duracao:
            frac = idade / self.duracao
            sx, sy = int(self.wx + self.vx * idade), int(self.wy + self.vy * idade - camera_y)
            if -30 <= sy <= ALTURA + 30:  # Otimização: Apenas desenha na tela se estiver na região da visão da câmera
                raio = int(self.raio + frac * 5)
                alpha = int(140 * (1.0 - frac))
                self.surf.fill((0, 0, 0, 0))
                pygame.draw.circle(self.surf, (210, 210, 210, alpha), (raio * 2, raio * 2), raio)
                pygame.draw.circle(self.surf, (240, 240, 240, max(0, alpha - 40)), (raio * 2 - 2, raio * 2 - 2),
                                   max(1, raio - 1))
                surface.blit(self.surf, (sx - raio * 2, sy - raio * 2))


class PowerUp:
    # A classe de Itens que dão bônus à Raposa. Encapsula sua hitbox (retângulo de mundo)
    # e lógica de brilho "pulsante".
    TAMANHO = 36

    def __init__(self, wx, wy, tipo):
        self.wx, self.wy, self.tipo, self.coletado = wx, wy, tipo, False
        self.glow_surf = pygame.Surface((self.TAMANHO + 16, self.TAMANHO + 16), pygame.SRCALPHA)
        glow_cor = (255, 190, 70) if self.tipo == "xp2" else (255, 230, 80)
        pygame.draw.circle(self.glow_surf, glow_cor, (self.TAMANHO // 2 + 8, self.TAMANHO // 2 + 8),
                           self.TAMANHO // 2 + 6)

    def rect_mundo(self):
        # Cria a Hitbox, permitindo que a classe `Player` interaja com o PowerUp via pygame.Rect()
        m = 6
        return pygame.Rect(int(self.wx) + m, int(self.wy) + m, TAMANHO_TILE - m * 2, TAMANHO_TILE - m * 2)

    def draw(self, surface, camera_y):
        if self.coletado:
            return
        sx = int(self.wx) + (TAMANHO_TILE - self.TAMANHO) // 2
        sy = int(self.wy - camera_y) + (TAMANHO_TILE - self.TAMANHO) // 2 - 3
        if -self.TAMANHO <= sy <= ALTURA:
            t = pygame.time.get_ticks()
            # Fórmula de animação para "Glow" (Piscar de claridade) no tempo de jogo.
            alpha = int(120 + 80 * abs((t % 800) / 400.0 - 1))
            icon = assets.images['pu_xp2'] if self.tipo == "xp2" else assets.images['pu_escudo']
            self.glow_surf.set_alpha(alpha)
            surface.blit(self.glow_surf, (sx - 8, sy - 8))
            surface.blit(icon, (sx, sy))


class Lilypad:
    # A Vitória-Régia no rio.
    def __init__(self, linha, wx, img):
        self.linha = linha
        self.wx = float(wx)
        self.wy = float(linha * TAMANHO_TILE)
        self.img = img
        self.recuo_ate = 0
        self.recuo_dx = 0.0

    def pisada(self, agora):
        # Quando a Raposa pisa sobre ela, balança.
        self.recuo_ate = agora + RECUO_DURACAO_MS
        self.recuo_dx = float(RECUO_PIXELS)

    def offset_desenho(self, agora):
        if agora >= self.recuo_ate:
            return 0.0
        t = 1.0 - (self.recuo_ate - agora) / RECUO_DURACAO_MS
        return self.recuo_dx * t

    def rect_mundo(self):
        return pygame.Rect(int(self.wx) + 4, int(self.wy) + 4, TAMANHO_TILE - 8, TAMANHO_TILE - 8)

    def draw(self, surface, camera_y, agora):
        sy = int(self.wy - camera_y)
        ox = int(self.offset_desenho(agora))
        if -TAMANHO_TILE <= sy <= ALTURA and self.img:
            surface.blit(self.img, (int(self.wx) + ox, sy))


class Player:
    # A classe mais extensa: controla inteiramente a entidade física que o usuário maneja.
    def __init__(self, world, cor_skin="verde"):
        self.world = world  # Ela salva uma "referência" do mundo principal para extrair colisões
        self.linha = int(PLAYER_ALVO_Y // TAMANHO_TILE)
        self.wx = float((LARGURA // TAMANHO_TILE // 2) * TAMANHO_TILE)
        self.wy = float(self.linha * TAMANHO_TILE)

        self.skin = assets.images['personagens'].get(cor_skin, assets.images['personagens']['verde'])
        self.imagem = self.skin['frente']

        # Fila de comandos: Buffer permite que se apertarmos "W" rápido duas vezes, os movimentos sejam armazenados e lidos.
        self.input_buffer = []
        self.score = 0
        self.linha_recorde = self.linha

        # Status especiais da Raposa:
        self.tem_escudo = False
        self.graca_ate = 0
        self.xp2_ate = 0
        self.tronco_atual = None
        self.slot_atual = 0
        self.lily_col_atual = None

        # Atributos de Animação de Movimento fluido (easing visual) em grid.
        self.anim_start = 0
        self.anim_duracao = 120
        self.visual_offset_x = 0.0
        self.visual_offset_y = 0.0
        self.last_move_axis = 'y'

        self.ind_ativo = pygame.Surface((TAMANHO_TILE - 8, 4), pygame.SRCALPHA)
        self.ind_ativo.fill((255, 255, 100, 160))
        self.ind_inativo = pygame.Surface((TAMANHO_TILE - 8, 4), pygame.SRCALPHA)
        self.ind_inativo.fill((255, 255, 255, 60))

        self.aura_escudo = pygame.Surface((TAMANHO_TILE + 16, TAMANHO_TILE + 16), pygame.SRCALPHA)
        pygame.draw.circle(self.aura_escudo, (255, 220, 60), (TAMANHO_TILE // 2 + 8, TAMANHO_TILE // 2 + 8),
                           TAMANHO_TILE // 2 + 6)

    def rect(self, camera_y):
        # Hitbox (caixa de detecção) baseada na tela do usuário (Screen Space) para interagir com câmera/carros
        return pygame.Rect(
            int(self.wx + self.visual_offset_x) + HITBOX_PLAYER_INSET,
            int(self.wy + self.visual_offset_y - camera_y) + HITBOX_PLAYER_INSET,
            TAMANHO_TILE - HITBOX_PLAYER_INSET * 2,
            TAMANHO_TILE - HITBOX_PLAYER_INSET * 2
        )

    def world_rect(self):
        # Hitbox baseada apenas no Mundo do jogo (World Space), usada para colidir em árvores
        return pygame.Rect(
            int(self.wx + self.visual_offset_x) + 8,
            int(self.wy + self.visual_offset_y) + 8,
            TAMANHO_TILE - 16, TAMANHO_TILE - 16
        )

    def queue_input(self, key):
        if len(self.input_buffer) < 2:
            self.input_buffer.append(key)

    def _posicao_segura_para_pontuar(self, linha):
        # Impede o jogador de ganhar ponto se for pular e morrer de imediato no momento em que chega na linha.
        tipo = self.world.gerar_tile(linha, self.score)[1]
        if tipo == TIPO_GRAMA:
            rect = pygame.Rect(int(self.wx) + 8, linha * TAMANHO_TILE + 8, TAMANHO_TILE - 16, TAMANHO_TILE - 16)
            return not self.world.colide_com_arvore(rect)
        if tipo == TIPO_ESTRADA:
            prect = pygame.Rect(int(self.wx) + 8, linha * TAMANHO_TILE + 8, TAMANHO_TILE - 16, TAMANHO_TILE - 16)
            for c in self.world.carros_ativos:
                if c.linha != linha:
                    continue
                car_rect = pygame.Rect(int(c.x) + 4, linha * TAMANHO_TILE + 4, c.largura - 8, TAMANHO_TILE - 8)
                if car_rect.colliderect(prect):
                    return False
            return True
        if tipo == TIPO_RIO:
            col = int(self.wx // TAMANHO_TILE)
            em_vitoria = any(
                int(v.wx // TAMANHO_TILE) == col for v in self.world.vitorias_ativas if v.linha == linha
            )
            em_tronco = any(
                t.linha == linha and t.tipo == "tronco" and t.aceita_embarque(self.wx)
                for t in self.world.troncos_ativos
            )
            return em_vitoria or em_tronco
        return False

    def process_input(self, agora):
        # Retira o teclado da fila e projeta a nova posição da Raposa.
        if not self.input_buffer:
            return
        key = self.input_buffer.pop(0)

        old_wx, old_wy = self.wx, self.wy
        novo_wx, novo_wy = self.wx, self.wy

        if key == pygame.K_w:
            novo_wy -= TAMANHO_TILE
            self.imagem = self.skin['costas']
            novo_wx = round(novo_wx / TAMANHO_TILE) * TAMANHO_TILE
        elif key == pygame.K_s:
            novo_wy += TAMANHO_TILE
            self.imagem = self.skin['frente']
            novo_wx = round(novo_wx / TAMANHO_TILE) * TAMANHO_TILE
        elif key == pygame.K_a:
            novo_wx -= TAMANHO_TILE
            self.imagem = self.skin['esquerda']
        elif key == pygame.K_d:
            novo_wx += TAMANHO_TILE
            self.imagem = self.skin['direita']

        test_rect = pygame.Rect(int(novo_wx) + 8, int(novo_wy) + 8, TAMANHO_TILE - 16, TAMANHO_TILE - 16)

        if not self.world.colide_com_arvore(test_rect):
            # Lógica extra pra movimentação se o jogador estiver "grudado" em cima de um Tronco
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
                bioma = self.world.fixar_bioma_linha(nova_linha, self.score)

                # Avalia o tipo de terreno do bloco, pra tocar o efeito sonoro de Passo adequado!
                som_tocar = None
                if tipo == TIPO_GRAMA:
                    if bioma == "floresta":
                        lista_sons = assets.sons['passos'].get('floresta')
                        if lista_sons:
                            som_tocar = random.choice(lista_sons)
                    elif bioma == "deserto":
                        lista_sons = assets.sons['passos'].get('deserto')
                        if lista_sons:
                            som_tocar = random.choice(lista_sons)
                    elif bioma == "urbano":
                        som_tocar = assets.sons['passos'].get('terra')
                elif tipo == TIPO_ESTRADA:
                    som_tocar = assets.sons['passos'].get('rua')
                elif tipo == TIPO_RIO:
                    som_tocar = assets.sons['passos'].get('agua')

                if som_tocar:
                    som_tocar.play()

        # O Clamp impede que ele saia vazando pra esquerda ou direita pela borda da tela.
        self.wx = clamp(self.wx, 0.0, float(LARGURA - TAMANHO_TILE))

        delta_x = old_wx - self.wx
        delta_y = old_wy - self.wy

        if delta_x != 0 or delta_y != 0:
            # Equação para calcular Easing de Movimento (fração). Deixa o andar dele "vivo" e elástico, não duro.
            self.last_move_axis = 'x' if abs(delta_x) > abs(delta_y) else 'y'
            tempo_passado = agora - self.anim_start
            if tempo_passado < self.anim_duracao:
                t = tempo_passado / self.anim_duracao
                frac = (1 - t) ** 2
                self.visual_offset_x = self.visual_offset_x * frac + delta_x
                self.visual_offset_y = self.visual_offset_y * frac + delta_y
            else:
                self.visual_offset_x = delta_x
                self.visual_offset_y = delta_y
            self.anim_start = agora

            nova_linha = int(self.wy // TAMANHO_TILE)
            if nova_linha < self.linha_recorde and self._posicao_segura_para_pontuar(nova_linha):
                self.linha_recorde = nova_linha
                self.score += 2 if agora < self.xp2_ate else 1

    def _atualizar_lilypad(self, player_linha, agora):
        col = int(self.wx // TAMANHO_TILE)
        lily = None
        for v in self.world.vitorias_ativas:
            if v.linha == player_linha and int(v.wx // TAMANHO_TILE) == col:
                lily = v
                break
        if lily:
            if self.lily_col_atual != col:
                lily.pisada(agora)
            self.lily_col_atual = col
        else:
            self.lily_col_atual = None

    def update(self, agora):
        self.process_input(agora)
        player_linha = int(self.wy // TAMANHO_TILE)
        tipo = self.world.gerar_tile(player_linha, self.score)[1]

        # Verifica coletas de itens na tela (Interação Entidade-Entidade)
        prect_mundo = self.world_rect()
        for pu in self.world.powerups_ativos:
            if not pu.coletado and prect_mundo.colliderect(pu.rect_mundo()):
                pu.coletado = True
                if pu.tipo == "escudo":
                    self.tem_escudo = True
                    som = assets.sons['powerups'].get('escudo')
                    if som:
                        som.play()
                elif pu.tipo == "xp2":
                    self.xp2_ate = agora + POWERUP_XP2_DURACAO_MS
                    som = assets.sons['powerups'].get('bonus_2x')
                    if som:
                        som.play()

        # Verifica se o jogador subiu num tronco
        if tipo == TIPO_RIO:
            ld = self.world.lane_data.get(player_linha, {})
            if ld.get("modo_rio") == "vitoria_regia":
                self.tronco_atual = None
                self._atualizar_lilypad(player_linha, agora)
            else:
                self.lily_col_atual = None
                if self.tronco_atual:
                    target_x = self.tronco_atual.slot_x_mundo(self.slot_atual)
                    self.wx = clamp(target_x, 0.0, float(LARGURA - TAMANHO_TILE))
                    if not self.tronco_atual.aceita_embarque(self.wx):
                        self.tronco_atual = None

                for t in [tr for tr in self.world.troncos_ativos if tr.linha == player_linha]:
                    if t.aceita_embarque(self.wx):
                        if self.tronco_atual != t:
                            if t.tipo == "tronco":
                                som = assets.sons['passos'].get('tronco')
                                if som:
                                    som.play()
                            t.pisada(agora)
                        self.tronco_atual, self.slot_atual = t, t.slot_do_x(self.wx)
                        self.wx = t.slot_x_mundo(self.slot_atual)
                        break
        else:
            self.tronco_atual = None
            self.lily_col_atual = None

    def draw(self, surface, camera_y, agora):
        cur_offset_x = 0
        cur_offset_y = 0
        img_to_draw = self.imagem
        dx, dy = 0, 0

        # Efeitos de esticar o sprite da raposa quando ela salta
        tempo_anim = agora - self.anim_start
        if tempo_anim < self.anim_duracao:
            t = tempo_anim / self.anim_duracao
            frac = (1 - t) ** 2
            cur_offset_x = self.visual_offset_x * frac
            cur_offset_y = self.visual_offset_y * frac
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

        px = int(self.wx + cur_offset_x) + dx
        py = int(self.wy + cur_offset_y - camera_y) + dy
        cx = int(self.wx + cur_offset_x)
        cy = int(self.wy + cur_offset_y - camera_y)

        # Se tiver na água num tronco, desenha o indicador verde no pé de qual slot de madeira ela está agarrada
        if self.tronco_atual:
            sy_t = int(self.tronco_atual.linha * TAMANHO_TILE - camera_y)
            for s in range(self.tronco_atual.num_slots):
                sx_slot = int(self.tronco_atual.slot_x_mundo(s))
                surf_ind = self.ind_ativo if s == self.slot_atual else self.ind_inativo
                surface.blit(surf_ind, (sx_slot + 4, sy_t + TAMANHO_TILE - 6))

        # Desenho final aplicando opacidades do Escudo ou Dano Temporário.
        if self.tem_escudo:
            pulso = int(120 + 80 * abs((agora % 600) / 300.0 - 1))
            self.aura_escudo.set_alpha(pulso)
            surface.blit(self.aura_escudo, (cx - 8, cy - 8))
            surface.blit(img_to_draw, (px, py))
        elif agora < self.graca_ate:
            if (agora // 80) % 2 == 0:  # Efeito "piscar" enquanto imortal (modulo 2 sobre o tempo)
                surface.blit(img_to_draw, (px, py))
        else:
            surface.blit(img_to_draw, (px, py))


class Carro:
    # Objeto inimigo clássico
    def __init__(self, linha, x, velocidade, direcao, img):
        self.linha, self.x, self.velocidade, self.direcao, self.img = linha, x, velocidade, direcao, img
        self.largura = img.get_width()

    def update(self, dt):
        self.x += self.velocidade * self.direcao * dt

    def screen_y(self, camera_y):
        return int(self.linha * TAMANHO_TILE - camera_y)

    def rect(self, camera_y):
        # A caixa de colisão do carro também tem uma redução interna (INSET) na hitbox,
        # para que fique amigável ao jogador escapar no pelo.
        return pygame.Rect(
            int(self.x) + HITBOX_CARRO_X_INSET,
            self.screen_y(camera_y) + HITBOX_CARRO_Y_INSET,
            self.largura - HITBOX_CARRO_X_INSET * 2,
            TAMANHO_TILE - HITBOX_CARRO_Y_INSET * 2
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
        self.recuo_ate = 0
        self.recuo_dx = 0.0
        self.img = self._montar_superficie()

    def _montar_superficie(self):
        # Gera visualmente troncos compridos mesclando a textura básica várias vezes
        surf = pygame.Surface((self.largura, TAMANHO_TILE), pygame.SRCALPHA)
        if self.tipo == "crocodilo":
            base = assets.images['rios']['jacare'] if self.direcao == 1 else assets.images['rios']['jacare_flip']
            base = pygame.transform.scale(base, (self.largura, TAMANHO_TILE))
            surf.blit(base, (0, 0))
        else:
            base = assets.images['rios']['tronco']
            for px in range(0, self.largura, TAMANHO_TILE):
                surf.blit(base, (px, 0))
        return surf

    def pisada(self, agora):
        self.recuo_ate = agora + RECUO_DURACAO_MS
        self.recuo_dx = -float(RECUO_PIXELS) if self.direcao == 1 else float(RECUO_PIXELS)

    def offset_desenho(self, agora):
        if agora >= self.recuo_ate:
            return 0.0
        t = 1.0 - (self.recuo_ate - agora) / RECUO_DURACAO_MS
        return self.recuo_dx * t

    def update(self, dt):
        self.x += self.velocidade * self.direcao * dt

    def slot_x_mundo(self, slot):
        return self.x + slot * TAMANHO_TILE

    def slot_do_x(self, wx):
        return max(0, min(self.num_slots - 1, round((wx - self.x) / TAMANHO_TILE)))

    def aceita_embarque(self, wx, tolerancia=TRONCO_EMBARQUE_TOLERANCIA):
        centro_jogador = wx + TAMANHO_TILE / 2
        return self.x - tolerancia <= centro_jogador <= self.x + self.largura + tolerancia

    def draw(self, surface, camera_y, agora):
        ox = int(self.offset_desenho(agora))
        sy = int(self.linha * TAMANHO_TILE - camera_y)
        surface.blit(self.img, (int(self.x) + ox, sy))


class Obstaculo:
    def __init__(self, linha, wx, img, nascida_em=0):
        self.linha = linha
        self.wx = float(wx)
        self.wy = float(linha * TAMANHO_TILE)
        self.img = img
        self.nascida_em = nascida_em

    def world_rect(self):
        return pygame.Rect(int(self.wx) + 8, int(self.wy) + 8, TAMANHO_TILE - 16, TAMANHO_TILE - 16)

    def draw(self, surface, camera_y, agora):
        sy = int(self.wy - camera_y)
        if -TAMANHO_TILE <= sy <= ALTURA:
            # Transição Fade-In do obstáculo na tela.
            tempo = max(0, agora - self.nascida_em)
            alpha = int(255 * (tempo / ARVORE_APARECIMENTO_MS)) if tempo < ARVORE_APARECIMENTO_MS else 255
            if self.img:
                if alpha < 255:
                    surf = self.img.copy()
                    surf.set_alpha(alpha)
                    surface.blit(surf, (int(self.wx), sy))
                else:
                    surface.blit(self.img, (int(self.wx), sy))