# main.py
import pygame
import sys
from config import *
import assets
from utils import load_save, save_game, draw_text_shadow, clamp
from world import World
from entities import Player
from ui import draw_button, draw_hud, draw_danger_zone, draw_controls, draw_powerups_hud, draw_new_player_screen, \
    draw_load_player_screen


class Game:
    def __init__(self):
        pygame.init()
        self.window = pygame.display.set_mode((LARGURA, ALTURA))
        pygame.display.set_caption("Cruze a Quatá! - Pro Edition")
        self.clock = pygame.time.Clock()
        assets.load_all_assets()

        self.save_data = load_save()
        self.state = ESTADO_MENU

        self.world = None
        self.player = None
        self.current_player = None

        self.show_controls = False
        self.onboarding_time = 0
        self.shake_remaining = 0
        self.input_text = ""
        self.input_error = ""
        self.scroll_y = 0

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
            mouse = pygame.mouse.get_pos()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit();
                    sys.exit()

                # --- MENU PRINCIPAL ---
                if self.state == ESTADO_MENU:
                    btn_new = pygame.Rect(LARGURA // 2 - 80, ALTURA // 2 - 10, 160, 45)
                    btn_load = pygame.Rect(LARGURA // 2 - 80, ALTURA // 2 + 45, 160, 45)
                    btn_ctrl = pygame.Rect(LARGURA // 2 - 80, ALTURA // 2 + 100, 160, 45)
                    btn_fechar_ctrl = pygame.Rect(LARGURA // 2 - 75, (ALTURA - 260) // 2 + 205, 150, 35)

                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_c: self.show_controls = not self.show_controls
                        if event.key == pygame.K_ESCAPE: self.show_controls = False

                    # Captura o CLIQUE (Mouse down) apenas uma vez
                    if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                        if self.show_controls and btn_fechar_ctrl.collidepoint(mouse):
                            self.show_controls = False
                        elif not self.show_controls:
                            if btn_ctrl.collidepoint(mouse):
                                self.show_controls = True
                            elif btn_new.collidepoint(mouse):
                                self.state = ESTADO_NEW_PLAYER
                                self.input_text = ""
                                self.input_error = ""
                            elif btn_load.collidepoint(mouse):
                                self.state = ESTADO_LOAD_PLAYER
                                self.scroll_y = 0

                # --- MENU NOVO JOGADOR ---
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

                # --- MENU CARREGAR JOGADOR ---
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
                            start_y = 135 + self.scroll_y
                            for p in list(self.save_data["players"].keys()):
                                row_rect = pygame.Rect(LARGURA // 2 - 160, start_y, 320, 50)
                                btn_play = pygame.Rect(row_rect.right - 105, row_rect.y + 10, 70, 30)
                                btn_del = pygame.Rect(row_rect.right - 28, row_rect.y + 12, 20, 20)

                                if btn_play.collidepoint(mouse):
                                    self.start_game(p)
                                    break
                                elif btn_del.collidepoint(mouse):
                                    del self.save_data["players"][p]
                                    save_game(self.save_data)
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

            self.window.fill((0, 0, 0))

            # --- DRAW CALLS ---
            if self.state == ESTADO_MENU:
                self.window.blit(assets.images['fundo'], (0, 0))

                btn_new = pygame.Rect(LARGURA // 2 - 80, ALTURA // 2 - 10, 160, 45)
                btn_load = pygame.Rect(LARGURA // 2 - 80, ALTURA // 2 + 45, 160, 45)
                btn_ctrl = pygame.Rect(LARGURA // 2 - 80, ALTURA // 2 + 100, 160, 45)

                draw_button(self.window, btn_new, "NEW PLAYER", btn_new.collidepoint(mouse))
                draw_button(self.window, btn_load, "LOAD PLAYER", btn_load.collidepoint(mouse))
                draw_button(self.window, btn_ctrl, "CONTROLS", btn_ctrl.collidepoint(mouse))

                if self.show_controls:
                    draw_controls(self.window)
                    btn_fechar = pygame.Rect(LARGURA // 2 - 75, (ALTURA - 260) // 2 + 205, 150, 35)
                    draw_button(self.window, btn_fechar, "FECHAR", btn_fechar.collidepoint(mouse))

            elif self.state == ESTADO_NEW_PLAYER:
                self.window.blit(assets.images['fundo'], (0, 0))
                draw_new_player_screen(self.window, self.input_text, self.input_error, mouse)

            elif self.state == ESTADO_LOAD_PLAYER:
                self.window.blit(assets.images['fundo'], (0, 0))

                total_height = len(self.save_data["players"]) * 60
                max_scroll = min(0, 420 - total_height - 20)
                self.scroll_y = clamp(self.scroll_y, max_scroll, 0)

                draw_load_player_screen(self.window, self.save_data["players"], mouse, self.scroll_y)

            elif self.state == ESTADO_JOGANDO:
                self.player.update(agora)
                self.world.update(self.player, self.player.score, agora)
                self.world.draw(self.window, self.player.score, agora)

                hl = pygame.Surface((TAMANHO_TILE, TAMANHO_TILE), pygame.SRCALPHA)
                pygame.draw.rect(hl, (255, 255, 255, 30), (0, 0, TAMANHO_TILE, TAMANHO_TILE), border_radius=8)
                self.window.blit(hl, (int(self.player.wx), int(self.player.wy - self.world.camera_y)))

                self.player.draw(self.window, self.world.camera_y, agora)
                draw_danger_zone(self.window, self.world.camera_y, self.player.wy)

                high = self.save_data["players"][self.current_player]["high_score"]
                draw_hud(self.window, self.current_player, self.player.score, high)
                draw_powerups_hud(self.window, self.player, agora)

                if self.world.check_death(self.player, agora):
                    if self.player.score > high:
                        self.save_data["players"][self.current_player]["high_score"] = self.player.score
                        save_game(self.save_data)
                    self.state = ESTADO_GAMEOVER
                    self.shake_remaining = 6

            elif self.state == ESTADO_GAMEOVER:
                offset_x = [10, -10, 8, -8, 5, -5][self.shake_remaining - 1] if self.shake_remaining > 0 else 0
                if self.shake_remaining > 0: self.shake_remaining -= 1

                self.window.blit(assets.images['fundo_fim'], (offset_x, 0))
                draw_text_shadow(self.window, assets.fonts['botao_grande'], f"Pontuação: {self.player.score}",
                                 (255, 220, 50), (LARGURA // 2, ALTURA // 2 + 15))

                r_btn = pygame.Rect(LARGURA // 2 - 165, ALTURA // 2 + 65, 150, 45)
                m_btn = pygame.Rect(LARGURA // 2 + 15, ALTURA // 2 + 65, 150, 45)
                draw_button(self.window, r_btn, "RETRY", r_btn.collidepoint(mouse))
                draw_button(self.window, m_btn, "MENU", m_btn.collidepoint(mouse))

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
            self.start_game(nome)


if __name__ == "__main__":
    Game().run()