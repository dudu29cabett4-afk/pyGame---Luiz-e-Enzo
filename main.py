# main.py
import pygame
import sys
import math
import random
from config import *
import assets
from utils import load_save, save_game, clamp
from world import World
from entities import Player, Particle
from ui import (
    draw_button, draw_hud, draw_danger_zone, draw_control_setup,
    draw_powerups_hud, draw_new_player_screen, draw_load_player_screen,
    draw_options_screen, draw_leaderboard_screen, draw_game_over_screen,
    GAMEOVER_PANEL_H,
    OPT_SLIDER_X, OPT_SLIDER_W, OPT_SLIDER_H,
    OPT_Y_FS, OPT_Y_MASTER, OPT_Y_MUSIC, OPT_Y_SFX, OPT_Y_CTRL, OPT_Y_BACK,
    slider_hit_test, slider_value_from_mouse,
)


class Game:
    def __init__(self):
        pygame.init()
        try:
            pygame.mixer.init()
        except pygame.error:
            pass
        self.save_data = load_save()
        self.settings = self.save_data["settings"]

        self.game_surface = pygame.Surface((LARGURA, ALTURA))
        self.apply_display_settings()

        pygame.display.set_caption("Cruze a Quatá!")
        self.clock = pygame.time.Clock()

        assets.load_all_assets()
        self.apply_audio_volumes()  # Aplica os volumes salvos logo ao abrir o jogo
        self.update_fullscreen_background()

        self.state = ESTADO_MENU
        self.world = None
        self.player = None
        self.current_player = None

        self.match_start_time = 0
        self.death_stats = {}

        self.match_high_score = 0
        self.record_broken = False
        self.record_banner_time = 0

        self.shake_remaining = 0
        self.input_text = ""
        self.input_error = ""
        self.scroll_y = 0
        self.dragging_slider = None

        # Gerenciamento de Áudio
        self.current_track = None
        self.current_ambient = None
        self.last_hover = None

        # Cache da fonte do banner de recorde
        texto_rec = "NOVO RECORDE!"
        self.record_surf_main = assets.fonts['botao_grande'].render(texto_rec, True, (255, 215, 0))
        self.record_surf_shadow = assets.fonts['botao_grande'].render(texto_rec, True, (0, 0, 0))

    def apply_display_settings(self):
        # O pygame.SCALED delega o upscale e o letterbox (barras pretas) para o hardware
        flags = pygame.SCALED
        if self.settings["fullscreen"]:
            flags |= pygame.FULLSCREEN

        self.window = pygame.display.set_mode((LARGURA, ALTURA), flags)

    def update_fullscreen_background(self):
        # Com pygame.SCALED, a resolução lógica é sempre LARGURA x ALTURA
        self.bg_fullscreen = assets.images['telas']['fullscreen']

    def get_mapped_mouse(self):
        # Com pygame.SCALED, o Pygame mapeia as coordenadas do mouse automaticamente
        return pygame.mouse.get_pos()

    def _slider_y_map(self):
        return {
            "vol_master": OPT_Y_MASTER,
            "vol_music": OPT_Y_MUSIC,
            "vol_sfx": OPT_Y_SFX,
        }

    def _try_start_slider_drag(self, mouse):
        for key, sy in self._slider_y_map().items():
            if slider_hit_test(OPT_SLIDER_X, sy, OPT_SLIDER_W, OPT_SLIDER_H,
                               self.settings[key], mouse[0], mouse[1]):
                self.dragging_slider = key
                self.settings[key] = slider_value_from_mouse(OPT_SLIDER_X, OPT_SLIDER_W, mouse[0])
                return True
        return False

    def apply_audio_volumes(self):
        master = self.settings['vol_master'] / 100.0
        music = self.settings['vol_music'] / 100.0 * master
        sfx = self.settings['vol_sfx'] / 100.0 * master

        # Aplica volume no streaming de música principal
        pygame.mixer.music.set_volume(music)

        # Exemplo de aplicação na música de fundo e efeitos
        for som in assets.sons['ambiente'].values():
            if isinstance(som, pygame.mixer.Sound): # Ignora as strings de path
                som.set_volume(music)
        for som in assets.sons['interface'].values():
            if isinstance(som, pygame.mixer.Sound):
                som.set_volume(sfx)
        for categoria in ['passos', 'powerups', 'mortes']:
            if categoria in assets.sons:
                for som in assets.sons[categoria].values():
                    if isinstance(som, list):
                        for s in som: s.set_volume(sfx)
                    elif isinstance(som, pygame.mixer.Sound):
                        som.set_volume(sfx)

    # ==========================================
    # GERENCIAMENTO DE ÁUDIO
    # ==========================================
    def play_track(self, track_name):
        if self.current_track == track_name: return
        self.current_track = track_name

        if track_name and (track_name + '_path') in assets.sons['ambiente']:
            caminho = assets.sons['ambiente'][track_name + '_path']
            pygame.mixer.music.load(caminho)
            pygame.mixer.music.play(loops=-1, fade_ms=500)
            self.apply_audio_volumes()  # Garante que a música inicie com o volume correto
        else:
            pygame.mixer.music.fadeout(500)

    def play_ambient(self, amb_name):
        if self.current_ambient == amb_name: return
        if self.current_ambient and self.current_ambient in assets.sons['ambiente']:
            som = assets.sons['ambiente'][self.current_ambient]
            if som: som.stop()
        self.current_ambient = amb_name
        if amb_name and amb_name in assets.sons['ambiente']:
            som = assets.sons['ambiente'][amb_name]
            if som: som.play(loops=-1, fade_ms=1000)

    def play_click(self):
        s = assets.sons['interface'].get('click')
        if s: s.play()

    def check_hover(self, rects_dict, mouse):
        hovered = None
        for name, rect in rects_dict.items():
            if rect.collidepoint(mouse):
                hovered = name
                break
        if hovered != self.last_hover:
            if hovered is not None:
                s = assets.sons['interface'].get('hover')
                if s: s.play()
            self.last_hover = hovered

    def start_game(self, player_name):
        self.current_player = player_name
        self.world = World()

        # Sorteia a cor da skin a cada nova tentativa!
        skin_sorteada = random.choice(["azul", "verde", "vermelho"])
        self.player = Player(self.world, cor_skin=skin_sorteada)

        self.world.camera_y = self.player.wy - PLAYER_ALVO_Y
        self.state = ESTADO_JOGANDO
        self.match_start_time = pygame.time.get_ticks()

        self.match_high_score = self.save_data["players"][self.current_player]["high_score"]
        self.record_broken = False
        self.record_banner_time = 0

    def run(self):
        while True:
            delta_ms = self.clock.tick(30)
            dt = delta_ms / 33.333

            agora = pygame.time.get_ticks()
            mouse = self.get_mapped_mouse()
            hover_dict = {}

            # Gerenciamento Musical Global
            if self.state in [ESTADO_MENU, ESTADO_NEW_PLAYER, ESTADO_LOAD_PLAYER, ESTADO_OPTIONS, ESTADO_CONTROLS,
                              ESTADO_LEADERBOARD]:
                self.play_track('menu')
                self.play_ambient(None)
            elif self.state == ESTADO_JOGANDO:
                self.play_track('jogo')

                # Bioma Ambiente baseado na altura da câmera do player
                linha_cam = int((self.player.wy - 100) // TAMANHO_TILE)
                bioma_atual = self.world.fixar_bioma_linha(linha_cam, self.player.score)
                if bioma_atual == "floresta":
                    self.play_ambient('passaros_floresta')
                elif bioma_atual == "urbano":
                    self.play_ambient('vento_urbano')
                else:
                    self.play_ambient(None)
            elif self.state == ESTADO_GAMEOVER:
                self.play_track(None)
                self.play_ambient(None)

            # ==========================================
            # LOOP DE EVENTOS
            # ==========================================
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

                if self.state == ESTADO_MENU:
                    btn_new = pygame.Rect(LARGURA // 2 - 80, ALTURA // 2 - 60, 160, 45)
                    btn_load = pygame.Rect(LARGURA // 2 - 80, ALTURA // 2 - 5, 160, 45)
                    btn_lb = pygame.Rect(LARGURA // 2 - 80, ALTURA // 2 + 50, 160, 45)
                    btn_opt = pygame.Rect(LARGURA // 2 - 80, ALTURA // 2 + 105, 160, 45)

                    if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                        if btn_new.collidepoint(mouse):
                            self.play_click()
                            self.state = ESTADO_NEW_PLAYER
                            self.input_text = ""
                            self.input_error = ""
                        elif btn_load.collidepoint(mouse):
                            self.play_click()
                            self.state = ESTADO_LOAD_PLAYER
                            self.scroll_y = 0
                        elif btn_lb.collidepoint(mouse):
                            self.play_click()
                            self.state = ESTADO_LEADERBOARD
                            self.scroll_y = 0
                        elif btn_opt.collidepoint(mouse):
                            self.play_click()
                            self.state = ESTADO_OPTIONS

                elif self.state == ESTADO_OPTIONS:
                    btn_fs = pygame.Rect(LARGURA // 2 - 120, OPT_Y_FS, 240, 40)
                    btn_ctrl = pygame.Rect(LARGURA // 2 - 120, OPT_Y_CTRL, 240, 45)
                    btn_back = pygame.Rect(LARGURA // 2 - 120, OPT_Y_BACK, 240, 45)

                    if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                        self.play_click()
                        self.state = ESTADO_MENU
                        save_game(self.save_data)

                    elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                        if btn_fs.collidepoint(mouse):
                            self.play_click()
                            self.settings["fullscreen"] = not self.settings["fullscreen"]
                            self.apply_display_settings()
                            self.update_fullscreen_background()
                            save_game(self.save_data)
                        elif self._try_start_slider_drag(mouse):
                            pass
                        elif btn_ctrl.collidepoint(mouse):
                            self.play_click()
                            self.state = ESTADO_CONTROLS
                        elif btn_back.collidepoint(mouse):
                            self.play_click()
                            self.state = ESTADO_MENU
                            save_game(self.save_data)

                    elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                        if self.dragging_slider:
                            self.play_click()
                            self.dragging_slider = None
                            self.apply_audio_volumes()  # Atualiza o volume em tempo real ao soltar
                            save_game(self.save_data)

                elif self.state == ESTADO_CONTROLS:
                    if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                        self.play_click()
                        self.state = ESTADO_OPTIONS
                    if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                        btn_fechar = pygame.Rect(LARGURA // 2 - 75, (ALTURA - 260) // 2 + 205, 150, 35)
                        if btn_fechar.collidepoint(mouse):
                            self.play_click()
                            self.state = ESTADO_OPTIONS

                elif self.state == ESTADO_LEADERBOARD:
                    if event.type == pygame.MOUSEWHEEL:
                        self.scroll_y += event.y * 30
                    elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                        self.play_click()
                        self.state = ESTADO_MENU
                    if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                        btn_back = pygame.Rect(LARGURA // 2 - 80, ALTURA - 80, 160, 40)
                        if btn_back.collidepoint(mouse):
                            self.play_click()
                            self.state = ESTADO_MENU

                elif self.state == ESTADO_NEW_PLAYER:
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_ESCAPE:
                            self.state = ESTADO_MENU
                        elif event.key == pygame.K_BACKSPACE:
                            self.input_text = self.input_text[:-1]
                        elif event.key == pygame.K_RETURN:
                            self.play_click()
                            self._try_create_player()
                        elif len(self.input_text) < 12 and event.unicode.isprintable():
                            self.input_text += event.unicode
                            self.input_error = ""

                    if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                        btn_create = pygame.Rect(LARGURA // 2 - 80, 300, 160, 40)
                        btn_back = pygame.Rect(LARGURA // 2 - 80, 360, 160, 40)
                        if btn_create.collidepoint(mouse):
                            self.play_click()
                            self._try_create_player()
                        elif btn_back.collidepoint(mouse):
                            self.play_click()
                            self.state = ESTADO_MENU

                elif self.state == ESTADO_LOAD_PLAYER:
                    if event.type == pygame.MOUSEWHEEL:
                        self.scroll_y += event.y * 30
                    elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                        self.play_click()
                        self.state = ESTADO_MENU

                    if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                        btn_back = pygame.Rect(LARGURA // 2 - 80, ALTURA - 80, 160, 40)
                        view_rect = pygame.Rect(LARGURA // 2 - 180, 120, 360, 420)

                        if btn_back.collidepoint(mouse):
                            self.play_click()
                            self.state = ESTADO_MENU
                        elif view_rect.collidepoint(mouse):
                            players_rev = list(self.save_data["players"].keys())[::-1]
                            start_y = 135 + self.scroll_y
                            for p in players_rev:
                                row_rect = pygame.Rect(LARGURA // 2 - 160, start_y, 320, 50)
                                btn_play = pygame.Rect(row_rect.right - 105, row_rect.y + 10, 70, 30)
                                btn_del = pygame.Rect(row_rect.right - 28, row_rect.y + 12, 20, 20)
                                if btn_play.collidepoint(mouse):
                                    self.play_click()
                                    self.start_game(p)
                                    break
                                elif btn_del.collidepoint(mouse):
                                    self.play_click()
                                    del self.save_data["players"][p]
                                    save_game(self.save_data)
                                    break
                                start_y += 60

                elif self.state == ESTADO_JOGANDO:
                    if event.type == pygame.KEYDOWN and event.key in [pygame.K_w, pygame.K_s, pygame.K_a, pygame.K_d]:
                        self.player.queue_input(event.key)

                elif self.state == ESTADO_GAMEOVER:
                    py = (ALTURA - GAMEOVER_PANEL_H) // 2 - 20
                    btn_retry = pygame.Rect(LARGURA // 2 - 150, py + GAMEOVER_PANEL_H - 70, 140, 45)
                    btn_menu = pygame.Rect(LARGURA // 2 + 10, py + GAMEOVER_PANEL_H - 70, 140, 45)

                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_r:
                            self.play_click()
                            self.start_game(self.current_player)
                        if event.key == pygame.K_m:
                            self.play_click()
                            self.state = ESTADO_MENU

                    if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                        if btn_retry.collidepoint(mouse):
                            self.play_click()
                            self.start_game(self.current_player)
                        elif btn_menu.collidepoint(mouse):
                            self.play_click()
                            self.state = ESTADO_MENU

            if self.dragging_slider and pygame.mouse.get_pressed()[0]:
                self.settings[self.dragging_slider] = slider_value_from_mouse(
                    OPT_SLIDER_X, OPT_SLIDER_W, mouse[0]
                )

            # ==========================================
            # RENDERIZAÇÃO DE TELAS E HOVERS
            # ==========================================
            self.game_surface.fill((0, 0, 0))

            if self.state == ESTADO_MENU:
                self.game_surface.blit(assets.images['telas'].get('fundomenu'), (0, 0))
                btn_new = pygame.Rect(LARGURA // 2 - 80, ALTURA // 2 - 60, 160, 45)
                btn_load = pygame.Rect(LARGURA // 2 - 80, ALTURA // 2 - 5, 160, 45)
                btn_lb = pygame.Rect(LARGURA // 2 - 80, ALTURA // 2 + 50, 160, 45)
                btn_opt = pygame.Rect(LARGURA // 2 - 80, ALTURA // 2 + 105, 160, 45)
                draw_button(self.game_surface, btn_new, "NEW PLAYER", btn_new.collidepoint(mouse))
                draw_button(self.game_surface, btn_load, "LOAD PLAYER", btn_load.collidepoint(mouse))
                draw_button(self.game_surface, btn_lb, "LEADERBOARD", btn_lb.collidepoint(mouse))
                draw_button(self.game_surface, btn_opt, "OPTIONS", btn_opt.collidepoint(mouse))
                hover_dict = {"new": btn_new, "load": btn_load, "lb": btn_lb, "opt": btn_opt}

            elif self.state == ESTADO_OPTIONS:
                self.game_surface.blit(assets.images['telas'].get('fullscreen'), (0, 0))
                draw_options_screen(self.game_surface, mouse, self.settings)
                btn_fs = pygame.Rect(LARGURA // 2 - 120, OPT_Y_FS, 240, 40)
                btn_ctrl = pygame.Rect(LARGURA // 2 - 120, OPT_Y_CTRL, 240, 45)
                btn_back = pygame.Rect(LARGURA // 2 - 120, OPT_Y_BACK, 240, 45)
                hover_dict = {"fs": btn_fs, "ctrl": btn_ctrl, "back": btn_back}

            elif self.state == ESTADO_CONTROLS:
                self.game_surface.blit(assets.images['telas'].get('fullscreen'), (0, 0))
                draw_options_screen(self.game_surface, mouse, self.settings)
                draw_control_setup(self.game_surface)
                btn_fechar = pygame.Rect(LARGURA // 2 - 75, (ALTURA - 260) // 2 + 205, 150, 35)
                draw_button(self.game_surface, btn_fechar, "FECHAR", btn_fechar.collidepoint(mouse))
                hover_dict = {"fechar": btn_fechar}

            elif self.state == ESTADO_LEADERBOARD:
                self.game_surface.blit(assets.images['telas'].get('fullscreen'), (0, 0))
                max_scroll = min(0, 420 - len(self.save_data["players"]) * 60 - 20)
                self.scroll_y = clamp(self.scroll_y, max_scroll, 0)
                btn_back, _ = draw_leaderboard_screen(self.game_surface, self.save_data["players"], mouse,
                                                      self.scroll_y)
                hover_dict = {"back": btn_back}

            elif self.state == ESTADO_NEW_PLAYER:
                self.game_surface.blit(assets.images['telas'].get('fullscreen'), (0, 0))
                btn_create, btn_back = draw_new_player_screen(self.game_surface, self.input_text, self.input_error,
                                                              mouse)
                hover_dict = {"create": btn_create, "back": btn_back}

            elif self.state == ESTADO_LOAD_PLAYER:
                self.game_surface.blit(assets.images['telas'].get('fullscreen'), (0, 0))
                max_scroll = min(0, 420 - len(self.save_data["players"]) * 60 - 20)
                self.scroll_y = clamp(self.scroll_y, max_scroll, 0)
                play_btns, del_btns, btn_back, view_rect = draw_load_player_screen(self.game_surface,
                                                                                   self.save_data["players"], mouse,
                                                                                   self.scroll_y)
                hover_dict = {"back": btn_back}
                if view_rect.collidepoint(mouse):
                    for k, v in play_btns.items(): hover_dict[f"p_{k}"] = v
                    for k, v in del_btns.items(): hover_dict[f"d_{k}"] = v

            elif self.state == ESTADO_JOGANDO:
                self.player.update(agora)
                self.world.update(self.player, self.player.score, agora, dt)

                if not self.record_broken and self.player.score > self.match_high_score and self.match_high_score > 0:
                    self.record_broken = True
                    self.record_banner_time = agora
                    s = assets.sons['interface'].get('recorde')
                    if s: s.play()

                    for _ in range(40):
                        vx = random.uniform(-5, 5)
                        vy = random.uniform(-5, 5)
                        px = 60
                        py = 50 + self.world.camera_y
                        self.world.particles.append(
                            Particle(px, py, vx, vy, (255, 215, 0), random.randint(600, 1200), random.randint(3, 6))
                        )

                self.world.draw(self.game_surface, self.player.score, agora)

                hl = pygame.Surface((TAMANHO_TILE, TAMANHO_TILE), pygame.SRCALPHA)
                pygame.draw.rect(hl, (255, 255, 255, 30), (0, 0, TAMANHO_TILE, TAMANHO_TILE), border_radius=8)
                self.game_surface.blit(hl, (int(self.player.wx), int(self.player.wy - self.world.camera_y)))

                self.player.draw(self.game_surface, self.world.camera_y, agora)
                draw_danger_zone(self.game_surface, self.world.camera_y, self.player.wy)

                draw_hud(self.game_surface, self.current_player, self.player.score, self.match_high_score)
                draw_powerups_hud(self.game_surface, self.player, agora)
                self.world.draw_biome_transitions(self.game_surface)

                if self.record_broken and (agora - self.record_banner_time) < 2500:
                    t = agora - self.record_banner_time
                    pulse = 1.0 + 0.05 * math.sin(t / 100.0)

                    if t < 500:
                        frac = t / 500.0
                        y = -50 + 130 * (1 - (1 - frac) ** 2)
                    elif t < 2000:
                        y = 80
                    else:
                        frac = (t - 2000) / 500.0
                        y = 80 - 130 * (frac ** 2)

                    # Usa as surfaces cacheadas em vez de renderizar a fonte novamente
                    new_w = int(self.record_surf_main.get_width() * pulse)
                    new_h = int(self.record_surf_main.get_height() * pulse)

                    surf_main = pygame.transform.scale(self.record_surf_main, (new_w, new_h))
                    surf_shadow = pygame.transform.scale(self.record_surf_shadow, (new_w, new_h))

                    rect = surf_main.get_rect(center=(LARGURA // 2, int(y)))
                    self.game_surface.blit(surf_shadow, (rect.x + 3, rect.y + 3))
                    self.game_surface.blit(surf_main, rect)

                is_dead, cause = self.world.check_death(self.player, agora)
                if is_dead:
                    new_record = self.player.score > self.match_high_score
                    if new_record:
                        self.save_data["players"][self.current_player]["high_score"] = self.player.score
                        save_game(self.save_data)

                    self.death_stats = {
                        "score": self.player.score,
                        "new_record": new_record,
                        "cause": cause,
                        "time_s": (agora - self.match_start_time) // 1000,
                    }

                    # Tocar Som de Morte
                    if cause == "afogado":
                        s = assets.sons['mortes'].get('agua')
                    elif cause == "atropelado":
                        s = assets.sons['mortes'].get('carro')
                    elif cause == "borda":
                        s = assets.sons['mortes'].get('borda')
                    else:
                        s = assets.sons['mortes'].get('geral')

                    if s: s.play()

                    self.state = ESTADO_GAMEOVER
                    self.shake_remaining = 6

            elif self.state == ESTADO_GAMEOVER:
                offset_x = [10, -10, 8, -8, 5, -5][self.shake_remaining - 1] if self.shake_remaining > 0 else 0
                if self.shake_remaining > 0:
                    self.shake_remaining -= 1

                cause = self.death_stats.get("cause", "")

                # Fundo correto de morte
                if cause == "afogado":
                    bg_img = assets.images['telas'].get('morte_afogado')
                elif cause == "borda":
                    bg_img = assets.images['telas'].get('morte_borda')
                elif cause == "atropelado":
                    bg_img = assets.images['telas'].get('morte_carro')
                else:
                    bg_img = assets.images['telas'].get('fullscreen')

                if bg_img:
                    self.game_surface.blit(bg_img, (offset_x, 0))

                py = (ALTURA - GAMEOVER_PANEL_H) // 2 - 20
                btn_retry = pygame.Rect(LARGURA // 2 - 150, py + GAMEOVER_PANEL_H - 70, 140, 45)
                btn_menu = pygame.Rect(LARGURA // 2 + 10, py + GAMEOVER_PANEL_H - 70, 140, 45)
                hover_dict = {"retry": btn_retry, "menu": btn_menu}

                draw_game_over_screen(self.game_surface, self.death_stats, mouse, btn_retry, btn_menu)

            # Executa a checagem global de Hover para todas as telas
            self.check_hover(hover_dict, mouse)

            # Com pygame.SCALED, basta desenhar a game_surface na window sem transform.scale
            self.window.blit(self.game_surface, (0, 0))

            pygame.display.flip()

    def _try_create_player(self):
        nome = self.input_text.strip()
        if not nome:
            self.input_error = "Nome não pode ser vazio!"
        elif nome in self.save_data["players"]:
            self.input_error = "Player já cadastrado!"
        else:
            self.save_data["players"][nome] = {"high_score": 0}
            save_game(self.save_data)
            self.state = ESTADO_LOAD_PLAYER
            self.scroll_y = 0


if __name__ == "__main__":
    Game().run()