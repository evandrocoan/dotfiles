# Brief de discussão: o caminho de uma decisão até o registro de arquitetura

**Estado:** em discussão

**Alimenta:**

- `nenhum ainda`; quando você mandar aplicar, as decisões vão para um plano de implementação

Documento de trabalho: explica os pontos em aberto e resume o que já foi decidido. Não substitui o
plano de implementação nem o registro de arquitetura, e nada escrito aqui autoriza trabalho; cada
decisão vale onde foi registrada.

## Resumo

Em outra conversa, você decidiu num brief remover um bloco da integração com o Redmine, e essa
decisão muda uma regra de um registro de arquitetura aprovado. Quando você mandou "registre as
decisões", o agente copiou a decisão só para o plano, marcou o brief como concluído e deixou o
registro de arquitetura para depois, sem avisar. Você só soube porque perguntou. O relato é o que
você colou aqui; aquele repositório e aquele plano eu não vi (não verificado).

A falha foi em parte de comportamento e em parte das skills, que deixam três buracos quando uma
decisão sua contraria um registro de arquitetura aprovado. Conferi os trechos das três skills nesta
sessão, em 2026-09-18, e os buracos existem. Estão decididas as seis escolhas entre
opções, todas com `registro pendente`: o D1, nomear o dono de cada decisão e manter o brief aberto
enquanto faltar um; o D2, a marca só na regra emendada; o D3, a emenda do registro antes da revisão
independente; o D4, a emenda feita pela sessão que conduziu a discussão; o D7, conferir o brief no
fechamento do plano; e o D8, um prefixo e uma sequência por seção nos briefs novos. Também está
decidido, com `registro pendente`, o D5: trocar a frase da `discussion-briefs` junto com as outras
mudanças. Estão decididos também, com `registro pendente`, o D6, rodar o caso novo no teste com
agente independente depois de aplicar as decisões, e o D9, dar aos itens de trabalho do modelo a
mesma profundidade dos itens de decisão. Não há item aberto. Os nove itens estão decididos, e nenhum foi
registrado ainda, porque não existe plano para recebê-los. O passo que falta é você mandar
registrar as decisões; aplicá-las exige um plano de alto risco, com revisão independente antes e
depois.

## Glossário

| Termo | O que é |
| --- | --- |
| skill | Pacote de instruções que o agente carrega para um tipo de tarefa. |
| brief | Documento de trabalho em português criado pela skill `discussion-briefs`; este arquivo é um. |
| registro de arquitetura | Documento durável, em inglês, que guarda uma decisão de desenho aprovada e as regras que o código deve obedecer; é regido pela skill `architecture-records`. |
| regra do registro | Uma frase do registro de arquitetura que o código tem de cumprir; a skill chama isso de invariante. No outro chat era a "invariante 18". |
| plano de implementação | Roteiro temporário, em inglês, da sequência de trabalho; é regido pela skill `plan-implementation`. |
| dono da decisão | O documento que manda naquela decisão. Decisão de desenho durável: o registro de arquitetura. Sequência de execução: o plano. |
| `registro pendente` | Marca que um item decidido carrega no brief enquanto o dono ainda não recebeu a decisão. |
| revisão independente | Revisão feita por um agente com contexto limpo, que só lê e relata; a `plan-implementation` a exige em trabalho de alto risco, antes e depois. |
| estado do registro | Rótulo do registro inteiro: proposto, em implementação, implementado ou substituído. |
| sessão que implementa | A conversa nova, no outro chat com o modelo Opus, que recebe o plano pronto e escreve testes e código. |
| alto risco | Classificação da `plan-implementation` para mudanças que mexem em arquitetura, autorização ou regras de revisão; exige plano completo e revisão independente. |

## Decisões que dependem de você

### D1 — O brief pode dar uma decisão como registrada quando só o plano a recebeu?

**Estado:** decidido

**Decisão:** opção 1. Ao registrar, o agente nomeia o dono de cada decisão: a decisão de desenho
durável vai para o registro de arquitetura, e a sequência de execução vai para o plano. Enquanto
faltar um dono, o item continua com `registro pendente` para ele, o brief não fecha, e a resposta no
chat diz o que ficou de fora e por quê. `registro pendente`: ainda não existe um plano para receber
esta decisão. Esta opção faz o brief ficar aberto por mais tempo, e o risco de ele ser esquecido
aberto depois da implementação virou o D7.

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

**Decisão:** opção 1, a marca só na regra, na variante por tamanho da mudança. Emenda pequena, de
uma ou duas regras, entra como bloco "emenda aprovada, em implementação" logo abaixo da regra
vigente. Mudança grande de desenho segue o caminho que a skill já tem, o registro novo no estado
proposto, com a linha de aviso no registro antigo, que só vira "substituído" quando o novo
estiver implementado. `registro pendente`: ainda não existe um plano para receber esta decisão.

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
mesma hora, com o código ainda no comportamento antigo, e nenhum registro passou a descrever o que
valia naquele momento. Falta também a emenda pequena antes do código: "emendar no lugar" quer dizer
reescrever a regra, o que apresenta o futuro como presente.

**O que este item acrescentaria de fato à skill:** três coisas pequenas. O bloco "emenda aprovada,
em implementação" para a emenda pequena. A linha de aviso no registro antigo enquanto o substituto
ainda está proposto. E a regra de que o antigo só vira "substituído" quando o novo estiver
implementado. O critério para escolher entre emendar e criar um registro novo não é novidade:
basta dizer que o critério dos incidentes vale também para uma decisão sua.

**Como fica na prática:**

| O que acontece | Opção 1: marca só na regra | Opção 2: registro novo, proposto | Opção 3: registro inteiro em implementação |
| --- | --- | --- | --- |
| Regra que vale hoje | Continua escrita como vigente. | Continua no registro antigo, intocada. | Continua escrita, mas o registro todo parece em fluxo. |
| Regra nova aprovada | Aparece ao lado, rotulada "emenda aprovada, em implementação". | Fica num registro novo, no estado proposto, que aponta para a regra que vai substituir. | Entra no texto, com uma nota dizendo o que ainda não foi entregue. |
| Quando o plano fecha | A regra nova substitui a antiga e o rótulo some. | A regra antiga é trocada e o registro novo é incorporado ou vira histórico. | O registro volta para "implementado". |
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
    update may skip the remote comparison. Until this amendment is implemented, the code follows
    the rule above.
```

Quando o plano fecha, o bloco some e a regra é reescrita:

```markdown
18. Every update sent to Redmine is first compared with the remote issue. No update may skip that
    comparison.
```

**O que impede a marca de virar bagunça:**

- Um lugar só. O bloco fica imediatamente abaixo da regra que ele muda, nunca numa seção de
  "emendas" no fim do arquivo.
- A regra vigente continua sem marca, e o bloco diz com todas as letras que o código ainda segue o
  texto de cima. Quem lê sabe o que vale hoje e o que está a caminho.
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
registro antigo. É o mesmo critério que a `architecture-records` já usa para incidentes: emendar
quando o contrato estava incompleto, e criar ou substituir um registro quando o desenho muda de
verdade.

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
novo.

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
`registro pendente`: ainda não existe um plano para receber esta decisão. Ela depende da opção 1 do
D2, que você também já escolheu: a regra nova entra com a marca "emenda aprovada, em
implementação", e por isso emendar primeiro não apresenta o futuro como comportamento atual.

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
"os registros já estão emendados; implemente contra eles". `registro pendente`: ainda não existe
um plano para receber esta decisão.

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
de fechamento, o plano anota isso e fecha. `registro pendente`: ainda não existe um plano para
receber esta decisão.

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
`registro pendente`: ainda não existe um plano para receber esta decisão.

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
para o que eles criam. `registro pendente`: ainda não existe um plano para receber esta decisão.

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
pequena, com duas rodadas. `registro pendente`: ainda não existe um plano para receber esta
decisão.

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
recomendação. `registro pendente`: ainda não existe um plano para receber esta decisão.

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

## Sem ação necessária

- Não proponho regra global nova para o "resolveu sozinho e em silêncio". A sua regra de nomear
  conflitos entre skills e mostrar as opções antes de agir já cobre isso. A falha foi de
  comportamento, e o D1 põe o aviso obrigatório no lugar onde ela aconteceu.
- Para o outro chat, as duas ordens servem, desde que você saiba qual está valendo. A que o agente
  propôs, revisão independente antes da emenda, é aceitável com as skills de hoje. A que eu
  recomendo no D3, emendar já, exige que só a parte do Redmine entre marcada como "em
  implementação", e não o registro inteiro, que é o assunto do D2.
- Aplicar D2, D3 e D4 muda a ordem de revisão e uma regra da skill de arquitetura. Pela
  `plan-implementation`, isso é mudança de alto risco: plano completo e revisão independente antes
  e depois. D1 e D5 são mudanças de redação só na `discussion-briefs`.
