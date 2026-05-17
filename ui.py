# ui.py
import pygame
from config import *
import assets
from utils import draw_text_shadow


def draw_button(surface, rect, label, hint, hover):
    cor = (180, 70, 10) if hover else (30, 30, 60)
    pygame.draw.rect(surface, cor, rect, border_radius=10)
    pygame.draw.rect(surface, (255, 200, 50), rect, 2, border_radius=10)

    t = assets.fonts['botao'].render(label, True, (255, 255, 255))
    surface.blit(t, t.get_rect(center=(rect.centerx, rect.centery - 7)))

    hint_t = assets.fonts['kbd'].render(f"[{hint}]", True, (220, 200, 100))
    surface.blit(hint_t, hint_t.get_rect(center=(rect.centerx, rect.centery + 13)))


def draw_hud(surface, score, high_score):
    draw_text_shadow(surface, assets.fonts['score'], f"Score: {score}", (255, 255, 255), (60, 20))
    draw_text_shadow(surface, assets.fonts['hud'], f"High: {high_score}", (255, 200, 50), (55, 50))


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

    pw, ph = 380, 300
    px, py = (LARGURA - pw) // 2, (ALTURA - ph) // 2

    painel = pygame.Surface((pw, ph), pygame.SRCALPHA)
    painel.fill((15, 18, 42, 235))
    pygame.draw.rect(painel, (255, 200, 50), (0, 0, pw, ph), 3, border_radius=14)
    surface.blit(painel, (px, py))

    draw_text_shadow(surface, assets.fonts['botao'], "CONTROLES", (255, 210, 50), (LARGURA // 2, py + 34))
    pygame.draw.line(surface, (255, 200, 50), (px + 20, py + 58), (px + pw - 20, py + 58), 1)

    msgs = [
        "W A S D - Movimentar",
        "R - Tentar Novamente (Retry)",
        "M - Voltar ao Menu",
        "ESC - Fechar telas"
    ]

    y = py + 95
    for msg in msgs:
        draw_text_shadow(surface, assets.fonts['titulo'], msg, (225, 232, 245), (LARGURA // 2, y))
        y += 35


def desenhar_hud_status(surface, bx, by, icon, restante_ms, total_ms, texto, cor_barra):
    frac = max(0.0, restante_ms / total_ms)
    bw, bh = 130, 18
    surface.blit(icon, (bx - 40, by - 8))
    pygame.draw.rect(surface, (30, 30, 60), (bx, by, bw, bh), border_radius=5)
    pygame.draw.rect(surface, cor_barra, (bx, by, int(bw * frac), bh), border_radius=5)
    pygame.draw.rect(surface, (255, 220, 80), (bx, by, bw, bh), 2, border_radius=5)
    t = assets.fonts['kbd'].render(texto, True, (255, 255, 255))
    surface.blit(t, t.get_rect(center=(bx + bw // 2, by + bh // 2)))


def draw_powerups_hud(surface, player, agora):
    if player.tem_escudo:
        bx, by = LARGURA - 140, 10
        surface.blit(assets.images['pu_escudo'], (bx - 40, by - 8))
        pygame.draw.rect(surface, (60, 30, 10), (bx, by, 130, 18), border_radius=5)
        pygame.draw.rect(surface, (255, 210, 50), (bx, by, 130, 18), border_radius=5)
        pygame.draw.rect(surface, (255, 240, 120), (bx, by, 130, 18), 2, border_radius=5)
        t = assets.fonts['kbd'].render("ESCUDO ATIVO", True, (60, 30, 0))
        surface.blit(t, t.get_rect(center=(bx + 65, by + 9)))

    if agora < player.xp2_ate:
        desenhar_hud_status(surface, LARGURA - 140, 38, assets.images['pu_xp2'],
                            player.xp2_ate - agora, POWERUP_XP2_DURACAO_MS,
                            f"XP x2 {(player.xp2_ate - agora) // 1000 + 1}s", (255, 210, 80))