# Cruze a Quatá! 🦊🚗

**Cruze a Quatá!** é um jogo arcade desenvolvido em Python utilizando a biblioteca Pygame, fortemente inspirado na mecânica clássica do *Crossy Road* e *Frogger*. O objetivo é cruzar estradas movimentadas, rios perigosos e desviar de obstáculos por diversos biomas procedurais (Floresta, Deserto e Urbano) garantindo a maior pontuação possível.

## 👥 Membros do Grupo
* Enzo
* Luiz
* Murilo

## 🎥 Demonstração (Pitch e Gameplay)
* **Vídeo Curto (Gameplay):** [LINK](https://youtu.be/mpU-mwO2X1Q)

## 🚀 Como instalar e rodar o jogo

**1. Pré-requisitos:**
Certifique-se de ter o [Python 3.x](https://www.python.org/downloads/) instalado no seu computador.

**2. Instalando as dependências:**
O projeto depende da biblioteca gráfica `pygame`. Para instalá-la, abra o terminal na pasta do projeto e execute:
```bash
pip install pygame
```

**3. Executando o jogo:**
Com as dependências instaladas, basta executar o arquivo principal:
```bash
python main.py
```

## 🎨 Design e Organização do Código
O jogo foi estruturado utilizando o paradigma de Orientação a Objetos (POO). A separação de responsabilidades foi feita nos seguintes arquivos:
* `main.py`: Loop principal, controle de estados de tela (Menu, Jogo, Game Over, etc.) e gerenciamento geral.
* `world.py`: Geração procedural do mapa, transição fluida de biomas e spawn de entidades.
* `entities.py`: Classes que representam objetos físicos do jogo (Player, Carros, Troncos, Partículas, Power-Ups).
* `ui.py`: Funções responsáveis pela renderização da interface de usuário (HUD, menus, botões).
* `assets.py`: Centralização e carregamento de mídias (imagens, fontes e sons).  
* `utils.py`: Funções auxiliares (matemática, salvar/carregar dados em JSON).
* `config.py`: Variáveis globais e constantes de balanceamento do jogo.

## 🤖 Uso de IA Generativa
Durante o desenvolvimento deste projeto, ferramentas de Inteligência Artificial Generativa (ChatGPT - GPT 5.5, Claude - Sonnet 4.6, Gemini Pro 3.1) foram utilizadas para inúmeros propósitos:
**1. Confecção de imagens, planejamento e organização procedural**
**2. Geração de código bruto a partir de uma modelagem previamente de Game Design, Interação com o código/jogo e Engenharia de Prompts**
**3. Detalhamento de ideias, formação da estrutura de entendimento de Game Design e Game Dev**

Eis os Prompts utilizados em cada IA (apenas para casos generativos ou de manutenção):


**Claude Sonnet 4.6**

Luiz
```bash
claude, eu preciso fazer um jogo em pygame, parecido com o jogo crossyroad, ou o jogo Frogger, em 2d, infinito, que conta 10 pontos acada parte da estrada que ele cruza
```
```bash
claude, com base nesse codigo de um jogo parecido com crossy road, quero adicionar carros que passam apenas nas faixas de rua, chamadas de estrada, parecido com o jogo original:
https://www.youtube.com/watch?v=nhfveOrXd6Y assim é o jogo original. entao quais sao as alterações que preciso fazer para adicionar esses caros, pensando que eu ja desenhei eles e ja tenho os arquivos deles e quero aleatoriezar as cores
```
```bash
https://www.youtube.com/watch?v=IQL3cNshU5s, claude, com base nesse video do jogo original, quero que as imagens dos carros andem igual o do jogo e tmb quero que o clique espaço para comecar fique na parte de cima
```
```bash
claude, eu quero que vc refaca a parte das arvores aleatorias, mudando os sprites e quero que vc arrume a hitbox dos poderes especiais
```
```bash
claude, por algum motivo o sistema das vitorias regias nao funciona ainda, quero que quando tiverem rios com 2 ou mais de comprimento, quero que tenha a possibilidade de ao inves de passar troncos, que tenham quadrados verdes que simbolizam as vitorias regias que sao fixas, ou seja, nao se movem com o fluxo do rio, e quando elas aparecem na sessao do rio, nao passem troncos nesta
```


**ChatGPT GPT 5.5**

Luiz
```bash
chat como faco para adicionar uma pequana animacao de fumacao personagem ande e a "câmera " acompanhe ele, e se ele ficar parado a câmera move sozinha para frente (enviei o codigo em anexo)
```
```bash
chat quero que vc crie algumas arvores que fiquem nas partes de grama verde nas quais o boneco nao consegue ficar em cima, e nos rios, quando vc tiver mais de uma fileira, exista uma possibilidade de nao passar troncos mas ter algumas vitorias regias (quadrados verdes) fixos na agua que nao passa tronco
```
```bash
chat como faco para adicionar uma pequana animacao de fumaca saindo da roda dos carrinhos
```


Murilo
```bash
[código] Separe isso em módulos de verdade. Também mapeie todos os gaps que esse jogo possui para se tornar um jogo em nível de mercado, sem realizar nada, apenas mapear. No mapeamento, aprofunde todos os detalhes necessários para se tornar um jogo em nível profissional, se atentando principalmente para a experiência do usuário.
```
```bash
Esse é o arquivo do jogo, sem modulação. Gostaria que toda e qualquer mudança que fizer no jogo a partir de agora, faça sem alterar muito a estrutura, mas fazendo o necessário para a mudança, tudo num .py só. A priori, gostaria que mudasse o botão da tela inicial "como jogar" para "intruções". Os textos estão mal alinhados e acredito que esteja poluída as intruções, poderia ser algo mais simples, como apenas os botões e uma mensagem de desafio cômica, pois o jogo foi inspirado no fato da Quatá ser uma rua movimentada entre dois prédios do Insper que os alunos circulam muito.
```
```bash
Ficou assim, arrume para caber na caixa de texto. Também adicione uma opção chamada "Controles" e os respectivos controles, w, a, s, d, de r vai para z (restart do jogo), de m vai para x (menu), h mantém (só mude INSTRUÇÕES para Instruções) e j para Controles. Não quero uma imagem.
```
```bash
Sempre que for mudar algo, me dê o código do arquivo todo, sem mudar a estrutura, apenas a implementação. Estou analisando a gameplay neste momento. Vejo que está tudo funcionando, mas a dinâmica está meio quebrada. Gostaria de ver mais conexão entre os biomas, um relief de uma transição para a outra com um pop-up de texto rápido na transição, sendo o texto da cor do bioma, mas um pouco mais escuro, com contorno preto. O crescimento dificuldade não está clara, não quero que o usuário leia que está mais difícil, mas quero que ele sinta o jogo fluindo mais difícil e variando sem caos entre ruas e rios. Também os bônus hora ou outra são sobrepostos pelas árvores e as árvores ficam aparecendo tarde demais na tela. O interessante seriam elas aparecerem, sim, mas na parte acima da raposa, onde ele não pode passar, pro usuário ter tempo de resposta.
```
```bash
Eu entrei no bioma deserto e ele me deu o nome do anterior
```
```bash
SIM. Quero o world.py e o main.py com isso corrigido.
```
```bash
Alguma mudança nos parâmetros da config? Qual o padrão a ser deixado nos quesitos de que eu estava falando?
```
```bash
Onde eu ajusto a transição dos cliques?
```
```bash
Eu entrei no bioma deserto e ele me deu o nome do anterior
```
```bash
Eu entrei no bioma deserto e ele me deu o nome do anterior
```
```bash
Olhe o meu config.py. Veja se ele pode manter 60x60 e o que deveria ser ajustado ao jogo.
```
```bash
Eu sinto que qualquer reladinha do carro no personagem já é gameover. Queria deixar mais fluída a gameplay, em que há bastante carros, mas com velocidades e hitbox plausíveis de uma gameplay amigável ao jogador. O que eu poderia mudar? E como eu faria para o personagem nascer mais abaixo?
```
```bash
Coloquei isso! Agora me ajude quanto ao escudo. Ele não está funcionando direito. Eu mudei para que ele não fosse "trapaçeável", em que quando você tinha três segundos de imunidade era só spammar W que ele avançaria muitos pontos. Mas eu gostaria que ele tivesse uma imunidade completa novamente, mas por apenas 1 segundo
```

**Gemini Pro 3.1 (Murilo)**

`Pela complexidade e tamanho dos prompts eviados, será enviado links para as conversas.`

Links: [Conversa 1](https://aistudio.google.com/app/prompts?state=%7B%22ids%22:%5B%221fiDA36mKJ9wYdffylPMglpiiuZmNsZ_I%22%5D,%22action%22:%22open%22,%22userId%22:%22115323767632476674625%22,%22resourceKeys%22:%7B%7D%7D&usp=sharing) [Conversa 2](https://aistudio.google.com/app/prompts?state=%7B%22ids%22:%5B%221JSu1axa68ooa5dmSySGq51IMfX7eUY7c%22%5D,%22action%22:%22open%22,%22userId%22:%22115323767632476674625%22,%22resourceKeys%22:%7B%7D%7D&usp=sharing) [Conversa 3](https://aistudio.google.com/app/prompts?state=%7B%22ids%22:%5B%221nBtkXUBHq5RIy8_OREL67fljhfGMZf7B%22%5D,%22action%22:%22open%22,%22userId%22:%22115323767632476674625%22,%22resourceKeys%22:%7B%7D%7D&usp=sharing) [Conversa 4](https://aistudio.google.com/app/prompts?state=%7B%22ids%22:%5B%221dVr7j44uHHZ55XvoWkSk5bCGYPstKelw%22%5D,%22action%22:%22open%22,%22userId%22:%22115323767632476674625%22,%22resourceKeys%22:%7B%7D%7D&usp=sharing) [Conversa 5](https://aistudio.google.com/app/prompts?state=%7B%22ids%22:%5B%221reGGcYNRrZZilWo7lueviHwl34kGVMRS%22%5D,%22action%22:%22open%22,%22userId%22:%22115323767632476674625%22,%22resourceKeys%22:%7B%7D%7D&usp=sharing) [Conversa 6](https://aistudio.google.com/app/prompts?state=%7B%22ids%22:%5B%221iQA4uM_MEh_0jQsnzhcm2xndu-GAwCw_%22%5D,%22action%22:%22open%22,%22userId%22:%22115323767632476674625%22,%22resourceKeys%22:%7B%7D%7D&usp=sharing) [Conversa 7](https://aistudio.google.com/app/prompts?state=%7B%22ids%22:%5B%221ZTE4GCWbHqlrBvGLhCEjLyXYMVjxPbhc%22%5D,%22action%22:%22open%22,%22userId%22:%22115323767632476674625%22,%22resourceKeys%22:%7B%7D%7D&usp=sharing)
