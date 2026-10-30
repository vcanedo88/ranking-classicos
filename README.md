# Ranking das Freguesias

Índice de Freguesia 2.0 dos 16 principais clássicos do futebol brasileiro, feito para o **Canal do Canedo**.

Site: https://vcanedo88.github.io/ranking-classicos/

## O que é

Para cada clássico, o índice mede o aproveitamento do time dominante nos **últimos 50 jogos oficiais** (vitória = 3, empate = 1, derrota = 0), com dois pesos:

- **Recência**, por bloco de 10 jogos: 1–10 ×3 · 11–20 ×2,5 · 21–30 ×2 · 31–40 ×1,5 · 41–50 ×1
- **Importância do jogo**:

| Tipo de jogo | Peso |
|---|---|
| Estadual (classificação), grupos de regional, Taça Rio de consolação | 1,0 |
| Mata-mata de estadual ou regional (inclui finais de turno) | 1,2 |
| Final de estadual ou regional, Supercopa, Recopa, Série B | 1,5 |
| Brasileirão e fase de grupos da Libertadores | 1,75 |
| Mata-mata de Copa do Brasil, Libertadores ou Sul-Americana | 2,0 |
| Final de Copa do Brasil, Libertadores ou Sul-Americana | 2,5 |

Cada mata-mata (ida e volta ou jogo único) vira **um jogo extra** vencido por quem avançou, com o peso da fase. Pênaltis contam como empate no jogo; quem vence a disputa leva o jogo extra. Confronto empatado sem pênaltis: avança quem tinha a vantagem do regulamento.

Índice = Σ(peso × pontos) ÷ Σ(peso × 3). Freguesia a partir de 65; vantagem clara a partir de 55.

## Estrutura

- `dados/jogos.csv` — base de jogos (conferida no oGol). Colunas especiais: `tipo` (`turno`, `consolacao`, `wo`) e `avancou_por_vantagem`.
- `dados/pesos.json` — pesos e limiares.
- `dados/classicos.json` — os 16 clássicos.
- `scripts/calcular.py` — gera `data/*.json` (site) e `csv/*.csv`.
- `index.html`, `assets/` — o site (GitHub Pages).

## Atualizar

1. Acrescente o novo jogo em `dados/jogos.csv`.
2. Rode `python3 scripts/calcular.py`.
3. Faça commit e push. O GitHub Pages publica sozinho.

Os escudos pertencem aos respectivos clubes. Fonte Montserrat sob SIL Open Font License 1.1.
