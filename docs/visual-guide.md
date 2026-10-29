# Guia visual: funcionários de IA (miniaturas colecionáveis)

## 1. Análise comparativa: referências × modelos rejeitados
| Aspecto | Referências | Modelos rejeitados (v1/v2) | Correção |
|---|---|---|---|
| Proporção | Cabeça ≈ 40–45% da altura; corpo compacto e largo; pernas curtas | Cabeça ≈ 30%, corpo alto e fino, pernas longas | Cabeça grande, tronco curto e largo, pernas ≈ 20% da altura |
| Rosto | Olhos médios, bem espaçados, na metade inferior do rosto; sorriso aberto; bochechas | Olhos grandes demais (efeito boneca), boca fina, cílios finos | Olhos ≈ 18% da largura do rosto, sorriso largo com dentes/língua, blush discreto |
| Volumes | Formas cheias e arredondadas (clay) ou blocos chanfrados (voxel), sem membros finos | Membros tubulares finos, transições moles | Membros grossos; mãos em bloco/luva; sem pescoço visível |
| Materiais | Cores saturadas, acabamento fosco; brilho só no capacete e em metais | Cores lavadas por excesso de luz e sheen | Laranja/azul saturados; plástico fosco (rough 0,55–0,75); coat só no capacete |
| Roupa | Peças legíveis em silhueta: jardineira, faixas refletivas, bolsos, cinto de ferramentas | Cascas lisas sobre o corpo | Peças sobrepostas em volume próprio, cada uma com detalhe de leitura |
| Apresentação | Personagem como peça de coleção, com base ou cenário | Personagem solto | Base colecionável (técnico) ou sala-vitrine (Muse e demais) |

## 2. Proporções (altura total = 1,0, incluindo o capacete)
| Parte | Altura | Largura | Notas |
|---|---|---|---|
| Base colecionável | 0,06 | 0,62 | grafite com filete de luz laranja |
| Botas | 0,075 | 0,14 cada | biqueira clara, sola grossa |
| Pernas | 0,17 | 0,13 cada | joelheira + faixa refletiva |
| Tronco | 0,255 | 0,31 | mais largo que alto |
| Cabeça | 0,33 | 0,36 | maior que o tronco, sem pescoço visível |
| Capacete | 0,13 | 0,45 (aba) | dois níveis + nervura + pala + emblema |

## 3. Rosto
- Olhos em 3 camadas (branco 0,062 → íris teal → pupila) + 1 brilho, a ~48% da altura da cabeça.
- Sobrancelhas grossas e retas, um pouco acima dos olhos; nariz pequeno; sorriso aberto e largo com língua.
- Blush retangular nas bochechas. Nada de cílios para o técnico.

## 4. Materiais (PBR, sem texturas)
| Uso | Cor (linear) | Rough | Extra |
|---|---|---|---|
| Capacete | 0,85 / 0,20 / 0,004 | 0,28 | coat 0,4 |
| Jardineira laranja | 0,80 / 0,17 / 0,004 | 0,60 | |
| Camisa azul | 0,025 / 0,075 / 0,25 | 0,75 | |
| Calça marrom | 0,13 / 0,065 / 0,025 | 0,75 | |
| Refletivo | 0,80 / 0,82 / 0,85 | 0,20 | metallic 0,5 |
| Pele | 0,55 / 0,30 / 0,18 | 0,55 | |

## 5. Roupa do técnico
Camisa azul de manga longa; jardineira laranja com peitilho, alças, botões dourados, duas faixas
refletivas e bolso com caneta; cinto escuro com fivela e bolsa de ferramentas; calça marrom com
joelheira e faixa refletiva; luvas grafite; botas com biqueira.

## 6. Muse (próxima etapa, após aprovação do técnico)
Mesma linguagem colecionável em clay: cabeça grande, corpo compacto, coque alto escuro, suéter
cinza de tricô volumoso, olhos médios. Sentada numa estação detalhada dentro de uma sala-vitrine
(laptop, 2 monitores com código, servidor com LEDs, prateleiras, post-its, plantas, luz quente).

## 7. Regras técnicas aprendidas
- Chanfrar cada bloco isoladamente; chanfro sobre blocos interpenetrados gera faces invertidas.
- Evitar faces coplanares sobrepostas (geram manchas pretas): recuar 2–4 mm a peça de trás.
- Iluminação de estúdio moderada (key ≈ 110 W): luz forte lava as cores saturadas.
