# main.py
import pygame
import sys
from config import *
import assets
from utils import load_save, save_game, draw_text_shadow, clamp
from world import World
from entities import Player
from ui import draw_button, draw_hud, draw_danger_zone, draw_control_setup, draw_powerups_hud, draw_new_player_screen, \
    draw_load_player_screen, draw_options_screen, draw_leaderboard_screen


class Game:
    def __init__(self):
        pygame.init()
        self.save_data = load_save()
        self.settings = self.save_data["settings"]

        # Superfície interna SEMPRE 500x700. O Display escala ela no final.
        self.game_surface = pygame.Surface((LARGURA, ALTURA))
        self.apply_display_settings()

        pygame.display.set_caption("Cruze a Quatá!")
        self.clock = pygame.time.Clock()
        assets.load_all_assets()

        self.state = ESTADO_MENU
        self.world = None
        self.player = None
        self.current_player = None

        self.onboarding_time = 0
        self.shake_remaining = 0
        self.input_text = ""
        self.input_error = ""
        self.scroll_y = 0
        self.dragging_slider = None

    def apply_display_settings(self):
        # Múltiplos da resolução interna base (500x700)
        res_options = [(500, 700), (750, 1050), (1000, 1400)]
        idx = clamp(self.settings["resolution"], 0, 2)
        target_w, target_h = res_options[idx]

        if self.settings["fullscreen"]:
            info = pygame.display.Info()
            # Inicia sem borda ocupando o monitor
            self.window = pygame.display.set_mode((info.current_w, info.current_h), pygame.FULLSCREEN)
        else:
            self.window = pygame.display.set_mode((target_w, target_h))

        # Calcula o scaling e as bordas pretas para manter a proporção (Aspect Ratio) original do jogo
        win_w, win_h = self.window.get_size()
        scale_w = win_w / LARGURA
        scale_h = win_h / ALTURA
        self.scale = min(scale_w, scale_h)

        self.scaled_w = int(LARGURA * self.scale)
        self.scaled_h = int(ALTURA * self.scale)
        self.offset_x = (win_w - self.scaled_w) // 2
        self.offset_y = (win_h - self.scaled_h) // 2

    def get_mapped_mouse(self):
        # Transforma o mouse cru do Monitor de volta na coordenada 500x700 do jogo pra lógica não quebrar
        raw_mx, raw_my = pygame.mouse.get_pos()
        mx = (raw_mx - self.offset_x) / self.scale
        my = (raw_my - self.offset_y) / self.scale
        return int(mx), int(my)

    def start_game(self, player_name):
        self.current_player = player_name
        self.world = World()
        self.player = Player(self.world)
        self.world.camera_y = self.player.wy - PLAYER_ALVO_Y
        self.state = ESTADO_JOGANDO
        self.onboarding_time = pygame.time.get_ticks()

    def run(self):
        while True:
            self.clock.tick(30)
            agora = pygame.time.get_ticks()
            mouse = self.get_mapped_mouse()  # Mouse sempre será interpretado no contexto 500x700!

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit();
                    sys.exit()

                # --- MENU PRINCIPAL ---
                if self.state == ESTADO_MENU:
                    btn_new = pygame.Rect(LARGURA // 2 - 80, ALTURA // 2 - 60, 160, 45)
                    btn_load = pygame.Rect(LARGURA // 2 - 80, ALTURA // 2 - 5, 160, 45)
                    btn_lb = pygame.Rect(LARGURA // 2 - 80, ALTURA // 2 + 50, 160, 45)
                    btn_opt = pygame.Rect(LARGURA // 2 - 80, ALTURA // 2 + 105, 160, 45)

                    if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                        if btn_new.collidepoint(mouse):
                            self.state = ESTADO_NEW_PLAYER;
                            self.input_text = "";
                            self.input_error = ""
                        elif btn_load.collidepoint(mouse):
                            self.state = ESTADO_LOAD_PLAYER;
                            self.scroll_y = 0
                        elif btn_lb.collidepoint(mouse):
                            self.state = ESTADO_LEADERBOARD;
                            self.scroll_y = 0
                        elif btn_opt.collidepoint(mouse):
                            self.state = ESTADO_OPTIONS

                # --- OPÇÕES ---
                elif self.state == ESTADO_OPTIONS:
                    btn_fs = pygame.Rect(LARGURA // 2 - 120, 120, 240, 40)
                    btn_res = pygame.Rect(LARGURA // 2 - 120, 175, 240, 40)
                    track_master = pygame.Rect(LARGURA // 2 - 100, 270, 200, 12)
                    track_music = pygame.Rect(LARGURA // 2 - 100, 330, 200, 12)
                    track_sfx = pygame.Rect(LARGURA // 2 - 100, 390, 200, 12)
                    btn_ctrl = pygame.Rect(LARGURA // 2 - 120, 470, 240, 45)
                    btn_back = pygame.Rect(LARGURA // 2 - 120, 530, 240, 45)

                    if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                        self.state = ESTADO_MENU
                        save_game(self.save_data)

                    elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                        if btn_fs.collidepoint(mouse):
                            self.settings["fullscreen"] = not self.settings["fullscreen"]
                            self.apply_display_settings()
                            save_game(self.save_data)
                        elif btn_res.collidepoint(mouse):
                            self.settings["resolution"] = (self.settings["resolution"] + 1) % 3
                            self.apply_display_settings()
                            save_game(self.save_data)
                        elif track_master.collidepoint(mouse):
                            self.dragging_slider = "vol_master"
                        elif track_music.collidepoint(mouse):
                            self.dragging_slider = "vol_music"
                        elif track_sfx.collidepoint(mouse):
                            self.dragging_slider = "vol_sfx"
                        elif btn_ctrl.collidepoint(mouse):
                            self.state = ESTADO_CONTROLS
                        elif btn_back.collidepoint(mouse):
                            self.state = ESTADO_MENU
                            save_game(self.save_data)

                    elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                        if self.dragging_slider:
                            self.dragging_slider = None
                            save_game(self.save_data)

                # --- CONTROL SETUP ---
                elif self.state == ESTADO_CONTROLS:
                    if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                        self.state = ESTADO_OPTIONS

                    if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                        btn_fechar = pygame.Rect(LARGURA // 2 - 75, (ALTURA - 260) // 2 + 205, 150, 35)
                        if btn_fechar.collidepoint(mouse): self.state = ESTADO_OPTIONS

                # --- LEADERBOARD ---
                elif self.state == ESTADO_LEADERBOARD:
                    if event.type == pygame.MOUSEWHEEL:
                        self.scroll_y += event.y * 30
                    elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                        self.state = ESTADO_MENU
                    if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                        btn_back = pygame.Rect(LARGURA // 2 - 80, ALTURA - 80, 160, 40)
                        if btn_back.collidepoint(mouse): self.state = ESTADO_MENU

                # --- NOVO JOGADOR ---
                elif self.state == ESTADO_NEW_PLAYER:
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_ESCAPE:
                            self.state = ESTADO_MENU
                        elif event.key == pygame.K_BACKSPACE:
                            self.input_text = self.input_text[:-1]
                        elif event.key == pygame.K_RETURN:
                            self._try_create_player()
                        elif len(self.input_text) < 12 and event.unicode.isprintable():
                            self.input_text += event.unicode
                            self.input_error = ""

                    if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                        btn_create = pygame.Rect(LARGURA // 2 - 80, 300, 160, 40)
                        btn_back = pygame.Rect(LARGURA // 2 - 80, 360, 160, 40)
                        if btn_create.collidepoint(mouse):
                            self._try_create_player()
                        elif btn_back.collidepoint(mouse):
                            self.state = ESTADO_MENU

                # --- CARREGAR JOGADOR ---
                elif self.state == ESTADO_LOAD_PLAYER:
                    if event.type == pygame.MOUSEWHEEL:
                        self.scroll_y += event.y * 30
                    elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                        self.state = ESTADO_MENU

                    if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                        btn_back = pygame.Rect(LARGURA // 2 - 80, ALTURA - 80, 160, 40)
                        view_rect = pygame.Rect(LARGURA // 2 - 180, 120, 360, 420)

                        if btn_back.collidepoint(mouse):
                            self.state = ESTADO_MENU
                        elif view_rect.collidepoint(mouse):
                            players_rev = list(self.save_data["players"].keys())[::-1]
                            start_y = 135 + self.scroll_y
                            for p in players_rev:
                                row_rect = pygame.Rect(LARGURA // 2 - 160, start_y, 320, 50)
                                btn_play = pygame.Rect(row_rect.right - 105, row_rect.y + 10, 70, 30)
                                btn_del = pygame.Rect(row_rect.right - 28, row_rect.y + 12, 20, 20)
                                if btn_play.collidepoint(mouse):
                                    self.start_game(p); break
                                elif btn_del.collidepoint(mouse):
                                    del self.save_data["players"][p]
                                    save_game(self.save_data);
                                    break
                                start_y += 60

                # --- JOGANDO ---
                elif self.state == ESTADO_JOGANDO:
                    if event.type == pygame.KEYDOWN and event.key in [pygame.K_w, pygame.K_s, pygame.K_a, pygame.K_d]:
                        self.player.queue_input(event.key)

                # --- GAME OVER ---
                elif self.state == ESTADO_GAMEOVER:
                    btn_retry = pygame.Rect(LARGURA // 2 - 165, ALTURA // 2 + 65, 150, 45)
                    btn_menu = pygame.Rect(LARGURA // 2 + 15, ALTURA // 2 + 65, 150, 45)
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_r: self.start_game(self.current_player)
                        if event.key == pygame.K_m: self.state = ESTADO_MENU
                    if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                        if btn_retry.collidepoint(mouse):
                            self.start_game(self.current_player)
                        elif btn_menu.collidepoint(mouse):
                            self.state = ESTADO_MENU

            # PROCESSAMENTO DO ARRASTO DE SLIDER (Independente de Event Loop pra ser Liso!)
            if pygame.mouse.get_pressed()[0] and self.dragging_slider:
                x_base, w_base = LARGURA // 2 - 100, 200
                val = (mouse[0] - x_base) / w_base * 100
                self.settings[self.dragging_slider] = int(clamp(val, 0, 100))

            # === FASE DE RENDERIZAÇÃO NA SUPERFÍCIE INTERNA ===
            self.game_surface.fill((0, 0, 0))

            if self.state == ESTADO_MENU:
                self.game_surface.blit(assets.images['fundo'], (0, 0))
                btn_new = pygame.Rect(LARGURA // 2 - 80, ALTURA // 2 - 60, 160, 45)
                btn_load = pygame.Rect(LARGURA // 2 - 80, ALTURA // 2 - 5, 160, 45)
                btn_lb = pygame.Rect(LARGURA // 2 - 80, ALTURA // 2 + 50, 160, 45)
                btn_opt = pygame.Rect(LARGURA // 2 - 80, ALTURA // 2 + 105, 160, 45)
                draw_button(self.game_surface, btn_new, "NEW PLAYER", btn_new.collidepoint(mouse))
                draw_button(self.game_surface, btn_load, "LOAD PLAYER", btn_load.collidepoint(mouse))
                draw_button(self.game_surface, btn_lb, "LEADERBOARD", btn_lb.collidepoint(mouse))
                draw_button(self.game_surface, btn_opt, "OPTIONS", btn_opt.collidepoint(mouse))

            elif self.state == ESTADO_OPTIONS:
                self.game_surface.blit(assets.images['fundo'], (0, 0))
                draw_options_screen(self.game_surface, mouse, self.settings)

            elif self.state == ESTADO_CONTROLS:
                self.game_surface.blit(assets.images['fundo'], (0, 0))
                draw_options_screen(self.game_surface, mouse, self.settings)
                draw_control_setup(self.game_surface)
                btn_fechar = pygame.Rect(LARGURA // 2 - 75, (ALTURA - 260) // 2 + 205, 150, 35)
                draw_button(self.game_surface, btn_fechar, "FECHAR", btn_fechar.collidepoint(mouse))

            elif self.state == ESTADO_LEADERBOARD:
                self.game_surface.blit(assets.images['fundo'], (0, 0))
                max_scroll = min(0, 420 - len(self.save_data["players"]) * 60 - 20)
                self.scroll_y = clamp(self.scroll_y, max_scroll, 0)
                draw_leaderboard_screen(self.game_surface, self.save_data["players"], mouse, self.scroll_y)

            elif self.state == ESTADO_NEW_PLAYER:
                self.game_surface.blit(assets.images['fundo'], (0, 0))
                draw_new_player_screen(self.game_surface, self.input_text, self.input_error, mouse)

            elif self.state == ESTADO_LOAD_PLAYER:
                self.game_surface.blit(assets.images['fundo'], (0, 0))
                max_scroll = min(0, 420 - len(self.save_data["players"]) * 60 - 20)
                self.scroll_y = clamp(self.scroll_y, max_scroll, 0)
                draw_load_player_screen(self.game_surface, self.save_data["players"], mouse, self.scroll_y)

            elif self.state == ESTADO_JOGANDO:
                self.player.update(agora)
                self.world.update(self.player, self.player.score, agora)
                self.world.draw(self.game_surface, self.player.score, agora)

                hl = pygame.Surface((TAMANHO_TILE, TAMANHO_TILE), pygame.SRCALPHA)
                pygame.draw.rect(hl, (255, 255, 255, 30), (0, 0, TAMANHO_TILE, TAMANHO_TILE), border_radius=8)
                self.game_surface.blit(hl, (int(self.player.wx), int(self.player.wy - self.world.camera_y)))

                self.player.draw(self.game_surface, self.world.camera_y, agora)
                draw_danger_zone(self.game_surface, self.world.camera_y, self.player.wy)

                high = self.save_data["players"][self.current_player]["high_score"]
                draw_hud(self.game_surface, self.current_player, self.player.score, high)
                draw_powerups_hud(self.game_surface, self.player, agora)

                if self.world.check_death(self.player, agora):
                    if self.player.score > high:
                        self.save_data["players"][self.current_player]["high_score"] = self.player.score
                        save_game(self.save_data)
                    self.state = ESTADO_GAMEOVER
                    self.shake_remaining = 6

            elif self.state == ESTADO_GAMEOVER:
                offset_x = [10, -10, 8, -8, 5, -5][self.shake_remaining - 1] if self.shake_remaining > 0 else 0
                if self.shake_remaining > 0: self.shake_remaining -= 1

                self.game_surface.blit(assets.images['fundo_fim'], (offset_x, 0))
                draw_text_shadow(self.game_surface, assets.fonts['botao_grande'], f"Pontuação: {self.player.score}",
                                 (255, 220, 50), (LARGURA // 2, ALTURA // 2 + 15))

                r_btn = pygame.Rect(LARGURA // 2 - 165, ALTURA // 2 + 65, 150, 45)
                m_btn = pygame.Rect(LARGURA // 2 + 15, ALTURA // 2 + 65, 150, 45)
                draw_button(self.game_surface, r_btn, "RETRY", r_btn.collidepoint(mouse))
                draw_button(self.game_surface, m_btn, "MENU", m_btn.collidepoint(mouse))

            # === FASE DE POST-PROCESSING E DISPLAY FINAL ===
            self.window.fill((12, 15, 22))  # Cor do Pillarbox (Bordas ao redor do Jogo)
            scaled_final = pygame.transform.scale(self.game_surface, (self.scaled_w, self.scaled_h))
            self.window.blit(scaled_final, (self.offset_x, self.offset_y))

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