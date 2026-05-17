# world.py
import random
import pygame
from config import *
import assets
from entities import Carro, Tronco, Arvore, Particle, Fumaca, VitoriaRegia, PowerUp


class World:
    def __init__(self):
        self.tile_map = {}
        self.lane_data = {}
        self.bioma_cache = {}
        self.bioma_por_linha = {}

        self.carros_ativos = []
        self.troncos_ativos = []
        self.arvores_ativas = []
        self.vitorias_ativas = []
        self.powerups_ativos = []
        self.fumacas_ativas = []
        self.particles = []

        self.camera_y = 0
        self.camera_ativa = False

        for l in range(-5, 10): self.gerar_tile(l)

    def get_bioma(self, score):
        if score < 50: return "grama"
        if score < 100: return "areia"
        bucket = (score - 100) // CICLO_BIOMA_DURACAO
        if bucket not in self.bioma_cache:
            opcoes = [b for b in BIOMAS if b != self.bioma_cache.get(bucket - 1, "gelo")]
            self.bioma_cache[bucket] = random.choice(opcoes)
        return self.bioma_cache[bucket]

    def rio_congelado(self, score):
        return self.get_bioma(score) == "gelo"

    def fixar_bioma_linha(self, linha, score):
        if linha not in self.bioma_por_linha:
            self.bioma_por_linha[linha] = self.get_bioma(score)
        return self.bioma_por_linha[linha]

    def gerar_tile(self, linha):
        if linha not in self.tile_map:
            if linha >= -SAFE_ZONE_LINHAS:
                self.tile_map[linha] = (assets.images['grama'], TIPO_GRAMA)
            else:
                tipo = random.choices([TIPO_GRAMA, TIPO_ESTRADA, TIPO_RIO], weights=[3, 4, 1])[0]
                img = assets.images['grama'] if tipo == TIPO_GRAMA else (
                    assets.images['estrada'] if tipo == TIPO_ESTRADA else None)
                self.tile_map[linha] = (img, tipo)
        return self.tile_map[linha]

    def colide_com_arvore(self, rect):
        return any(a.world_rect().colliderect(rect) for a in self.arvores_ativas)

    def desenhar_grama_luxo(self, surface, y, bioma):
        cores = {"areia": (210, 180, 100), "gelo": (200, 230, 255)}
        if bioma in cores:
            pygame.draw.rect(surface, cores[bioma], (0, y, LARGURA, TAMANHO_TILE))
            for x in range(0, LARGURA, TAMANHO_TILE):
                if bioma == "areia":
                    pygame.draw.circle(surface, (190, 160, 80), (x + 12, y + 18), 3)
                elif bioma == "gelo":
                    pygame.draw.rect(surface, (100, 130, 110), (0, y, LARGURA, TAMANHO_TILE))
                    pygame.draw.ellipse(surface, (210, 230, 220), (x + 3, y + 5, 18, 8))
        else:
            for x in range(0, LARGURA, TAMANHO_TILE): surface.blit(assets.images['grama'], (x, y))

    def desenhar_agua_luxo(self, surface, sy, linha, dir):
        agua = pygame.Surface((LARGURA, TAMANHO_TILE), pygame.SRCALPHA)
        desloc = (pygame.time.get_ticks() // 60) % 30
        xs = range(-30 + desloc, LARGURA + 30, 30) if dir == 1 else range(LARGURA + 30 - desloc, -30, -30)
        for i, xi in enumerate(xs):
            yoff = 5 if i % 2 == 0 else 0
            pygame.draw.ellipse(agua, (180, 220, 255, 90), (xi, TAMANHO_TILE // 2 - 3 + yoff, 18, 6))
        surface.blit(agua, (0, sy))

    def spawn_entities(self, linha_ini, linha_fim, score, agora):
        for l in range(linha_ini, linha_fim + 1):
            tipo = self.gerar_tile(l)[1]
            bioma = self.fixar_bioma_linha(l, score)

            # --- Árvores e PowerUps (Garante que nunca caem no mesmo X) ---
            if tipo == TIPO_GRAMA and l < -SAFE_ZONE_LINHAS:
                colunas_ocupadas = set()

                # Chance adaptativa de Arvores
                chance_arvore = ARVORE_CHANCE_BASE + min(score / ARVORE_CHANCE_EXTRA_SCORE, ARVORE_CHANCE_EXTRA_MAX)
                if random.random() < chance_arvore:
                    if not any(a.linha == l for a in self.arvores_ativas):
                        wx = random.randint(1, (LARGURA // TAMANHO_TILE) - 2) * TAMANHO_TILE
                        self.arvores_ativas.append(Arvore(l, wx, agora))
                        colunas_ocupadas.add(wx)

                # Chance de Power-Up
                if len([p for p in self.powerups_ativos if not p.coletado]) < MAX_POWERUPS_ATIVOS:
                    if not any(p.wy // TAMANHO_TILE == l for p in self.powerups_ativos):
                        if random.random() < POWERUP_CHANCE_SPAWN:
                            colunas_livres = [c * TAMANHO_TILE for c in range(1, (LARGURA // TAMANHO_TILE) - 1) if
                                              c * TAMANHO_TILE not in colunas_ocupadas]
                            if colunas_livres:
                                wx = random.choice(colunas_livres)
                                pu_tipo = "escudo" if random.random() < 0.5 else "xp2"
                                self.powerups_ativos.append(PowerUp(wx, l * TAMANHO_TILE, pu_tipo))

            # --- Carros (Gaps Randômicos a cada spawn) ---
            if tipo == TIPO_ESTRADA:
                if l not in self.lane_data:
                    d = 1 if l % 2 == 0 else -1
                    self.lane_data[l] = {"dir": d, "v": random.uniform(4, 8), "next_x": -100 if d == 1 else LARGURA}

                ld = self.lane_data[l]
                ja_existem = [c for c in self.carros_ativos if c.linha == l]
                if not ja_existem:
                    img = random.choice(assets.images['carros_r'] if ld['dir'] == 1 else assets.images['carros_l'])
                    self.carros_ativos.append(Carro(l, ld['next_x'], ld['v'], ld['dir'], img))
                    ld['next_x'] += ld['dir'] * random.randint(200, 400)  # Gap dinamico
                else:
                    ultimo = max(ja_existem, key=lambda c: c.x * ld['dir'])
                    if (ld['dir'] == 1 and ultimo.x >= ld['next_x']) or (ld['dir'] == -1 and ultimo.x <= ld['next_x']):
                        img = random.choice(assets.images['carros_r'] if ld['dir'] == 1 else assets.images['carros_l'])
                        spawn_x = -100 if ld['dir'] == 1 else LARGURA
                        self.carros_ativos.append(Carro(l, spawn_x, ld['v'], ld['dir'], img))
                        ld['next_x'] += ld['dir'] * random.randint(200, 400)

            # --- Rio / Crocodilos (Quebrando o padrão) ---
            elif tipo == TIPO_RIO and not self.rio_congelado(score):
                if l not in self.lane_data:
                    d = 1 if l % 2 == 0 else -1
                    is_vitoria = random.random() < 0.35 and any(
                        self.gerar_tile(nl)[1] == TIPO_RIO for nl in [l - 1, l + 1])
                    self.lane_data[l] = {"dir": d, "v": random.uniform(2, 4), "next_x": -100 if d == 1 else LARGURA,
                                         "modo_rio": "vitoria_regia" if is_vitoria else "troncos"}

                ld = self.lane_data[l]
                if ld["modo_rio"] == "vitoria_regia":
                    if not any(v.linha == l for v in self.vitorias_ativas):
                        cols = sorted(random.sample(range(1, (LARGURA // TAMANHO_TILE) - 1), random.randint(2, 4)))
                        for c in cols: self.vitorias_ativas.append(
                            VitoriaRegia(l, c * TAMANHO_TILE + (TAMANHO_TILE - VitoriaRegia.TAMANHO) // 2))
                else:
                    ja_existem = [t for t in self.troncos_ativos if t.linha == l]
                    t_tipo = "crocodilo" if bioma == "areia" else "tronco"

                    if not ja_existem:
                        slots = random.choice(TRONCO_SLOTS_OPCOES)
                        self.troncos_ativos.append(Tronco(l, ld['next_x'], ld['v'], ld['dir'], slots, t_tipo))
                        ld['next_x'] += ld['dir'] * random.randint(150, 350)  # Gap e tamanho dinamicos
                    else:
                        ultimo = max(ja_existem, key=lambda c: c.x * ld['dir'])
                        if (ld['dir'] == 1 and ultimo.x >= ld['next_x']) or (
                                ld['dir'] == -1 and ultimo.x <= ld['next_x']):
                            slots = random.choice(TRONCO_SLOTS_OPCOES)
                            spawn_x = -(slots * TAMANHO_TILE) if ld['dir'] == 1 else LARGURA
                            self.troncos_ativos.append(Tronco(l, spawn_x, ld['v'], ld['dir'], slots, t_tipo))
                            ld['next_x'] += ld['dir'] * random.randint(150, 350)

    def update(self, player, score, agora):
        if player.wy < self.camera_y + PLAYER_ALVO_Y: self.camera_ativa = True
        vel_scroll = VEL_SCROLL_INICIAL + (VEL_SCROLL_MAX - VEL_SCROLL_INICIAL) * min(score / SCORE_PARA_MAX_VEL, 1.0)
        if self.camera_ativa: self.camera_y -= vel_scroll
        target_cam = player.wy - PLAYER_ALVO_Y
        if self.camera_y > target_cam: self.camera_y -= max(vel_scroll + 1.0, (self.camera_y - target_cam) * 0.22)

        linha_ini = int(self.camera_y // TAMANHO_TILE) - 1
        linha_fim = int((self.camera_y + ALTURA) // TAMANHO_TILE) + 1
        self.spawn_entities(linha_ini, linha_fim, score, agora)

        for c in self.carros_ativos:
            c.update()
            if random.random() < 0.35:
                wx = c.x + 4 if c.direcao == 1 else c.x + c.largura - 4
                vx = random.uniform(-0.02, -0.01) if c.direcao == 1 else random.uniform(0.01, 0.02)
                self.fumacas_ativas.append(
                    Fumaca(wx, c.linha * TAMANHO_TILE + TAMANHO_TILE - 8, vx, random.uniform(-0.03, -0.018), agora))

        for t in self.troncos_ativos: t.update()
        for p in self.particles: p.update()

        self.carros_ativos[:] = [c for c in self.carros_ativos if -200 <= c.x <= LARGURA + 200]
        self.troncos_ativos[:] = [t for t in self.troncos_ativos if -200 <= t.x <= LARGURA + 200]
        self.powerups_ativos[:] = [p for p in self.powerups_ativos if not p.coletado]
        self.fumacas_ativas[:] = [f for f in self.fumacas_ativas if not f.expirou(agora)]

    def check_death(self, player, agora):
        py_screen = player.wy - self.camera_y
        if py_screen >= ALTURA or py_screen < -TAMANHO_TILE: return True

        prect = player.rect(self.camera_y)
        tipo = self.gerar_tile(int(player.wy // TAMANHO_TILE))[1]

        golpe_fatal = False
        if tipo == TIPO_ESTRADA and any(c.rect(self.camera_y).colliderect(prect) for c in self.carros_ativos):
            golpe_fatal = True
            if not player.tem_escudo: self.particles.append(
                Particle(player.wx + 24, player.wy + 24, 0, 0, (255, 100, 0), 600, 20))
        elif tipo == TIPO_RIO and not self.rio_congelado(player.score):
            em_vitoria = any(v.rect_mundo().colliderect(player.world_rect()) for v in self.vitorias_ativas if
                             v.linha == int(player.wy // TAMANHO_TILE))
            if player.tronco_atual is None and not em_vitoria:
                golpe_fatal = True
                if not player.tem_escudo: self.particles.append(
                    Particle(player.wx + 24, player.wy + 24, 0, 0, (150, 200, 255), 600, 20))

        if golpe_fatal:
            if player.tem_escudo:
                player.tem_escudo = False
                player.graca_ate = agora + 600
                return False
            return True
        return False

    def draw(self, surface, score, agora):
        linha_ini = int(self.camera_y // TAMANHO_TILE) - 1
        linha_fim = int((self.camera_y + ALTURA) // TAMANHO_TILE) + 1

        for l in range(linha_ini, linha_fim + 1):
            sy = int(l * TAMANHO_TILE - self.camera_y)
            img, tipo = self.gerar_tile(l)
            bioma = self.fixar_bioma_linha(l, score)

            if tipo == TIPO_GRAMA:
                self.desenhar_grama_luxo(surface, sy, bioma)
            else:
                if img: surface.blit(img, (0, sy))
                if tipo == TIPO_RIO:
                    if self.rio_congelado(score):
                        pygame.draw.rect(surface, (210, 238, 255), (0, sy, LARGURA, TAMANHO_TILE))
                        pygame.draw.rect(surface, (235, 248, 255), (0, sy + TAMANHO_TILE // 2 - 5, LARGURA, 10))
                    else:
                        pygame.draw.rect(surface, (80, 170, 230), (0, sy, LARGURA, TAMANHO_TILE))
                        self.desenhar_agua_luxo(surface, sy, l, self.lane_data.get(l, {"dir": 1})["dir"])

        for v in self.vitorias_ativas: v.draw(surface, self.camera_y)
        for pu in self.powerups_ativos: pu.draw(surface, self.camera_y)
        for f in self.fumacas_ativas: f.draw(surface, self.camera_y, agora)
        for t in self.troncos_ativos: surface.blit(t.img, (int(t.x), int(t.linha * TAMANHO_TILE - self.camera_y)))
        for c in self.carros_ativos: surface.blit(c.img, (int(c.x), int(c.linha * TAMANHO_TILE - self.camera_y)))
        for a in self.arvores_ativas: a.draw(surface, self.camera_y, agora, self.fixar_bioma_linha(a.linha, score))
        self.particles[:] = [p for p in self.particles if p.draw(surface, self.camera_y, agora)]