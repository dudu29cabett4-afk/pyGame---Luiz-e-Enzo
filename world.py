# world.py
import random
import pygame
from config import *
import assets
from entities import Carro, Tronco, Obstaculo, Particle, Fumaca, Lilypad, PowerUp
from utils import clamp

class World:
    def __init__(self):
        self.tile_map = {}
        self.lane_data = {}
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

        # Pré-gera as primeiras linhas seguras e do começo do jogo
        for l in range(-5, 10):
            self.gerar_tile(l)

    def colide_com_arvore(self, rect):
        return any(a.world_rect().colliderect(rect) for a in self.arvores_ativas)

    def colide_com_vitoria_regia(self, rect):
        return any(v.world_rect().colliderect(rect) for v in self.vitorias_ativas)

    def _registrar_transicao_bioma(self, linha, bioma_anterior, bioma_atual):
        chave = (linha, bioma_anterior, bioma_atual)
        if chave in self.bioma_transicoes_vistas:
            return
        self.bioma_transicoes_vistas.add(chave)
        self.bioma_transicoes.append({
            "linha": linha,
            "de": bioma_anterior,
            "para": bioma_atual
        })

    def get_bioma(self, score):
        # Cicla na ordem exata de config.BIOMAS: ["floresta", "deserto", "urbano"]
        # A cada CICLO_BIOMA_DURACAO (ex: 50 pontos), muda o bioma.
        idx = (int(score) // CICLO_BIOMA_DURACAO) % len(BIOMAS)
        return BIOMAS[idx]

    def rio_congelado(self, score):
        # Sem bioma de neve agora, rios sempre estarão em estado líquido/sujo.
        return False

    def fixar_bioma_linha(self, linha, score):
        if linha not in self.bioma_por_linha:
            bioma = self.get_bioma(score)
            self.bioma_por_linha[linha] = bioma

            bioma_anterior = self.bioma_por_linha.get(linha - 1)
            # Aciona transição apenas se houver uma mudança real entre linhas
            if bioma_anterior is not None and bioma_anterior != bioma:
                self._registrar_transicao_bioma(linha, bioma_anterior, bioma)
        return self.bioma_por_linha[linha]

    def gerar_tile(self, linha, score=0):
        if linha not in self.tile_map:
            bioma = self.fixar_bioma_linha(linha, score)

            if linha >= -SAFE_ZONE_LINHAS:
                tipo = TIPO_GRAMA
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

            colunas = (LARGURA // TAMANHO_TILE) + 1
            tiles_sorteados = []

            if tipo == TIPO_ESTRADA:
                banco_imagens = assets.images.get('estradas', [])
            elif tipo == TIPO_GRAMA:
                banco_imagens = assets.images['biomas'][bioma]['solos']
            else:
                banco_imagens = assets.images['biomas'][bioma]['aguas']

            for _ in range(colunas):
                img_sorteada = random.choice(banco_imagens) if banco_imagens else None
                tiles_sorteados.append(img_sorteada)

            self.tile_map[linha] = (tiles_sorteados, tipo)

        return self.tile_map[linha]

    def spawn_entities(self, linha_ini, linha_fim, score, agora):
        diff_base = min(score / SCORE_DIFICULDADE_MAX, 1.0)
        diff_f = diff_base * diff_base * (3.0 - 2.0 * diff_base)

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
                chance_arvore = ARVORE_CHANCE_BASE + min(score / ARVORE_CHANCE_EXTRA_SCORE, ARVORE_CHANCE_EXTRA_MAX)
                max_arvores_linha = 1 + int(3 * diff_f)
                arvores_na_linha = [a for a in self.arvores_ativas if a.linha == l]

                if len(arvores_na_linha) < max_arvores_linha and random.random() < chance_arvore:
                    colunas_totais = LARGURA // TAMANHO_TILE
                    col_centro = colunas_totais // 2
                    livres = [c * TAMANHO_TILE for c in range(1, colunas_totais - 1)
                              if c not in (col_centro - 1, col_centro) and (c not in ocupadas)]

                    if livres:
                        wx = random.choice(livres)
                        imgs_obs = assets.images['biomas'][bioma]['obstaculos']
                        img_obs = random.choice(imgs_obs) if imgs_obs else None

                        if img_obs:
                            self.arvores_ativas.append(Obstaculo(l, wx, img_obs, agora - 220))
                        ocupadas.add(wx // TAMANHO_TILE)

                if len([p for p in self.powerups_ativos if not p.coletado]) < MAX_POWERUPS_ATIVOS:
                    if not any(p.wy // TAMANHO_TILE == l for p in self.powerups_ativos):
                        if random.random() < POWERUP_CHANCE_SPAWN:
                            cols_com_arvore = {int(a.wx // TAMANHO_TILE) for a in arvores_na_linha}
                            livres = []
                            for c in range(1, (LARGURA // TAMANHO_TILE) - 1):
                                if c in cols_com_arvore: continue
                                if any(abs(c - col) <= 1 for col in cols_com_arvore): continue
                                if c * TAMANHO_TILE in ocupadas: continue
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
                    imgs_carro = assets.images['carros_r'] if ld['dir'] == 1 else assets.images['carros_l']
                    img = random.choice(imgs_carro) if imgs_carro else None
                    if img:
                        self.carros_ativos.append(Carro(l, ld['next_x'], ld['v'], ld['dir'], img))
                    ld['next_x'] += ld['dir'] * random.randint(car_sp_min, car_sp_max)
                else:
                    ultimo = max(ja_existem, key=lambda c: c.x * ld['dir'])
                    if (ld['dir'] == 1 and ultimo.x >= ld['next_x']) or (ld['dir'] == -1 and ultimo.x <= ld['next_x']):
                        imgs_carro = assets.images['carros_r'] if ld['dir'] == 1 else assets.images['carros_l']
                        img = random.choice(imgs_carro) if imgs_carro else None
                        spawn_x = -100 if ld['dir'] == 1 else LARGURA
                        if img:
                            self.carros_ativos.append(Carro(l, spawn_x, ld['v'], ld['dir'], img))
                        ld['next_x'] += ld['dir'] * random.randint(car_sp_min, car_sp_max)

            elif tipo == TIPO_RIO:
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

                        imgs_lily = assets.images.get('lilypads', [])
                        for c in set(cols):
                            img_lily = random.choice(imgs_lily) if imgs_lily else None
                            if img_lily:
                                self.vitorias_ativas.append(Lilypad(l, c * TAMANHO_TILE, img_lily))
                else:
                    ja_existem = [t for t in self.troncos_ativos if t.linha == l]
                    # Crocodilo aparece com 20% de chance, independente do bioma, pra dar diversidade
                    t_tipo = "crocodilo" if random.random() < 0.2 else "tronco"

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

    def update(self, player, score, agora, dt):
        if player.wy < self.camera_y + PLAYER_ALVO_Y:
            self.camera_ativa = True

        # MOTIVO TÉCNICO: A velocidade da câmera também deve ser escalada pelo dt para não engasgar.
        vel_scroll = (VEL_SCROLL_INICIAL + (VEL_SCROLL_MAX - VEL_SCROLL_INICIAL) * min(score / SCORE_PARA_MAX_VEL,
                                                                                       1.0)) * dt
        if self.camera_ativa:
            self.camera_y -= vel_scroll

        target_cam = player.wy - PLAYER_ALVO_Y
        if self.camera_y > target_cam:
            self.camera_y -= max(vel_scroll + 1.0, (self.camera_y - target_cam) * 0.22)

        linha_ini = int(self.camera_y // TAMANHO_TILE) - 15
        linha_fim = int((self.camera_y + ALTURA) // TAMANHO_TILE) + 1
        self.spawn_entities(linha_ini, linha_fim, score, agora)

        for c in self.carros_ativos:
            c.update(dt)  # Passando dt
            if random.random() < 0.35:
                wx = c.x + 4 if c.direcao == 1 else c.x + c.largura - 4
                vx = random.uniform(-0.02, -0.01) if c.direcao == 1 else random.uniform(0.01, 0.02)
                self.fumacas_ativas.append(
                    Fumaca(wx, c.linha * TAMANHO_TILE + TAMANHO_TILE - 8, vx, random.uniform(-0.03, -0.018), agora))

        for t in self.troncos_ativos:
            t.update(dt)  # Passando dt
        for p in self.particles:
            p.update(dt)  # Passando dt

        # ==========================================
        # RESOLUÇÃO DO MEMORY LEAK MASSIVO
        # ==========================================
        # MOTIVO TÉCNICO: A câmera sobe (valores negativos). Qualquer linha maior que o limite visual ficou para trás.
        # Varremos todas as listas de entidades e estruturas de dados e as purgamos da RAM.
        linha_limite = int((self.camera_y + ALTURA) // TAMANHO_TILE) + SAFE_ZONE_LINHAS + 2

        self.carros_ativos[:] = [c for c in self.carros_ativos if
                                 -200 <= c.x <= LARGURA + 200 and c.linha <= linha_limite]
        self.troncos_ativos[:] = [t for t in self.troncos_ativos if
                                  -200 <= t.x <= LARGURA + 200 and t.linha <= linha_limite]
        self.powerups_ativos[:] = [p for p in self.powerups_ativos if
                                   not p.coletado and (p.wy // TAMANHO_TILE) <= linha_limite]
        self.fumacas_ativas[:] = [f for f in self.fumacas_ativas if not f.expirou(agora)]

        self.arvores_ativas[:] = [a for a in self.arvores_ativas if a.linha <= linha_limite]
        self.vitorias_ativas[:] = [v for v in self.vitorias_ativas if v.linha <= linha_limite]

        # Limpeza do dicionário procedural
        chaves_remover = [l for l in self.tile_map if l > linha_limite]
        for l in chaves_remover:
            del self.tile_map[l]
            if l in self.bioma_por_linha:
                del self.bioma_por_linha[l]
            if l in self.lane_data:
                del self.lane_data[l]

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
                self.particles.append(Particle(player.wx + 24, player.wy + 24, 0, 0, (255, 100, 0), 600, 20))
        elif tipo == TIPO_RIO:
            player_coluna = int(player.wx // TAMANHO_TILE)
            player_linha = int(player.wy // TAMANHO_TILE)

            # Ignora hitboxes animadas e verifica a matemática cravada da grid
            em_vitoria = any(
                int(v.wx // TAMANHO_TILE) == player_coluna
                for v in self.vitorias_ativas
                if v.linha == player_linha
            )

            if player.tronco_atual is None and not em_vitoria:
                golpe_fatal = True
                causa = "afogado"
                if not player.tem_escudo:
                    self.particles.append(Particle(player.wx + 24, player.wy + 24, 0, 0, (150, 200, 255), 600, 20))

        if golpe_fatal:
            if player.tem_escudo:
                player.tem_escudo = False
                player.graca_ate = agora + 1200
                return False, None
            return True, causa

        return False, None

    def draw_biome_transitions(self, surface):
        for evento in self.bioma_transicoes:
            linha = evento["linha"]
            sy = int(linha * TAMANHO_TILE - self.camera_y)

            # Desenha só se a linha estiver minimamente na tela
            if sy < -TAMANHO_TILE * 2 or sy > ALTURA + TAMANHO_TILE:
                continue

            bioma_de = evento["de"]
            img_transicao = assets.images['biomas'][bioma_de].get('transicao')

            if img_transicao:
                w = img_transicao.get_width()
                if w > 0:
                    # Se for pequena repete pro lado, se for do tamanho da tela gruda 1x só
                    for x in range(0, LARGURA, w):
                        surface.blit(img_transicao, (x, sy))

    def draw(self, surface, score, agora):
        linha_ini = int(self.camera_y // TAMANHO_TILE) - 1
        linha_fim = int((self.camera_y + ALTURA) // TAMANHO_TILE) + 1

        # 1. Desenha o fundo e salva as transições
        for l in range(linha_ini, linha_fim + 1):
            sy = int(l * TAMANHO_TILE - self.camera_y)
            dados, tipo = self.gerar_tile(l, score)

            self.fixar_bioma_linha(l, score)

            if dados:
                for col, tile_img in enumerate(dados):
                    if tile_img:
                        surface.blit(tile_img, (col * TAMANHO_TILE, sy))

        # 2. Desenha transições de chão por cima do solo normal
        self.draw_biome_transitions(surface)

        # 3. Desenha entidades e partículas
        for v in self.vitorias_ativas:
            v.draw(surface, self.camera_y)
        for f in self.fumacas_ativas:
            f.draw(surface, self.camera_y, agora)
        for t in self.troncos_ativos:
            surface.blit(t.img, (int(t.x), int(t.linha * TAMANHO_TILE - self.camera_y)))
        for c in self.carros_ativos:
            surface.blit(c.img, (int(c.x), int(c.linha * TAMANHO_TILE - self.camera_y)))
        for a in self.arvores_ativas:
            # Mandando bioma pro draw() caso ainda precise
            a.draw(surface, self.camera_y, agora, self.fixar_bioma_linha(a.linha, score))
        for pu in self.powerups_ativos:
            pu.draw(surface, self.camera_y)

        self.particles[:] = [p for p in self.particles if p.draw(surface, self.camera_y, agora)]