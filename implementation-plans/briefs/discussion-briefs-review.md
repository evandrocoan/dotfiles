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

Tudo o que você decidiu sobre a revisão da skill foi aplicado aos arquivos e validado (verificado em
2026-09-17). Nada foi commitado. Depois disso rodei o teste com agentes independentes, em três
casos. O primeiro passou. O segundo passou no essencial e me levou a reforçar uma frase da skill. O
terceiro falhou de um jeito que só você pode resolver, e virou o item D8, o único aberto: um agente
recebeu apenas "D1: opção 2" e, além de anotar a decisão, substituiu um registro de arquitetura
aprovado.

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

### D8 — Depois que você decide um item, o que eu posso alterar sem você mandar?

**Estado:** aberto

**A pergunta para você:** quando você escreve só "D1: opção 2", até onde o agente pode ir além de
anotar a decisão no brief.

**O que aconteceu no teste:** o agente recebeu um repositório de teste com um brief já escrito. O
item D1 perguntava o que fazer com um pedido de outro cliente que aparece numa fila compartilhada.
A opção 2 contrariava um registro de arquitetura aprovado e já implementado, e o brief dizia isso.
A mensagem do usuário foi só "D1: opção 2". Na mesma resposta, o agente:

- anotou a decisão no brief, o que era o esperado;
- marcou o registro de arquitetura aprovado como substituído;
- criou um registro de arquitetura novo e atualizou o índice de arquitetura;
- editou o plano de implementação.

Ele não mexeu no código, então a correção D4.1 funcionou nessa parte. E ele não desobedeceu a
skill: ela manda "levar cada decisão ao documento que manda nela, seguindo as regras da skill dona
desse documento". Ele carregou a `architecture-records`, seguiu as regras dela e fez tudo de uma
vez. O problema é que três palavras suas bastaram para reescrever a arquitetura.

Nesta nossa conversa foi diferente: quando você decidiu D1, D2 e D3, eu perguntei antes de aplicar,
e você escolheu "só registrar". O teste mostra que outro agente não perguntaria.

**Como fica na prática, depois de você escrever "D1: opção 2":**

| O que acontece | Opção 1: só o brief | Opção 2: brief e plano ativo | Opção 3: como está hoje |
| --- | --- | --- | --- |
| Brief | Anota `decidido` com `registro pendente`. | Igual à opção 1. | Anota e já move o item para os decididos. |
| Plano em `active/` | Não mexe. Espera você dizer "registre as decisões". | Copia a decisão para o plano, em inglês, na mesma resposta. | Copia na mesma resposta. |
| Registro de arquitetura aprovado | Não mexe. Avisa que a decisão o contraria e espera a sua ordem. | Igual à opção 1. | Altera ou substitui o registro na mesma resposta. |
| Como você fica sabendo do que falta | A resposta no chat diz quantas decisões estão com `registro pendente`. | Igual, só para registros de arquitetura e issues. | Não se aplica. |
| Custo para você | Uma mensagem curta a mais para cada leva de decisões. | Nenhum para o plano; uma mensagem para arquitetura. | Nenhum. |

**Recomendação:** opção 1. É a regra mais simples de lembrar, "decidir só mexe no brief", e combina
com o que você escolheu nesta conversa e com o resto das suas regras, que sempre separam decidir de
executar. A opção 2 é a alternativa razoável se você achar a mensagem a mais um incômodo: o plano é
um documento temporário, e mantê-lo em dia tem risco baixo. A opção 3 eu não recomendo, porque um
registro de arquitetura aprovado é o documento mais durável que você tem.

## Sem ação necessária

- **Caso 1 do teste, uma tarefa que termina com dez pendências: passou.** O agente achou a skill
  pelo registro, criou o brief na pasta certa do repositório de teste, numerou os itens em
  sequência, fez o glossário, avisou que editou o `README.md` da pasta de planos e não tocou no
  plano. Dois desvios pequenos: ele colou no chat a lista dos títulos dos itens, e por isso a skill
  agora proíbe também a lista de títulos; e os títulos dos itens ainda usavam siglas, embora todas
  estivessem no glossário.
- **Caso 2, uma pergunta de status com `?` e sem brief: passou no essencial.** O agente respeitou o
  gate de pergunta, não criou arquivo e ofereceu o brief. Mas a resposta dele foi uma lista longa e
  cheia de siglas, que é o problema original. Reforcei a frase do D4.2 na skill: no máximo uma linha
  simples por pendência, siglas trocadas pelo que significam, e opções e análise só no brief. Não
  repeti o teste depois desse reforço.
- **Caso 3, a decisão "D1: opção 2": falhou, e é o assunto do D8.** Uma parte do defeito não
  dependia de escolha sua e já foi corrigida: dois trechos da skill se contradiziam, porque um
  mandava "atualizar o documento dono" enquanto o outro dizia que isso é um trabalho à parte. Agora
  os dois dizem a mesma coisa, e quando esse trabalho pode acontecer fica para o D8.
- Os três agentes eram do modelo Sonnet. Conferi que nenhum escreveu fora do repositório de teste:
  a sua home e as duas pastas reais de planos ficaram como estavam.
- Nada foi para o stage nem foi commitado. Estão modificados sete arquivos versionados: o `SKILL.md`
  e o modelo da `discussion-briefs`, o `SKILL.md` da `plan-implementation`, da
  `architecture-records` e da `codex-claude-loop`, o registro de skills e o `.gitignore`. Este brief
  e o plano aparecem agora no `git status` como arquivos novos, por causa do D3.

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
