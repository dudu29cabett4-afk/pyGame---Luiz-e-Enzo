# ui.py
import pygame
from config import *
import assets
from utils import draw_text_shadow


def draw_button(surface, rect, label, hover, font_key='botao'):
    cor = (180, 70, 10) if hover else (30, 30, 60)
    pygame.draw.rect(surface, cor, rect, border_radius=8)
    pygame.draw.rect(surface, (255, 200, 50), rect, 2, border_radius=8)
    t = assets.fonts[font_key].render(label, True, (255, 255, 255))
    surface.blit(t, t.get_rect(center=rect.center))


def draw_hud(surface, player_name, score, high_score):
    draw_text_shadow(surface, assets.fonts['hud'], f"Player: {player_name}", (150, 220, 255), (15, 10),
                     anchor="topleft", offset=1)
    draw_text_shadow(surface, assets.fonts['score'], f"Score: {score}", (255, 255, 255), (15, 30), anchor="topleft")
    draw_text_shadow(surface, assets.fonts['hud'], f"High: {high_score}", (255, 200, 50), (15, 55), anchor="topleft")


def draw_danger_zone(surface, camera_y, player_wy):
    dist = ALTURA - (player_wy - camera_y)
    alpha = min(150, max(0, int(255 - (dist * 1.5))))
    if alpha > 0:
        rect = pygame.Surface((LARGURA, 40), pygame.SRCALPHA)
        rect.fill((255, 0, 0, alpha))
        surface.blit(rect, (0, ALTURA - 40))


def draw_controls(surface):
    overlay = pygame.Surface((LARGURA, ALTURA), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 180))
    surface.blit(overlay, (0, 0))

    pw, ph = 320, 260
    px, py = (LARGURA - pw) // 2, (ALTURA - ph) // 2

    painel = pygame.Surface((pw, ph), pygame.SRCALPHA)
    painel.fill((15, 18, 42, 235))
    pygame.draw.rect(painel, (255, 200, 50), (0, 0, pw, ph), 3, border_radius=14)
    surface.blit(painel, (px, py))

    draw_text_shadow(surface, assets.fonts['botao_grande'], "CONTROLS", (255, 210, 50), (LARGURA // 2, py + 30))
    pygame.draw.line(surface, (255, 200, 50), (px + 20, py + 50), (px + pw - 20, py + 50), 1)

    msgs = [
        "W A S D - Movimentar",
        "R - Tentar Novamente (Retry)",
        "M - Voltar ao Menu",
        "ESC - Fechar telas/Voltar"
    ]

    y = py + 80
    for msg in msgs:
        draw_text_shadow(surface, assets.fonts['hud'], msg, (225, 232, 245), (LARGURA // 2, y))
        y += 35


def desenhar_hud_status(surface, bx, by, icon, restante_ms, total_ms, texto, cor_barra):
    frac = max(0.0, restante_ms / total_ms)
    bw, bh = 110, 16
    surface.blit(icon, (bx - 30, by - 10))
    pygame.draw.rect(surface, (30, 30, 60), (bx, by, bw, bh), border_radius=4)
    pygame.draw.rect(surface, cor_barra, (bx, by, int(bw * frac), bh), border_radius=4)
    pygame.draw.rect(surface, (255, 220, 80), (bx, by, bw, bh), 1, border_radius=4)
    t = assets.fonts['kbd'].render(texto, True, (255, 255, 255))
    surface.blit(t, t.get_rect(center=(bx + bw // 2, by + bh // 2)))


def draw_powerups_hud(surface, player, agora):
    if player.tem_escudo:
        bx, by = LARGURA - 120, 15
        surface.blit(assets.images['pu_escudo'], (bx - 30, by - 10))
        pygame.draw.rect(surface, (60, 30, 10), (bx, by, 110, 16), border_radius=4)
        pygame.draw.rect(surface, (255, 210, 50), (bx, by, 110, 16), border_radius=4)
        pygame.draw.rect(surface, (255, 240, 120), (bx, by, 110, 16), 1, border_radius=4)
        t = assets.fonts['kbd'].render("ESCUDO ATIVO", True, (60, 30, 0))
        surface.blit(t, t.get_rect(center=(bx + 55, by + 8)))

    if agora < player.xp2_ate:
        desenhar_hud_status(surface, LARGURA - 120, 45, assets.images['pu_xp2'],
                            player.xp2_ate - agora, POWERUP_XP2_DURACAO_MS,
                            f"XP x2 {(player.xp2_ate - agora) // 1000 + 1}s", (255, 210, 80))


def draw_new_player_screen(surface, input_text, error_msg, mouse_pos):
    overlay = pygame.Surface((LARGURA, ALTURA), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 200))
    surface.blit(overlay, (0, 0))

    draw_text_shadow(surface, assets.fonts['botao_grande'], "NEW PLAYER", (255, 210, 50), (LARGURA // 2, 150))

    box_rect = pygame.Rect(LARGURA // 2 - 120, 200, 240, 40)
    pygame.draw.rect(surface, (20, 20, 40), box_rect, border_radius=5)
    pygame.draw.rect(surface, (255, 255, 255), box_rect, 2, border_radius=5)

    txt = assets.fonts['hud'].render(input_text + ("_" if pygame.time.get_ticks() % 1000 < 500 else ""), True,
                                     (255, 255, 255))
    surface.blit(txt, txt.get_rect(center=box_rect.center))

    if error_msg:
        draw_text_shadow(surface, assets.fonts['kbd'], error_msg, (255, 50, 50), (LARGURA // 2, 260))

    btn_create = pygame.Rect(LARGURA // 2 - 80, 300, 160, 40)
    btn_back = pygame.Rect(LARGURA // 2 - 80, 360, 160, 40)

    draw_button(surface, btn_create, "SALVAR", btn_create.collidepoint(mouse_pos))
    draw_button(surface, btn_back, "VOLTAR", btn_back.collidepoint(mouse_pos))

    return btn_create, btn_back


def draw_load_player_screen(surface, players_dict, mouse_pos, scroll_y):
    overlay = pygame.Surface((LARGURA, ALTURA), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 200))
    surface.blit(overlay, (0, 0))

    draw_text_shadow(surface, assets.fonts['botao_grande'], "SELECT PLAYER", (255, 210, 50), (LARGURA // 2, 80))

    play_buttons = {}
    delete_buttons = {}

    view_rect = pygame.Rect(LARGURA // 2 - 180, 120, 360, 420)
    pygame.draw.rect(surface, (15, 18, 42), view_rect, border_radius=10)
    pygame.draw.rect(surface, (100, 100, 150), view_rect, 2, border_radius=10)

    surface.set_clip(view_rect)

    players = list(players_dict.keys())
    start_y = 135 + scroll_y

    active_mouse = mouse_pos if view_rect.collidepoint(mouse_pos) else (-1, -1)

    if not players:
        draw_text_shadow(surface, assets.fonts['hud'], "Nenhum jogador cadastrado.", (150, 150, 150),
                         (LARGURA // 2, start_y + 50))
    else:
        for p in players:
            score = players_dict[p].get("high_score", 0)

            row_rect = pygame.Rect(LARGURA // 2 - 160, start_y, 320, 50)
            pygame.draw.rect(surface, (30, 30, 60), row_rect, border_radius=8)

            n_txt = assets.fonts['hud'].render(p, True, (255, 255, 255))
            s_txt = assets.fonts['kbd'].render(f"High: {score}", True, (255, 200, 50))
            surface.blit(n_txt, (row_rect.x + 15, row_rect.y + 8))
            surface.blit(s_txt, (row_rect.x + 15, row_rect.y + 30))

            # Botao Play
            btn_play = pygame.Rect(row_rect.right - 105, row_rect.y + 10, 70, 30)
            draw_button(surface, btn_play, "PLAY", btn_play.collidepoint(active_mouse), 'kbd')

            # Botao Deletar (Menor)
            btn_del = pygame.Rect(row_rect.right - 28, row_rect.y + 12, 20, 20)
            hover_del = btn_del.collidepoint(active_mouse)
            pygame.draw.rect(surface, (200, 50, 50) if hover_del else (120, 30, 30), btn_del, border_radius=4)
            pygame.draw.rect(surface, (255, 100, 100), btn_del, 1, border_radius=4)

            # Cruz branca (X) ajustada para o botão menor
            pygame.draw.line(surface, (255, 255, 255), (btn_del.x + 5, btn_del.y + 5),
                             (btn_del.right - 5, btn_del.bottom - 5), 2)
            pygame.draw.line(surface, (255, 255, 255), (btn_del.right - 5, btn_del.y + 5),
                             (btn_del.x + 5, btn_del.bottom - 5), 2)

            play_buttons[p] = btn_play
            delete_buttons[p] = btn_del
            start_y += 60

    surface.set_clip(None)

    btn_back = pygame.Rect(LARGURA // 2 - 80, ALTURA - 80, 160, 40)
    draw_button(surface, btn_back, "VOLTAR", btn_back.collidepoint(mouse_pos))

    return play_buttons, delete_buttons, btn_back, view_rect