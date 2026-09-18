# Brief de discussão: revisão independente da skill discussion-briefs

**Estado:** concluído

**Alimenta:**

- [plano de implementação](../completed/discussion-briefs-review.md), que recebeu as decisões em
  inglês
- o pacote da skill, em [SKILL.md](../../.claude/skills/discussion-briefs/SKILL.md) e no
  [modelo](../../.claude/skills/discussion-briefs/assets/discussion-brief-template.md)

Documento de trabalho: explica os pontos em aberto e resume o que já foi decidido. Não substitui o
plano de implementação nem o registro de arquitetura, e nada escrito aqui autoriza trabalho; cada
decisão vale onde foi registrada.

## Resumo

Tudo o que você decidiu sobre a revisão da skill, do D1 ao D9, está aplicado nos arquivos, validado
e registrado no plano (verificado em 2026-09-17). Não há item aberto nem decisão com
`registro pendente`. O teste com agentes independentes terminou com os três casos passando: criar um
brief a partir de uma tarefa com muitas pendências; responder a uma pergunta de status com um resumo
curto, sem criar arquivo; e anotar uma decisão só no brief, sem tocar no registro de arquitetura. Os
dois últimos só passaram depois das regras que você escolheu no D8 e no D9.

## Glossário

| Termo | O que é |
| --- | --- |
| skill | Pacote de instruções que o agente carrega para um tipo de tarefa; o texto fica em `SKILL.md`. |
| brief | Documento de trabalho em português criado pela skill `discussion-briefs`; este arquivo é um. |
| modelo | O arquivo `discussion-brief-template.md`, que dá a estrutura inicial de todo brief. |
| plano de implementação | Roteiro em inglês que eu sigo ao implementar; fica em `implementation-plans/active/` enquanto está em andamento, vai para `completed/` quando termina, e é regido pela sua skill `plan-implementation`. |
| registro de arquitetura | Documento durável, sempre em inglês, que guarda uma decisão de arquitetura aprovada; é regido pela sua skill `architecture-records`. |
| `codex-claude-loop` | Sua skill que coordena duas sessões, uma do Codex e uma do Claude, por meio de um arquivo compartilhado, o arquivo de handoff. |
| `documentation` | Sua skill com as regras para escrever qualquer arquivo Markdown. |
| gate de pergunta | Sua regra global: em mensagem com `?`, eu só respondo e não edito nem crio nada. |
| `registro pendente` | Marca que um item decidido carrega enquanto a decisão ainda não foi copiada para o plano, o registro de arquitetura ou a issue que manda nela. |
| repositório de teste | Pasta descartável, fora da sua home, com um projeto de mentira; cada caso do teste rodou numa delas. |
| Sonnet | Modelo Claude menor que o desta sessão; usei-o nos testes porque o revisor se preocupava com o comportamento de modelos mais fracos. |
| commit `e2fcf6a` | Seu commit "Add a shared workflow for discussion briefs", que contém a primeira versão da skill (verificado em 2026-09-17). |

## Sem ação necessária

- **Caso 1 do teste, uma tarefa que termina com dez pendências: passou.** O agente achou a skill
  pelo registro, criou o brief na pasta certa do repositório de teste, numerou os itens em
  sequência, fez o glossário, avisou que editou o `README.md` da pasta de planos e não tocou no
  plano. Dois desvios pequenos: ele colou no chat a lista dos títulos dos itens, e por isso a skill
  agora proíbe também a lista de títulos; e os títulos dos itens ainda usavam siglas, embora todas
  estivessem no glossário.
- **Caso 2, uma pergunta de status com `?` e sem brief: passou nas três rodadas finais, depois do
  D9.** Antes disso falhou duas vezes: numa, o agente carregou a skill e respondeu com a lista
  longa; na outra, nem carregou a skill. Nas três rodadas finais ele carregou a skill, não criou
  arquivo, respondeu com seis pendências em uma linha cada, apontou a que mais destrava e ofereceu
  o brief. Em duas delas sobraram algumas siglas acompanhadas da explicação; na terceira, nenhuma.
  Não testei o sentido contrário do D9, isto é, se a skill passou a ser carregada à toa em pedidos
  só de explicação.
- **Caso 3, a decisão "D1: opção 2": passou na segunda rodada, depois do D8.** Pela comparação dos
  arquivos antes e depois, só o brief mudou: o item ficou `decidido` com `registro pendente`, o
  registro de arquitetura e o plano ficaram idênticos, e o agente avisou da contradição e disse como
  mandar registrar.
- Todos os agentes do teste eram do modelo Sonnet, um por rodada. Conferi que nenhum escreveu fora
  do repositório de teste: a sua home e as duas pastas reais de planos ficaram como estavam.
- O que já está no Git (verificado em 2026-09-17): você commitou as correções do D1 ao D7 em
  `8318838`, "Clarify discussion brief authority and lifecycle", e as do D8 em `922148f`, "Require
  explicit promotion of discussion brief decisions". As do D9 ainda não foram commitadas: estão
  modificados o `SKILL.md` da `discussion-briefs`, o registro de skills e este brief, e o plano
  mudou da pasta `active/` para `completed/`.

## Decididos e descartados

Todas as decisões abaixo estão registradas, em inglês, na tabela de decisões do
[plano](../completed/discussion-briefs-review.md) e aplicadas no arquivo indicado em cada linha.

### D1 — Quando eu devo criar um brief sem você pedir?

**Decisão:** só para pontos que estão esperando por você, isto é, uma decisão, uma autorização ou
algo que depende de terceiros; pedido de explicação fica no chat e subagentes nunca criam brief —
aplicada no [SKILL.md](../../.claude/skills/discussion-briefs/SKILL.md) e no
[registro de skills](../../.codex/AGENTS.md).

### D2 — A `plan-implementation` deve saber que os briefs existem?

**Decisão:** sim. Ela agora manda ler o brief do mesmo assunto antes de planejar, copiar as decisões
dele para o plano e consertar os links do brief quando o plano muda de pasta; a `discussion-briefs`
avisa no chat quando edita o `README.md` da pasta de planos — aplicada no
[SKILL.md da plan-implementation](../../.claude/skills/plan-implementation/SKILL.md).

### D3 — Os briefs deste repositório home devem ser salvos no Git?

**Decisão:** sim. A pasta `implementation-plans/briefs/` foi liberada — aplicada no
[.gitignore](../../.gitignore). Commitar continua sendo escolha sua.

### D4 — Corrigir seis defeitos de redação da skill

**Decisão:** você aprovou os seis, todos aplicados no
[SKILL.md](../../.claude/skills/discussion-briefs/SKILL.md) e no
[modelo](../../.claude/skills/discussion-briefs/assets/discussion-brief-template.md):

- D4.1 — registrar uma decisão é copiá-la para o plano, o registro de arquitetura ou a issue, nunca
  implementá-la; até lá o item fica com `registro pendente`. O teste mostrou que isso ainda não
  basta para proteger um registro de arquitetura, o que virou o D8.
- D4.2 — se o brief seria criado numa mensagem com `?`, eu respondo com um resumo curto e ofereço
  o brief para depois.
- D4.3 — texto proposto só é aplicado na próxima instrução sobre o brief ou o assunto dele, e toda
  resposta a uma pergunta lista os itens com reescrita pendente.
- D4.4 — itens que esperam outra pessoa ganharam o estado `resolvido`.
- D4.5 — da `documentation`, o brief segue só as regras de formatação; sem sumário, sem link preso
  a commit, sem contagem no resumo do modelo.
- D4.6 — os itens são sempre D1, D2, D3; rótulos do plano aparecem dentro do texto e no glossário.

### D5 — Aplicar os ajustes menores do modelo e do texto

**Decisão:** você aprovou os dez, aplicados nos mesmos dois arquivos do D4:

- D5.1 — a seção final do modelo virou "Decididos e descartados".
- D5.2 — saiu o estado `em discussão` dos itens.
- D5.3 — a linha "Decisão" só aparece quando existe decisão.
- D5.4 — as linhas do cabeçalho do modelo ficaram separadas.
- D5.5 — o parágrafo inicial de todo brief diz que ele não autoriza trabalho.
- D5.6 — o título "Decisões suas" virou "Decisões que dependem de você".
- D5.7 — o brief fica abaixo de todos os outros documentos e nunca é autoridade; uma decisão sua
  anotada nele vale pela sua declaração, e nesse caso atualiza-se o dono, não o brief.
- D5.8 — a skill diz onde fica o brief em repositórios organizados de outro jeito e o proíbe dentro
  de uma pasta de arquitetura.
- D5.9 — "Alimenta" aceita uma lista, e o modelo mostra `não verificado` e a data de verificação.
- D5.10 — a frase sobre commit do brief usa a mesma redação da `plan-implementation`.

### D6 — Testar a skill com um agente independente

**Decisão:** fazer, depois das correções. Rodei os três casos recomendados; os resultados estão no
resumo, no D8 e em "Sem ação necessária", e ficam registrados no
[plano](../completed/discussion-briefs-review.md).

### D7 — Alinhar a frase sobre commit de duas outras skills

**Decisão:** trocar a frase copiada pelo padrão da `plan-implementation` — aplicada no
[SKILL.md da architecture-records](../../.claude/skills/architecture-records/SKILL.md) e no
[SKILL.md da codex-claude-loop](../../.claude/skills/codex-claude-loop/SKILL.md).

### D8 — Depois que você decide um item, o que eu posso alterar sem você mandar?

**Decisão:** opção 1, decidir só mexe no brief. O item fica `decidido` com `registro pendente`, e
copiar a decisão para o plano, para um registro de arquitetura ou para uma issue espera a sua ordem;
a resposta no chat diz quantas decisões estão pendentes de registro. Como atenuante, a
`plan-implementation` confere, antes de cada fase, se o brief do assunto tem itens com
`registro pendente` — aplicada no [SKILL.md](../../.claude/skills/discussion-briefs/SKILL.md) e no
[SKILL.md da plan-implementation](../../.claude/skills/plan-implementation/SKILL.md).

### D9 — O que fazer quando o agente nem carrega a skill ao responder uma pergunta de status?

**Decisão:** opção 1, definir a fronteira com todas as letras. Uma pergunta cuja resposta seria uma
lista de pendências esperando por você, como "o que falta para fechar isso?", não é pedido só de
explicação, e a skill deve ser carregada antes de responder. Isso ajustou a frase criada pelo D1 sem
desfazê-lo — aplicada no [SKILL.md](../../.claude/skills/discussion-briefs/SKILL.md) e no
[registro de skills](../../.codex/AGENTS.md).
