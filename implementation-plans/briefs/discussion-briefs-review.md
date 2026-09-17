# Brief de discussão: revisão independente da skill discussion-briefs

**Estado:** em discussão

**Alimenta:**

- [plano de implementação](../active/discussion-briefs-review.md), que recebeu as decisões em
  inglês
- o pacote da skill, em [SKILL.md](../../.claude/skills/discussion-briefs/SKILL.md) e no
  [modelo](../../.claude/skills/discussion-briefs/assets/discussion-brief-template.md)

Documento de trabalho: explica os pontos em aberto e resume o que já foi decidido. Não substitui o
plano de implementação nem o registro de arquitetura, e nada escrito aqui autoriza trabalho; cada
decisão vale onde foi registrada.

## Resumo

Tudo o que você decidiu sobre a revisão da skill, do D1 ao D8, está aplicado nos arquivos e
validado (verificado em 2026-09-17). O teste com agentes independentes rodou em três casos. A
criação de um brief a partir de uma tarefa com muitas pendências passou. A decisão "D1: opção 2"
falhou na primeira rodada, virou o D8 e, com a regra que você escolheu, passou na segunda: o agente
só mexeu no brief e avisou que a decisão contrariava um registro de arquitetura aprovado. A pergunta
de status com `?` continua falhando e virou o D9, o único item aberto: o agente respeita o `?`, mas
responde com a lista longa e cheia de siglas.

## Glossário

| Termo | O que é |
| --- | --- |
| skill | Pacote de instruções que o agente carrega para um tipo de tarefa; o texto fica em `SKILL.md`. |
| brief | Documento de trabalho em português criado pela skill `discussion-briefs`; este arquivo é um. |
| modelo | O arquivo `discussion-brief-template.md`, que dá a estrutura inicial de todo brief. |
| plano de implementação | Roteiro em inglês que eu sigo ao implementar; fica em `implementation-plans/active/` e é regido pela sua skill `plan-implementation`. |
| registro de arquitetura | Documento durável, sempre em inglês, que guarda uma decisão de arquitetura aprovada; é regido pela sua skill `architecture-records`. |
| `codex-claude-loop` | Sua skill que coordena duas sessões, uma do Codex e uma do Claude, por meio de um arquivo compartilhado, o arquivo de handoff. |
| `documentation` | Sua skill com as regras para escrever qualquer arquivo Markdown. |
| gate de pergunta | Sua regra global: em mensagem com `?`, eu só respondo e não edito nem crio nada. |
| `registro pendente` | Marca que um item decidido carrega enquanto a decisão ainda não foi copiada para o plano, o registro de arquitetura ou a issue que manda nela. |
| repositório de teste | Pasta descartável, fora da sua home, com um projeto de mentira; cada caso do teste rodou numa delas. |
| Sonnet | Modelo Claude menor que o desta sessão; usei-o nos testes porque o revisor se preocupava com o comportamento de modelos mais fracos. |
| commit `e2fcf6a` | Seu commit "Add a shared workflow for discussion briefs", que contém a primeira versão da skill (verificado em 2026-09-17). |

## Decisões que dependem de você

### D9 — O que fazer quando o agente nem carrega a skill ao responder uma pergunta de status?

**Estado:** aberto

**A pergunta para você:** como garantir que, quando você pergunta "o que falta?", a resposta venha
curta e sem siglas, e não como a lista longa que motivou esta skill.

**O que aconteceu no teste:** repeti o caso 2, em que o usuário pergunta "o que falta para fechar o
plano order-sync-hardening?" num repositório de teste com dez pendências. Rodei duas vezes, com
agentes iguais:

- Na primeira rodada, o agente carregou a `discussion-briefs`, não criou arquivo por causa do `?` e
  ofereceu o brief. Mas respondeu com uma lista longa e cheia de siglas. Por isso reforcei a frase
  da skill que pede um resumo curto.
- Na segunda rodada, o agente nem carregou a `discussion-briefs`. Ele carregou só a
  `plan-implementation`, tratou a mensagem como uma pergunta comum e respondeu com a mesma lista
  longa e cheia de siglas, sem oferecer brief. Não criou nenhum arquivo, então o gate de pergunta
  foi respeitado.

Ou seja, a frase reforçada nem chegou a ser lida. O problema não está no texto da regra, e sim no
lugar onde ela mora: dentro de uma skill que um modelo mais fraco pode não carregar justamente
quando a mensagem é uma pergunta. A entrada da skill no registro diz "em vez de listar no chat", mas
o agente leu a mensagem como simples pergunta de status.

Há uma tensão com o D1, que foi escolha sua. Por causa dele, o registro diz agora que a skill "não
vale para pedidos só de explicação", e "o que falta para fechar o plano?" pode ser lido como um
pedido de explicação. Com o mesmo texto no registro, um agente carregou a skill e o outro não, então
a fronteira ficou ambígua. Não foi o reforço da frase que piorou o resultado.

**Por que importa:** perguntar "o que falta?" é o caso mais comum de todos, e é nele que a lista
cheia de siglas nasce.

**Opções:**

1. Definir a fronteira com todas as letras, na entrada do registro de skills e na descrição da
   skill: uma pergunta cuja resposta seria uma lista de pendências esperando por você não é "pedido
   só de explicação", e a skill deve ser carregada antes de responder. Isso mexe na frase que o D1
   criou, sem desfazer o D1: "explique as três formas de fazer retry" continua no chat. É uma
   mudança pequena em dois lugares, e depois eu repito o caso 2 mais de uma vez. Não é garantia: é
   um empurrão na escolha da skill, e o modelo ainda pode errar.
2. Pôr a regra do resumo curto nas suas instruções globais, junto do gate de pergunta, que está
   sempre carregado: "se a resposta a uma pergunta for uma lista de várias pendências esperando pelo
   usuário, responda com um resumo curto e sem siglas e ofereça um brief". Garante que a regra seja
   lida. Não afrouxa o gate, só acrescenta um formato de resposta. O custo é colocar uma regra de
   uma skill específica no arquivo global, que você quer enxuto.
3. Aceitar como está. Numa pergunta, a lista pode vir longa; você responde "crie um brief" e o
   arquivo nasce na mensagem seguinte. Não custa nada, mas o problema original continua existindo
   nesse caminho.

**Recomendação:** opção 1 primeiro, com o caso 2 repetido duas ou três vezes. Se ainda falhar, a
opção 2 é a que resolve de verdade.

## Sem ação necessária

- **Caso 1 do teste, uma tarefa que termina com dez pendências: passou.** O agente achou a skill
  pelo registro, criou o brief na pasta certa do repositório de teste, numerou os itens em
  sequência, fez o glossário, avisou que editou o `README.md` da pasta de planos e não tocou no
  plano. Dois desvios pequenos: ele colou no chat a lista dos títulos dos itens, e por isso a skill
  agora proíbe também a lista de títulos; e os títulos dos itens ainda usavam siglas, embora todas
  estivessem no glossário.
- **Caso 2, uma pergunta de status com `?` e sem brief: falhou, e é o assunto do D9.** Nas duas
  rodadas o agente respeitou o gate de pergunta e não criou arquivo, mas respondeu com a lista
  longa.
- **Caso 3, a decisão "D1: opção 2": passou na segunda rodada, depois do D8.** Pela comparação dos
  arquivos antes e depois, só o brief mudou: o item ficou `decidido` com `registro pendente`, o
  registro de arquitetura e o plano ficaram idênticos, e o agente avisou da contradição e disse como
  mandar registrar.
- Todos os agentes do teste eram do modelo Sonnet, um por rodada. Conferi que nenhum escreveu fora
  do repositório de teste: a sua home e as duas pastas reais de planos ficaram como estavam.
- As correções do D1 ao D7 já estão no Git: você as commitou em `8318838`, "Clarify discussion
  brief authority and lifecycle", junto com este brief e o plano (verificado em 2026-09-17). As do
  D8 ainda não foram commitadas: estão modificados o `SKILL.md` da `discussion-briefs`, o `SKILL.md`
  da `plan-implementation`, o plano e este brief.

## Decididos e descartados

Todas as decisões abaixo estão registradas, em inglês, na tabela de decisões do
[plano](../active/discussion-briefs-review.md) e aplicadas no arquivo indicado em cada linha.

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
[plano](../active/discussion-briefs-review.md).

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
