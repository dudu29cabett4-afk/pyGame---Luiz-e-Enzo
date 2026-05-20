import random
import pygame
from config import *
import assets
from entities import Carro, Tronco, Arvore, Particle, Fumaca, VitoriaRegia, PowerUp
from utils import draw_text_outline, clamp


BIOMA_CORES = {
    "grama": (118, 178, 92),
    "areia": (204, 174, 96),
    "gelo": (188, 228, 248),
}

BIOMA_LABELS = {
    "grama": "GRAMA",
    "areia": "AREIA",
    "gelo": "GELO",
}

TRANSICAO_BIOMA_MS = 1300
TRANSICAO_BIOMA_ALTURA = 26
ARVORE_APARECIMENTO_VISUAL_MS = max(220, ARVORE_APARECIMENTO_MS // 2)


class World:
    def __init__(self):
        self.tile_map = {}
        self.lane_data = {}
        self.bioma_cache = {}
        self.bioma_por_linha = {}
        self.bioma_transicoes = []
        self.bioma_transicoes_vistas = set()

        self.carros_ativos = []
        self.troncos_ativos = []
        self.arvores_ativas = []
        self.vitorias_ativas = []
        self.powerups_ativos = []
        self.fumacas_ativas = []
        self.particles = []

        self.camera_y = 0
        self.camera_ativa = False

        for l in range(-5, 10):
            self.gerar_tile(l)

    def _bioma_cor(self, bioma):
        return BIOMA_CORES.get(bioma, BIOMA_CORES["grama"])

    def _bioma_texto(self, bioma):
        return BIOMA_LABELS.get(bioma, bioma.upper())

    def _registrar_transicao_bioma(self, linha, bioma_anterior, bioma_atual):
        chave = (linha, bioma_anterior, bioma_atual)
        if chave in self.bioma_transicoes_vistas:
            return
        self.bioma_transicoes_vistas.add(chave)
        self.bioma_transicoes.append({
            "linha": linha,
            "de": bioma_anterior,
            "para": bioma_atual,
            "nascida_em": pygame.time.get_ticks(),
        })

    def get_bioma(self, score):
        if score < 50:
            return "grama"
        if score < 100:
            return "areia"
        bucket = (score - 100) // CICLO_BIOMA_DURACAO
        if bucket not in self.bioma_cache:
            opcoes = [b for b in BIOMAS if b != self.bioma_cache.get(bucket - 1, "gelo")]
            self.bioma_cache[bucket] = random.choice(opcoes)
        return self.bioma_cache[bucket]

    def rio_congelado(self, score):
        return self.get_bioma(score) == "gelo"

    def fixar_bioma_linha(self, linha, score):
        if linha not in self.bioma_por_linha:
            bioma = self.get_bioma(score)
            self.bioma_por_linha[linha] = bioma
            bioma_anterior = self.bioma_por_linha.get(linha - 1)
            if bioma_anterior is not None and bioma_anterior != bioma:
                self._registrar_transicao_bioma(linha, bioma_anterior, bioma)
        return self.bioma_por_linha[linha]

    def gerar_tile(self, linha, score=0):
        if linha not in self.tile_map:
            if linha >= -SAFE_ZONE_LINHAS:
                self.tile_map[linha] = (assets.images['grama'], TIPO_GRAMA)
            else:
                # Sistema Dinâmico de Pesos (com continuidade entre linhas)
                if score < BREAKPOINT_FASE2:
                    pesos = list(PESOS_GRID_FASE1)
                elif score < BREAKPOINT_FASE3:
                    pesos = list(PESOS_GRID_FASE2)
                else:
                    pesos = list(PESOS_GRID_FASE3)

                prev_tipo = self.tile_map.get(linha - 1, (None, None))[1]
                if prev_tipo == TIPO_GRAMA:
                    pesos = [pesos[0] + 3, max(1, pesos[1] - 1), max(1, pesos[2] - 1)]
                elif prev_tipo == TIPO_ESTRADA:
                    pesos = [max(1, pesos[0] - 1), pesos[1] + 3, max(1, pesos[2] - 1)]
                elif prev_tipo == TIPO_RIO:
                    pesos = [max(1, pesos[0] - 1), max(1, pesos[1] - 1), pesos[2] + 3]

                tipo = random.choices([TIPO_GRAMA, TIPO_ESTRADA, TIPO_RIO], weights=pesos)[0]
                img = assets.images['grama'] if tipo == TIPO_GRAMA else (
                    assets.images['estrada'] if tipo == TIPO_ESTRADA else None)
                self.tile_map[linha] = (img, tipo)
        return self.tile_map[linha]

    def colide_com_arvore(self, rect):
        return any(a.world_rect().colliderect(rect) for a in self.arvores_ativas)

    def desenhar_grama_luxo(self, surface, y, bioma):
        cores = {"areia": (210, 180, 100), "gelo": (200, 230, 255)}
        if bioma in cores:
            surface.fill(cores[bioma], (0, y, LARGURA, TAMANHO_TILE))
            for x in range(0, LARGURA, TAMANHO_TILE):
                if bioma == "areia":
                    pygame.draw.circle(surface, (190, 160, 80), (x + 12, y + 18), 3)
                    pygame.draw.circle(surface, (222, 195, 120), (x + 26, y + 28), 2)
                elif bioma == "gelo":
                    pygame.draw.rect(surface, (100, 130, 110), (0, y, LARGURA, TAMANHO_TILE))
                    pygame.draw.ellipse(surface, (210, 230, 220), (x + 3, y + 5, 18, 8))
                    pygame.draw.ellipse(surface, (235, 248, 255), (x + 18, y + 16, 14, 6))
        else:
            for x in range(0, LARGURA, TAMANHO_TILE):
                surface.blit(assets.images['grama'], (x, y))

    def desenhar_agua_luxo(self, surface, sy, linha, dir):
        agua = pygame.Surface((LARGURA, TAMANHO_TILE), pygame.SRCALPHA)
        desloc = (pygame.time.get_ticks() // 60) % 30
        xs = range(-30 + desloc, LARGURA + 30, 30) if dir == 1 else range(LARGURA + 30 - desloc, -30, -30)
        for i, xi in enumerate(xs):
            yoff = 5 if i % 2 == 0 else 0
            pygame.draw.ellipse(agua, (180, 220, 255, 90), (xi, TAMANHO_TILE // 2 - 3 + yoff, 18, 6))
        surface.blit(agua, (0, sy))

    def spawn_entities(self, linha_ini, linha_fim, score, agora):
        # Progressão suave para evitar saltos bruscos de dificuldade
        diff_base = min(score / SCORE_DIFICULDADE_MAX, 1.0)
        diff_f = diff_base * diff_base * (3.0 - 2.0 * diff_base)

        # Interpolação Lerp para Velocidades e Spawns
        car_v_min = CARRO_VEL_BASE[0] + (CARRO_VEL_TETO[0] - CARRO_VEL_BASE[0]) * diff_f
        car_v_max = CARRO_VEL_BASE[1] + (CARRO_VEL_TETO[1] - CARRO_VEL_BASE[1]) * diff_f
        car_sp_min = int(round(CARRO_SPAWN_BASE[0] + (CARRO_SPAWN_TETO[0] - CARRO_SPAWN_BASE[0]) * diff_f))
        car_sp_max = int(round(CARRO_SPAWN_BASE[1] + (CARRO_SPAWN_TETO[1] - CARRO_SPAWN_BASE[1]) * diff_f))

        tron_v_min = TRONCO_VEL_BASE[0] + (TRONCO_VEL_TETO[0] - TRONCO_VEL_BASE[0]) * diff_f
        tron_v_max = TRONCO_VEL_BASE[1] + (TRONCO_VEL_TETO[1] - TRONCO_VEL_BASE[1]) * diff_f
        tron_sp_min = int(round(TRONCO_SPAWN_BASE[0] + (TRONCO_SPAWN_TETO[0] - TRONCO_SPAWN_BASE[0]) * diff_f))
        tron_sp_max = int(round(TRONCO_SPAWN_BASE[1] + (TRONCO_SPAWN_TETO[1] - TRONCO_SPAWN_BASE[1]) * diff_f))

        for l in range(linha_ini, linha_fim + 1):
            tipo = self.gerar_tile(l, score)[1]
            bioma = self.fixar_bioma_linha(l, score)

            if tipo == TIPO_GRAMA and l < -SAFE_ZONE_LINHAS:
                ocupadas = {int(a.wx // TAMANHO_TILE) for a in self.arvores_ativas if a.linha == l}

                # Árvores um pouco mais controladas e com pré-aparição mais cedo
                chance_arvore = ARVORE_CHANCE_BASE + min(score / ARVORE_CHANCE_EXTRA_SCORE, ARVORE_CHANCE_EXTRA_MAX)
                max_arvores_linha = 1 + int(3 * diff_f)
                arvores_na_linha = [a for a in self.arvores_ativas if a.linha == l]

                if len(arvores_na_linha) < max_arvores_linha and random.random() < chance_arvore:
                    colunas_totais = LARGURA // TAMANHO_TILE
                    col_centro = colunas_totais // 2

                    # Mantém as margens e os dois corredores centrais livres
                    livres = [c * TAMANHO_TILE for c in range(1, colunas_totais - 1)
                              if c not in (col_centro - 1, col_centro) and (c not in ocupadas)]

                    if livres:
                        wx = random.choice(livres)
                        self.arvores_ativas.append(Arvore(l, wx, agora - int(ARVORE_APARECIMENTO_VISUAL_MS * 0.72)))
                        ocupadas.add(wx // TAMANHO_TILE)

                if len([p for p in self.powerups_ativos if not p.coletado]) < MAX_POWERUPS_ATIVOS:
                    if not any(p.wy // TAMANHO_TILE == l for p in self.powerups_ativos):
                        if random.random() < POWERUP_CHANCE_SPAWN:
                            cols_com_arvore = {int(a.wx // TAMANHO_TILE) for a in arvores_na_linha}
                            livres = []
                            for c in range(1, (LARGURA // TAMANHO_TILE) - 1):
                                if c in cols_com_arvore:
                                    continue
                                if any(abs(c - col) <= 1 for col in cols_com_arvore):
                                    continue
                                if c * TAMANHO_TILE in ocupadas:
                                    continue
                                livres.append(c * TAMANHO_TILE)
                            if livres:
                                wx = random.choice(livres)
                                pu_tipo = "escudo" if random.random() < 0.5 else "xp2"
                                self.powerups_ativos.append(PowerUp(wx, l * TAMANHO_TILE, pu_tipo))

            if tipo == TIPO_ESTRADA:
                if l not in self.lane_data:
                    d = 1 if l % 2 == 0 else -1
                    self.lane_data[l] = {"dir": d, "v": random.uniform(car_v_min, car_v_max),
                                         "next_x": -100 if d == 1 else LARGURA}

                ld = self.lane_data[l]
                ja_existem = [c for c in self.carros_ativos if c.linha == l]

                if not ja_existem:
                    ld['next_x'] = -100 if ld['dir'] == 1 else LARGURA
                    img = random.choice(assets.images['carros_r'] if ld['dir'] == 1 else assets.images['carros_l'])
                    self.carros_ativos.append(Carro(l, ld['next_x'], ld['v'], ld['dir'], img))
                    ld['next_x'] += ld['dir'] * random.randint(car_sp_min, car_sp_max)
                else:
                    ultimo = max(ja_existem, key=lambda c: c.x * ld['dir'])
                    if (ld['dir'] == 1 and ultimo.x >= ld['next_x']) or (ld['dir'] == -1 and ultimo.x <= ld['next_x']):
                        img = random.choice(assets.images['carros_r'] if ld['dir'] == 1 else assets.images['carros_l'])
                        spawn_x = -100 if ld['dir'] == 1 else LARGURA
                        self.carros_ativos.append(Carro(l, spawn_x, ld['v'], ld['dir'], img))
                        ld['next_x'] += ld['dir'] * random.randint(car_sp_min, car_sp_max)

            elif tipo == TIPO_RIO and not self.rio_congelado(score):
                if l not in self.lane_data:
                    d = 1 if l % 2 == 0 else -1
                    is_vitoria = random.random() < 0.35 and any(
                        self.gerar_tile(nl)[1] == TIPO_RIO for nl in [l - 1, l + 1])
                    self.lane_data[l] = {"dir": d, "v": random.uniform(tron_v_min, tron_v_max),
                                         "next_x": -100 if d == 1 else LARGURA,
                                         "modo_rio": "vitoria_regia" if is_vitoria else "troncos"}

                ld = self.lane_data[l]
                if ld["modo_rio"] == "vitoria_regia":
                    if not any(v.linha == l for v in self.vitorias_ativas):
                        cols_adjacentes = [int(v.wx // TAMANHO_TILE) for v in self.vitorias_ativas if
                                           v.linha in (l - 1, l + 1)]
                        qtd = random.randint(3, 5)
                        cols = random.sample(range(1, (LARGURA // TAMANHO_TILE) - 1), qtd)

                        if cols_adjacentes:
                            cols[0] = random.choice(cols_adjacentes)

                        for c in set(cols):
                            self.vitorias_ativas.append(VitoriaRegia(l, c * TAMANHO_TILE))
                else:
                    ja_existem = [t for t in self.troncos_ativos if t.linha == l]
                    t_tipo = "crocodilo" if bioma == "areia" else "tronco"

                    if not ja_existem:
                        slots = random.choice(TRONCO_SLOTS_OPCOES)
                        ld['next_x'] = -(slots * TAMANHO_TILE) if ld['dir'] == 1 else LARGURA
                        self.troncos_ativos.append(Tronco(l, ld['next_x'], ld['v'], ld['dir'], slots, t_tipo))
                        ld['next_x'] += ld['dir'] * random.randint(tron_sp_min, tron_sp_max)
                    else:
                        ultimo = max(ja_existem, key=lambda c: c.x * ld['dir'])
                        if (ld['dir'] == 1 and ultimo.x >= ld['next_x']) or (
                                ld['dir'] == -1 and ultimo.x <= ld['next_x']):
                            slots = random.choice(TRONCO_SLOTS_OPCOES)
                            spawn_x = -(slots * TAMANHO_TILE) if ld['dir'] == 1 else LARGURA
                            self.troncos_ativos.append(Tronco(l, spawn_x, ld['v'], ld['dir'], slots, t_tipo))
                            ld['next_x'] += ld['dir'] * random.randint(tron_sp_min, tron_sp_max)

    def update(self, player, score, agora):
        if player.wy < self.camera_y + PLAYER_ALVO_Y:
            self.camera_ativa = True
        vel_scroll = VEL_SCROLL_INICIAL + (VEL_SCROLL_MAX - VEL_SCROLL_INICIAL) * min(score / SCORE_PARA_MAX_VEL, 1.0)
        if self.camera_ativa:
            self.camera_y -= vel_scroll
        target_cam = player.wy - PLAYER_ALVO_Y
        if self.camera_y > target_cam:
            self.camera_y -= max(vel_scroll + 1.0, (self.camera_y - target_cam) * 0.22)

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

        for t in self.troncos_ativos:
            t.update()
        for p in self.particles:
            p.update()

        self.carros_ativos[:] = [c for c in self.carros_ativos if -200 <= c.x <= LARGURA + 200]
        self.troncos_ativos[:] = [t for t in self.troncos_ativos if -200 <= t.x <= LARGURA + 200]
        self.powerups_ativos[:] = [p for p in self.powerups_ativos if not p.coletado]
        self.fumacas_ativas[:] = [f for f in self.fumacas_ativas if not f.expirou(agora)]

    def check_death(self, player, agora):
        if agora < player.graca_ate:
            return False, None

        py_screen = player.wy - self.camera_y
        if py_screen >= ALTURA or py_screen < -TAMANHO_TILE:
            return True, "borda"

        prect = player.rect(self.camera_y)
        tipo = self.gerar_tile(int(player.wy // TAMANHO_TILE))[1]

        golpe_fatal = False
        causa = None

        if tipo == TIPO_ESTRADA and any(c.rect(self.camera_y).colliderect(prect) for c in self.carros_ativos):
            golpe_fatal = True
            causa = "atropelado"
            if not player.tem_escudo:
                self.particles.append(
                    Particle(player.wx + 24, player.wy + 24, 0, 0, (255, 100, 0), 600, 20))
        elif tipo == TIPO_RIO and not self.rio_congelado(player.score):
            em_vitoria = any(v.rect_mundo().colliderect(player.world_rect()) for v in self.vitorias_ativas if
                             v.linha == int(player.wy // TAMANHO_TILE))
            if player.tronco_atual is None and not em_vitoria:
                golpe_fatal = True
                causa = "afogado"
                if not player.tem_escudo:
                    self.particles.append(
                        Particle(player.wx + 24, player.wy + 24, 0, 0, (150, 200, 255), 600, 20))

        if golpe_fatal:
            if player.tem_escudo:
                player.tem_escudo = False
                player.graca_ate = agora + 1200
                return False, None
            return True, causa

        return False, None

    def draw_biome_transitions(self, surface, agora):
        if not self.bioma_transicoes:
            return

        ativos = []
        for evento in self.bioma_transicoes:
            idade = agora - evento["nascida_em"]
            if idade > TRANSICAO_BIOMA_MS + 300:
                continue

            linha = evento["linha"]
            sy = int(linha * TAMANHO_TILE - self.camera_y)
            if sy < -TAMANHO_TILE or sy > ALTURA + TAMANHO_TILE:
                ativos.append(evento)
                continue

            bioma_de = evento["de"]
            bioma_para = evento["para"]
            cor_de = self._bioma_cor(bioma_de)
            cor_para = self._bioma_cor(bioma_para)

            faixa_h = TRANSICAO_BIOMA_ALTURA * 2
            faixa = pygame.Surface((LARGURA, faixa_h), pygame.SRCALPHA)
            for y in range(faixa_h):
                t = y / max(1, faixa_h - 1)
                if t < 0.5:
                    u = t * 2.0
                    cor = [int(cor_de[i] * (1.0 - u) + cor_para[i] * u) for i in range(3)]
                    alpha = 110 + int(35 * (1.0 - u))
                else:
                    u = (t - 0.5) * 2.0
                    cor = [int(cor_para[i] * (1.0 - 0.35 * u) + cor_de[i] * 0.18 * u) for i in range(3)]
                    alpha = 105 + int(20 * (1.0 - u))
                pygame.draw.line(faixa, (*cor, alpha), (0, y), (LARGURA, y))

            meio = faixa_h // 2
            for x in range(0, LARGURA, TAMANHO_TILE // 2):
                pygame.draw.circle(faixa, (255, 255, 255, 18), (x + (TAMANHO_TILE // 4), meio), 2)
                pygame.draw.circle(faixa, (*self._bioma_cor(bioma_para), 38), (x + (TAMANHO_TILE // 2), meio + 2), 3)

            y_blit = clamp(sy - TRANSICAO_BIOMA_ALTURA, 0, ALTURA - faixa_h)
            surface.blit(faixa, (0, y_blit))

            if idade < TRANSICAO_BIOMA_MS:
                if idade < 220:
                    alpha = idade / 220.0
                elif idade < 900:
                    alpha = 1.0
                else:
                    alpha = max(0.0, 1.0 - (idade - 900) / 400.0)

                texto = self._bioma_texto(bioma_para)
                cor_texto = tuple(max(0, int(c * 0.72)) for c in self._bioma_cor(bioma_para))
                y_txt = clamp(sy - 12, 66, ALTURA - 54)

                draw_text_outline(surface, assets.fonts['botao_grande'], texto, cor_texto,
                                  (LARGURA // 2, y_txt), outline_color=(0, 0, 0), outline=1,
                                  alpha=int(255 * alpha))

            ativos.append(evento)

        self.bioma_transicoes = ativos

    def draw(self, surface, score, agora):
        linha_ini = int(self.camera_y // TAMANHO_TILE) - 1
        linha_fim = int((self.camera_y + ALTURA) // TAMANHO_TILE) + 1

        for l in range(linha_ini, linha_fim + 1):
            sy = int(l * TAMANHO_TILE - self.camera_y)
            img, tipo = self.gerar_tile(l, score)
            bioma = self.fixar_bioma_linha(l, score)

            if tipo == TIPO_GRAMA:
                self.desenhar_grama_luxo(surface, sy, bioma)
            else:
                if img:
                    surface.blit(img, (0, sy))
                if tipo == TIPO_RIO:
                    if self.rio_congelado(score):
                        pygame.draw.rect(surface, (210, 238, 255), (0, sy, LARGURA, TAMANHO_TILE))
                        pygame.draw.rect(surface, (235, 248, 255), (0, sy + TAMANHO_TILE // 2 - 5, LARGURA, 10))
                    else:
                        pygame.draw.rect(surface, (80, 170, 230), (0, sy, LARGURA, TAMANHO_TILE))
                        self.desenhar_agua_luxo(surface, sy, l, self.lane_data.get(l, {"dir": 1})["dir"])

            prev_bioma = self.bioma_por_linha.get(l - 1)
            if prev_bioma is not None and prev_bioma != bioma:
                self._registrar_transicao_bioma(l, prev_bioma, bioma)

        for v in self.vitorias_ativas:
            v.draw(surface, self.camera_y)
        for f in self.fumacas_ativas:
            f.draw(surface, self.camera_y, agora)
        for t in self.troncos_ativos:
            surface.blit(t.img, (int(t.x), int(t.linha * TAMANHO_TILE - self.camera_y)))
        for c in self.carros_ativos:
            surface.blit(c.img, (int(c.x), int(c.linha * TAMANHO_TILE - self.camera_y)))
        for a in self.arvores_ativas:
            a.draw(surface, self.camera_y, agora, self.fixar_bioma_linha(a.linha, score))
        for pu in self.powerups_ativos:
            pu.draw(surface, self.camera_y)
        self.particles[:] = [p for p in self.particles if p.draw(surface, self.camera_y, agora)]
