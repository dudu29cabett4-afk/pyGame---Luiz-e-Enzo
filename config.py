# config.py
# Arquivo de configurações do jogo.
# Centralizar variáveis globais e constantes em um único arquivo é uma excelente prática
# de programação. Isso facilita o balanceamento, pois evita "magic numbers" (números
# fixos espalhados pelo código) e permite alterar t0do o comportamento geral do jogo modificando
# apenas estas regras de base.

ALTURA = 960 #PADRÃO 768
LARGURA = 660 #PADRÃO 528

TAMANHO_TILE = 60 # Cada bloco de grid e de movimento (jogador só pode se mover 60 pixels por vez)
PLAYER_ALVO_Y = ALTURA * 3 // 5 - 30

VEL_SCROLL_INICIAL = 0.25 # Velocidade inicial na qual a câmera empurra a tela para baixo
VEL_SCROLL_MAX = 4.0
SCORE_PARA_MAX_VEL = 300

SAFE_ZONE_LINHAS = 1

ARVORE_PREGEN_LINHAS = 10
ARVORE_APARECIMENTO_MS = 500
ARVORE_CHANCE_BASE = 0.025
FUMACA_CHANCE_POR_FRAME = 0.08
ARVORE_CHANCE_EXTRA_MAX = 0.025
ARVORE_CHANCE_EXTRA_SCORE = 2000
POWERUP_CHANCE_SPAWN = 0.05

TRONCO_SLOTS_OPCOES = [1, 2, 3, 4]
CROCODILO_CHANCE = 0.15

# Fluxo constante de troncos/jacarés (gap fixo em pixels entre entidades)
TRONCO_GAP_FIXO = 60
TRONCO_COBERTURA_EXTRA = 250
TRONCO_EMBARQUE_TOLERANCIA = 14

# Obstáculos e bônus só spawnam N linhas à frente da raposa
OBSTACULO_BUFFER_LINHAS = 10

# Constantes de Transições de tela animadas em milisegundos (ms)
TRANSICAO_MENU_MS = 250
TRANSICAO_JOGO_MS = 1000
TRANSICAO_MORTE_MS = 75

CORES_RAPOSA = ["azul", "verde", "vermelho"]
COR_RAPOSA_PADRAO = "vermelho"

RECUO_DURACAO_MS = 180
RECUO_PIXELS = 6

BIOMAS = ["floresta", "deserto", "urbano"]
CICLO_BIOMA_DURACAO = 100

POWERUP_XP2_DURACAO_MS = 8000
MAX_POWERUPS_ATIVOS = 1

TIPO_GRAMA = "grama"
TIPO_ESTRADA = "estrada"
TIPO_RIO = "rio"

# Definindo IDs pros estados da Máquina de Estados da classe Game (Controla Telas)
ESTADO_MENU = 0
ESTADO_JOGANDO = 1
ESTADO_GAMEOVER = 2
ESTADO_NEW_PLAYER = 3
ESTADO_LOAD_PLAYER = 4
ESTADO_OPTIONS = 5
ESTADO_LEADERBOARD = 7
ESTADO_PAUSE = 8

SCORE_DIFICULDADE_MAX = 300

BREAKPOINT_FASE2 = 100
BREAKPOINT_FASE3 = 200
PESOS_GRID_FASE1 = [60, 35, 5] # Maior peso significa maior chance do gerador sorteá-lo (SOLO, CARRO, RIO)
PESOS_GRID_FASE2 = [50, 40, 10]
PESOS_GRID_FASE3 = [40, 60, 0]

CARRO_VEL_BASE = (2.0, 4.0)
CARRO_VEL_TETO = (4.0, 8.0)

TRONCO_VEL_BASE = (1.5, 2.5)
TRONCO_VEL_TETO = (4.5, 7.5)

CARRO_SPAWN_BASE = (180, 240)
CARRO_SPAWN_TETO = (150, 180)

# Espaçamento menor = mais troncos/jacarés no rio
TRONCO_SPAWN_BASE = (150, 180)
TRONCO_SPAWN_TETO = (120, 150)

# Inset é a margem interior (Redução da Hitbox de perigo pra dar vantagem ao jogador)
HITBOX_PLAYER_INSET = 12
HITBOX_CARRO_X_INSET = 12
HITBOX_CARRO_Y_INSET = 10