# ui.py
import math
import pygame
from config import *
import assets
from utils import draw_text_shadow, clamp

# Cache global para overlays escuros
_overlay_cache = {}

def get_overlay(alpha):
    if alpha not in _overlay_cache:
        surf = pygame.Surface((LARGURA, ALTURA), pygame.SRCALPHA)
        surf.fill((0, 0, 0, alpha))
        _overlay_cache[alpha] = surf
    return _overlay_cache[alpha]

# Layout da tela de opções (compartilhado com main.py)
OPT_SLIDER_X = LARGURA // 2 - 100
OPT_SLIDER_W = 200
OPT_SLIDER_H = 12
OPT_SLIDER_KNOB = 14
OPT_Y_FS = 120
OPT_Y_MASTER = 200
OPT_Y_MUSIC = 260
OPT_Y_SFX = 320
OPT_Y_CTRL = 400
OPT_Y_BACK = 460


def draw_button(surface, rect, label, hover, font_key='botao'):
    cor = (180, 70, 10) if hover else (30, 30, 60)
    pygame.draw.rect(surface, cor, rect, border_radius=8)
    pygame.draw.rect(surface, (255, 200, 50), rect, 2, border_radius=8)
    t = assets.fonts[font_key].render(label, True, (255, 255, 255))
    surface.blit(t, t.get_rect(center=rect.center))


def slider_thumb_x(x, w, value):
    return x + int(w * (value / 100))


def slider_hit_test(x, y, w, h, value, mx, my):
    thumb_x = slider_thumb_x(x, w, value)
    thumb_y = y + h // 2
    track = pygame.Rect(x, y - 14, w, h + 28)
    if track.collidepoint(mx, my):
        return True
    dx, dy = mx - thumb_x, my - thumb_y
    return dx * dx + dy * dy <= OPT_SLIDER_KNOB ** 2


def slider_value_from_mouse(x, w, mx):
    return int(clamp((mx - x) / w * 100, 0, 100))


def draw_slider(surface, x, y, w, h, value, label):
    draw_text_shadow(surface, assets.fonts['hud'], label, (255, 255, 255), (x + w // 2, y - 20))
    track_rect = pygame.Rect(x, y, w, h)
    pygame.draw.rect(surface, (30, 30, 50), track_rect, border_radius=h // 2)
    fill_width = int(w * (value / 100))
    if fill_width > 0:
        fill_rect = pygame.Rect(x, y, fill_width, h)
        pygame.draw.rect(surface, (255, 200, 50), fill_rect, border_radius=h // 2)
    thumb_x = x + fill_width
    thumb_y = y + h // 2
    pygame.draw.circle(surface, (255, 255, 255), (thumb_x, thumb_y), OPT_SLIDER_KNOB)
    pygame.draw.circle(surface, (150, 100, 20), (thumb_x, thumb_y), OPT_SLIDER_KNOB, 2)
    draw_text_shadow(surface, assets.fonts['kbd'], f"{value}%", (200, 200, 200), (x + w + 30, y + h // 2))


def draw_options_screen(surface, mouse_pos, settings):
    surface.blit(get_overlay(210), (0, 0))

    draw_text_shadow(surface, assets.fonts['botao_grande'], "OPTIONS", (255, 210, 50), (LARGURA // 2, 70))

    btn_fs = pygame.Rect(LARGURA // 2 - 120, OPT_Y_FS, 240, 40)
    fs_text = "FULLSCREEN: ON" if settings["fullscreen"] else "FULLSCREEN: OFF"
    draw_button(surface, btn_fs, fs_text, btn_fs.collidepoint(mouse_pos))

    draw_slider(surface, OPT_SLIDER_X, OPT_Y_MASTER, OPT_SLIDER_W, OPT_SLIDER_H, settings["vol_master"], "VOLUME MASTER")
    draw_slider(surface, OPT_SLIDER_X, OPT_Y_MUSIC, OPT_SLIDER_W, OPT_SLIDER_H, settings["vol_music"], "VOLUME MÚSICA")
    draw_slider(surface, OPT_SLIDER_X, OPT_Y_SFX, OPT_SLIDER_W, OPT_SLIDER_H, settings["vol_sfx"], "VOLUME EFEITOS")

    btn_ctrl = pygame.Rect(LARGURA // 2 - 120, OPT_Y_CTRL, 240, 45)
    btn_back = pygame.Rect(LARGURA // 2 - 120, OPT_Y_BACK, 240, 45)

    draw_button(surface, btn_ctrl, "CONTROL SETUP", btn_ctrl.collidepoint(mouse_pos))
    draw_button(surface, btn_back, "VOLTAR", btn_back.collidepoint(mouse_pos))


def draw_hud(surface, player_name, score, high_score):
    draw_text_shadow(surface, assets.fonts['botao_grande'], f"{player_name}", (0, 255, 200), (15, 10), anchor="topleft",
                     offset=2)
    draw_text_shadow(surface, assets.fonts['score'], f"Score: {score}", (255, 255, 255), (15, 42), anchor="topleft")
    draw_text_shadow(surface, assets.fonts['hud'], f"High: {high_score}", (255, 200, 50), (15, 68), anchor="topleft")


def draw_danger_zone(surface, camera_y, player_wy):
    dist = ALTURA - (player_wy - camera_y)
    alpha = min(150, max(0, int(255 - (dist * 1.5))))
    if alpha > 0:
        rect = pygame.Surface((LARGURA, 40), pygame.SRCALPHA)
        rect.fill((255, 0, 0, alpha))
        surface.blit(rect, (0, ALTURA - 40))


def draw_control_setup(surface):
    surface.blit(get_overlay(180), (0, 0))
    pw, ph = 320, 260
    px, py = (LARGURA - pw) // 2, (ALTURA - ph) // 2
    painel = pygame.Surface((pw, ph), pygame.SRCALPHA)
    painel.fill((15, 18, 42, 235))
    pygame.draw.rect(painel, (255, 200, 50), (0, 0, pw, ph), 3, border_radius=14)
    surface.blit(painel, (px, py))
    draw_text_shadow(surface, assets.fonts['botao_grande'], "CONTROL SETUP", (255, 210, 50), (LARGURA // 2, py + 30))
    pygame.draw.line(surface, (255, 200, 50), (px + 20, py + 50), (px + pw - 20, py + 50), 1)
    msgs = ["W A S D - Movimentar", "R - Tentar Novamente", "M - Voltar ao Menu", "ESC - Fechar telas/Voltar"]
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
    surface.blit(get_overlay(200), (0, 0))
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
    surface.blit(get_overlay(200), (0, 0))
    draw_text_shadow(surface, assets.fonts['botao_grande'], "SELECT PLAYER", (255, 210, 50), (LARGURA // 2, 80))
    play_buttons = {}
    delete_buttons = {}
    view_rect = pygame.Rect(LARGURA // 2 - 180, 120, 360, 420)
    pygame.draw.rect(surface, (15, 18, 42), view_rect, border_radius=10)
    pygame.draw.rect(surface, (100, 100, 150), view_rect, 2, border_radius=10)
    surface.set_clip(view_rect)
    players = list(players_dict.keys())[::-1]
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
            btn_play = pygame.Rect(row_rect.right - 105, row_rect.y + 10, 70, 30)
            draw_button(surface, btn_play, "PLAY", btn_play.collidepoint(active_mouse), 'kbd')
            btn_del = pygame.Rect(row_rect.right - 28, row_rect.y + 12, 20, 20)
            hover_del = btn_del.collidepoint(active_mouse)
            pygame.draw.rect(surface, (200, 50, 50) if hover_del else (120, 30, 30), btn_del, border_radius=4)
            pygame.draw.rect(surface, (255, 100, 100), btn_del, 1, border_radius=4)
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


def draw_leaderboard_screen(surface, players_dict, mouse_pos, scroll_y):
    surface.blit(get_overlay(200), (0, 0))
    draw_text_shadow(surface, assets.fonts['botao_grande'], "LEADERBOARD", (255, 210, 50), (LARGURA // 2, 80))
    view_rect = pygame.Rect(LARGURA // 2 - 180, 120, 360, 420)
    pygame.draw.rect(surface, (15, 18, 42), view_rect, border_radius=10)
    pygame.draw.rect(surface, (100, 100, 150), view_rect, 2, border_radius=10)
    surface.set_clip(view_rect)
    sorted_players = sorted(players_dict.items(), key=lambda x: x[1]['high_score'], reverse=True)
    start_y = 135 + scroll_y
    if not sorted_players:
        draw_text_shadow(surface, assets.fonts['hud'], "Nenhum dado.", (150, 150, 150), (LARGURA // 2, start_y + 50))
    else:
        for i, (p_name, data) in enumerate(sorted_players):
            row_rect = pygame.Rect(LARGURA // 2 - 170, start_y, 340, 50)
            if i == 0:
                bg_cor, rank_cor = (255, 200, 0), (150, 100, 0)
            elif i == 1:
                bg_cor, rank_cor = (200, 200, 200), (100, 100, 100)
            elif i == 2:
                bg_cor, rank_cor = (205, 127, 50), (100, 50, 20)
            else:
                bg_cor, rank_cor = (30, 30, 50), (150, 150, 150)
            pygame.draw.rect(surface, bg_cor, row_rect, border_radius=10)
            rank_txt = assets.fonts['botao'].render(f"#{i + 1}", True, rank_cor)
            surface.blit(rank_txt, rank_txt.get_rect(center=(row_rect.x + 30, row_rect.centery)))
            n_cor = (0, 0, 0) if i < 3 else (255, 255, 255)
            draw_text_shadow(surface, assets.fonts['botao'], p_name, n_cor, (row_rect.centerx - 20, row_rect.centery),
                             offset=(0 if i < 3 else 1))
            box_score = pygame.Rect(row_rect.right - 80, row_rect.y + 10, 70, 30)
            box_surf = pygame.Surface((box_score.w, box_score.h), pygame.SRCALPHA)
            pygame.draw.rect(box_surf, (0, 0, 0, 80), (0, 0, box_score.w, box_score.h), border_radius=6)
            surface.blit(box_surf, box_score)
            s_cor = (255, 255, 255) if i < 3 else (255, 200, 50)
            s_txt = assets.fonts['kbd'].render(str(data['high_score']), True, s_cor)
            surface.blit(s_txt, s_txt.get_rect(center=box_score.center))
            start_y += 60
    surface.set_clip(None)
    btn_back = pygame.Rect(LARGURA // 2 - 80, ALTURA - 80, 160, 40)
    draw_button(surface, btn_back, "VOLTAR", btn_back.collidepoint(mouse_pos))
    return btn_back, view_rect


GAMEOVER_PANEL_H = 300


def draw_game_over_screen(surface, stats, mouse_pos, btn_retry, btn_menu):
    # MOTIVO TÉCNICO: Removido o bloco "if stats['cause'] == 'atropelado': surface.blit(...)"
    # que chamava a chave inexistente "bg_atropelo". O main.py já cuida desse fundo.

    pw, ph = 340, GAMEOVER_PANEL_H
    px, py = (LARGURA - pw) // 2, (ALTURA - ph) // 2 - 20

    painel = pygame.Surface((pw, ph), pygame.SRCALPHA)
    painel.fill((15, 18, 42, 235))
    pygame.draw.rect(painel, (255, 200, 50), (0, 0, pw, ph), 3, border_radius=14)
    surface.blit(painel, (px, py))

    causas_texto = {
        "atropelado": "Atropelado!",
        "afogado": "Afogado!",
        "borda": "Ficou para trás!"
    }
    causa_str = causas_texto.get(stats['cause'], "Você morreu!")

    draw_text_shadow(surface, assets.fonts['botao_grande'], causa_str, (255, 100, 100), (LARGURA // 2, py + 35))
    pygame.draw.line(surface, (255, 200, 50), (px + 20, py + 60), (px + pw - 20, py + 60), 1)

    infos = [
        (f"Score Final: {stats['score']}", (255, 255, 255)),
        (f"Tempo: {stats['time_s']} segundos", (200, 255, 200)),
    ]

    y_pos = py + 110
    for texto, cor in infos:
        draw_text_shadow(surface, assets.fonts['hud'], texto, cor, (LARGURA // 2, y_pos))
        y_pos += 40

    if stats['new_record']:
        alpha = int(128 + 127 * math.sin(pygame.time.get_ticks() / 150.0))
        glow_color = (255, 215, 0, alpha)
        surf_recorde = assets.fonts['botao_grande'].render("Avante sempre!", True, glow_color[:3])
        surf_recorde.set_alpha(alpha)
        r_rect = surf_recorde.get_rect(center=(LARGURA // 2, y_pos + 10))
        surface.blit(surf_recorde, r_rect)

    draw_button(surface, btn_retry, "RETRY (R)", btn_retry.collidepoint(mouse_pos))
    draw_button(surface, btn_menu, "MENU (M)", btn_menu.collidepoint(mouse_pos))
