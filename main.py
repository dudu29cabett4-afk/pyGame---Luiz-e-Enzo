# main.py
import pygame
import sys
from config import *
import assets
from utils import load_save, save_game, draw_text_shadow
from world import World
from entities import Player
from ui import draw_button, draw_hud, draw_danger_zone, draw_controls, draw_powerups_hud


class Game:
    def __init__(self):
        pygame.init()
        self.window = pygame.display.set_mode((LARGURA, ALTURA))
        pygame.display.set_caption("Cruze a Quatá! - Pro Edition")
        self.clock = pygame.time.Clock()
        assets.load_all_assets()

        self.save_data = load_save()
        self.high_score = self.save_data.get('high_score', 0)
        self.state = ESTADO_MENU

        self.world = None
        self.player = None

        self.show_controls = False
        self.onboarding_time = 0
        self.shake_remaining = 0

    def start_game(self):
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

                if self.state == ESTADO_MENU:
                    btn_inst = pygame.Rect(LARGURA // 2 - 110, ALTURA // 2 + 30, 220, 58)
                    btn_fechar = pygame.Rect(LARGURA // 2 - 75, (ALTURA - 300) // 2 + 242, 150, 42)

                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_SPACE and not self.show_controls: self.start_game()
                        if event.key == pygame.K_c: self.show_controls = not self.show_controls
                        if event.key == pygame.K_ESCAPE: self.show_controls = False

                    if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                        if self.show_controls and btn_fechar.collidepoint(mouse):
                            self.show_controls = False
                        elif not self.show_controls and btn_inst.collidepoint(mouse):
                            self.show_controls = True

                elif self.state == ESTADO_JOGANDO:
                    if event.type == pygame.KEYDOWN and event.key in [pygame.K_w, pygame.K_s, pygame.K_a, pygame.K_d]:
                        self.player.queue_input(event.key)

                elif self.state == ESTADO_GAMEOVER:
                    btn_retry = pygame.Rect(LARGURA // 2 - 185, ALTURA // 2 + 65, 170, 58)
                    btn_menu = pygame.Rect(LARGURA // 2 + 15, ALTURA // 2 + 65, 170, 58)
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_r: self.start_game()
                        if event.key == pygame.K_m: self.state = ESTADO_MENU
                    if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                        if btn_retry.collidepoint(mouse): self.start_game()
                        if btn_menu.collidepoint(mouse): self.state = ESTADO_MENU

            self.window.fill((0, 0, 0))

            if self.state == ESTADO_MENU:
                self.window.blit(assets.images['fundo'], (0, 0))
                if pygame.time.get_ticks() % 1000 < 500:
                    draw_text_shadow(self.window, assets.fonts['botao'], "ESPAÇO para começar", (255, 255, 255),
                                     (LARGURA // 2, ALTURA // 2 - 20))

                draw_button(self.window, pygame.Rect(LARGURA // 2 - 110, ALTURA // 2 + 30, 220, 58), "CONTROLES", "C",
                            pygame.Rect(LARGURA // 2 - 110, ALTURA // 2 + 30, 220, 58).collidepoint(mouse))

                if self.show_controls:
                    draw_controls(self.window)
                    draw_button(self.window, pygame.Rect(LARGURA // 2 - 75, (ALTURA - 300) // 2 + 242, 150, 42),
                                "FECHAR", "ESC",
                                pygame.Rect(LARGURA // 2 - 75, (ALTURA - 300) // 2 + 242, 150, 42).collidepoint(mouse))

            elif self.state == ESTADO_JOGANDO:
                self.player.update(agora)
                self.world.update(self.player, self.player.score, agora)

                self.world.draw(self.window, self.player.score, agora)
                hl = pygame.Surface((TAMANHO_TILE, TAMANHO_TILE), pygame.SRCALPHA)
                pygame.draw.rect(hl, (255, 255, 255, 30), (0, 0, TAMANHO_TILE, TAMANHO_TILE), border_radius=8)
                self.window.blit(hl, (int(self.player.wx), int(self.player.wy - self.world.camera_y)))

                self.player.draw(self.window, self.world.camera_y, agora)
                draw_danger_zone(self.window, self.world.camera_y, self.player.wy)
                draw_hud(self.window, self.player.score, self.high_score)
                draw_powerups_hud(self.window, self.player, agora)

                if agora - self.onboarding_time < 4000:
                    txt = assets.fonts['hud'].render("W = Sobe | Fuja da faixa vermelha!", True, (255, 255, 255))
                    rt = txt.get_rect(center=(LARGURA // 2, ALTURA // 2 + 50))
                    pygame.draw.rect(self.window, (0, 0, 0, 150), rt.inflate(20, 10), border_radius=5)
                    self.window.blit(txt, rt)

                if self.world.check_death(self.player, agora):
                    if self.player.score > self.high_score:
                        self.high_score = self.player.score
                        self.save_data['high_score'] = self.high_score
                        save_game(self.save_data)
                    self.state = ESTADO_GAMEOVER
                    self.shake_remaining = 6

            elif self.state == ESTADO_GAMEOVER:
                offset_x = 0
                if self.shake_remaining > 0:
                    offset_x = [10, -10, 8, -8, 5, -5][self.shake_remaining - 1]
                    self.shake_remaining -= 1

                self.window.blit(assets.images['fundo_fim'], (offset_x, 0))
                draw_text_shadow(self.window, assets.fonts['botao'], f"Pontuação: {self.player.score}", (255, 220, 50),
                                 (LARGURA // 2, ALTURA // 2 + 15))

                r_btn = pygame.Rect(LARGURA // 2 - 185, ALTURA // 2 + 65, 170, 58)
                m_btn = pygame.Rect(LARGURA // 2 + 15, ALTURA // 2 + 65, 170, 58)
                draw_button(self.window, r_btn, "RETRY", "R", r_btn.collidepoint(mouse))
                draw_button(self.window, m_btn, "MENU", "M", m_btn.collidepoint(mouse))

            pygame.display.flip()


if __name__ == "__main__":
    Game().run()