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
        self.linhas_transicao = {}

        self.carros_ativos = []
        self.troncos_ativos = []
        self.arvores_ativas = []
        self.vitorias_ativas = []
        self.powerups_ativos = []
        self.fumacas_ativas = []
        self.particles = []

        self.camera_y = 0
        self.camera_ativa = False
        self._cache_tiles_transicao = {}

        for l in range(-5, 10):
            self.gerar_tile(l)

    def colide_com_arvore(self, rect):
        return any(a.world_rect().colliderect(rect) for a in self.arvores_ativas)

    def get_bioma(self, score):
        idx = (int(score) // CICLO_BIOMA_DURACAO) % len(BIOMAS)
        return BIOMAS[idx]

    def fixar_bioma_linha(self, linha, score):
        if linha not in self.bioma_por_linha:
            bioma = self.get_bioma(score)
            bioma_anterior = self.bioma_por_linha.get(linha - 1)
            if bioma_anterior is not None and bioma_anterior != bioma:
                self.linhas_transicao[linha - 1] = bioma_anterior
            self.bioma_por_linha[linha] = bioma
        return self.bioma_por_linha[linha]

    def _tiles_linha_transicao(self, bioma):
        if bioma not in self._cache_tiles_transicao:
            img_trans = assets.images['biomas'][bioma].get('transicao')
            colunas = (LARGURA // TAMANHO_TILE) + 1
            tiles = []
            if img_trans:
                for col in range(colunas):
                    x = col * TAMANHO_TILE
                    if x + TAMANHO_TILE <= img_trans.get_width():
                        tiles.append(img_trans.subsurface((x, 0, TAMANHO_TILE, TAMANHO_TILE)).copy())
                    else:
                        tiles.append(img_trans)
            if not tiles:
                solos = assets.images['biomas'][bioma]['solos']
                tiles = [random.choice(solos) if solos else None for _ in range(colunas)]
            self._cache_tiles_transicao[bioma] = tiles
        return self._cache_tiles_transicao[bioma]

    def gerar_tile(self, linha, score=0):
        if linha not in self.tile_map:
            bioma = self.fixar_bioma_linha(linha, score)
            colunas = (LARGURA // TAMANHO_TILE) + 1

            if linha in self.linhas_transicao:
                bioma_trans = self.linhas_transicao[linha]
                tiles_sorteados = list(self._tiles_linha_transicao(bioma_trans))
                while len(tiles_sorteados) < colunas:
                    tiles_sorteados.append(tiles_sorteados[-1] if tiles_sorteados else None)
                self.tile_map[linha] = (tiles_sorteados[:colunas], TIPO_GRAMA)
                return self.tile_map[linha]

            if linha >= -SAFE_ZONE_LINHAS:
                tipo = TIPO_GRAMA
            else:
                if score < BREAKPOINT_FASE2:
                    pesos = list(PESOS_GRID_FASE1)
                elif score < BREAKPOINT_FASE3:
                    pesos = list(PESOS_GRID_FASE2)
                else:
                    pesos = list(PESOS_GRID_FASE3)

                prev_tipo = self.tile_map.get(linha - 1, (None, None))[1]
                if prev_tipo == TIPO_GRAMA:
                    pesos = [pesos[0] + 3, pesos[1], max(0, pesos[2] - 1)]
                elif prev_tipo == TIPO_ESTRADA:
                    pesos = [max(1, pesos[0] - 1), pesos[1] + 3, max(1, pesos[2] - 1)]
                elif prev_tipo == TIPO_RIO:
                    pesos = [max(1, pesos[0] - 1), max(1, pesos[1] - 1), pesos[2] + 3]

                w = [max(0, pesos[0]), max(0, pesos[1]), max(0, pesos[2])]
                if sum(w) == 0:
                    w = [1, 0, 0]
                tipo = random.choices([TIPO_GRAMA, TIPO_ESTRADA, TIPO_RIO], weights=w)[0]

            if tipo == TIPO_ESTRADA:
                banco_imagens = assets.images.get('estradas', [])
            elif tipo == TIPO_GRAMA:
                banco_imagens = assets.images['biomas'][bioma]['solos']
            else:
                banco_imagens = assets.images['biomas'][bioma]['aguas']

            tiles_sorteados = []
            for _ in range(colunas):
                img_sorteada = random.choice(banco_imagens) if banco_imagens else None
                tiles_sorteados.append(img_sorteada)

            self.tile_map[linha] = (tiles_sorteados, tipo)

        return self.tile_map[linha]

    def _linha_acima_do_buffer(self, linha, player):
        linha_player = int(player.wy // TAMANHO_TILE)
        return linha <= linha_player - OBSTACULO_BUFFER_LINHAS

    def _tronco_livre(self, linha, x, largura):
        for t in self.troncos_ativos:
            if t.linha != linha:
                continue
            if t.x < x + largura and t.x + t.largura > x:
                return False
        return True

    def _criar_tronco(self, linha, ld, x, slots, t_tipo):
        if not self._tronco_livre(linha, x, slots * TAMANHO_TILE):
            return None
        t = Tronco(linha, x, ld['v'], ld['dir'], slots, t_tipo)
        self.troncos_ativos.append(t)
        return t

    def _manter_fluxo_troncos(self, linha, ld):
        """Mantém troncos/jacarés passando sem pausas, com gap fixo e sem sobreposição."""
        ja = [t for t in self.troncos_ativos if t.linha == linha]

        if not ja:
            slots = random.choice(TRONCO_SLOTS_OPCOES)
            largura = slots * TAMANHO_TILE
            spawn_x = -largura if ld['dir'] == 1 else LARGURA
            t_tipo = "crocodilo" if random.random() < CROCODILO_CHANCE else "tronco"
            self._criar_tronco(linha, ld, spawn_x, slots, t_tipo)
            return

        if ld['dir'] == 1:
            # Entram pela esquerda; garante cobertura contínua
            esquerdo = min(ja, key=lambda t: t.x)
            if esquerdo.x > -max(TRONCO_SLOTS_OPCOES) * TAMANHO_TILE:
                slots = random.choice(TRONCO_SLOTS_OPCOES)
                largura = slots * TAMANHO_TILE
                novo_x = esquerdo.x - TRONCO_GAP_FIXO - largura
                t_tipo = "crocodilo" if random.random() < CROCODILO_CHANCE else "tronco"
                self._criar_tronco(linha, ld, novo_x, slots, t_tipo)

            direito = max(ja, key=lambda t: t.x + t.largura)
            spawns = 0
            while direito.x + direito.largura < LARGURA + TRONCO_COBERTURA_EXTRA and spawns < 4:
                slots = random.choice(TRONCO_SLOTS_OPCOES)
                novo_x = direito.x + direito.largura + TRONCO_GAP_FIXO
                t_tipo = "crocodilo" if random.random() < CROCODILO_CHANCE else "tronco"
                criado = self._criar_tronco(linha, ld, novo_x, slots, t_tipo)
                if not criado:
                    break
                ja.append(criado)
                direito = criado
                spawns += 1
        else:
            direito = max(ja, key=lambda t: t.x + t.largura)
            if direito.x + direito.largura < LARGURA + max(TRONCO_SLOTS_OPCOES) * TAMANHO_TILE:
                slots = random.choice(TRONCO_SLOTS_OPCOES)
                novo_x = direito.x + direito.largura + TRONCO_GAP_FIXO
                t_tipo = "crocodilo" if random.random() < CROCODILO_CHANCE else "tronco"
                self._criar_tronco(linha, ld, novo_x, slots, t_tipo)

            esquerdo = min(ja, key=lambda t: t.x)
            spawns = 0
            while esquerdo.x > -TRONCO_COBERTURA_EXTRA and spawns < 4:
                slots = random.choice(TRONCO_SLOTS_OPCOES)
                largura = slots * TAMANHO_TILE
                novo_x = esquerdo.x - TRONCO_GAP_FIXO - largura
                t_tipo = "crocodilo" if random.random() < CROCODILO_CHANCE else "tronco"
                criado = self._criar_tronco(linha, ld, novo_x, slots, t_tipo)
                if not criado:
                    break
                ja.append(criado)
                esquerdo = criado
                spawns += 1

    def _colisao_com_obstaculos(self, rect):
        return any(a.world_rect().colliderect(rect) for a in self.arvores_ativas)

    def spawn_entities(self, linha_ini, linha_fim, score, agora, player):
        diff_base = min(score / SCORE_DIFICULDADE_MAX, 1.0)
        diff_f = diff_base * diff_base * (3.0 - 2.0 * diff_base)

        car_v_min = CARRO_VEL_BASE[0] + (CARRO_VEL_TETO[0] - CARRO_VEL_BASE[0]) * diff_f
        car_v_max = CARRO_VEL_BASE[1] + (CARRO_VEL_TETO[1] - CARRO_VEL_BASE[1]) * diff_f
        car_sp_min = int(round(CARRO_SPAWN_BASE[0] + (CARRO_SPAWN_TETO[0] - CARRO_SPAWN_BASE[0]) * diff_f))
        car_sp_max = int(round(CARRO_SPAWN_BASE[1] + (CARRO_SPAWN_TETO[1] - CARRO_SPAWN_BASE[1]) * diff_f))

        tron_v_min = TRONCO_VEL_BASE[0] + (TRONCO_VEL_TETO[0] - TRONCO_VEL_BASE[0]) * diff_f
        tron_v_max = TRONCO_VEL_BASE[1] + (TRONCO_VEL_TETO[1] - TRONCO_VEL_BASE[1]) * diff_f

        linha_player = int(player.wy // TAMANHO_TILE)
        linha_fim_rio = linha_fim + 25

        for l in range(linha_ini, linha_fim_rio + 1):
            tipo = self.gerar_tile(l, score)[1]
            bioma = self.fixar_bioma_linha(l, score)

            if tipo == TIPO_GRAMA and l < -SAFE_ZONE_LINHAS and self._linha_acima_do_buffer(l, player):
                ocupadas = {int(a.wx // TAMANHO_TILE) for a in self.arvores_ativas if a.linha == l}
                chance_arvore = ARVORE_CHANCE_BASE + min(score / ARVORE_CHANCE_EXTRA_SCORE, ARVORE_CHANCE_EXTRA_MAX)
                max_arvores_linha = 1 + int(3 * diff_f)
                arvores_na_linha = [a for a in self.arvores_ativas if a.linha == l]

                if len(arvores_na_linha) < max_arvores_linha and random.random() < chance_arvore:
                    colunas_totais = LARGURA // TAMANHO_TILE
                    col_centro = colunas_totais // 2
                    livres = [c * TAMANHO_TILE for c in range(1, colunas_totais - 1)
                              if c not in (col_centro - 1, col_centro) and c not in ocupadas]

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
                                if c in cols_com_arvore:
                                    continue
                                if any(abs(c - col) <= 1 for col in cols_com_arvore):
                                    continue
                                if c in ocupadas:
                                    continue
                                wx = c * TAMANHO_TILE
                                test = pygame.Rect(wx + 6, l * TAMANHO_TILE + 6,
                                                   TAMANHO_TILE - 12, TAMANHO_TILE - 12)
                                if self._colisao_com_obstaculos(test):
                                    continue
                                livres.append(wx)
                            if livres:
                                wx = random.choice(livres)
                                pu_tipo = "escudo" if random.random() < 0.5 else "xp2"
                                self.powerups_ativos.append(PowerUp(wx, l * TAMANHO_TILE, pu_tipo))

            if l > linha_fim:
                continue

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
                    if (ld['dir'] == 1 and ultimo.x >= ld['next_x']) or (
                            ld['dir'] == -1 and ultimo.x <= ld['next_x']):
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
                    self._manter_fluxo_troncos(l, ld)

    def update(self, player, score, agora, dt):
        if player.wy < self.camera_y + PLAYER_ALVO_Y:
            self.camera_ativa = True

        vel_scroll = (VEL_SCROLL_INICIAL + (VEL_SCROLL_MAX - VEL_SCROLL_INICIAL) * min(score / SCORE_PARA_MAX_VEL,
                                                                                       1.0)) * dt
        if self.camera_ativa:
            self.camera_y -= vel_scroll

        target_cam = player.wy - PLAYER_ALVO_Y
        if self.camera_y > target_cam:
            self.camera_y -= max(vel_scroll + 1.0, (self.camera_y - target_cam) * 0.22)

        linha_ini = int(self.camera_y // TAMANHO_TILE) - 15
        linha_fim = int((self.camera_y + ALTURA) // TAMANHO_TILE) + 1
        self.spawn_entities(linha_ini, linha_fim, score, agora, player)

        for c in self.carros_ativos:
            c.update(dt)
            if random.random() < FUMACA_CHANCE_POR_FRAME:
                wx = c.x + 4 if c.direcao == 1 else c.x + c.largura - 4
                vx = random.uniform(-0.02, -0.01) if c.direcao == 1 else random.uniform(0.01, 0.02)
                self.fumacas_ativas.append(
                    Fumaca(wx, c.linha * TAMANHO_TILE + TAMANHO_TILE - 8, vx, random.uniform(-0.03, -0.018), agora))

        for t in self.troncos_ativos:
            t.update(dt)
        for p in self.particles:
            p.update(dt)

        linha_limite = int((self.camera_y + ALTURA) // TAMANHO_TILE) + SAFE_ZONE_LINHAS + 2

        self.carros_ativos[:] = [c for c in self.carros_ativos if
                                 -200 <= c.x <= LARGURA + 200 and c.linha <= linha_limite]
        self.troncos_ativos[:] = [t for t in self.troncos_ativos if
                                  -300 <= t.x <= LARGURA + 300 and t.linha <= linha_limite + 25]
        self.powerups_ativos[:] = [p for p in self.powerups_ativos if
                                   not p.coletado and (p.wy // TAMANHO_TILE) <= linha_limite]
        self.fumacas_ativas[:] = [f for f in self.fumacas_ativas if not f.expirou(agora)]
        self.arvores_ativas[:] = [a for a in self.arvores_ativas if a.linha <= linha_limite]
        self.vitorias_ativas[:] = [v for v in self.vitorias_ativas if v.linha <= linha_limite]

        chaves_remover = [l for l in self.tile_map if l > linha_limite]
        for l in chaves_remover:
            del self.tile_map[l]
            if l in self.bioma_por_linha:
                del self.bioma_por_linha[l]
            if l in self.lane_data:
                del self.lane_data[l]
            if l in self.linhas_transicao:
                del self.linhas_transicao[l]

    def check_death(self, player, agora):
        py_screen = player.wy - self.camera_y
        if py_screen >= ALTURA or py_screen < -TAMANHO_TILE:
            return True, "borda"

        if agora < player.graca_ate:
            return False, None

        prect = player.rect(self.camera_y)
        tipo = self.gerar_tile(int(player.wy // TAMANHO_TILE), player.score)[1]

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

            if player.tronco_atual and player.tronco_atual.tipo == "crocodilo":
                golpe_fatal = True
                causa = "jacare"
            else:
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
                player.graca_ate = agora + 1000
                return False, None
            return True, causa

        return False, None

    def draw(self, surface, score, agora):
        linha_ini = int(self.camera_y // TAMANHO_TILE) - 1
        linha_fim = int((self.camera_y + ALTURA) // TAMANHO_TILE) + 1

        for l in range(linha_ini, linha_fim + 1):
            sy = int(l * TAMANHO_TILE - self.camera_y)
            dados, tipo = self.gerar_tile(l, score)
            self.fixar_bioma_linha(l, score)
            if dados:
                for col, tile_img in enumerate(dados):
                    if tile_img:
                        surface.blit(tile_img, (col * TAMANHO_TILE, sy))

        for v in self.vitorias_ativas:
            v.draw(surface, self.camera_y, agora)
        for f in self.fumacas_ativas:
            f.draw(surface, self.camera_y, agora)
        for t in self.troncos_ativos:
            t.draw(surface, self.camera_y, agora)
        for c in self.carros_ativos:
            surface.blit(c.img, (int(c.x), int(c.linha * TAMANHO_TILE - self.camera_y)))
        for a in self.arvores_ativas:
            a.draw(surface, self.camera_y, agora)
        for pu in self.powerups_ativos:
            pu.draw(surface, self.camera_y)

        self.particles[:] = [p for p in self.particles if p.draw(surface, self.camera_y, agora)]
