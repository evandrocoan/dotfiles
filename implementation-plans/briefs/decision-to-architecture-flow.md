# Brief de discussão: o caminho de uma decisão até o registro de arquitetura

**Estado:** em discussão

**Acompanhamento atual:** [brief de correções e fechamento](decision-to-architecture-closure.md).
Este documento fica preservado como referência das decisões e do estado conferido em 22/09/2026.
O novo brief concentra a discussão atual; a mudança de documento não encerra o trabalho nem
altera as decisões abaixo.

**Alimenta:**

- [plano de implementação](../active/decision-to-architecture-flow.md), que recebeu as decisões
  tomadas, inclusive a autorização ampliada D24 e sua consequência para D23, em inglês, e os
  pareceres de D19 e D21. O plano registra a
  sequência das decisões promovidas. Pelo D11, nenhum registro de arquitetura é criado: as skills
  são a autoridade durável e recebem as regras na
  execução do plano.

Documento de trabalho: explica os pontos em aberto e resume o que já foi decidido. Não substitui o
plano de implementação nem o registro de arquitetura, e nada escrito aqui autoriza trabalho; cada
decisão vale onde foi registrada.

## Resumo

**A revisão encontrou problemas nas skills e falhas diferentes nos modelos.** Revisei as quatro
skills centrais (`architecture-records`, `plan-implementation`, `discussion-briefs` e
`documentation`) e cinco templates relevantes. O Sol xhigh fez a conferência independente dos
achados principais. Isso não é uma auditoria de todas as skills instaladas nem a revisão E2.

Os achados que justificam correção são:

- **Defeito de escopo em `documentation`:** a existência de um arquivo de instruções na raiz
  aciona a obrigação de criar os três arquivos de compatibilidade, inclusive numa revisão
  somente leitura. A autorização superior continua impedindo a escrita, mas a skill deve
  limitar essa obrigação aos trabalhos em que a configuração das instruções está no escopo.
- **Ambiguidade no template de arquitetura:** dentro de Non-goals, pede para carregar as regras
  preservadas “aqui”. Pode parecer que garantias obrigatórias pertencem aos itens excluídos.
  O texto deve distinguir mudança fora do escopo de comportamento que continua obrigatório.
- **Custo de uso e manutenção:** há regras repetidas e muitas exceções para descobrir qual
  conferência se aplica à fase atual. É um risco de compreensão, sem prova de que causou a
  falha do Sonnet. O próprio plano e este brief acumularam histórico demais; reduzi este resumo,
  mantendo decisões e resultados anteriores no plano.

A regra central de preservar garantias expressas na prosa e no fluxo já é explícita. A skill
não permite tornar uma obrigação opcional só porque seu futuro responsável é desconhecido.
O template ambíguo nem foi lido na última extração do Sonnet, portanto não explica aquele erro.

Executei uma tentativa nova com cada configuração pedida, sequencialmente, com arquivos e
critérios congelados. Escolhi high para Sol e Opus. Não corrigi respostas nem repeti tentativas.
O Sonnet abaixo é a referência anterior com as mesmas skills, não uma quarta rodada nova.

| Configuração | Preservou confirmação/avanço como obrigação futura | Resultado restante |
| --- | --- | --- |
| Sonnet 5/xhigh, referência anterior | Não; citou somente o comportamento antigo. | Também falhou em validação, vigência do registro e leitura de `documentation`. |
| Terra xhigh | Sim. | Não vinculou a validação do novo responsável à retirada da proteção antiga. |
| Sol high | Sim. | Mesma lacuna de transição; também disse que o registro atual vale só até registrar D1. |
| Opus 5/high | Sim. | Vinculou a transição ao teste do filtro, mas não ao avanço/ack; transformou a proibição da DLQ em proibição de qualquer armazenamento reprocessável, que o registro não autorizava. |

**Nenhuma tentativa passou em todos os critérios.** A falha de transição dos três modelos novos
não equivale à perda da obrigação observada no Sonnet. Na prática, falta exigir que o caminho
que confirma o descarte seja localizado e validado antes de retirar a proteção anterior.
Já a proibição extra do Opus ampliaria a decisão do usuário se fosse transportada para o registro.
Nenhum modelo alterou documentos ou código neste exercício de análise.

Conferi todas as chamadas e suas respostas: somente leituras e listagens permitidas. Os dois
rastros do Codex deixam o corpo inicial da tarefa criptografado; guardei o prompt enviado e a
correspondência entre os rastros, mas a entrega em texto claro permanece `UNVERIFIED`. O Opus
teve modelo/esforço, tarefa exata, diretório, resposta terminal e saída normal confirmados.
Os resultados mecânicos `UNVERIFIED` ficam separados da conferência completa dos efeitos pelo
autor. A [avaliação detalhada](../active/decision-to-architecture-flow.md#comparative-extraction-results)
registra os critérios, métricas e limites; os
[achados nas skills](../active/decision-to-architecture-flow.md#skill-source-review) apontam os
textos concretos. Evidências temporárias: S
`post-audit-b1-b3-410811bdf229/live/skill-quality-comparison-01/`.

Recomendo corrigir primeiro os dois defeitos textuais e tratar a organização por fase em uma
mudança separada, preservando as regras aprovadas. **Nenhuma skill foi alterada nesta revisão.**
Uma observação por configuração não estabelece ranking geral nem demonstra a causa da falha.
As três respostas mostram que a preservação é compreensível; não aprovam a geração posterior
do registro e do plano.

A revisão e as três tentativas terminaram. O plano maior continua ativo: a aprovação
comportamental de D18/D22, a conferência completa do autor e a revisão final independente E2
não foram satisfeitas por este diagnóstico. **Nenhuma decisão está pendente de registro.**
D1 está preservada, D20.2 continua excluindo `run-large-4`, E1/E3 estão resolvidos e E2 continua
sendo o único ponto externo aberto, em sessão nova aberta por você. As falhas anteriores
continuam documentadas nas seções históricas do plano.

## Glossário

| Termo | O que é |
| --- | --- |
| skill | Pacote de instruções que o agente carrega para um tipo de tarefa. |
| brief | Documento de trabalho em português criado pela skill `discussion-briefs`; este arquivo é um. |
| registro de arquitetura | Documento durável, em inglês, que guarda uma decisão de desenho aprovada e as regras que o código deve obedecer; é regido pela skill `architecture-records`. |
| regra do registro | Uma frase do registro de arquitetura que o código tem de cumprir; a skill chama isso de invariante. No outro chat era a "invariante 18". |
| plano de implementação | Roteiro temporário, em inglês, da sequência de trabalho; é regido pela skill `plan-implementation`. |
| dono da decisão | O documento onde a decisão fica registrada quando você manda registrar. Decisão de desenho durável: o registro de arquitetura. Sequência de execução: o plano. Não é o mesmo que autoridade, que é o texto que governa o que o agente faz, como uma skill ou um registro implementado. |
| `registro pendente` | Marca que um item decidido carrega no brief enquanto o dono ainda não recebeu a decisão. |
| revisão independente | Revisão feita por um agente com contexto limpo, que só lê e relata; a `plan-implementation` a exige em trabalho de alto risco, antes e depois. |
| estado do registro | Rótulo do registro inteiro: proposto, em implementação, implementado ou substituído. |
| sessão que implementa | A conversa nova, no outro chat com o modelo Opus, que recebe o plano pronto e escreve testes e código. |
| `references/` | Subpasta de uma skill com documentos que o agente só abre quando o `SKILL.md` manda, numa situação específica. |
| advisor | Ferramenta da sessão anterior do Claude que consultava outro modelo para aconselhamento; está indisponível nesta sessão do Codex. |
| juiz | Script meu que confere mecanicamente o resultado de uma rodada do teste: os arquivos, o diretório do Git e a transcrição. O que pede leitura, como a resposta do agente, eu confiro lendo. |
| DLQ | A fila de reprocessamento (dead-letter queue) do repositório fictício usado nas rodadas; aparece numa regra do registro de arquitetura de teste. |
| avanço/ack | Confirmação de que uma mensagem já foi consumida, para que a leitura da fila possa avançar; o teste deve preservar isso também quando uma mensagem de outro cliente é descartada. |
| Sol | Modelo `gpt-5.6-sol`, que produziu em `xhigh` o parecer recebido em D19; também fez a primeira auditoria de fechamento. |
| Sonnet | Modelo Claude: a rodada high reprovou; a tentativa xhigh sem interação falhou na preparação; a rodada interativa e o par posterior com instruções anteriores/reorganizadas reprovaram nos critérios de conteúdo. |
| Terra xhigh | Configuração `gpt-5.6-terra` com esforço `xhigh`; a rodada D24 foi executada e reprovada, com avaliação preservada. |
| fixture | Conjunto isolado de arquivos de exemplo sobre o qual o agente do teste trabalha, sem alterar o projeto real. |
| alto risco | Classificação da `plan-implementation` para mudanças que mexem em arquitetura, autorização ou regras de revisão; exige plano completo e revisão independente. |
| Astra | Modelo `gpt-6-astra`, que fez as revisões anteriores do plano e a segunda auditoria; a sessão que agora escreve não pode revisar o próprio trabalho. |
| B1 | Achado sobre a trava por fase impedir o registro que resolveria a pendência; a correção foi implementada e conferida localmente. |
| B2 | Achado sobre um controle de teste que parecia remover regras, mas conservava seu significado em outra seção. |
| B3 | Achado sobre a ausência da revisão independente herdada antes da frase e da rodada do D16. |
| `run-large-4` | Quarta execução do caso grande, a única autorizada por D16; seus arquivos e sua resposta estão guardados. |
| controle feito à mão | Resultado montado pelo autor para conferir se o juiz aceita um caso válido ou rejeita um defeito específico; não executa um agente. |
| rejulgamento | Leitura e conferência de arquivos já produzidos, sem gerar nova resposta de modelo. |
| rodada nova | Execução de um agente em uma cópia isolada do caso de teste; consome recursos e precisa de autorização própria. |
| risco herdado | Continuação material que mantém as revisões e os critérios de fechamento do plano de alto risco a que pertence. |

## Decisões que dependem de você

### D1 — O brief pode dar uma decisão como registrada quando só o plano a recebeu?

**Estado:** decidido

**Decisão:** opção 1. Ao registrar, o agente nomeia o dono de cada decisão: a decisão de desenho
durável vai para o registro de arquitetura, e a sequência de execução vai para o plano. Enquanto
faltar um dono, o item continua com `registro pendente` para ele, o brief não fecha, e a resposta no
chat diz o que ficou de fora e por quê. Registrada no
[plano](../active/decision-to-architecture-flow.md). Esta opção faz o brief ficar aberto por
mais tempo, e o risco de ele ser esquecido aberto depois da implementação virou o D7.

**A pergunta para você:** se o brief deve continuar com `registro pendente`, e sem poder ser
concluído, enquanto o registro de arquitetura não receber uma decisão que é dele.

**O que aconteceu:** no outro chat, a decisão de remover o bloco do Redmine muda uma regra de um
registro de arquitetura aprovado. Depois de "registre as decisões", o agente escreveu a decisão no
plano, trocou no brief as marcas `registro pendente` por links para o plano e marcou o brief como
concluído. O registro de arquitetura ficou com o contrato antigo, como "segundo passo de quem
implementar". Ele tinha motivos reais para adiar, mas decidiu sozinho e não disse nada.

**O que teria sido o certo no exemplo:** o agente podia ter emendado o registro na hora. Você já
tinha aprovado a decisão e mandado registrar, e a `architecture-records` diz que o registro muda
primeiro quando uma decisão deliberada muda o desenho aprovado. Bastava a regra nova entrar rotulada
como "emenda aprovada, em implementação", com a regra vigente ainda escrita, que é o assunto do D2.
Adiar a emenda para depois da revisão independente também era uma escolha possível; qual das duas
ordens vale é o assunto do D3. O que não era aceitável era escolher em silêncio. Os erros foram
três, todos sobre o que o brief e o chat diziam enquanto a emenda não acontecia: o brief trocou
`registro pendente` por um link para o plano, embora o dono de uma decisão de desenho seja o
registro de arquitetura; o brief foi marcado como concluído; e o agente não contou que a arquitetura
tinha ficado para depois nem o motivo.

| Momento | O que aconteceu | O que teria acontecido com a opção 1 |
| --- | --- | --- |
| Você manda "registre as decisões" | A decisão vai só para o plano. | A decisão vai para o plano e, se a emenda não for feita na hora, o agente diz isso. |
| O item no brief | `registro pendente` vira link para o plano. | Ganha o link para o plano e mantém `registro pendente` para o registro de arquitetura, com o motivo do adiamento. |
| O estado do brief | Concluído. | Em discussão, até o registro de arquitetura receber a decisão. |
| A resposta no chat | Diz que os registros ficaram "no contrato antigo, de propósito", como passo de quem implementar. | Diz que falta o registro de arquitetura e por quê, quantas decisões estão pendentes, e oferece emendar já ou depois da revisão. |
| Depois da emenda | Ficaria para outra sessão. | O item ganha o link para o registro emendado e o brief pode ser concluído. |

Este item não decide quando o registro é emendado. Ele só garante que você veja que ainda não foi.

**Por que importa:** um brief concluído quer dizer "tudo está registrado onde manda". Ali não era
verdade, e nada no brief nem no chat mostrava isso.

**Opções:**

1. Nomear o dono de cada decisão ao registrar. Decisão de desenho durável vai para o registro de
   arquitetura; a sequência de execução vai para o plano. Enquanto faltar um dono, o item continua
   com `registro pendente` para ele, o brief não fecha, e a resposta no chat diz o que ficou de fora
   e por quê.
2. Deixar como está: o agente escolhe onde registrar e quando o brief fecha.

**Pontos negativos de cada opção:**

- Opção 1: o brief fica aberto por mais tempo; no caso do Redmine, até a revisão independente e a
  emenda do registro acontecerem. O agente precisa julgar o que é "decisão de desenho durável" e
  pode errar para os dois lados. Aparecem mais avisos de `registro pendente` no chat.
- Opção 2: a falha que você sentiu pode se repetir, porque nada obriga o agente a avisar.

**Recomendação:** opção 1. Mexe só na `discussion-briefs`, é mudança de redação e resolve o
problema sem depender dos outros itens.

### D2 — Como escrever no registro uma regra nova que ainda não tem código?

**Estado:** decidido

**Decisão:** opção 1, a marca só na regra, na variante por tamanho da mudança. Emenda pequena
entra como bloco "emenda aprovada, em implementação" logo abaixo da regra vigente. Mudança grande
de desenho segue o caminho que a skill já tem, o registro novo no estado proposto, com a linha de
aviso no registro antigo, que só vira "substituído" quando o novo estiver implementado. Registrada
no [plano](../active/decision-to-architecture-flow.md).
O que separa a mudança pequena da grande você decidiu no D10, opção 4: o objetivo decide, sem
contagem de regras. Por isso a frase "de uma ou duas regras" saiu desta decisão.

**A pergunta para você:** de que forma um registro de arquitetura já implementado mostra uma regra
que você aprovou, mas que o código ainda não cumpre.

**Contexto:** a `architecture-records` só tem estado para o registro inteiro. Ela também proíbe
apresentar comportamento futuro como atual. No caso do Redmine, uma única regra muda e o resto do
registro continua valendo. A skill não diz o que fazer: marcar o registro inteiro como "em
implementação" é exagero, e não marcar nada é apresentar o futuro como presente.

**O que a skill já tem sobre substituir um registro (verificado em 2026-09-19):** o estado
"proposto", para um registro que descreve comportamento pretendido e ainda não entregue; o estado
"substituído", em que o registro antigo é guardado como histórico, com link para o novo, sem que
dois registros mandem ao mesmo tempo; e um critério para escolher entre emendar e substituir. Esse
critério diz: emenda-se quando o contrato estava incompleto, e cria-se ou substitui-se um registro
só quando muda de verdade o modelo de donos, a fronteira de autoridade, a ordem das etapas, o
significado de uma falha ou a política de recuperação. Hoje a skill usa a substituição em três
situações:

- Quando um incidente mostra que o desenho está errado. É aqui que o critério acima está escrito, e
  só aqui.
- Quando a execução de um plano revela uma decisão durável faltando ou errada: emenda-se ou
  substitui-se o registro primeiro, e depois refazem-se os passos do plano. A `plan-implementation`
  manda parar e pedir orientação se isso passar do que você autorizou.
- Quando você toma uma decisão deliberada. A skill só menciona isso de passagem, ao dizer que o
  registro aprovado manda "até que uma decisão deliberada o substitua ou emende", e não dá
  procedimento nenhum.

**O que falta nela:** nas três situações, a skill não diz em que momento o registro antigo vira
"substituído": quando o novo nasce como proposto, ou só quando o novo é implementado. No caso 3 do
teste da `discussion-briefs`, o agente criou o registro novo e marcou o antigo como substituído na
mesma hora, sem mudar código nenhum, e nenhum registro passou a descrever o que valia naquele
momento. Se o código daquele repositório de teste seguia o registro antigo não foi verificado.
Falta também a emenda pequena antes do código: "emendar no lugar" quer dizer reescrever a regra, o
que apresenta o futuro como presente.

**O que este item acrescentaria de fato à skill:** três coisas pequenas. O bloco "emenda aprovada,
em implementação" para a emenda pequena. A linha de aviso no registro antigo enquanto o substituto
ainda está proposto. E a regra de que o antigo só vira "substituído" quando o novo estiver
implementado. O critério para escolher entre o bloco e o registro novo você decidiu no D10: a
revisão independente mostrou que o critério dos incidentes não é o mesmo que a regra por tamanho
descrita mais abaixo, e nenhum dos dois ficou.

**Como fica na prática:**

| O que acontece | Opção 1: marca só na regra | Opção 2: registro novo, proposto | Opção 3: registro inteiro em implementação |
| --- | --- | --- | --- |
| Regra que vale hoje | Continua escrita como vigente. | Continua no registro antigo, intocada. | Continua escrita, mas o registro todo parece em fluxo. |
| Regra nova aprovada | Aparece ao lado, rotulada "emenda aprovada, em implementação". | Fica num registro novo, no estado proposto, que aponta para a regra que vai substituir. | Entra no texto, com uma nota dizendo o que ainda não foi entregue. |
| Quando o plano fecha | A regra nova substitui a antiga e o rótulo some. | O registro novo passa a "implementado", e o antigo passa a "substituído" e fica guardado como histórico. | O registro volta para "implementado". |
| Mudança na skill | Um conceito novo e pequeno: o bloco de emenda dentro de um registro implementado. | Quase nada: os estados já existem; entram a linha de aviso no registro antigo e o momento em que ele vira "substituído". | Nenhuma. |

**Como a opção 1 ficaria dentro de um registro:** o exemplo é inventado, porque não vi o registro
real do Redmine, e está em inglês, como todo registro de arquitetura. Hoje, antes da sua decisão:

```markdown
18. Every update sent to Redmine is first compared with the remote issue. The `redmine_native`
    block may skip that comparison for the fields it owns.
```

Depois de "registre as decisões", com o código ainda antigo:

```markdown
18. Every update sent to Redmine is first compared with the remote issue. The `redmine_native`
    block may skip that comparison for the fields it owns.

    **Approved amendment, in implementation:** the `redmine_native` block is removed, and no
    update may skip the remote comparison. Until this amendment is implemented, the rule above
    stays in force.
```

Quando o plano fecha, o bloco some e a regra é reescrita:

```markdown
18. Every update sent to Redmine is first compared with the remote issue. No update may skip that
    comparison.
```

**O que impede a marca de virar bagunça:**

- Um lugar só. O bloco fica imediatamente abaixo da regra que ele muda, nunca numa seção de
  "emendas" no fim do arquivo.
- A regra vigente continua sem marca, e o bloco diz com todas as letras que a regra de cima
  continua valendo. Ele não descreve o estado do código, porque o andamento mora no plano. Quem lê
  sabe o que vale hoje e o que está a caminho.
- No máximo uma emenda pendente por regra. Se você mudar de ideia, o bloco é reescrito, não
  empilhado.
- É temporária e cobrada no fechamento. A `architecture-records` já tem uma passada obrigatória de
  limpeza antes de um registro ser dado como implementado; o bloco de emenda entra na lista do que
  não pode sobrar.
- Sem datas, links de plano ou andamento dentro do bloco, porque a skill já proíbe diário de
  execução no registro.

**É confuso ter emendas dentro da arquitetura?** Um pouco, porque por um tempo a mesma regra
aparece em duas versões. Mas as alternativas confundem mais. Não marcar nada, que é o que acontece
hoje, deixa o registro parecendo estável quando já existe uma decisão sua que o contradiz; foi o
caso do outro chat. Na opção 2, quem lê a regra antiga só descobre que ela vai mudar se houver nela
um aviso apontando para o registro novo, e esse aviso já é uma pequena marca. Na opção 3, nenhuma
regra fica marcada e o leitor não sabe qual delas está mudando.

**Variante da opção 1, por tamanho da mudança:** usar o bloco só para emenda pequena, de uma ou
duas regras. Quando a mudança mexe em várias regras, no fluxo ou em quem é dono do quê, usar o
caminho que a skill já tem, um registro novo no estado proposto, acrescido da linha de aviso no
registro antigo. Eu tinha escrito aqui que este era o mesmo critério que a `architecture-records`
usa para incidentes. Não é: o da skill olha a natureza da mudança, e não a quantidade de regras.
Nenhum dos dois ficou: no D10 você escolheu o teste do objetivo.

**Como ficaria o registro novo, num exemplo inventado de mudança grande:** imagine que a decisão
fosse mudar o jeito inteiro de gravar no Redmine, com toda gravação passando por um pacote revisado
em vez de o agente gravar direto. Isso mexeria em três regras, no desenho do fluxo e em quem é dono
da comparação com o remoto. Com blocos de emenda, o registro antigo ficaria com três blocos e a
seção de fluxo reescrita pela metade. Com o registro novo, três coisas mudam no momento da decisão.

Nasce um arquivo novo com o desenho inteiro, no estado proposto, que já existe na skill e significa
"comportamento pretendido, ainda não é o que o código faz":

```markdown
# Redmine reviewed writes

**Status:** Proposed. This record is not current functionality. It will supersede
[Redmine sync](redmine-sync.md) when implemented.

## Decision

Every write to Redmine goes through a reviewed package...
```

O registro antigo ganha uma única linha de aviso no topo, e todas as regras dele continuam
intactas e valendo:

```markdown
# Redmine sync

**Status:** Implemented. A proposed replacement exists:
[Redmine reviewed writes](redmine-reviewed-writes.md). This record describes current behavior
until that one is implemented.
```

E o índice `architecture/README.md` ganha a entrada do registro novo. Quando o plano fecha, o
registro novo passa a "implementado", e o antigo passa a "substituído", com link para o novo, e fica
guardado como histórico. É o ciclo que a skill já descreve hoje.

**Como escolher entre o bloco e o registro novo:** a diferença está em onde o texto novo vive
enquanto o código não muda. No bloco, ele fica embaixo da própria regra, e no fim só aquela regra é
reescrita. No registro novo, o desenho fica inteiro num arquivo próprio, e o registro antigo
continua limpo, descrevendo o que vale hoje. A regra prática: se a mudança cabe em uma ou duas
regras, sem tocar no fluxo nem em quem é dono do quê, usa-se o bloco; se não cabe, usa-se o registro
novo. Esta regra prática juntava quantidade e natureza e deixou de valer: no D10 você a trocou
pelo teste do objetivo.

**Pontos negativos de cada opção:**

- Opção 1: a skill ganha mais uma regra. Por um tempo o registro mostra duas versões da mesma regra
  lado a lado, e alguém pode ler a errada. O fechamento do plano precisa conferir que o bloco saiu.
  Na variante por tamanho, o agente ainda precisa julgar o que é "emenda pequena", e pode errar.
- Opção 2: multiplica registros pequenos. A regra fica espalhada em dois arquivos até o fechamento,
  e o índice de arquitetura muda duas vezes. É pesado para emendar uma frase.
- Opção 3: é desproporcional. Quem lê não sabe qual parte está mudando, e fica mais difícil saber o
  que vale hoje.

**Recomendação:** opção 1 na variante por tamanho. Para uma emenda pequena, ela mantém num lugar só
o que vale hoje e o que está a caminho; para uma mudança grande de desenho, o registro novo evita
encher o registro antigo de blocos.

### D3 — O que vem primeiro: a revisão independente do plano ou a emenda do registro?

**Estado:** decidido

**Decisão:** opção 2, emenda primeiro. Você decide; o registro de arquitetura é emendado; o plano
nasce do registro emendado; a revisão independente examina os dois; depois vem código.
Registrada no [plano](../active/decision-to-architecture-flow.md). Ela depende da opção 1 do
D2, que você também já escolheu: a regra nova entra com a marca "emenda aprovada, em
implementação", e por isso emendar primeiro não apresenta o futuro como comportamento atual.

**Esclarecimentos das revisões:** não fazem parte do que você decidiu; são o modo como o plano
aplica a decisão, e a segunda revisão conferiu que eles preservam "emenda primeiro". As revisões
independentes apontaram que emendar primeiro é uma exceção deliberada à regra da
`plan-implementation` de revisar antes de qualquer passo, e não uma leitura do texto de hoje. Por
isso o plano dá limites à exceção: antes da revisão só entra o bloco rotulado do D2, ou o registro
novo proposto com a linha de aviso e a entrada dele no índice de arquitetura; nenhum outro texto do
registro, nenhum código e nenhum arquivo de instruções muda. O que fazer quando mexer no registro
obriga a uma mudança fora desses limites, como traduzir um registro que não está em inglês, é uma
escolha sua: no D12 você decidiu que, nesse caso, a emenda recua para depois da revisão.

**A pergunta para você:** qual é a ordem quando é o próprio plano que propõe a mudança de desenho.

**Contexto:** as duas skills puxam para lados diferentes e nenhuma resolve. A
`architecture-records` diz que, quando uma decisão durável muda, o registro é emendado primeiro e o
plano nasce dele. A `plan-implementation` diz que trabalho de alto risco passa por revisão
independente antes de qualquer passo de implementação, e não diz se emendar o registro conta como
passo de implementação.

**Opções:**

1. Revisão primeiro. Você decide; o plano é escrito com a mudança ainda como proposta; a revisão
   independente examina o plano; o registro é emendado; só depois vem código.
2. Emenda primeiro. Você decide; o registro é emendado; o plano nasce do registro emendado; a
   revisão independente examina os dois; depois vem código.

**Pontos negativos de cada opção:**

- Opção 1: até a revisão terminar, o plano propõe algo que o registro ainda proíbe, e os dois
  discordam de propósito. A decisão não mora no dono dela durante esse tempo, e o brief não pode ser
  concluído. O revisor examina a decisão sem ver a redação final do contrato.
- Opção 2: se o revisor achar defeito na decisão central, o registro é emendado duas vezes. O custo
  é pequeno, porque se corrige um bloco de texto rotulado como emenda, e não código. Nesse
  intervalo, o registro mostra uma regra que a revisão pode derrubar; por isso ela só pode entrar
  com o rótulo "emenda aprovada, em implementação", que depende do D2.

**Recomendação:** opção 2, junto com a opção 1 do D2. A decisão passa a morar no dono dela na mesma
hora, sem janela em que plano e registro discordam. O revisor independente examina o plano junto
com a redação real do contrato, o que melhora a revisão. E quem escreve a emenda é a sessão que
ainda tem a discussão fresca, o que combina com o D4. O rótulo diz a verdade: você aprovou a regra,
e o código ainda não a cumpre. Sem a marcação do D2, eu ficaria com a opção 1, porque aí a emenda
apresentaria o futuro como presente.

### D4 — Quem emenda o registro: a sessão da discussão ou a sessão que implementa?

**Estado:** decidido

**Decisão:** opção 1. Quem emenda o registro de arquitetura é sempre a sessão que conduziu a
discussão e escreveu o plano, antes de passar o trabalho adiante. A sessão que implementa recebe
"os registros já estão emendados; implemente contra eles". Registrada no
[plano](../active/decision-to-architecture-flow.md).

**A pergunta para você:** quem escreve a emenda do registro de arquitetura quando o trabalho é
passado para outra sessão implementar.

**Contexto:** no outro chat, a emenda foi empurrada para a sessão que implementa, por inércia. A
redação do contrato é onde o contexto da discussão mais pesa: os seus argumentos, as medições e o
motivo de cada regra. Uma conversa nova reconstrói isso a partir do plano, com perda.

**Opções:**

1. Sempre a sessão que conduziu a discussão e escreveu o plano, antes de passar o trabalho
   adiante. Quem implementa recebe "os registros já estão emendados; implemente contra eles".
2. A sessão que implementa, como um passo do plano.
3. A sessão da discussão por padrão, mas o plano pode atribuir a emenda a outra sessão, desde que
   diga o motivo.

**Pontos negativos de cada opção:**

- Opção 1: a conversa da discussão, que costuma estar longa, fica ainda mais pesada e cara. Se ela
  já estiver perto do limite de contexto, a qualidade da emenda cai.
- Opção 2: quem escreve o contrato escreve também o código, na mesma sessão, e o contrato pode se
  dobrar ao código. O contexto da discussão se perde.
- Opção 3: a exceção tende a ser usada por inércia, que foi exatamente o que aconteceu.

**Recomendação:** opção 1. Combina com a `codex-claude-loop`, em que a sessão planejadora já é dona
do plano e a outra só implementa.

### D7 — Como evitar que um brief fique aberto e esquecido depois da implementação?

**Estado:** decidido

**Decisão:** opção 1, conferir no fechamento do plano. Antes de mover um plano para `completed/`, a
`plan-implementation` manda abrir o brief do mesmo assunto. Se houver decisão com
`registro pendente`, o plano não fecha. Se houver só item aberto, o agente avisa você na mensagem
de fechamento, o plano anota isso e fecha. Registrada no
[plano](../active/decision-to-architecture-flow.md).

**Esclarecimento das revisões:** não faz parte do que você decidiu; é o modo como o plano aplica a
decisão, e a segunda revisão conferiu que ele a preserva. Esta conferência não afrouxa nenhuma
regra de fechamento que já existe. Um item aberto que represente uma validação, uma autorização ou
um acesso obrigatório continua impedindo o fechamento pelas regras atuais da
`plan-implementation`; "fecha" quer dizer que esta conferência, sozinha, não segura o plano.

**A pergunta para você:** quem confere, e quando, se sobrou um brief aberto sobre um assunto que já
foi implementado.

**Pode acontecer:** sim. Conferi as duas skills em 2026-09-19. O brief só é olhado em três momentos:
quando um plano sobre o mesmo assunto é criado, antes de cada fase de um plano em andamento, e só
para itens com `registro pendente`, e quando o plano muda de pasta, só para consertar links. Ninguém
olha o brief na hora de fechar o plano, e nada lista os briefs que continuam em discussão. O estado
fica só no cabeçalho do arquivo, numa pasta sem divisão entre abertos e concluídos. Três caminhos
levam a um brief esquecido:

- Sobra um item que você nunca decidiu, como um teste opcional. O plano fecha, a implementação
  termina, e o brief fica em discussão para sempre.
- Sobra uma decisão com `registro pendente`, porque o trabalho foi feito sem plano formal, ou por
  uma sessão que não carregou a `discussion-briefs`. A decisão D1 aumenta esse risco, porque o brief
  passa a esperar também o registro de arquitetura.
- Tudo foi decidido e registrado, mas o agente que registrou a última decisão não marcou o brief
  como concluído.

**Por que importa:** um brief aberto e esquecido é uma lista de pendências que ninguém lê. Se tiver
uma decisão sua ainda não registrada, ela pode ser contrariada pela implementação sem que ninguém
perceba.

**Opções:**

1. Conferir no fechamento do plano. Antes de mover um plano para `completed/`, a
   `plan-implementation` manda abrir o brief do mesmo assunto. Se houver decisão com
   `registro pendente`, o plano não fecha. Se houver item aberto, o agente avisa você na mensagem de
   fechamento e o plano anota isso, mas fecha.
2. Lembrete passivo. Sempre que a `discussion-briefs` for carregada num repositório, o agente lista
   em uma linha do chat os briefs que continuam em discussão ali.
3. Separar por pasta, `briefs/active/` e `briefs/completed/`, como os planos. Um brief esquecido
   fica visível só de listar a pasta.
4. Nada. Você confere quando lembrar.

**Pontos negativos de cada opção:**

- Opção 1: só cobre trabalho que tem plano formal; um trabalho de rotina, sem plano, não passa por
  esse fechamento. Acrescenta mais uma regra ao fechamento da `plan-implementation`, que já é longo.
  Bloquear o fechamento por `registro pendente` pode segurar um plano por causa de uma decisão que
  nem era dele, se o brief misturar assuntos.
- Opção 2: só avisa, e tarde. O aviso aparece quando a `discussion-briefs` é carregada, isto é,
  quando surgem pendências novas, quando você pede ou refina um brief, ou quando faz uma pergunta de
  status. Nenhum desses momentos está ligado à hora em que alguém implementa. Exemplo: na segunda
  você decide um item, que fica com `registro pendente`; na terça outra sessão implementa o assunto
  num trabalho de rotina, sem plano, e a skill nem é carregada; na sexta você pergunta "o que
  falta?" sobre outro assunto, e só então aparece a linha dizendo que o brief tem uma decisão não
  registrada, com o código escrito há três dias. Trabalho sem plano não tem ponto de conferência
  nenhum, e por isso ali o aviso só pode chegar depois; para avisar antes, a regra teria de morar
  nas instruções globais, que é uma mudança bem mais pesada. Além disso, um aviso repetido acaba
  ignorado, embora dê para reduzir o ruído a uma linha, mostrada só quando existir algum brief em
  discussão. O custo é baixo: basta ler a linha de estado de cada arquivo da pasta `briefs/`.
- Opção 3: mover arquivos quebra links, inclusive os do plano para o brief, e exige mais uma regra
  de conserto de links. É mais estrutura para um documento de trabalho, e você acabou de pedir que
  os itens parem de mudar de lugar dentro dele.
- Opção 4: o problema que você levantou continua sem dono.

**Recomendação:** opção 1. É o momento natural, porque o fechamento do plano já é uma conferência, e
ela pega justamente o caso perigoso, a decisão não registrada. As opções 1 e 2 não competem: a 1
previne, e a 2 detecta. A 2 cobre o ponto fraco da 1, que é o trabalho sem plano formal, e pega
também o caso em que tudo foi registrado mas ninguém marcou o brief como concluído. Ela pode entrar
junto ou depois, ao custo de uma frase a mais na `discussion-briefs`.

### D8 — Os itens de trabalho devem ter um prefixo próprio, como T1, em vez de D5?

**Estado:** decidido

**Decisão:** opção 2, um prefixo e uma sequência por seção. Decisões entre opções usam D, trabalho
que posso fazer usa T, e o que depende de terceiros ganha um prefixo próprio. Cada seção começa no
1, e um item novo recebe o próximo número da sua seção. O número de um item continua sem mudar
nunca: se um item mudar de natureza, cria-se um novo na seção certa, e o antigo fica `descartado`,
apontando para o novo. Vale para os briefs novos; este brief e os que já existem ficam como estão.
Registrada no [plano](../active/decision-to-architecture-flow.md).

**A pergunta para você:** se o identificador de um item deve mostrar de que tipo ele é.

**Contexto:** hoje a `discussion-briefs` numera todos os itens de um brief numa sequência só, D1,
D2, D3, seja qual for a seção. O "D" nasceu de "decisão", e por isso o D5 parece fora de lugar numa
seção que se chama "Trabalho que posso fazer". A sua leitura foi a natural: ali caberia um T1. A
regra que pesa do outro lado é que o número de um item nunca muda, para que um "D5" citado no chat
continue apontando para a mesma coisa.

**O seu ponto é de organização:** com uma sequência só, a ordem de leitura quebra sempre que um item
novo entra numa seção que não é a última. Neste brief, quem lê de cima para baixo encontra D1, D2,
D3, D4, D7, D8 e só depois D5 e D6, e a seção de trabalho começa no 5. Com um prefixo por seção,
cada seção começa no 1 e um item novo recebe o próximo número da própria seção: a leitura fica D1 a
D6 e depois T1, T2, sempre em ordem.

**Opções:**

1. Manter uma sequência só, com o prefixo D, e explicar. O modelo do brief passa a dizer que o
   número identifica o item, e não o tipo dele, e a seção de trabalho ganha uma linha explicando por
   que os itens dela também esperam uma resposta sua.
2. Um prefixo por seção: D para decisão entre opções, T para trabalho que posso fazer, e outro para
   o que depende de terceiros.
3. Um prefixo neutro para todos os itens, como P1, de "ponto", numa sequência só.

**Pontos negativos de cada opção:**

- Opção 1: o "D" continua parecendo "decisão", e a explicação precisa ser lida para a confusão não
  se repetir. A ordem de leitura continua quebrando quando entra um item novo fora da última seção.
- Opção 2: passam a existir duas ou três sequências para acompanhar. Se um item mudar de natureza
  durante a discussão, por exemplo um trabalho que vira escolha entre opções, o identificador não
  pode mudar. Isso é raro e tem saída sem renumerar: cria-se um item novo na seção certa, e o antigo
  fica marcado `descartado`, apontando para o novo.
- Opção 3: resolve a confusão sem criar sequências, mas os briefs que já existem usam D, e durante
  um tempo conviveriam os dois estilos.

**Recomendação:** opção 2, prefixo e sequência por seção. Ela resolve o que você apontou, a ordem
dentro de cada seção, e a regra de nunca renumerar continua valendo. A opção 3 tira a confusão do
"D", mas não conserta a ordem de leitura. Os briefs que já existem ficam como estão.

### D10 — Quando vale mais escrever um registro novo do que emendar o antigo?

**Estado:** decidido

**Decisão:** opção 4, o objetivo decide. O bloco é o padrão, e o registro novo entra quando emendar
o registro antigo deixaria mais ruído do que escrever um novo. O agente lista os lugares do registro
que a decisão obriga a mudar, mostra a lista no chat junto com a forma que escolheu e, na dúvida,
pergunta antes de escrever. Não há contagem fixa de regras, e por isso a frase "de uma ou duas
regras" saiu da decisão do D2. Registrada no
[plano](../active/decision-to-architecture-flow.md).

**A pergunta para você:** no D2 você escolheu o bloco de emenda para a mudança pequena e o registro
novo para a mudança grande. Falta dizer como o agente escolhe entre as duas formas.

**O objetivo da escolha:** evitar muito ruído no registro de arquitetura quando seria mais fácil
escrever um novo. O bloco serve enquanto deixa o registro legível. O registro novo serve quando
emendar o antigo daria mais ruído e mais trabalho do que escrever outro.

**Por que este item existe:** na explicação do D2 eu escrevi que a regra "uma ou duas regras, sem
tocar no fluxo nem em quem é dono do quê" era o mesmo critério que a `architecture-records` já usa
em incidentes. O revisor independente mostrou que não é. Conferi o trecho da skill em 2026-09-19, e
ele tem razão: o critério da skill olha a natureza da mudança e não conta regras. O erro foi da
minha explicação. A sua escolha no D2 continua valendo, e o que ficou sem definição é como separar
a mudança pequena da grande. O número "uma ou duas" também era arbitrário: a skill não fala em
número nenhum.

**O que cada forma custa:**

- O bloco é local. O leitor vê a regra vigente e a emenda juntas e entende as duas. Ele não
  representa bem uma mudança de estrutura, como uma seção de fluxo reescrita, um diagrama ou a
  tabela de quem é dono do quê. E, quando os blocos cobrem boa parte do registro, o leitor precisa
  montar o desenho novo de cabeça.
- O registro novo é caro. Pela `architecture-records`, o registro substituído deixa de mandar, e
  por isso o novo tem de carregar tudo o que continua valendo, e não só a parte que mudou. Num
  registro grande, isso é reescrever quase tudo para mudar uma frase. Entram ainda o arquivo novo,
  a entrada no índice, a linha de aviso e a troca para "substituído" no fechamento.

**As cinco coisas que a skill olha hoje,** e que as opções 1 e 3 usam, com exemplos no registro do
Redmine:

| O que a skill chama | Exemplo |
| --- | --- |
| Modelo de donos | Qual componente é responsável pela comparação com o Redmine remoto. |
| Fronteira de autoridade | Quem dá a palavra final sobre pular a comparação: o agente, o servidor ou você. |
| Ordem das etapas | Comparar, depois revisar, depois gravar. |
| Significado de uma falha | Se a comparação falha, isso quer dizer "aborte" ou só "avise". |
| Política de recuperação | Depois da falha: tentar de novo, desfazer ou perguntar a você. |

**Quatro exemplos para comparar as opções.** Só o exemplo C é real, e todos são no registro do
Redmine:

- Exemplo A, uma regra só, que muda quem manda: "quem decide se uma atualização pode pular a
  comparação passa a ser o servidor, e não mais o agente". Cabe num bloco, mas muda a fronteira de
  autoridade.
- Exemplo B, quatro regras que só completam detalhes: quatro campos a mais passam pela mesma
  comparação com o remoto. Nenhuma das cinco coisas muda.
- Exemplo C, o caso do outro chat: remover o bloco `redmine_native`. É uma regra só e, pelo que
  você colou, nenhuma das cinco coisas muda: a comparação continua com o mesmo dono e só perde uma
  exceção (não verificado; não vi o registro real).
- Exemplo D, o exemplo grande do D2: toda gravação passa por um pacote revisado, em vez de o agente
  gravar direto. Mexe em três regras, na seção de fluxo e em quem é dono da comparação.

**Opções:**

1. A natureza decide. Registro novo quando a decisão muda uma das cinco coisas da tabela acima;
   bloco em todos os outros casos, seja qual for o número de regras. Ao registrar, o agente escreve
   no chat a classificação que fez e por quê. A quantidade vira só um alerta: se os blocos forem se
   espalhar por muitas regras do mesmo registro, o agente para antes de escrever e pergunta se você
   prefere o registro novo.
2. A quantidade decide. Uma ou duas regras, bloco; mais que isso, registro novo.
3. As duas condições juntas, que é a leitura literal do que está escrito no D2. Bloco só quando são
   uma ou duas regras e nenhuma das cinco coisas muda; qualquer outro caso vira registro novo.
4. O objetivo decide. O bloco é o padrão, e o registro novo entra quando emendar o registro antigo
   deixaria mais ruído do que escrever um novo. Para julgar, o agente lista os lugares do registro
   que a decisão obriga a mudar: regras, seções de fluxo, diagramas e tabelas. Lista curta e só de
   regras dá bloco. Lista longa, ou que inclua fluxo, diagrama ou tabela, dá registro novo. Ele
   mostra a lista no chat junto com a forma que escolheu, por exemplo "toca as regras 4, 7 e 18 e
   nenhuma seção de fluxo; usei blocos", e na dúvida pergunta antes de escrever. Não há contagem
   fixa de regras. A escolha é reversível, porque é só texto, escrito antes de qualquer código; e
   a revisão independente, que pelo D3 examina o registro emendado junto com o plano, também julga
   a forma. Continuam valendo duas travas que já existem: a skill só admite registro novo quando o
   desenho muda de verdade, e o registro antigo só vira "substituído" quando o novo estiver
   implementado. No caso raro em que muita coisa muda sem alterar o desenho, o agente usa blocos e
   pergunta antes. A natureza da mudança não escolhe a forma: ela decide o cuidado, e mudança de
   arquitetura já é de alto risco na `plan-implementation`, com revisão independente. Na skill
   entram dois exemplos curtos, um de cada lado: o C e o D.

**Como fica na prática:**

| Caso | Opção 1: natureza | Opção 2: quantidade | Opção 3: as duas | Opção 4: objetivo |
| --- | --- | --- | --- | --- |
| Exemplo A, uma regra que muda quem manda | Registro novo inteiro por uma frase. | Bloco. | Registro novo. | Bloco, com plano de alto risco e revisão independente. |
| Exemplo B, quatro regras de detalhe | Quatro blocos, e o agente pergunta antes. | Registro novo. | Registro novo. | Blocos; a lista no chat mostra as quatro regras. |
| Exemplo C, o bloco do Redmine | Bloco. | Bloco. | Bloco. | Bloco. |
| Exemplo D, o jeito inteiro de gravar | Registro novo. | Registro novo. | Registro novo. | Registro novo, porque a lista inclui a seção de fluxo. |
| O que a skill passa a testar | A natureza, que é uma aproximação do objetivo. | Um número arbitrário. | As duas aproximações juntas. | O próprio objetivo, com a lista como evidência. |

**Pontos negativos de cada opção:**

- Opção 1: manda escrever um registro inteiro por causa de uma frase, como no exemplo A, que é o
  exagero que o objetivo quer evitar. Quando muitas regras mudam sem o desenho mudar, deixa blocos
  por todo o registro. Julgar se "a fronteira de autoridade mudou" exige interpretação.
- Opção 2: o número é arbitrário. Três regras pequenas já viram registro novo, e uma regra só cuja
  mudança obriga a reescrever o fluxo entra como bloco. A mesma skill ficaria com dois critérios,
  um para incidente e outro para decisão sua.
- Opção 3: é a mais estrita e a que mais gera registros novos sem necessidade. No exemplo B, quatro
  detalhes viram um registro inteiro. O agente aplica dois testes em vez de um.
- Opção 4: é um julgamento, e dois agentes podem escolher formas diferentes para a mesma mudança.
  Um modelo mais fraco tende a ficar no padrão, o bloco, mesmo quando o registro novo seria melhor;
  o que compensa é a lista no chat, a pergunta na dúvida e a revisão independente. No exemplo A, uma
  mudança de autoridade fica por um tempo como bloco dentro de um registro "implementado", e alguém
  pode ler a regra errada. O teste do D6, que você aprovou só para a mudança pequena, não exercita
  este julgamento; isso pediria a variante grande, que seria outra decisão sua.

**Recomendação:** opção 4. É a única que testa o objetivo em vez de uma aproximação dele, e errar
custa pouco, porque a forma se troca antes de qualquer código. A opção 1 parece mais segura no
exemplo A, mas o arquivo novo não acrescenta proteção nenhuma: o bloco tem rótulo, o agente mostra a
lista no chat, e o plano já é de alto risco. A frase da skill, "create or supersede a record only
when" o desenho muda, põe uma condição necessária para criar um registro; ela não obriga a criar um
toda vez que o desenho muda, e a opção 4 a respeita. A opção 3 é a que corresponde, palavra por
palavra, ao texto que você aprovou no D2: "uma ou duas regras, sem tocar no fluxo nem em quem é dono
do quê". As opções 1, 2 e 4 mudam esse texto. Na opção 4, a frase "de uma ou duas regras" sai da
linha de decisão do D2, e entra o teste do objetivo.

### D11 — As decisões sobre o fluxo precisam de um registro de arquitetura próprio?

**Estado:** decidido

**Decisão:** opção 1. As skills são a autoridade durável do fluxo, e nenhum registro de arquitetura
é criado. Cada regra nova leva o motivo numa frase dentro da própria skill, e as alternativas
rejeitadas ficam no plano concluído e neste brief. A `architecture-records` ganha uma frase dizendo
que as regras de fluxo das skills compartilhadas moram nas próprias skills. Com isso, D1 a D4 e D7
não voltam a ter a marca de registro pendente, porque o plano é o dono da sequência, e as skills
recebem as regras quando o plano for executado. Registrada no
[plano](../active/decision-to-architecture-flow.md).

**A pergunta para você:** onde fica guardado, de forma durável, o fluxo que D1 a D4 e D7 criam, da
decisão até o fechamento do plano: só no texto das três skills, também num registro de
arquitetura deste repositório, ou num arquivo de apoio dentro de uma das skills.

**O que aconteceu:** quando registrei as decisões, escrevi que o plano era "o único dono" delas
porque este repositório não tem a pasta `architecture/`. O revisor independente apontou que a falta
da pasta não decide isso, e ele tem razão. A `architecture-records` classifica pelo conteúdo: vira
registro o que guarda donos entre componentes, regras não locais, ou uma decisão duradoura com o
motivo e as alternativas rejeitadas. Ela também manda criar a pasta quando ela não existe. D1 a D4 e
D7 mudam responsabilidades e ordem entre três skills. Decidir sozinho que "isso não é arquitetura"
seria repetir a falha que originou este brief, a escolha de dono em silêncio; por isso a escolha é
sua. Retirei a frase do "único dono" do plano e deste brief.

**O que está em jogo:** a regra atual vai morar nas skills em todas as opções. A diferença é onde
mora o porquê: por que a emenda vem antes da revisão, por que quem emenda é a sessão da discussão, e
quais alternativas você rejeitou. Hoje isso está neste brief, que é documento de trabalho em
português e sem autoridade, e no plano, que é roteiro temporário.

**Como foi até agora (verificado em 2026-09-19):** este repositório não tem nenhum registro de
arquitetura. As nove decisões da revisão da `discussion-briefs`, que também mexeram em regras de
revisão e de fechamento, ficaram só nas skills e no plano concluído.

**O que é um arquivo `references/`, usado na opção 3:** uma skill é uma pasta. O arquivo `SKILL.md`
é o que o agente carrega sempre que a skill se aplica. Dentro da pasta pode existir uma subpasta
`references/`, com documentos que o agente só abre quando o `SKILL.md` manda, numa situação
específica. Quatro skills suas já usam isso (verificado em 2026-09-19): a `docker`, a `gitlab-ci`, a
`test-quality` e a `skill-creator`. Na `docker`, por exemplo, o `SKILL.md` diz "leia
`references/compose.md` antes de criar ou mudar um arquivo Compose"; quem só mexe num Dockerfile
nunca abre esse arquivo e não gasta nada com ele.

Aqui, o arquivo guardaria o porquê das regras deste brief, em inglês, porque é texto para agentes.
Para cada regra: a decisão, o motivo, as alternativas que você rejeitou e a falha que a motivou, sem
histórico de execução. Ele ficaria dentro de uma das três skills, e eu proporia a
`architecture-records`, que é a dona do assunto "como uma decisão chega ao registro". Nas três
skills entraria uma linha só, junto das regras novas: "antes de mudar estas regras, leia
`references/<arquivo>`; ele guarda os motivos e as alternativas rejeitadas, e muda junto com elas".

| Quem está trabalhando | O que ele lê |
| --- | --- |
| O agente que aplica a regra, em qualquer repositório | Só o `SKILL.md`, como hoje. A linha de aviso não se aplica a ele, e o arquivo não é aberto. |
| O agente que vai editar aquelas regras numa das skills | O `SKILL.md` e, por causa da linha de aviso, o arquivo com os motivos. |

O arquivo não manda em nada: quem manda é a regra escrita no `SKILL.md`, e ele só explica. Ele não
tem estados, índice, passada de fechamento nem cadeia de rastreabilidade, que são as obrigações de
um registro de arquitetura. E ele viaja com a skill: está disponível em qualquer repositório onde a
skill é usada, ao contrário de uma pasta `architecture/` na sua home.

**Qual opção um modelo mais fraco segue melhor:** a 1 e a 3 empatam, e a 2 é a pior.

- Modelo fraco segue o que está no texto que ele já carregou. Cada "vá ler outro arquivo" é um
  passo que ele pode pular; num dos testes com agente desta sessão, o Sonnet nem carregou a skill.
  Nas opções 1 e 3, a regra inteira está no `SKILL.md`.
- Na opção 2, a regra fica em quatro lugares, o registro e as três skills. Se os textos divergirem
  um pouco, um modelo fraco não resolve o conflito e segue o que leu por último.
- Na opção 2, o registro ficaria em `architecture/` do repositório da sua home, mas o agente que
  precisa da regra costuma estar em outro repositório, como o do Redmine. Ali o registro nem está no
  espaço de trabalho dele.
- A opção 2 cria um laço: um registro de arquitetura sobre como emendar registros de arquitetura.
  Na home, um modelo fraco poderia tratar qualquer ajuste de redação numa skill como "implementação
  governada por registro" e disparar o ciclo inteiro de plano, revisão e fechamento por uma frase.

**Opções:**

1. As skills são a autoridade durável. Cada regra nova leva o motivo numa frase dentro da própria
   skill, como as skills já fazem, e as alternativas rejeitadas ficam no plano concluído e neste
   brief. Nenhum registro é criado. Para o próximo agente não ter de decidir isto de novo, a
   `architecture-records` ganha uma frase dizendo que as regras de fluxo das skills compartilhadas
   moram nas próprias skills.
2. Criar `architecture/` neste repositório, com um registro em inglês sobre o caminho da decisão
   até o registro, e as três skills apontam para ele.
3. Igual à opção 1, e o porquê completo vai para um arquivo `references/` dentro de uma das skills,
   com uma linha de aviso nas três. A frase nova da `architecture-records` diz que as regras de
   fluxo das skills compartilhadas, e o motivo delas, moram nos próprios pacotes das skills.

**Como fica na prática:**

| O que acontece | Opção 1: só as skills | Opção 2: registro de arquitetura | Opção 3: skills e `references/` |
| --- | --- | --- | --- |
| Onde fica a regra atual | Nas três skills. | Nas três skills, em forma curta, e no registro, com o contexto. | Nas três skills. |
| Onde fica o porquê | Uma frase em cada skill; o resto no plano concluído e neste brief. | No registro, com as alternativas rejeitadas e os riscos. | Uma frase em cada skill; o resto no arquivo `references/`, em inglês. |
| O agente que aplica a regra em outro repositório | Lê a regra no `SKILL.md`. | Lê a regra curta no `SKILL.md`; o registro fica fora do alcance dele. | Lê a regra no `SKILL.md`; não abre o arquivo. |
| O que muda agora | O plano segue e ganha a frase nova da `architecture-records`. | O registro nasce primeiro, no estado proposto, e o plano é refeito a partir dele, que é a ordem do seu D3. D1 a D4 e D7 voltam a ter `registro pendente` para o registro até ele existir. | O plano segue e ganha a frase nova, o arquivo e as três linhas de aviso. |
| Arquivos novos | Nenhum. | A pasta, o índice `architecture/README.md`, o registro, e regras novas no `.gitignore` para a pasta ser rastreada. | Um arquivo, numa pasta de skill que já é rastreada. |
| No fechamento | A passada de fechamento da `plan-implementation`. | Essa, e também a passada de limpeza da `architecture-records`, que leva o registro a "implementado". | A mesma da opção 1, conferindo também o arquivo. |
| Quem mexer nas skills no futuro | Vê a regra e o motivo curto. | É obrigado pela skill a ler o registro antes de mudar a regra. | É mandado pela linha de aviso a ler o arquivo antes de mudar a regra. |

**Pontos negativos de cada opção:**

- Opção 1: o porquê completo fica espalhado entre um documento de trabalho em português e um plano
  concluído, e nada obriga quem editar as skills a lê-los. Uma edição futura pode desfazer o D3 sem
  saber que a outra ordem foi considerada e rejeitada. Pela letra das suas skills, estas decisões
  pedem registro: a `architecture-records` fala em "decisão duradoura com motivo e alternativas
  rejeitadas", e a `documentation` manda usar a `architecture-records` quando muda uma ordem de
  etapas ou uma fronteira de dono entre componentes, deixando nas instruções só a regra curta. A
  opção 1 abre uma exceção a isso, e por isso inclui a frase nova na `architecture-records`.
- Opção 2: é o primeiro registro de arquitetura de um repositório de dotfiles, e cria uma estrutura
  inteira para um registro só. A cadeia de rastreabilidade que a skill exige, da regra até os testes
  e o replay gravado, quase não se aplica a texto de skill, porque os testes com agente são
  descartáveis; várias linhas ficariam como "indisponível". A mesma regra passa a existir em quatro
  lugares e precisa de disciplina para não divergir. O registro não fica à vista do agente que
  trabalha em outro repositório, e cria o laço descrito acima. O plano atual teria de ser refeito e
  revisado de novo.
- Opção 3: o arquivo pode ficar velho, se alguém mudar a regra e esquecer dele; a linha de aviso
  manda atualizar os dois juntos, mas depende de o agente obedecer. O motivo de regras que estão em
  três skills fica guardado dentro de uma só, e as outras duas apontam para a pasta vizinha, o que
  é uma ligação entre pacotes que hoje não existe. Abre a mesma exceção da opção 1 à letra da
  `architecture-records` e da `documentation`. É mais um arquivo para manter.

**Recomendação:** opção 3. Para o agente que aplica a regra ela é igual à opção 1, que é a mais
fácil de seguir. E ela resolve o ponto fraco da opção 1: o porquê completo passa a ter um lugar
durável, em inglês, que viaja com a skill e é indicado a quem for mexer nas regras. O custo é um
arquivo curto e três linhas. Se uma frase de motivo por regra bastar para você, a opção 1 serve. Não
é uma recomendação forte contra a opção 2: a letra da `architecture-records` e da `documentation`
aponta para ela, e é por isso que a escolha ficou com você. Pelo critério da simplicidade, a opção
1 vence: não cria arquivo nem ligação entre skills, e o que se perde é só um ponteiro para o motivo
completo, que continua guardado no plano concluído e neste brief.

### D12 — E quando emendar o registro obriga a uma manutenção que a exceção do D3 não cobre?

**Estado:** decidido

**Decisão:** opção 1, recuar para a ordem comum. Quando mexer no registro obriga a uma mudança fora
dos limites da exceção do D3, como traduzir um registro que não está em inglês ou remover um
sumário manual, a exceção não vale: o agente avisa no chat, o item do brief mantém
`registro pendente` para o registro, e a manutenção e a emenda entram como passos do plano, depois
da revisão independente. A conferência por fase da `plan-implementation` ganha a ressalva "exceto o
passo que registra a decisão naquele dono". Registrada no
[plano](../active/decision-to-architecture-flow.md).

**Esclarecimento das revisões:** não faz parte do que você decidiu; é o modo como o plano aplica a
decisão. A terceira revisão mostrou que a ressalva, escrita só como "o passo", deixava duas brechas:
alguém podia ler que a conferência inteira fica dispensada, inclusive a sua instrução de registrar,
ou a tradução obrigatória continuava travada, por não ser ela o passo que registra a decisão. Por
isso o plano define a unidade liberada: a emenda do registro junto com a manutenção que a
`architecture-records` torna obrigatória para aquela edição, depois da revisão do plano. A ressalva
dispensa só a pendência que essa unidade resolve. A sua instrução de registrar continua exigida,
outras pendências e o trabalho que depende da emenda continuam passando pela conferência, e quem
faz a unidade é a sessão da discussão, como no D4.

**A pergunta para você:** no D3 você escolheu emendar o registro antes da revisão do plano. O que o
agente faz quando mexer naquele registro obriga, pelas regras da `architecture-records`, a uma
mudança maior do que o bloco de emenda.

**O que aconteceu:** a primeira revisão independente fez o plano dar limites à exceção do D3: antes
da revisão só entra o bloco rotulado, ou o registro novo proposto com a linha de aviso e a entrada
no índice, e nenhum outro texto do registro muda. A segunda revisão mostrou que esses limites batem
de frente com duas obrigações que a `architecture-records` já tem (conferido em 2026-09-19):

- Se o registro não está em inglês, ou mistura idiomas, a skill manda traduzir o arquivo inteiro e
  o índice na mesma mudança em que alguém mexe nele.
- Se o registro tem um sumário manual, a skill manda removê-lo quando o registro é editado.

Nos dois casos, para pôr um bloco de três linhas, o agente teria de reescrever o arquivo inteiro
antes da revisão, o que os limites proíbem. Para o plano não ficar sem saída, escrevi nele um
comportamento: a exceção não vale, o agente avisa, e a emenda fica para depois da revisão do plano.
Isso é uma escolha entre alternativas, e você não a fez. Por isso virou este item, e a execução do
plano espera por ele.

**Exemplo:** o registro do Redmine está em português. Você decide remover o `redmine_native` e manda
registrar. Para emendar, o agente tem de traduzir o registro todo para o inglês. Uma tradução pode
mudar sem querer o sentido de uma regra, e nesse momento nenhuma revisão olhou para ela.

**Opções:**

1. Recuar para a ordem comum. A exceção não vale naquele caso: o agente avisa no chat, deixa o item
   do brief com `registro pendente` para o registro, e a tradução ou limpeza e a emenda entram como
   passos do plano, depois da revisão independente. Na skill isso é uma frase, junto dos limites
   da exceção, com os dois exemplos dentro dela para um modelo mais fraco reconhecer o caso. Entra
   também uma ressalva na conferência que a `plan-implementation` faz antes de cada fase. Essa
   conferência não deixa começar uma fase afetada por uma decisão enquanto algum dono não a
   recebeu; no recuo, o passo que emenda o registro é justamente o que entrega a decisão a esse
   dono, e sem a ressalva "exceto o passo que registra a decisão naquele dono" ele ficaria
   bloqueado por ela.
2. Manutenção primeiro, como trabalho separado. O agente faz a tradução ou a limpeza sozinha, sem
   mudar regra nenhuma, e só depois aplica a emenda antes da revisão, como o D3 manda.
3. Perguntar a você caso a caso, mostrando o tamanho da manutenção.

**Como fica na prática:**

| O que acontece | Opção 1: recuar | Opção 2: manutenção primeiro | Opção 3: perguntar |
| --- | --- | --- | --- |
| Registro em português, decisão pequena | A emenda espera a revisão; o brief fica aberto com `registro pendente` para o registro. | O registro é traduzido inteiro antes da revisão, e depois recebe o bloco. | O agente para e pergunta. |
| Registro com sumário manual | Igual: espera a revisão. | O sumário sai, e depois entra o bloco. | O agente para e pergunta. |
| Registro em inglês e sem sumário, o caso comum | Não muda nada: emenda primeiro, como no D3. | Igual. | Igual. |
| Texto novo nas skills | Uma frase, e uma ressalva de uma oração na conferência por fase. | Um procedimento a mais: o que conta como manutenção, e como garantir que ela não mudou regra. | Uma frase. |

**Pontos negativos de cada opção:**

- Opção 1: nesses casos volta o problema que o D3 queria evitar, porque a decisão fica um tempo sem
  morar no dono dela. O D1 torna isso visível, já que o item mantém `registro pendente` e o brief
  não fecha, mas o brief fica aberto por mais tempo. Depende da ressalva na conferência por fase;
  sem ela, o passo que emenda o registro ficaria travado.
- Opção 2: uma tradução inteira de um registro com regras é uma mudança grande feita antes de
  qualquer revisão, e é justamente onde um sentido pode mudar sem ninguém ver. Precisa de regra
  para separar manutenção de mudança de conteúdo, e a skill fica mais complicada.
- Opção 3: é mais uma pergunta para você numa hora em que você só mandou registrar, e a resposta
  tende a ser sempre a mesma.

**Recomendação:** opção 1. O caso é raro, porque os registros novos já nascem em inglês e sem
sumário; a regra cabe numa frase; e ela não faz nenhuma mudança grande passar antes da revisão. É a
mais simples, que é o critério que você usou no D10 e no D11.

### D13 — Quais conferências da `architecture-records` valem na hora de passar o plano para outra sessão?

**Estado:** decidido

**Decisão:** opção 1, separar os dois momentos numa frase no começo da seção 11 da
`architecture-records`. Quando a sessão da discussão passa o registro emendado e o plano para quem
vai implementar, valem só as conferências sobre a forma do registro. As conferências sobre
implementação concluída valem quando a implementação fecha. Registrada no
[plano](../active/decision-to-architecture-flow.md).

**Esclarecimento das revisões:** a revisão independente do replanejamento achou que o plano tinha
escrito o D13 como se cada conferência valesse em um momento só. Não é isso que este item diz: no
fechamento da implementação valem todas as conferências, como hoje, e as de forma valem também na
passagem do planejamento. A lista do plano também estava incompleta. Ficaram classificadas como de
forma, além das que este item cita: nada de diário em nenhum ponto do registro, a inspeção de
arquivos não rastreados e de diffs, o relato do que mudou e o limite de autorização do Git. Ficaram
como de fechamento, além das citadas: nenhum caminho antigo concorrendo com o atual, estados finais
consistentes, os rastros nos dois sentidos e a retirada dos blocos de emenda e dos avisos cuja
implementação fechou. Para nenhuma conferência ficar de fora por esquecimento, a frase da skill vai
nomear só as que esperam o fechamento; toda conferência que ela não nomear vale nos dois momentos.

**A pergunta para você:** pelo D4, a sessão da discussão emenda o registro e só então passa o
trabalho para a sessão que implementa. A `architecture-records` tem uma lista de conferências
"antes do handoff". Falta dizer quais delas valem nessa passagem, que acontece antes de existir
qualquer implementação.

**O que aconteceu:** a segunda passada independente do fechamento, feita pelo Sol em 2026-09-19,
achou uma colisão dentro da própria skill (conferi o texto, e ela existe). A seção 7a, nova, diz que
a sessão da discussão faz a emenda "before handing the work to another session". A seção 11, que já
existia, começa com "Before handoff:" e exige, entre outras coisas, que a matriz de fechamento do
plano não tenha nada pendente e que a segunda passada de conformidade já tenha sido feita. Essas
duas coisas só existem depois da implementação. Lidas juntas ao pé da letra, a sessão da discussão
nunca poderia passar o trabalho adiante. A skill diz que todo "must" e "never" dela é uma trava de
entrega, e o plano diz que a exceção do D3 não dispensa nenhuma outra obrigação da skill. Por isso
escolher quais conferências valem em cada momento não é algo para eu resolver sozinho.

**Exemplo:** você decide remover o `redmine_native`, e o agente emenda o registro e escreve o plano.
Na hora de entregar para a sessão do Opus implementar, ele lê "antes do handoff, confirme que a
segunda passada de conformidade foi concluída". Nada foi implementado ainda, então não há passada
nenhuma para confirmar. Um agente cuidadoso trava; um descuidado pula a lista inteira.

**Opções:**

1. Separar os dois momentos numa frase no começo da seção 11. Na passagem do registro emendado e do
   plano para quem vai implementar, valem só as conferências sobre a forma do registro: estado
   explícito, índice com link para cada registro, comportamento proposto não descrito como atual,
   o bloco de emenda correto, links válidos, nada de sumário manual e checagem de espaços. As
   conferências sobre implementação concluída, que são rastreabilidade até o código, replay, matriz
   de fechamento sem pendência e segunda passada, valem quando a implementação fecha.
2. Mexer só na redação do D4, trocando "handing the work" por outra expressão, sem tocar na seção
   11.

**Como fica na prática:**

| O que acontece | Opção 1: separar os momentos | Opção 2: só trocar a palavra |
| --- | --- | --- |
| Sessão da discussão passa o plano adiante | Confere a forma do registro e entrega. | Entrega, mas a lista "antes do handoff" continua lá, sem dizer se vale. |
| Fechamento da implementação | Todas as conferências valem, como hoje. | Igual. |
| Um registro proposto comum, fora deste fluxo | A mesma frase resolve a dúvida, que já existia antes. | A dúvida continua. |
| Texto novo na skill | Uma frase na seção 11. | Uma palavra na seção 7a. |

**Pontos negativos de cada opção:**

- Opção 1: mexe numa seção de travas da skill, e a lista de quais conferências são "de forma"
  precisa ficar certa; uma conferência posta do lado errado deixaria de ser cobrada na passagem.
- Opção 2: não resolve a colisão, só a esconde; o próximo revisor acha de novo, e um agente pode
  tanto travar quanto pular a lista inteira.

**Recomendação:** opção 1. É uma frase, resolve também a dúvida que já existia para registros
propostos, e não dispensa nenhuma conferência: só diz quando cada uma vale.

### D14 — O teste do D6 fica aceito como está, ou você autoriza rodadas novas?

**Estado:** decidido

**Decisão:** opção 4. Você autoriza três rodadas novas do teste com agente independente, uma para
cada caminho: o caso pequeno de novo, limpo; a variante grande do D2; e o recuo do D12, com um
registro em português. O D13 entra na skill antes das rodadas. Se uma rodada falhar por defeito de
skill, eu corrijo e a rodada daquele caso recomeça. Registrada no
[plano](../active/decision-to-architecture-flow.md).

**Esclarecimentos das revisões:** a revisão independente do replanejamento apertou os critérios das
três rodadas, sem mudar o que você autorizou. No caso grande, o registro novo precisa trazer a sua
decisão correta nas regras, no fluxo e no dono da conferência, e o plano precisa receber a decisão;
antes, um registro com rótulos e links certos e a regra antiga dentro passaria. No caso pequeno, a
resposta precisa mostrar a lista dos lugares que a decisão muda e a forma escolhida, que o D10
exige. No recuo, o índice da pasta de arquitetura também fica em português, nada nessa pasta pode
mudar, e o plano precisa ganhar, depois da revisão, os passos de tradução do registro e do índice e
o da emenda. O plano prevê resultados defeituosos feitos à mão para os casos que ele lista, e o
juiz tem de reprovar cada um antes das rodadas; nem todo critério novo tem um, e a lista do D10 na
resposta do caso pequeno, por exemplo, eu confiro lendo. As duas rodadas antigas do D6 deixam de
aparecer no plano como "passaram": ficam anotadas critério por critério, com os dois limites
descritos abaixo.

**A pergunta para você:** as duas rodadas do teste acertaram o que tinha falhado no outro chat, mas
a segunda passada independente achou dois limites que eu não tinha visto. Você decide se isso basta
ou se quer rodadas novas, que o D6 não autorizou.

**O que as duas rodadas fizeram certo (conferido por mim e pelo Sol):** só o registro, o plano e o
brief mudaram; o registro ganhou exatamente um bloco, com o rótulo, embaixo da regra certa, dizendo
que a regra continua valendo; o brief ficou com os links para os dois donos e sem a marca
`registro pendente`; a resposta separou "registrado" de "implementado" e disse que a revisão do
plano vem antes do código; o código e o diretório do Git não mudaram; e as transcrições não
mostram nenhum comando de Git que mude estado.

**Os dois limites:**

- Na primeira rodada, depois de fazer as edições, o agente consultou o advisor dele, embora o
  pedido dissesse para trabalhar sozinho. Os arquivos não foram afetados, porque a consulta veio
  depois, mas não dá para saber quanto a resposta final foi influenciada: o conteúdo da consulta
  fica cifrado na transcrição. O meu juiz não olhava esse tipo de chamada; já corrigi o juiz, e ele
  agora reprova a primeira rodada nesse ponto.
- Na segunda rodada, o agente atualizou o passo do plano com o que você decidiu, mas não escreveu no
  plano que a revisão vem antes do código; disse isso só na resposta. O critério que eu tinha
  escrito, "o plano carrega a sequência", é ambíguo. O seu D6 diz "ele anota a sequência de execução
  no plano", e nessa leitura as duas rodadas passam. O Sol leu o critério junto com o D3, como "a
  ordem revisão e depois código está no plano", e nessa leitura só a primeira passa. O plano do
  repositório de teste também ajudou nisso: eu o montei sem o passo de revisão que todo plano de
  verdade tem.

**Opções:**

1. Aceitar como está, com os limites anotados no plano. Vale a leitura do seu D6 para o critério do
   plano, e a consulta ao advisor fica registrada como desvio da primeira rodada.
2. Autorizar duas rodadas novas, com as mesmas skills, o repositório de teste com o passo de
   revisão no plano, o pedido proibindo também o advisor, e o critério do plano escrito sem
   ambiguidade.
3. Antes, reforçar a skill para o agente escrever a ordem "revisão antes do código" no plano quando
   ele não a tiver, e depois rodar duas rodadas novas.
4. Autorizar três rodadas, uma para cada caminho: o caso pequeno de novo, limpo, com o passo de
   revisão no plano do repositório de teste e o advisor proibido no pedido; a variante grande do D2,
   em que o esperado é um registro novo no estado proposto, com a linha de aviso, sem marcar o
   antigo como substituído; e o recuo do D12, com um registro em português, em que o esperado é o
   agente não emendar, avisar e manter `registro pendente` para o registro. O D13 entra na skill
   antes das rodadas, para a evidência não ficar anterior a uma mudança de skill.

**O que acontece em cada resposta:**

| O que acontece | Opção 1: aceitar | Opção 2: duas rodadas novas | Opção 3: reforçar e rodar | Opção 4: três caminhos |
| --- | --- | --- | --- | --- |
| Custo | Nenhum. | Cerca de 250 mil tokens e dez minutos (estimativa pelas rodadas já feitas). | O mesmo, mais uma mudança de skill, que pede nova validação e nova conferência. | Cerca de 400 mil tokens e quinze minutos (estimativa), mais a montagem de dois repositórios de teste novos. |
| Evidência que fica | Uma rodada completa com desvio de advisor e uma com o plano na leitura fraca; a falha do outro chat não apareceu em nenhuma. | Duas rodadas limpas, ou a descoberta de que o limite se repete. | Igual à opção 2, para um texto de skill mais exigente. | O caso pequeno limpo, e a primeira evidência de comportamento da variante grande, da escolha do D10 e do recuo do D12, que hoje só foram lidos. |
| Risco | A matriz de fechamento fica com os limites escritos, e um revisor pode continuar achando pouco. | Um modelo pode consultar o advisor mesmo proibido; aí o limite fica confirmado, não removido. | Aumenta o texto da skill por causa de um detalhe do repositório de teste. | O mesmo risco do advisor. Uma rodada pode falhar por defeito de skill; aí eu corrijo e a rodada daquele caso recomeça, o que aumenta o custo. |

**Pontos negativos de cada opção:**

- Opção 1: a evidência fica menos limpa do que o critério pedia, e isso fica escrito para sempre no
  plano concluído.
- Opção 2: gasta tokens para melhorar a evidência de algo que já se comportou bem nas duas vezes.
- Opção 3: muda a skill por causa de um plano de teste mal montado; num plano de verdade, o passo de
  revisão já existe, porque a `plan-implementation` o exige como primeiro passo.
- Opção 4: é a mais cara. Uma rodada por caminho é pouca evidência para cada um, e uma falha pode
  abrir correções de skill e mais uma volta de fechamento. Cada caso novo precisa de um juiz
  próprio, feito por mim, que também pode ter buracos, como o primeiro teve.

**Recomendação:** opção 4. O caso pequeno já se comportou bem duas vezes, e repeti-lo ensina pouco.
Os caminhos que nunca rodaram são justamente onde um modelo mais fraco tende a errar: na revisão
anterior, o Sonnet substituiu um registro aprovado na hora, que é o erro que a variante grande
procura, e um registro em português convida a traduzir tudo ou a pendurar um bloco em inglês. Se o
custo pesar, a opção 1 continua defensável, porque a falha do outro chat não apareceu em nenhuma
das duas rodadas; a opção 2 é a que menos vale o que custa, e a opção 3 eu não faria.

### D15 — A segunda rodada do caso grande consultou o advisor proibido: a evidência basta ou rodo mais uma?

**Estado:** decidido

**Decisão:** opção 2. Você autoriza mais uma rodada do caso grande, com a proibição do advisor
escrita no pedido da forma mais forte. Se o agente consultar o advisor de novo, vale a opção 1 e
eu não rodo mais nada. Registrada no [plano](../active/decision-to-architecture-flow.md).

**A pergunta para você:** das três rodadas que você autorizou no D14, duas passaram limpas. A do
caso grande acertou o conteúdo, mas o agente consultou o advisor dele, que o pedido proibia. O D14
só prevê rodada nova quando a falha é defeito de skill, e esta não é. Você decide se a evidência
que sobrou basta ou se autoriza mais uma rodada desse caso.

**Por que o advisor era proibido:** o teste existe para responder uma pergunta só: um modelo mais
fraco, lendo apenas o texto das skills, faz a coisa certa sozinho? O advisor é um modelo mais forte
que enxerga a conversa inteira do agente e devolve conselhos. Se o agente o consulta, o resultado
passa a mostrar o que o Sonnet faz com a ajuda de um modelo mais forte, e não o que o texto da
skill consegue sozinho. Três coisas pioram isso:

- O conselho fica cifrado na transcrição. Eu vejo que a consulta aconteceu e o que o agente editou
  depois, mas não o que foi sugerido, então não dá para separar o que veio do Sonnet do que veio do
  advisor. Na segunda rodada do caso grande, foram cinco edições depois da consulta.
- As skills são compartilhadas com o Codex e o Copilot, e nem toda sessão tem advisor. O texto
  precisa funcionar sem ele.
- Foi exatamente isso que o Sol apontou ao reprovar o fechamento: a primeira rodada do D6 tinha
  consultado o advisor, e eu tinha contado a rodada como aprovada. Por isso a opção 4 do D14, que
  você escolheu, já dizia "o advisor proibido no pedido".

A proibição vale só dentro do teste. No trabalho de verdade o agente pode e deve consultar o
advisor, como eu mesmo faço nesta sessão. O agente do teste desobedeceu porque o programa em que
ele roda traz uma instrução fixa mandando consultar o advisor antes de dar o trabalho por pronto, e
essa instrução pesou mais que o meu pedido. No recuo do D12 eu escrevi a proibição em uma linha
separada, dizendo que ela vale também no fim do trabalho e passa por cima dessa instrução fixa, e o
agente obedeceu.

**O que aconteceu:**

- **Caso pequeno:** passou em tudo. O agente não abriu advisor, revisor nem subagente. Um limite:
  a resposta diz que o bloco foi para a regra 3, mas não explica por que escolheu o bloco.
- **Recuo do D12 (registro em português):** passou em tudo. O agente não tocou na pasta de
  arquitetura, pôs no plano a tradução do registro e do índice e depois a emenda, tudo depois da
  revisão, manteve `registro pendente` para o registro com o motivo e não concluiu o brief.
- **Caso grande, primeira rodada:** falhou na leitura, por uma lacuna da skill. O registro novo se
  declarou substituto só de uma parte do antigo e disse que as regras da fila de reprocessamento
  continuavam valendo no registro antigo. A `architecture-records` não dizia que o registro novo
  substitui o antigo inteiro. Acrescentei essa frase, com o motivo, e rodei o caso de novo, como o
  D14 prevê.
- **Caso grande, segunda rodada:** com a frase nova, o agente escreveu certo: registro novo no
  estado proposto, dizendo que substitui o antigo quando for implementado, com as regras que não
  mudam copiadas, a entrada no índice, um aviso só no registro antigo, e o plano e o brief
  atualizados. Aí, já com tudo pronto, ele consultou o advisor e fez mais cinco ajustes no registro
  novo e no índice. O conteúdo da consulta fica cifrado na transcrição.

**O que eu consegui recuperar:** a transcrição guarda cada edição que o agente fez, na ordem.
Refiz os arquivos exatamente como estavam antes da consulta ao advisor, e o juiz aprova esse
estado em todas as conferências de arquivo; li o registro novo e ele está correto. O que não dá
para recuperar é a resposta final sem influência do advisor, porque ela foi escrita depois. A
resposta do caso grande sem advisor só existe na primeira rodada, e lá ela cumpriu o que se pedia:
mostrou a lista dos lugares que a decisão muda, a forma escolhida com o motivo, e separou
"registrado" de "implementado".

**Opções:**

1. Aceitar a evidência como está: os arquivos de antes da consulta valem para o registro, o plano e
   o brief, a resposta da primeira rodada vale para a resposta, e a consulta proibida fica anotada
   no plano como desvio.
2. Autorizar mais uma rodada do caso grande, com a proibição do advisor escrita no pedido da forma
   mais forte que usei no recuo do D12, onde funcionou. Se o agente consultar o advisor de novo,
   vale a opção 1 e não rodo mais nada.

**Como fica na prática:**

| O que acontece | Opção 1: aceitar | Opção 2: mais uma rodada |
| --- | --- | --- |
| Custo | Nenhum. | Cerca de 150 mil tokens e sete minutos (pelas rodadas já feitas). |
| Evidência do caso grande | Arquivos de uma rodada e resposta de outra, com o desvio anotado. | Uma rodada inteira limpa, ou a confirmação de que o Sonnet consulta o advisor mesmo proibido. |
| Fechamento do plano | Sigo direto para a conferência de fechamento e a passada do Sol. | O mesmo, depois da rodada. |
| Risco com o Sol | Ele pode reprovar de novo, porque o critério diz que qualquer desvio reprova a rodada. | Menor, se a rodada sair limpa. |

**Pontos negativos de cada opção:**

- Opção 1: a evidência do caso grande fica montada de dois pedaços, e o plano registra uma rodada
  reprovada como prova. Foi exatamente evidência fraca que reprovou o fechamento da primeira vez.
- Opção 2: gasta tokens, e a rodada pode consultar o advisor de novo; a proibição mais forte
  funcionou uma vez só, então não há garantia.

**Recomendação:** opção 2. É barata perto do que já foi gasto, e dá a chance de fechar o caso
grande com uma rodada inteira limpa. O limite fica combinado de antemão: se o advisor aparecer de
novo, fico com a opção 1 e sigo para o fechamento.

### D16 — A rodada nova não mostrou na conversa a lista dos lugares que a decisão muda: corrijo ou aceito?

**Estado:** decidido

**Decisão:** opção 2. A `discussion-briefs` ganha uma frase, no parágrafo da promoção, mandando a
resposta trazer a lista e a forma que a `architecture-records` pede, e o caso grande roda mais uma
vez, uma rodada só. Se a lista ainda não aparecer, vale a opção 1 e eu não rodo mais nada; a frase
fica na skill mesmo assim. Registrada no [plano](../active/decision-to-architecture-flow.md).

**A pergunta para você:** a rodada que você autorizou no D15 saiu sem advisor e acertou todos os
arquivos. Falhou em uma coisa só, na leitura: a resposta ao usuário não mostrou a lista dos lugares
do registro que a decisão muda. Você decide se isso vira mais uma frase numa skill, com mais uma
rodada, ou se fica anotado como limite e o plano segue para o fechamento.

**O que é essa lista:** é uma frase na resposta, não um bloco. Pelo D10, antes de escolher entre o
bloco de emenda e o registro novo, o agente enumera os lugares do registro que a decisão obriga a
mudar, só pelos nomes (regras, seção de fluxo, diagramas, tabelas), e diz na conversa essa lista
junto com a forma que escolheu. No caso pequeno ficaria "muda só a regra 3, então usei o bloco de
emenda". No caso grande, a primeira rodada escreveu "a mudança era grande demais (fluxo, dono da
conferência e vários invariantes) para caber num bloco de emenda, então usei registro novo". Ela
existe para você conferir a escolha na hora. Sem ela, você lê "criei um registro novo" e não tem
como saber se um bloco bastava.

**O que aconteceu:** na rodada nova, a resposta disse que criou um registro novo no estado
proposto, que ele substitui o antigo quando for implementado, que o antigo ganhou o aviso e que a
revisão do plano vem antes do código. A lista ("muda o fluxo, o dono da conferência e três das cinco
regras") apareceu só nas notas internas da sessão, que você não veria. Juntando todas as rodadas:

| Rodada | A resposta mostrou a lista com a forma? |
| --- | --- |
| D6, primeira rodada | Sim, mas essa rodada consultou o advisor antes de responder. |
| D6, segunda rodada | Só disse qual regra mudou. |
| Caso pequeno do D14 | Disse o único lugar (regra 3) e a forma (bloco), sem o motivo. |
| Caso grande, primeira rodada | Sim: lista, forma e motivo. |
| Caso grande, segunda rodada | Sim, mas a resposta foi escrita depois da consulta ao advisor. |
| Caso grande, rodada do D15 | Não: só a forma. |
| Caso grande, rodada do D16, já com a frase nova | Sim: lista, forma e motivo. |

**Por que eu acho que acontece:** a ordem de mostrar a lista está na `architecture-records`, na
parte que ensina a escolher a forma. Só que a resposta ao usuário é montada seguindo a
`discussion-briefs`, que tem a sua própria relação do que a mensagem da conversa traz (link do
brief, quantos itens abertos, o que mudou) e não cita a lista. O Sonnet segue a relação que está
mais perto e esquece a outra. É uma hipótese; só uma rodada depois da correção mostra se é isso.
Há uma segunda candidata, que é o próprio teste: o meu pedido manda o agente entregar a resposta ao
usuário e, separado, notas da sessão, e foi nas notas que a lista caiu. A primeira rodada do caso
grande pôs a lista na resposta com o mesmo pedido, então o pedido não impede, mas pode puxar a
análise para as notas. Uma rodada nova não separa bem essas duas causas.

**Opções:**

1. Aceitar como limite. O plano anota que o Sonnet mostra a lista de forma irregular, o D10 fica
   como verificado por leitura do texto e só em parte pelas rodadas, e eu sigo para o fechamento e
   a passada do Sol.
2. Acrescentar uma frase na `discussion-briefs`, no parágrafo da promoção, mandando a resposta
   trazer a lista e a forma que a `architecture-records` pede, e rodar o caso grande mais uma vez.
   Se a lista ainda não aparecer, vale a opção 1 e não rodo mais nada. A frase fica na skill mesmo
   assim, porque ela só aponta para uma regra que a `architecture-records` já tem; a rodada testa
   se o Sonnet passa a segui-la, e não se a regra está certa.

**Como fica na prática:**

| O que acontece | Opção 1: aceitar como limite | Opção 2: uma frase e uma rodada |
| --- | --- | --- |
| Custo | Nenhum. | Cerca de 150 mil tokens e sete minutos, mais a validação da skill. |
| No uso de verdade | Em parte das vezes você lê "criei um registro novo" sem a lista, e tem de perguntar por quê. | A resposta tende a trazer a lista sempre; a rodada mostra se a frase resolve. |
| Texto das skills | Não muda. | A `discussion-briefs` ganha uma frase que aponta para uma regra da `architecture-records`. |
| Fechamento do plano | Sigo agora. A linha do D15 na matriz fica como "falhou em um critério, aceito por você". | Sigo depois da rodada. |
| Risco com o Sol | Ele pode reprovar, porque o critério diz que qualquer falha reprova a rodada; a sua decisão escrita é o que sustenta o aceite. | Menor, se a rodada sair limpa. |

**Pontos negativos de cada opção:**

- Opção 1: o D10 nasceu justamente para você poder conferir a escolha da forma, e é essa parte que
  fica funcionando só às vezes com modelos mais fracos.
- Opção 2: é a segunda frase de skill que sai destas rodadas, e a mesma instrução passa a aparecer
  em duas skills (uma manda, a outra lembra), o que é mais um ponto para manter igual no futuro.
  Também não há garantia de que a rodada saia limpa: cada rodada até aqui achou alguma coisa.

**Recomendação:** opção 2, com o limite já combinado de uma rodada só. A falha é pequena, mas cai
exatamente no que o D10 promete a você, e a correção é uma frase. Se você estiver cansado do ciclo
de rodadas, a opção 1 é defensável: os arquivos saíram certos em todas as rodadas sem advisor, e a
lista é uma cortesia da resposta, não uma trava.

### D17 — A rodada feita antes da revisão pode contar como evidência de fechamento?

**Estado:** decidido

**Decisão:** opção 3. Adiar a escolha sobre aceitar a evidência da `run-large-4` até receber o
parecer do Sol em D19. Registrada no
[plano](../active/decision-to-architecture-flow.md#governing-decisions-and-invariants).

**Situação atual:** o parecer foi recebido em 2026-09-21, com veredito não pronto. O adiamento
escolhido não aceitava nem rejeitava a evidência. Depois do parecer, você escolheu D20.2: conservar
a rodada antiga como histórico e não usá-la para fechar a obrigação de D16. As duas decisões
estão registradas no plano.

**O que é:** a `run-large-4`, autorizada no D16, produziu o registro novo, o plano e o brief de
teste e mostrou na resposta a lista de lugares alterados. A auditoria leu esses resultados e não
apontou falta na lista. Porém, a frase da skill e a rodada foram feitas antes da revisão
independente que a continuação do plano exigia. Esse é o B3: houve uma falha real de ordem, e uma
revisão feita agora não pode transformar aquela revisão ausente em revisão prévia.

**Por que importa:** este item tratava de decidir se os resultados observados poderiam contribuir
para fechar o caso grande apesar desse desvio; D20.2 resolveu essa escolha. Por exemplo, a resposta
guardada prova que a lista apareceu
naquela execução; ela não prova que a skill passou pela revisão exigida nem que um agente seguirá
a proposta nova de B1. O autor pode separar esses fatos, mas não aceitar a lacuna por você. A
obrigação de evidência de D16 depende da nova rodada autorizada em D18, conforme a escolha D20.2,
e não se considera satisfeita antes de avaliar seu resultado.

**Opções:**

1. Aceitar o resultado como evidência comportamental limitada, depois da revisão independente do
   texto atual e do replanejamento e da correção/reavaliação do B2. O plano mantém escrito que a
   revisão prévia faltou; nenhuma revisão obrigatória futura é dispensada. Aproveita o material
   já pago, mas o revisor ainda pode apontar cobertura insuficiente para alguma obrigação.
2. Não aceitar essa rodada como evidência para fechar D16. Os arquivos e a falha de processo
   continuam preservados como histórico. A obrigação fica sem evidência aceita, e uma alternativa
   depende do que você decidir em D18; rejeitar não autoriza automaticamente outra rodada.
3. Adiar a escolha até receber o parecer do Sol em D19. O revisor avalia a utilidade e os limites
   do material, sem decidir por você; até sua resposta, a aceitação continua pendente.

**Custo e risco:** aceitar não gasta tokens de uma execução nova, mas conserva a limitação de
processo e pode não bastar para o fechamento. Rejeitar pode exigir outra fonte de evidência e
prolongar o trabalho. Adiar evita decidir antes do parecer, mas mantém a pendência. Em qualquer
opção, a revisão ausente continua registrada e a auditoria de fechamento ainda é obrigatória.

**Recomendação:** opção 3, decidir depois do parecer do Sol. O replanejamento agora delimita o que
os arquivos provam e o que não provam; a revisão deve conferir essa separação antes de você
escolher.
Isso não é uma decisão tomada por você nem uma aceitação provisória da rodada.

### D20 — Depois do parecer do Sol, aproveitar a evidência limitada da rodada antiga?

**Estado:** decidido

**Decisão:** opção 2. Não usar a `run-large-4` como evidência para fechar a obrigação de D16.
Preservar seus arquivos e observações como histórico e avaliar a evidência da nova rodada
autorizada em D18, quando ela puder acontecer. Se a nova rodada não bastar, a obrigação continua
aberta, sem repetição nem enfraquecimento automático do critério. Registrada no
[plano](../active/decision-to-architecture-flow.md#governing-decisions-and-invariants).

**O que é:** você escolheu em D17 esperar o parecer antes de aceitar ou rejeitar a `run-large-4`.
O parecer chegou e distingue duas coisas. A rodada mostrou promoção da decisão, forma do registro
e lista na resposta. Porém, não comprova um plano executável e seguro: o plano de teste remove a
proteção do consumidor antes de criar ou localizar o roteador e depende de uma premissa ainda não
estabelecida. A revisão independente que deveria preceder a frase D16 e a rodada também faltou.

**Por que importa:** decidir o que essa evidência pode sustentar é uma escolha sua. D18 autoriza
uma execução nova sob condições, mas não aceita a antiga nem garante o resultado da futura. Esta
escolha afeta a evidência de B3 no fechamento; não impede corrigir B1/B2 depois da revisão exigida.

**Opções:**

1. Aceitar a rodada antiga somente como evidência limitada de promoção, forma e lista na resposta,
   com o desvio de revisão prévia e os problemas do plano de teste explícitos. Ela não demonstra
   qualidade integral do plano nem comportamento da redação nova de B1. A revisão, a correção B2,
   as validações aplicáveis e os requisitos da rodada D18 continuam obrigatórios.
2. Não usar a rodada antiga como evidência para fechar a obrigação de D16. Preservar todos os
   arquivos e observações como histórico e avaliar a evidência da rodada nova autorizada em D18,
   quando ela puder acontecer. Se a nova rodada não bastar, a obrigação continua aberta; não há
   repetição nem enfraquecimento automático do critério.

**Custo e risco:** a primeira opção aproveita evidência existente, mas exige limitar cada conclusão
para não apresentar um plano defeituoso como seguro. A segunda evita essa dependência no aceite,
mas deixa a comprovação aguardando a rodada nova, que pode falhar. Nenhuma opção muda o custo ou
amplia a autorização D18, e nenhuma reconstitui a revisão prévia que não ocorreu.

**Recomendação:** opção 2, por ser a alternativa mais conservadora para o fechamento. A rodada
antiga permanece como histórico, e a comprovação depende da nova rodada, após a revisão e as
correções aprovadas. Como D18 já autoriza essa execução, esta escolha não acrescenta outra rodada
nem muda o custo previsto. O resultado novo ainda precisa satisfazer os critérios; esta
recomendação não registra uma decisão em seu nome.

### D23 — Como seguir com o Terra depois da mudança nas instruções compartilhadas

**Estado:** decidido pela autorização de execução ampliada em D24

**Decisão:** preservar as instruções atuais e estabelecer uma nova base documentada para o
próximo lote, sem reverter o trabalho concorrente nem fingir igualdade com a rodada Sonnet high.
A instrução para executar os testes necessários autoriza também esse preparo. Registrada no
[plano](../active/decision-to-architecture-flow.md#current-authorization-and-next-validation-batch).

**O que é:** o Terra deveria receber as mesmas instruções compartilhadas congeladas antes do
Sonnet. Na conferência de 21/09/2026, `.codex/AGENTS.md` e a skill Docker mudaram enquanto eu
avaliava a resposta. O delta amplia a orientação para escolher comandos de execução com Docker
e seu gatilho no registro global. Não mexe diretamente nas três skills sob teste, mas o arquivo
global faz parte da entrada congelada e sua mudança precisa ficar explícita.

**Por que importa:** atualizar o hash sem registrar a diferença faria duas entradas distintas
parecerem idênticas. Reverter esses arquivos para recuperar o hash apagaria trabalho alheio e
não está autorizado. O Sonnet já terminou; sua tentativa high e suas falhas ficam preservadas
em qualquer opção. Uma nova rodada Sonnet não está incluída nesta escolha.

**Opções:**

1. **Replanejar a base do Terra com as instruções atuais.** Preservar o trabalho concorrente,
   conferir o delta após sua estabilização, registrar que as entradas globais diferem entre as
   rodadas e submeter a alteração do contrato à revisão herdada antes de executar o único Terra
   já autorizado. Manter a fixture original, o pedido, as skills testadas e os critérios; não
   fornecer ao Terra a resposta nem as falhas do Sonnet. Custa a conferência e a revisão do
   delta, sem consumir outra tentativa, e limita a comparação entre clientes.
2. **Adiar o Terra.** Preservar o pacote e a tentativa ainda disponível. Não há gasto de modelo
   agora, mas D22 e o fechamento continuam pendentes. Uma retomada ainda precisará resolver
   a diferença de instruções; o adiamento sozinho não recupera a entrada antiga.

**Recomendação:** opção 1. A mudança observada é de outro assunto, então vale preservá-la e
avaliar explicitamente seu efeito sobre o experimento. Isso não aceita a tentativa Sonnet como
aprovada e não altera os critérios para acomodar suas falhas.

**O que bloqueia:** lançar o Terra com uma base diferente da previamente congelada. A condição
vem do [contrato D22 no plano](../active/decision-to-architecture-flow.md#d22-one-complementary-terra-xhigh-run-in-codex).
Essa escolha está registrada por meio da instrução de execução D24; a revisão do ajuste e a
conferência das fontes precedem o novo lote.

### D24 — Executar quantos testes forem necessários para concluir a validação

**Estado:** decidido e registrado

**Decisão:** você autorizou executar Sonnet, Terra e outros testes de modelo necessários, em
quantidade suficiente para concluir a validação, e pediu o próximo passo, prompt ou instrução.
Isso substitui os limites anteriores de uma única tentativa. A autorização inclui preparar a
base atual e executar os testes; não exige outra rodada de confirmação só para registrar essa
mesma ordem. Registrada no
[plano](../active/decision-to-architecture-flow.md#current-authorization-and-next-validation-batch).

**Como será executado:** primeiro Terra xhigh e depois Sonnet 5/xhigh, sequencialmente, com
fixtures novas e a mesma base dentro do lote. Eu inicio o Terra aqui. Para o Sonnet, preparo a
sessão isolada e o prompt; uma execução local só substitui a abertura manual se suas opções e
captura puderem ser verificadas. Nenhuma configuração global será alterada.

**Limites preservados:** cada rodada deve responder a uma hipótese, verificar outra configuração
ou conferir uma correção revisada. Os critérios, os limites de Git, a proibição de auxiliares
dentro dos testes e a revisão independente continuam valendo. Falhas ficam guardadas; o resultado
de um modelo não transforma a falha de outro em aprovação. A autorização não permite enfraquecer
um teste para fazê-lo passar nem gastar repetidamente sem obter informação nova.

## Trabalho que posso fazer com sua autorização

Esta seção reúne tarefas que eu sei fazer e que não pedem uma escolha entre desenhos diferentes. O
que elas esperam de você é só a resposta: fazer, não fazer ou adiar. Por isso também são pontos
esperando por você, e seguem a mesma numeração dos outros itens; o "D" do identificador marca o
item, e não o tipo dele. Na seção de cima, ao contrário, você escolhe entre opções que têm
consequências diferentes. Autorizar um item aqui só é anotado no brief; para eu executar, ainda é
preciso uma instrução sua, como "aplique o D5".

### D5 — Trocar a frase da `discussion-briefs` que manda o agente para um beco sem saída

**Estado:** decidido

**Decisão:** fazer, na mesma passada em que D2, D3 e D4 forem aplicados, porque a frase nova aponta
para o que eles criam. Registrada no [plano](../active/decision-to-architecture-flow.md).

**A pergunta para você:** se eu troco uma frase da `discussion-briefs`. A resposta é só fazer, não
fazer ou adiar.

**A frase:** na parte da skill que trata de registrar decisões, está escrito, em inglês: "quando a
decisão contraria um registro aprovado, avise e deixe a skill do próprio registro decidir como o
registro muda".

**O problema, num exemplo:** você decide no brief "remover o bloco do Redmine" e manda "registre as
decisões". O agente vê que a decisão contraria um registro de arquitetura aprovado, lê essa frase e
vai procurar na `architecture-records` como o registro deve mudar. Só que ela não tem procedimento
para uma decisão sua, como o D2 mostrou: fala de incidentes e de planos em execução, e não diz como
emendar uma regra antes de o código existir nem quando um registro antigo vira "substituído". A
frase manda o agente para um lugar que não tem a resposta, e ele improvisa. No outro chat, o
improviso foi adiar a emenda em silêncio. No teste da skill, foi substituir o registro na hora.

**O que mudaria:** depois que D2, D3 e D4 forem aplicados, a `architecture-records` passa a ter esse
procedimento. A frase deixaria de ser vaga e diria o caminho com todas as letras, mais ou menos
assim: "quando a decisão contraria um registro aprovado, avise; ao registrar, a sessão que conduziu
a discussão emenda o registro antes da revisão independente, com o bloco de emenda para mudança
pequena ou com um registro novo proposto para mudança grande, como a `architecture-records`
descreve". É a ponta que liga a `discussion-briefs` às regras novas das outras duas skills.

**Por que importa:** sem essa troca, as outras skills ficam corrigidas, mas o agente que parte de um
brief continua lendo uma frase vaga e pode não achar o procedimento novo.

**O que acontece em cada resposta:**

- Fazer: a frase é trocada junto com as mudanças do D1, que são no mesmo arquivo.
- Não fazer: a frase continua apontando para a `architecture-records` de forma genérica. Depois de
  D2, D3 e D4 ela deixa de ser um beco sem saída, mas continua vaga.
- Adiar: o mesmo que não fazer, por enquanto.

**Custo e risco:** uma frase numa skill. Só faz sentido depois de D2, D3 e D4 aplicados, porque ela
aponta para o que eles criam.

**Recomendação:** fazer, na mesma passada em que as outras decisões forem aplicadas.

### D6 — Acrescentar ao teste da skill o caso que falhou de verdade no outro chat

**Estado:** decidido

**Decisão:** fazer, depois de aplicar as decisões deste brief, começando pela variante da mudança
pequena, com duas rodadas. Registrada no [plano](../active/decision-to-architecture-flow.md).

**A pergunta para você:** se eu monto e rodo um caso de teste novo depois de aplicar as decisões
deste brief. A resposta é só fazer, não fazer ou adiar.

**O que é esse teste:** quando mudei a `discussion-briefs`, não confiei só na leitura do texto.
Rodei agentes independentes: um agente novo, de um modelo menor, o Sonnet, recebe um repositório de
mentira, descartável, e uma mensagem realista de usuário, sem saber qual é o resultado esperado.
Depois eu comparo os arquivos do repositório antes e depois e leio a resposta dele. Hoje existem
três casos:

- Uma tarefa que termina com dez pendências: o agente deve criar um brief.
- A pergunta "o que falta para fechar o plano?": ele deve responder com um resumo curto, sem criar
  arquivo.
- A mensagem "D1: opção 2", quando a opção contraria um registro de arquitetura aprovado: ele deve
  só anotar a decisão no brief.

**O que falta:** nenhum caso cobre a mensagem seguinte, "registre as decisões", quando uma das
decisões pertence a um registro de arquitetura aprovado. Foi exatamente aí que o outro chat falhou.
O terceiro caso para uma mensagem antes.

**Como seria o caso novo:** o repositório de teste teria um brief com um item já decidido e com
`registro pendente`, um registro de arquitetura implementado que essa decisão contraria, e um plano
ativo. A mensagem do usuário seria só "registre as decisões". Com as escolhas que você fez de D1 a
D5, o esperado é:

- O agente emenda o registro de arquitetura na hora, com o bloco "emenda aprovada, em
  implementação" logo abaixo da regra, e deixa a regra vigente intacta.
- Ele anota a sequência de execução no plano.
- No brief, o item perde o `registro pendente` e ganha os links para o registro e para o plano.
- A resposta no chat diz o que foi registrado e onde, e avisa que a revisão independente vem em
  seguida.
- Ele não toca no código e não marca o registro antigo como substituído.

Uma segunda variante cobriria a mudança grande de desenho, em que o esperado é um registro novo no
estado proposto e uma linha de aviso no registro antigo.

**Por que importa:** as regras de D1 a D5 vão virar texto em três skills, e só um teste mostra se
um modelo mais fraco as segue. Na revisão anterior da skill, os testes acharam dois defeitos reais
que a leitura não tinha achado: um agente que reescreveu a arquitetura a partir de "D1: opção 2", e
outro que nem carregou a skill numa pergunta de status.

**O que acontece em cada resposta:**

- Fazer: depois de aplicar as decisões, eu monto o repositório de teste e rodo o caso duas ou três
  vezes. Se falhar, eu relato o que vi, e o que exigir escolha sua vira item novo num brief.
- Não fazer: as regras entram sem evidência de que funcionam, e o primeiro teste passa a ser o seu
  uso real.
- Adiar: as decisões são aplicadas agora, e o teste fica para quando você mandar.

**Custo e risco:** cada rodada consumiu entre 86 e 196 mil tokens e de um a nove minutos. Duas
variantes com duas rodadas cada ficam entre 400 e 800 mil tokens (estimativa, não verificado). Tudo
roda num repositório descartável, fora da sua home, e conferi nas rodadas anteriores que nenhum
agente escreveu fora dele.

**Recomendação:** fazer, depois de aplicar as decisões, começando pela variante da mudança pequena,
com duas rodadas.

### D9 — Dar aos itens de trabalho do modelo a mesma profundidade dos itens de decisão

**Estado:** decidido

**Decisão:** fazer, junto com as outras mudanças da `discussion-briefs`. O item de trabalho do
modelo passa a pedir a pergunta para você, um exemplo concreto, o que acontece em cada resposta e a
recomendação. Registrada no [plano](../active/decision-to-architecture-flow.md).

**A pergunta para você:** se eu mudo o modelo do brief para que os itens desta seção nasçam bem
explicados. A resposta é só fazer, não fazer ou adiar.

**O problema:** você não entendeu o D5 e achou o D6 pouco descrito, e a causa é a mesma. No modelo
da `discussion-briefs`, um item de decisão tem a pergunta, o contexto, as opções e a recomendação.
Um item de trabalho só tem três campos curtos: o que é, por que importa, e custo e risco. Eu
preenchi esses três campos e parei. A regra da skill de escrever cada item para quem não acompanhou
o trabalho vale para todos os itens, mas o modelo não puxa isso nos itens de trabalho.

**O que mudaria:** o item de trabalho do modelo passaria a pedir também a pergunta para você, um
exemplo concreto do problema, o que acontece em cada resposta, isto é, fazer, não fazer ou adiar, e
a recomendação. É o formato que o D5 e o D6 têm agora.

**Por que importa:** sem isso, o próximo brief repete o defeito, e você volta a pedir explicação
item por item, que é o que a skill existe para evitar.

**O que acontece em cada resposta:**

- Fazer: mudo o modelo junto com as outras mudanças da `discussion-briefs`.
- Não fazer: o modelo fica como está, e a profundidade dos itens de trabalho depende de o agente
  lembrar da regra geral.
- Adiar: o mesmo que não fazer, por enquanto.

**Custo e risco:** alguns campos a mais no modelo; os briefs ficam um pouco mais longos.

**Recomendação:** fazer.

### D18 — Autorizar uma rodada nova depois da revisão ou manter o limite atual?

**Estado:** decidido

**Decisão:** fazer. Você autoriza uma única rodada adicional do caso grande, em sessão
independente que você abra, somente depois da revisão e das correções aprovadas. Modelo, pedido,
critérios e limites precisam estar registrados antes; o agente do teste não abre advisor nem
subagentes, não há repetição automática e outros casos não estão autorizados. Registrada no
[plano](../active/decision-to-architecture-flow.md#governing-decisions-and-invariants).

**Situação atual:** a tentativa original foi executada com Sonnet 5/high e reprovada; E1 foi
resolvido como recebimento, com os desvios de preparação preservados. D24 agora rege as novas
rodadas Terra xhigh e Sonnet xhigh, mantendo os critérios e exigindo a conferência do lançamento.

**A pergunta para você:** autorizar uma rodada nova delimitada, não autorizar, ou adiar essa
escolha até a revisão do replanejamento. O D16 permitiu uma rodada só, e ela já aconteceu; sua
instrução anterior proibia outra rodada e qualquer subagente. A decisão acima permite apenas
a rodada delimitada em Fazer, depois de atendidos os pré-requisitos.

**O que seria feito:** uma rodada nova executa outro agente em um ambiente isolado e produz
arquivos e uma resposta novos. Isso é diferente da correção B2: nela o autor apenas corrige os
controles feitos à mão e rejulga resultados guardados. O rejulgamento não mostra como um modelo
reagirá à nova redação de B1. Uma rodada do caso grande também não demonstra, por si, o caminho de
recuo com registro em português.

**O que acontece em cada resposta:**

- **Fazer:** autorizar uma única rodada adicional do caso grande, em sessão independente que você
  abra, só depois da revisão e das correções aprovadas. O plano precisa registrar antes o modelo,
  o pedido, os critérios e os limites; o agente do teste não abre advisor nem subagentes. Não há
  repetição automática se falhar. Essa escolha não autoriza rodadas dos outros caminhos; se a
  revisão mostrar que o caso necessário é outro, a proposta volta para você antes de executar.
- **Não fazer:** manter zero rodadas novas. O trabalho se limita à revisão, aos controles, ao
  rejulgamento e às evidências existentes que você aceitar em D17. Se isso não satisfizer uma
  obrigação, ela continua aberta; o autor não a marca como verificada para concluir o plano.
- **Adiar:** manter a proibição atual até o Sol apontar uma necessidade concreta, ou concluir que
  não precisa de rodada. Você então decide com o caso e o ganho de evidência definidos. Silêncio
  ou entrega do parecer não contam como autorização.

**Custo e risco:** D16 estimava cerca de 150 mil tokens e sete minutos para uma rodada grande,
com base nas anteriores; esse é um parâmetro histórico, não uma cotação ou duração verificada
agora. Você confirmou a disponibilidade do Sonnet 5; a seleção na sessão nova ainda precisa ser
conferida. Outra execução
pode falhar novamente e não corrige a ordem da rodada antiga. Não fazer economiza essa execução,
mas pode deixar uma obrigação de validação sem atendimento.

**Recomendação:** adiar até a revisão indicar qual propriedade precisaria de evidência nova.
A correção do juiz e a leitura dos resultados existentes vêm primeiro. Não recomendo repetir o
caso grande apenas para encobrir a revisão que faltou, nem ampliar o limite sem escolha explícita.

### D22 — Autorizar a preparação e uma rodada adicional com Terra xhigh

**Estado:** decidido

**Decisão:** fazer. Autorizar a preparação da avaliação das transcrições do Codex e uma única
rodada adicional do caso grande com `gpt-5.6-terra` em `xhigh`, iniciada por esta sessão, com
contexto novo e depois do Sonnet, somente após a confirmação independente, as correções e os
controles aprovados. Sem advisor, outros agentes dentro do teste, repetição automática,
substituição de modelo ou rodadas dos outros casos. Registrada no
[plano](../active/decision-to-architecture-flow.md#governing-decisions-and-invariants).

**Situação atual:** preparação e controles concluídos. Uma transcrição existente do próprio
D21 forneceu o formato real do Codex; o leitor é selecionado explicitamente e não aprova
evidência desconhecida. Terra xhigh foi executado sob D24 e reprovado: arquitetura atualizada,
plano e brief intocados. A transcrição e a avaliação por critério estão preservadas no plano.
D24 resolveu D23 com a base atual; os hashes permaneceram iguais durante o lote.
A decisão original acima permanece como histórico; os limites de novas rodadas seguem D24.

**A pergunta para você:** fazer, não fazer ou adiar a preparação e uma única rodada adicional do
caso grande com Terra xhigh, além da rodada Sonnet prevista em D18.

**O que é:** testar as mesmas regras no Codex, com `gpt-5.6-terra` em `xhigh`. Eu abriria o agente
com contexto novo, sem herdar esta conversa, depois que o Sonnet terminasse. Ele receberia outra
cópia dos arquivos originais e o mesmo pedido de registrar as decisões, sem as respostas
esperadas, os achados do Sol ou o resultado do Sonnet. Contexto novo não isola automaticamente
o sistema de arquivos; os limites de acesso e a transcrição completa precisam ser verificáveis.

**Por que importa:** um resultado do Sonnet no Claude não mostra como o Terra se comporta no
Codex. Por exemplo, os dois podem produzir registros corretos, mas só um deles apresentar a
lista de alterações na resposta. A comparação observaria o conjunto modelo e cliente; uma
rodada de cada não estabelece qual modelo é superior nem mede uma taxa de sucesso.

**O que precisa ser preparado:** o juiz atual reconhece ferramentas e transcrições do Claude.
Seu leitor não pode tratar uma transcrição Codex vazia, incompleta ou desconhecida como sucesso.
A proposta inclui identificar o formato em uma transcrição existente, cujo acesso esteja no
escopo, preparar a leitura específica do Codex e verificá-la com controles feitos à mão. Eles
incluem alteração fora da fixture, comando Git proibido, delegação, leitura das respostas
ocultadas e falta de resultado de ferramenta. Isso não autoriza uma rodada exploratória de agente
para descobrir o formato. Todos os arquivos antigos continuam protegidos.

**O que acontece em cada resposta:**

- **Fazer:** autorizar essa preparação e uma rodada Terra xhigh, depois da confirmação independente,
  das correções e dos controles aprovados. Eu inicio o agente; você não precisa abrir uma sessão
  Terra manualmente. Não há advisor, outros agentes dentro do teste, repetição automática,
  substituição de modelo ou rodadas dos outros casos. A autorização precisa ser registrada no
  plano antes da execução.
- **Não fazer:** manter apenas a rodada Sonnet de D18. A ausência de teste Terra fica como limite;
  não bloqueia o trabalho já autorizado nem inventa uma obrigação nova para fechar o plano.
- **Adiar:** deixar Terra como proposta. A revisão D21, as correções e a rodada D18 podem avançar
  com seus próprios pré-requisitos, sem aguardar essa escolha.

**Custo e risco:** uma execução adicional de modelo, mais a preparação da leitura da transcrição.
O custo e a duração ainda não foram medidos. O Terra pode falhar ou deixar evidência insuficiente;
a autorização atual D24 permite novas rodadas com finalidade diagnóstica registrada. Se um teste exigir mudança nas skills ou
no caso, a comparação precisa ser replanejada antes do Terra, sem orientar o segundo agente com
os erros do primeiro. Um resultado Terra favorável não transforma uma falha do Sonnet em aprovação.

**Recomendação:** fazer, se você pretende usar essas skills com Terra no Codex. A cobertura
complementa a rodada Claude e mantém a avaliação igual por critério. Você escolheu fazer e mandou
registrar; o Sol confirmou o desenho em D21. A execução depende dos demais pré-requisitos.

## Depende de outras pessoas ou de acesso

### D19 — Receber a revisão independente do replanejamento

**Estado:** resolvido

**Resultado recebido:** em 2026-09-21 você entregou o parecer do Sol. O relatório informa contexto
novo e metadados de orquestração com `gpt-5.6-sol` em `xhigh`. A base informada é o HEAD
`50531033fdb16ef7f2c4362413c768a3a2143a09`, branch `master`, sete commits à frente, quatro
arquivos modificados e nada staged. O parecer declara trabalho somente de leitura e dá o veredito
**não pronto para implementação**. A entrega foi cumprida; isso não aprova o plano.

**O que foi revisado:** a proposta de mudança na trava por fase, a correção dos controles de teste,
a preservação das evidências e o tratamento da revisão ausente em D16. O revisor também leu a
frase D16 já escrita. Esta leitura não transforma a revisão ausente em revisão prévia.

**Correções bloqueantes apontadas pelo Sol:**

| Achado | Problema concreto | Correção pedida |
| --- | --- | --- |
| Ordem do recuo no consumidor | A `discussion-briefs` ainda manda emendar e só depois registrar a sequência no plano, embora D12 exija plano e revisão antes da emenda. | Explicitar registro → plano → revisão no fluxo comum e plano → revisão → manutenção/emenda → entrega no recuo. |
| Cobertura do bloqueio por fase | O cenário question-only proíbe só registro e implementação, sem cobrir criar/alterar plano ou iniciar revisão; falta a mesma decisão pendente em um terceiro dono. | Conferir a proibição completa do turno de pergunta e manter a execução bloqueada até arquitetura, plano e terceiro dono receberem a decisão. |
| Universo de preservação | Os manifests de hashes não definem todos os caminhos históricos protegidos. | Enumerar um conjunto fechado, incluindo o transcript D16 e o estado Git das fixtures; comparar os mesmos caminhos, preservar cópias verificadas dos dois fontes editáveis e recusar colisões também nos manifests. |

**Correções não bloqueantes:** explicitar na matriz que a `run-large-4` não comprova a qualidade
integral do plano produzido e esclarecer na sequência que D17/D18 não bloqueiam as correções B1/B2.
Só decisões novas provocadas pelos achados da revisão poderiam bloquear essas correções. Os cinco
achados são apresentados como correções, sem nova decisão substantiva necessária para tratá-los.

**O que continua bloqueado:** editar skills, construtor ou juiz antes da instrução de retomada;
executar a rodada autorizada em D18 antes dos requisitos;
usar B3 como aceite para o fechamento; e fazer a auditoria final antes das correções e validações.
A decisão sobre a evidência antiga é D20.2 e está registrada no plano. D18 foi autorizado pelo
usuário em 2026-09-21, após a elaboração do relatório; sua autorização está registrada e continua
condicional.

**Registro:** parecer recebido e promovido ao
[plano](../active/decision-to-architecture-flow.md#plan-review), com os achados e o veredito.

**Encaminhamento cumprido:** as propostas foram corrigidas e confirmadas em D21 pelo subagente
Sol xhigh. A implementação depende da instrução posterior de retomada prevista no plano. A futura
auditoria independente de fechamento continua separada; o autor não pode fornecê-la.

### D21 — Confirmar o plano corrigido e o desenho dos testes com o Sol

**Estado:** resolvido

**Decisão:** fazer o recomendado: confirmar o plano corrigido e o desenho dos testes com o Sol
antes de preparar a rodada do Sonnet. Você autorizou a revisão aqui por um subagente
`gpt-5.6-sol` em `xhigh`, em contexto novo e somente leitura, substituindo a abertura manual
apenas para D21. O revisor não edita, não executa testes e não abre outros agentes. Registrada no
[plano](../active/decision-to-architecture-flow.md#governing-decisions-and-invariants).

**Situação atual:** encaminhamento registrado e revisão concluída em 2026-09-21. O subagente Sol
xhigh confirmou **pronto para implementação**, depois de conferir as correções do plano e a última
frase histórica. Nenhuma decisão substantiva nova foi necessária. O revisor preservou skills,
scripts e testes;
o autor implementou as correções e executou os controles depois da sua instrução de terminar.
Não há decisão nova sobre D1.

**Resultado:** confirmação independente recebida. A revisão avaliou as correções de D19, o
detalhamento dos testes e a preparação e a rodada Terra autorizadas em D22, sem receber uma
orientação para aprovar. Os achados foram corrigidos no plano e conferidos pelo mesmo revisor;
os hashes das versões examinadas e o veredito estão registrados no
[plano](../active/decision-to-architecture-flow.md#d21-confirmation-of-the-revised-plan).
D19 permanece resolvido como entrega do relatório anterior.

**Achados de D21 e correções confirmadas no plano:**

| Achado | Consequência | Correção no plano |
| --- | --- | --- |
| Ordem contraditória dentro da skill de planejamento | Um trecho manda sempre emendar antes do plano, mesmo quando D12 exige plano e revisão primeiro. | Incluir esse trecho entre os consumidores de B1 e distinguir as duas ordens, tanto para criar quanto para atualizar um plano existente. |
| Perda do avanço/ack no caso grande | O resultado pode preservar o filtro e ainda impedir a leitura da fila de avançar. Os controles antigos do caso grande compartilham essa omissão. | Preservar a obrigação do registro original e exigir localizar e validar o responsável antes de remover a proteção. Os controles distinguem omissão no registro e omissão no plano. B2 passa a 26 resultados e o conjunto de conteúdo D18 a sete, herdado por Terra. As afirmações históricas amplas ficam qualificadas até o rejulgamento. |
| Falta de controles da transcrição Claude | A avaliação atual ignora destinos de leituras e pode aceitar acesso às respostas ocultas ou transcrição incompleta. | Exigir controles feitos à mão de leituras, efeitos, caminhos e completude antes do Sonnet, incluindo leituras permitidas das instruções e skills. A preparação Codex não substitui essa conferência. |
| Controles Codex menores que suas obrigações | Um leitor pode reconhecer patches e Git, mas ignorar outras escritas por shell, escapes de caminho ou a falta de conclusão da transcrição. | Reconstruir no formato Codex todos os controles de efeitos, leituras, caminhos e completude previstos para Claude, mais escrita aninhada permitida e proibida. Um resultado Claude não valida o leitor Codex. |

O Sol considerou adequados os limites de preservação, o tratamento da evidência antiga, a
ausência de Git na fixture e a separação entre Sonnet e Terra. Nenhum achado foi rejeitado.
Se a investigação futura do avanço/ack revelar uma escolha real de arquitetura, ela volta para
você; o plano não inventa agora um protocolo ou uma implementação do roteador.

**O que mudou:** o plano agora separa a ordem comum da ordem de recuo, inclui a proibição completa
no turno de pergunta e a mesma decisão ainda pendente em um terceiro dono, e define quais
arquivos históricos serão preservados e comparados. Também divide a execução: os controles e o
rejulgamento ficam comigo; a rodada autorizada fica com o Sonnet, em sessão nova aberta por você,
como D18 já prevê. A rodada complementar Terra, iniciada por mim no Codex, foi autorizada em D22
e está registrada no plano.

**Pontos confirmados pelo revisor:** além da promoção da decisão, o teste novo deve detectar um
plano que retire a proteção do consumidor antes de preparar e verificar o roteador. Foram
propostos controles feitos à mão para essa falha, uma premissa inventada, a lista escondida nas
notas e a substituição descrita como já concluída. A fixture nova preservará a ausência de Git
do original guardado, para não criar um repositório sem autorização; o revisor aceitou esse
limite. O teste não comprova comportamento específico de um repositório Git
inicializado nem executa a migração descrita no plano produzido.
O revisor também confirmou o desenho da leitura das ferramentas do Codex, seus controles contra
aprovação indevida, a preservação dos arquivos e a separação entre as autorizações D18 e D22.

**Por que importa:** o autor pode corrigir e preparar os testes, mas não fornecer a confirmação
independente do próprio desenho. Um exemplo é um juiz que aceita um texto porque encontrou uma
palavra, embora a regra tenha sido perdida; testar o próprio juiz antes da rodada do Sonnet reduz
esse risco. Uma rodada nova não deve ser gasta enquanto o desenho de avaliação continuar falho.

**O que fica aguardando:** E1 foi resolvido como recebimento da sessão Sonnet high reprovada.
O lote D24 foi revisado e executado: Terra reprovou; a preparação do Sonnet xhigh negou a leitura
global obrigatória. A rodada interativa posterior resolveu E3, com identidade, isolamento e
retenção conferidos antes da tarefa, mas reprovou em dois critérios de conteúdo.
Novas rodadas precisam da finalidade diagnóstica de D24; os critérios continuam iguais.
E2 acompanha a auditoria independente de fechamento após as evidências exigidas.

**Custo e risco:** a revisão foi somente de leitura, sem testes ou agentes adicionais pelo revisor.
Casos novos de comportamento, como o recuo
com registro em português, continuam fora da autorização D18; se forem exigidos, precisam de uma
proposta própria antes da execução. Nenhum custo novo foi medido nesta etapa.

**Recomendação:** confirmar o plano corrigido com o Sol antes de preparar a rodada do Sonnet.
Você escolheu seguir essa recomendação, ela está registrada e o delta foi confirmado.
Não é necessária outra escolha sobre D17, D18 ou D20. O
[plano](../active/decision-to-architecture-flow.md#test-responsibilities-and-acceptance-contract)
contém os critérios e a divisão de trabalho confirmados pelo parecer.

### E1 — Receber a sessão Sonnet e sua transcrição completa

**Estado:** resolvido como recebimento; a preparação e o teste não passaram

Você abriu a sessão e forneceu sua resposta. Localizei a transcrição nativa completa da sessão
`8876fc0b-1f63-46eb-b03f-8818a2e274f8` e conferi as 28 chamadas com resultados e a resposta final.
Ela confirma Sonnet 5/high e o pedido preparado, mas começou na pasta pessoal, com outro projeto
também disponível. Não houve a conferência de isolamento antes de enviar o pedido. Isso fica
registrado como desvio, sem tentar restaurar retroativamente a preparação planejada.

A tentativa original terminou e foi reprovada pelos defeitos de conteúdo descritos no resumo.
Os arquivos, a resposta e a transcrição foram preservados. Resolver o recebimento não satisfaz
D18 nem fecha D16. A autorização posterior D24 permite as novas rodadas e resolve D23 com
a base atual; a reprovação original permanece registrada.

### E2 — Receber a auditoria independente de fechamento após as rodadas

**Estado:** aberto

**O que é:** falta a segunda passagem sobre a implementação e suas evidências finais. A revisão
D21 examinou o plano; não examinou as skills e os leitores que foram alterados depois dela. Esta
sessão passou a ser autora e não pode emitir o parecer independente do próprio trabalho.

**De quem depende:** uma sessão nova de revisão aberta por você, pela rota já registrada no plano.
As autorizações do Sol cobrem revisões de plano, incluindo D21 e o experimento posterior; não
trocam essa rota de fechamento.

**O que bloqueia:** concluir o plano e movê-lo para `completed/`.

**Próximo passo:** depois das evidências das rodadas e da auditoria do autor, eu preparo o prompt
com o baseline e os artefatos finais para essa sessão. Não há razão para abri-la antes disso.

### E3 — Abrir a sessão interativa do Sonnet xhigh

**Estado:** resolvido como acesso e abertura; rodada avaliada e reprovada por conteúdo

**O que aconteceu:** o Claude local negou `Read` para as instruções globais porque o comando
não tinha interface de aprovação. O Sonnet continuou sem as skills. A saída fica preservada;
não vou repetir essa leitura por outro caminho nem desabilitar as permissões.

**Resolução:** você mandou que eu abrisse o Claude interativo. A nova sessão confirmou
Sonnet 5/xhigh, a pasta isolada e nenhum diretório adicional antes de receber o pedido congelado.
As leituras necessárias foram aprovadas uma a uma, sem ampliar permanentemente as permissões.

**Evidência:** em S `post-audit-b1-b3-410811bdf229/live/d24-manual-02/`, o lançador original
e seu erro foram preservados: `--mcp-config` consumia o prompt como outro argumento. Corrigi
a ordem em `open-sonnet.interactive.sh`, antes de qualquer pedido ao modelo. A captura inicial
e `interactive-preflight.json` registram a sessão. O cliente passou pela configuração inicial,
com tema Auto, autenticação da conta existente e confiança na fixture; não afirmo que seu
estado global de execução ficou intocado. Não alterei padrões globais de modelo, esforço ou
permissão.

**Limite:** resolver E3 não aprova o teste. A avaliação completa está em `sonnet-result/`:
substituição integral e pré-requisito de avanço/ack reprovados, com os demais resultados e
limitações discriminados. A sessão foi encerrada normalmente depois da resposta, sem pedido
de correção ao modelo. E2 continua posterior às evidências exigidas e à auditoria do autor.

## Sem ação necessária

- Não proponho regra global nova para o "resolveu sozinho e em silêncio". A sua regra de nomear
  conflitos entre skills e mostrar as opções antes de agir já cobre isso. A falha foi de
  comportamento, e o D1 põe o aviso obrigatório no lugar onde ela aconteceu.
- O procedimento de emenda D3 já está escrito nas skills, com o recuo D12. A compatibilidade do
  bloqueio por fase foi corrigida em B1; o conselho antigo de esperar a criação desse
  procedimento não descreve mais o estado atual. A aplicação no outro repositório não foi
  verificada e não faz parte desta continuação.
- Aplicar D2, D3 e D4 muda a ordem de revisão e uma regra da skill de arquitetura. Pela
  `plan-implementation`, isso é mudança de alto risco: plano completo e revisão independente antes
  e depois. D1 e D5 são mudanças de redação só na `discussion-briefs`.
