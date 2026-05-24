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
    draw_button, draw_hud, draw_danger_zone,
    draw_powerups_hud, draw_new_player_screen, draw_load_player_screen,
    draw_options_screen, draw_leaderboard_screen, draw_game_over_screen,
    draw_pause_screen, draw_transition_overlay,
    GAMEOVER_PANEL_H, MENU_BTN_W, MENU_BTN_H,
    OPT_SLIDER_X, OPT_SLIDER_W, OPT_SLIDER_H,
    OPT_Y_FS, OPT_Y_VOLUME, OPT_Y_BACK,
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
        self.window = None
        self.apply_display_settings()

        pygame.display.set_caption("Cruze a Quatá!")
        self.clock = pygame.time.Clock()

        assets.load_all_assets()
        self.apply_audio_volumes()

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
        self.pending_delete = None
        self.selected_color = COR_RAPOSA_PADRAO

        self.current_track = None
        self.current_ambient = None
        self.last_hover = None

        self.transition = None
        self._pending_setup = None

        texto_rec = "NOVO RECORDE!"
        self.record_surf_main = assets.fonts['botao_grande'].render(texto_rec, True, (255, 215, 0))
        self.record_surf_shadow = assets.fonts['botao_grande'].render(texto_rec, True, (0, 0, 0))

    def apply_display_settings(self):
        if self.settings.get("fullscreen"):
            info = pygame.display.Info()
            self.window = pygame.display.set_mode((info.current_w, info.current_h), pygame.FULLSCREEN)
        else:
            self.window = pygame.display.set_mode((LARGURA, ALTURA), pygame.SCALED)

    def get_mapped_mouse(self):
        mx, my = pygame.mouse.get_pos()
        if self.settings.get("fullscreen"):
            sw, sh = self.window.get_size()
            if sw > 0 and sh > 0:
                return int(mx * LARGURA / sw), int(my * ALTURA / sh)
        return mx, my

    def blit_to_window(self):
        sw, sh = self.window.get_size()
        if (sw, sh) == (LARGURA, ALTURA):
            self.window.blit(self.game_surface, (0, 0))
        else:
            escalada = pygame.transform.scale(self.game_surface, (sw, sh))
            self.window.blit(escalada, (0, 0))

    def request_state(self, new_state, agora, setup_fn=None):
        if self.transition:
            return
        if new_state == self.state and setup_fn is None:
            return
        self._pending_setup = setup_fn
        self.transition = {"target": new_state, "start": agora}

    def _finish_transition(self):
        if self._pending_setup:
            self._pending_setup()
            self._pending_setup = None
        self.transition = None

    def transition_progress(self, agora):
        if not self.transition:
            return 1.0
        return clamp((agora - self.transition["start"]) / TRANSICAO_DURACAO_MS, 0.0, 1.0)

    def is_transitioning(self):
        return self.transition is not None

    def _try_start_slider_drag(self, mouse):
        if slider_hit_test(OPT_SLIDER_X, OPT_Y_VOLUME, OPT_SLIDER_W, OPT_SLIDER_H,
                           self.settings["vol_master"], mouse[0], mouse[1]):
            self.dragging_slider = "vol_master"
            self.settings["vol_master"] = slider_value_from_mouse(OPT_SLIDER_X, OPT_SLIDER_W, mouse[0])
            return True
        return False

    def apply_audio_volumes(self):
        master = self.settings['vol_master'] / 100.0
        self.settings['vol_music'] = self.settings['vol_master']
        self.settings['vol_sfx'] = self.settings['vol_master']

        pygame.mixer.music.set_volume(master)

        for som in assets.sons['ambiente'].values():
            if isinstance(som, pygame.mixer.Sound):
                som.set_volume(master)
        for som in assets.sons['interface'].values():
            if isinstance(som, pygame.mixer.Sound):
                som.set_volume(master)
        for categoria in ['passos', 'powerups', 'mortes']:
            if categoria in assets.sons:
                for som in assets.sons[categoria].values():
                    if isinstance(som, list):
                        for s in som:
                            s.set_volume(master)
                    elif isinstance(som, pygame.mixer.Sound):
                        som.set_volume(master)

    def play_track(self, track_name):
        if self.current_track == track_name:
            return
        self.current_track = track_name

        if track_name and (track_name + '_path') in assets.sons['ambiente']:
            caminho = assets.sons['ambiente'][track_name + '_path']
            pygame.mixer.music.load(caminho)
            pygame.mixer.music.play(loops=-1, fade_ms=500)
            self.apply_audio_volumes()
        else:
            pygame.mixer.music.fadeout(500)

    def play_ambient(self, amb_name):
        if self.current_ambient == amb_name:
            return
        if self.current_ambient and self.current_ambient in assets.sons['ambiente']:
            som = assets.sons['ambiente'][self.current_ambient]
            if som:
                som.stop()
        self.current_ambient = amb_name
        if amb_name and amb_name in assets.sons['ambiente']:
            som = assets.sons['ambiente'][amb_name]
            if som:
                som.play(loops=-1, fade_ms=1000)

    def play_click(self):
        s = assets.sons['interface'].get('click')
        if s:
            s.play()

    def check_hover(self, rects_dict, mouse):
        hovered = None
        for name, rect in rects_dict.items():
            if rect.collidepoint(mouse):
                hovered = name
                break
        if hovered != self.last_hover:
            if hovered is not None:
                s = assets.sons['interface'].get('hover')
                if s:
                    s.play()
            self.last_hover = hovered

    def start_game(self, player_name):
        self.current_player = player_name
        self.world = World()
        cor = self.save_data["players"][player_name].get("cor", COR_RAPOSA_PADRAO)
        self.player = Player(self.world, cor_skin=cor)
        self.world.camera_y = self.player.wy - PLAYER_ALVO_Y
        self.match_start_time = pygame.time.get_ticks()
        self.match_high_score = self.save_data["players"][self.current_player]["high_score"]
        self.record_broken = False
        self.record_banner_time = 0

    def _on_player_death(self, agora, cause):
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

        if cause == "afogado":
            s = assets.sons['mortes'].get('agua')
        elif cause == "atropelado":
            s = assets.sons['mortes'].get('carro')
        elif cause == "borda":
            s = assets.sons['mortes'].get('borda')
        elif cause == "jacare":
            s = assets.sons['mortes'].get('jacare')
        else:
            s = assets.sons['mortes'].get('geral')
        if s:
            s.play()

        self.request_state(ESTADO_GAMEOVER, agora)
        self.shake_remaining = 6

    def _menu_btn_rects(self):
        cx = LARGURA // 2 - MENU_BTN_W // 2
        return {
            "new": pygame.Rect(cx, ALTURA // 2 - 70, MENU_BTN_W, MENU_BTN_H),
            "load": pygame.Rect(cx, ALTURA // 2 - 10, MENU_BTN_W, MENU_BTN_H),
            "lb": pygame.Rect(cx, ALTURA // 2 + 50, MENU_BTN_W, MENU_BTN_H),
            "opt": pygame.Rect(cx, ALTURA // 2 + 110, MENU_BTN_W, MENU_BTN_H),
        }

    def run(self):
        while True:
            delta_ms = self.clock.tick(30)
            dt = delta_ms / 33.333

            agora = pygame.time.get_ticks()
            mouse = self.get_mapped_mouse()
            hover_dict = {}

            if self.transition and self.transition_progress(agora) >= 1.0:
                self.state = self.transition["target"]
                self._finish_transition()

            transitioning = self.is_transitioning()
            prog = self.transition_progress(agora)

            if not transitioning:
                if self.state in [ESTADO_MENU, ESTADO_NEW_PLAYER, ESTADO_LOAD_PLAYER, ESTADO_OPTIONS,
                                  ESTADO_LEADERBOARD]:
                    self.play_track('menu')
                    self.play_ambient(None)
                elif self.state == ESTADO_JOGANDO:
                    self.play_track('jogo')
                    linha_cam = int((self.player.wy - 100) // TAMANHO_TILE)
                    bioma_atual = self.world.fixar_bioma_linha(linha_cam, self.player.score)
                    if bioma_atual == "floresta":
                        self.play_ambient('passaros_floresta')
                    elif bioma_atual == "urbano":
                        self.play_ambient('vento_urbano')
                    else:
                        self.play_ambient(None)
                elif self.state in [ESTADO_GAMEOVER, ESTADO_PAUSE]:
                    self.play_track(None)
                    self.play_ambient(None)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

                if transitioning:
                    continue

                if self.state == ESTADO_PAUSE:
                    if event.type == pygame.KEYDOWN and event.key in (pygame.K_ESCAPE, pygame.K_p):
                        self.play_click()
                        self.state = ESTADO_JOGANDO
                    elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                        btn_resume = pygame.Rect(LARGURA // 2 - 100, 280, 200, 45)
                        btn_menu = pygame.Rect(LARGURA // 2 - 100, 340, 200, 45)
                        if btn_resume.collidepoint(mouse):
                            self.play_click()
                            self.state = ESTADO_JOGANDO
                        elif btn_menu.collidepoint(mouse):
                            self.play_click()
                            self.request_state(ESTADO_MENU, agora)

                elif self.state == ESTADO_MENU:
                    btns = self._menu_btn_rects()
                    if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                        if btns["new"].collidepoint(mouse):
                            self.play_click()
                            self.request_state(ESTADO_NEW_PLAYER, agora,
                                               lambda: (setattr(self, 'input_text', ''),
                                                        setattr(self, 'input_error', ''),
                                                        setattr(self, 'selected_color', COR_RAPOSA_PADRAO)))
                        elif btns["load"].collidepoint(mouse):
                            self.play_click()
                            self.request_state(ESTADO_LOAD_PLAYER, agora,
                                               lambda: (setattr(self, 'scroll_y', 0),
                                                        setattr(self, 'pending_delete', None)))
                        elif btns["lb"].collidepoint(mouse):
                            self.play_click()
                            self.request_state(ESTADO_LEADERBOARD, agora, lambda: setattr(self, 'scroll_y', 0))
                        elif btns["opt"].collidepoint(mouse):
                            self.play_click()
                            self.request_state(ESTADO_OPTIONS, agora)

                elif self.state == ESTADO_OPTIONS:
                    btn_fs = pygame.Rect(LARGURA // 2 - 120, OPT_Y_FS, 240, 40)
                    btn_back = pygame.Rect(LARGURA // 2 - 120, OPT_Y_BACK, 240, 45)

                    if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                        self.play_click()
                        self.request_state(ESTADO_MENU, agora, lambda: save_game(self.save_data))

                    elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                        if btn_fs.collidepoint(mouse):
                            self.play_click()
                            self.settings["fullscreen"] = not self.settings["fullscreen"]
                            self.apply_display_settings()
                            save_game(self.save_data)
                        elif self._try_start_slider_drag(mouse):
                            pass
                        elif btn_back.collidepoint(mouse):
                            self.play_click()
                            self.request_state(ESTADO_MENU, agora, lambda: save_game(self.save_data))

                    elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                        if self.dragging_slider:
                            self.play_click()
                            self.dragging_slider = None
                            self.apply_audio_volumes()
                            save_game(self.save_data)

                elif self.state == ESTADO_LEADERBOARD:
                    if event.type == pygame.MOUSEWHEEL:
                        self.scroll_y += event.y * 30
                    elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                        self.play_click()
                        self.request_state(ESTADO_MENU, agora)
                    if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                        btn_back = pygame.Rect(LARGURA // 2 - 80, ALTURA - 80, 160, 40)
                        if btn_back.collidepoint(mouse):
                            self.play_click()
                            self.request_state(ESTADO_MENU, agora)

                elif self.state == ESTADO_NEW_PLAYER:
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_ESCAPE:
                            self.play_click()
                            self.request_state(ESTADO_MENU, agora)
                        elif event.key == pygame.K_BACKSPACE:
                            self.input_text = self.input_text[:-1]
                        elif event.key == pygame.K_RETURN:
                            self.play_click()
                            self._try_create_player(agora)
                        elif len(self.input_text) < 12 and event.unicode.isprintable():
                            self.input_text += event.unicode
                            self.input_error = ""

                    if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                        start_x = LARGURA // 2 - (len(CORES_RAPOSA) * 76) // 2 + 8
                        for i, cor in enumerate(CORES_RAPOSA):
                            if pygame.Rect(start_x + i * 76, 245, 64, 64).collidepoint(mouse):
                                self.play_click()
                                self.selected_color = cor
                                break
                        btn_create = pygame.Rect(LARGURA // 2 - 90, 340, 180, 45)
                        btn_back = pygame.Rect(LARGURA // 2 - 90, 400, 180, 45)
                        if btn_create.collidepoint(mouse):
                            self.play_click()
                            self._try_create_player(agora)
                        elif btn_back.collidepoint(mouse):
                            self.play_click()
                            self.request_state(ESTADO_MENU, agora)

                elif self.state == ESTADO_LOAD_PLAYER:
                    if event.type == pygame.MOUSEWHEEL:
                        self.scroll_y += event.y * 30
                    elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                        self.play_click()
                        self.pending_delete = None
                        self.request_state(ESTADO_MENU, agora)

                    if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                        btn_back = pygame.Rect(LARGURA // 2 - 80, ALTURA - 80, 160, 40)
                        view_rect = pygame.Rect(LARGURA // 2 - 180, 120, 360, 420)

                        if btn_back.collidepoint(mouse):
                            self.play_click()
                            self.pending_delete = None
                            self.request_state(ESTADO_MENU, agora)
                        elif view_rect.collidepoint(mouse):
                            players_rev = list(self.save_data["players"].keys())[::-1]
                            start_y = 135 + self.scroll_y
                            for p in players_rev:
                                row_rect = pygame.Rect(LARGURA // 2 - 160, start_y, 320, 50)
                                btn_play = pygame.Rect(row_rect.right - 105, row_rect.y + 10, 70, 30)
                                btn_del = pygame.Rect(row_rect.right - 28, row_rect.y + 12, 20, 20)
                                if btn_play.collidepoint(mouse):
                                    self.play_click()
                                    self.pending_delete = None
                                    nome = p
                                    self.request_state(ESTADO_JOGANDO, agora,
                                                       lambda n=nome: self.start_game(n))
                                    break
                                elif btn_del.collidepoint(mouse):
                                    self.play_click()
                                    if self.pending_delete == p:
                                        del self.save_data["players"][p]
                                        save_game(self.save_data)
                                        self.pending_delete = None
                                    else:
                                        self.pending_delete = p
                                    break
                                start_y += 60

                elif self.state == ESTADO_JOGANDO:
                    if event.type == pygame.KEYDOWN:
                        if event.key in (pygame.K_ESCAPE, pygame.K_p):
                            self.play_click()
                            self.state = ESTADO_PAUSE
                        elif event.key in [pygame.K_w, pygame.K_s, pygame.K_a, pygame.K_d]:
                            self.player.queue_input(event.key)

                elif self.state == ESTADO_GAMEOVER:
                    py = (ALTURA - GAMEOVER_PANEL_H) // 2 - 20
                    btn_retry = pygame.Rect(LARGURA // 2 - 150, py + GAMEOVER_PANEL_H - 70, 140, 45)
                    btn_menu = pygame.Rect(LARGURA // 2 + 10, py + GAMEOVER_PANEL_H - 70, 140, 45)

                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_r:
                            self.play_click()
                            nome = self.current_player
                            self.request_state(ESTADO_JOGANDO, agora, lambda n=nome: self.start_game(n))
                        if event.key == pygame.K_m:
                            self.play_click()
                            self.request_state(ESTADO_MENU, agora)

                    if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                        if btn_retry.collidepoint(mouse):
                            self.play_click()
                            nome = self.current_player
                            self.request_state(ESTADO_JOGANDO, agora, lambda n=nome: self.start_game(n))
                        elif btn_menu.collidepoint(mouse):
                            self.play_click()
                            self.request_state(ESTADO_MENU, agora)

            if self.dragging_slider and pygame.mouse.get_pressed()[0]:
                self.settings[self.dragging_slider] = slider_value_from_mouse(
                    OPT_SLIDER_X, OPT_SLIDER_W, mouse[0]
                )
                self.apply_audio_volumes()

            self.game_surface.fill((0, 0, 0))

            if self.state == ESTADO_MENU:
                self.game_surface.blit(assets.images['telas'].get('fundomenu'), (0, 0))
                btns = self._menu_btn_rects()
                draw_button(self.game_surface, btns["new"], "NOVO JOGADOR", btns["new"].collidepoint(mouse))
                draw_button(self.game_surface, btns["load"], "CARREGAR", btns["load"].collidepoint(mouse))
                draw_button(self.game_surface, btns["lb"], "RANKING", btns["lb"].collidepoint(mouse))
                draw_button(self.game_surface, btns["opt"], "OPÇÕES", btns["opt"].collidepoint(mouse))
                hover_dict = btns

            elif self.state == ESTADO_OPTIONS:
                self.game_surface.blit(assets.images['telas'].get('fullscreen'), (0, 0))
                draw_options_screen(self.game_surface, mouse, self.settings)
                btn_fs = pygame.Rect(LARGURA // 2 - 120, OPT_Y_FS, 240, 40)
                btn_back = pygame.Rect(LARGURA // 2 - 120, OPT_Y_BACK, 240, 45)
                hover_dict = {"fs": btn_fs, "back": btn_back}

            elif self.state == ESTADO_LEADERBOARD:
                self.game_surface.blit(assets.images['telas'].get('fullscreen'), (0, 0))
                max_scroll = min(0, 420 - len(self.save_data["players"]) * 60 - 20)
                self.scroll_y = clamp(self.scroll_y, max_scroll, 0)
                btn_back, _ = draw_leaderboard_screen(self.game_surface, self.save_data["players"], mouse,
                                                      self.scroll_y)
                hover_dict = {"back": btn_back}

            elif self.state == ESTADO_NEW_PLAYER:
                self.game_surface.blit(assets.images['telas'].get('fullscreen'), (0, 0))
                btn_create, btn_back, _ = draw_new_player_screen(
                    self.game_surface, self.input_text, self.input_error, mouse, self.selected_color
                )
                hover_dict = {"create": btn_create, "back": btn_back}

            elif self.state == ESTADO_LOAD_PLAYER:
                self.game_surface.blit(assets.images['telas'].get('fullscreen'), (0, 0))
                max_scroll = min(0, 420 - len(self.save_data["players"]) * 60 - 20)
                self.scroll_y = clamp(self.scroll_y, max_scroll, 0)
                play_btns, del_btns, btn_back, view_rect = draw_load_player_screen(
                    self.game_surface, self.save_data["players"], mouse, self.scroll_y, self.pending_delete
                )
                hover_dict = {"back": btn_back}
                if view_rect.collidepoint(mouse):
                    for k, v in play_btns.items():
                        hover_dict[f"p_{k}"] = v
                    for k, v in del_btns.items():
                        hover_dict[f"d_{k}"] = v

            elif self.state == ESTADO_JOGANDO and not transitioning:
                self.player.update(agora)
                self.world.update(self.player, self.player.score, agora, dt)

                if not self.record_broken and self.player.score > self.match_high_score:
                    self.record_broken = True
                    self.record_banner_time = agora
                    s = assets.sons['interface'].get('recorde')
                    if s:
                        s.play()
                    for _ in range(40):
                        vx = random.uniform(-5, 5)
                        vy = random.uniform(-5, 5)
                        px = 60
                        py = 50 + self.world.camera_y
                        self.world.particles.append(
                            Particle(px, py, vx, vy, (255, 215, 0), random.randint(600, 1200), random.randint(3, 6))
                        )

                is_dead, cause = self.world.check_death(self.player, agora)
                if is_dead:
                    self._on_player_death(agora, cause)
                else:
                    self.world.draw(self.game_surface, self.player.score, agora)
                    hl = pygame.Surface((TAMANHO_TILE, TAMANHO_TILE), pygame.SRCALPHA)
                    pygame.draw.rect(hl, (255, 255, 255, 30), (0, 0, TAMANHO_TILE, TAMANHO_TILE), border_radius=8)
                    self.game_surface.blit(hl, (int(self.player.wx), int(self.player.wy - self.world.camera_y)))
                    self.player.draw(self.game_surface, self.world.camera_y, agora)
                    draw_danger_zone(self.game_surface, self.world.camera_y, self.player.wy)
                    draw_hud(self.game_surface, self.current_player, self.player.score, self.match_high_score)
                    draw_powerups_hud(self.game_surface, self.player, agora)

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
                        new_w = int(self.record_surf_main.get_width() * pulse)
                        new_h = int(self.record_surf_main.get_height() * pulse)
                        surf_main = pygame.transform.scale(self.record_surf_main, (new_w, new_h))
                        surf_shadow = pygame.transform.scale(self.record_surf_shadow, (new_w, new_h))
                        rect = surf_main.get_rect(center=(LARGURA // 2, int(y)))
                        self.game_surface.blit(surf_shadow, (rect.x + 3, rect.y + 3))
                        self.game_surface.blit(surf_main, rect)

            elif self.state == ESTADO_PAUSE:
                if self.world and self.player:
                    self.world.draw(self.game_surface, self.player.score, agora)
                    self.player.draw(self.game_surface, self.world.camera_y, agora)
                    draw_hud(self.game_surface, self.current_player, self.player.score, self.match_high_score)
                btn_resume, btn_menu = draw_pause_screen(self.game_surface, mouse)
                hover_dict = {"resume": btn_resume, "menu": btn_menu}

            elif self.state == ESTADO_GAMEOVER:
                offset_x = [10, -10, 8, -8, 5, -5][self.shake_remaining - 1] if self.shake_remaining > 0 else 0
                if self.shake_remaining > 0:
                    self.shake_remaining -= 1

                cause = self.death_stats.get("cause", "")
                if cause == "afogado":
                    bg_img = assets.images['telas'].get('morte_afogado')
                elif cause == "borda":
                    bg_img = assets.images['telas'].get('morte_borda')
                elif cause == "atropelado":
                    bg_img = assets.images['telas'].get('morte_carro')
                elif cause == "jacare":
                    bg_img = assets.images['telas'].get('morte_jacare')
                else:
                    bg_img = assets.images['telas'].get('fullscreen')

                if bg_img:
                    self.game_surface.blit(bg_img, (offset_x, 0))

                py = (ALTURA - GAMEOVER_PANEL_H) // 2 - 20
                btn_retry = pygame.Rect(LARGURA // 2 - 150, py + GAMEOVER_PANEL_H - 70, 140, 45)
                btn_menu = pygame.Rect(LARGURA // 2 + 10, py + GAMEOVER_PANEL_H - 70, 140, 45)
                hover_dict = {"retry": btn_retry, "menu": btn_menu}
                draw_game_over_screen(self.game_surface, self.death_stats, mouse, btn_retry, btn_menu)

            if transitioning:
                draw_transition_overlay(self.game_surface, prog)

            if not transitioning:
                self.check_hover(hover_dict, mouse)

            self.blit_to_window()
            pygame.display.flip()

    def _try_create_player(self, agora):
        nome = self.input_text.strip()
        if not nome:
            self.input_error = "Nome não pode ser vazio!"
        elif nome in self.save_data["players"]:
            self.input_error = "Player já cadastrado!"
        else:
            self.save_data["players"][nome] = {
                "high_score": 0,
                "cor": self.selected_color,
            }
            save_game(self.save_data)
            self.request_state(ESTADO_LOAD_PLAYER, agora,
                               lambda: setattr(self, 'scroll_y', 0))


if __name__ == "__main__":
    Game().run()
