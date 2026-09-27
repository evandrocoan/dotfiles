# Brief de discussão: correções e fechamento das skills de arquitetura

**Estado:** em discussão

**Alimenta:**

- [plano de implementação existente](../active/decision-to-architecture-flow.md).

Documento de trabalho em português. Explica o que ainda precisa ser resolvido; não substitui o
plano nem autoriza execução. As escolhas e autorizações anteriores continuam no
[brief preservado](decision-to-architecture-flow.md). Este passa a ser o documento de discussão
atual, conforme seu pedido de um briefing novo. A dependência E2 conserva seu identificador.

## Resumo

Em **25/09/2026**, o
[diagnóstico de corte e auditoria final](../history/decision-to-architecture-flow-pre-condensation.md#completed-diagnostic-cutover-and-final-audit-check)
terminou em **HOLD para Sonnet 5/xhigh e Opus 5/xhigh**. As respostas citaram mais
obrigações, mas nenhuma extração autorizou a redação. O Sonnet chamou a troca de atômica e
deixou os dois filtros ativos entre a ativação do roteador e a retirada da checagem antiga; também não
propôs verificar a replayabilidade da DLQ. O Opus previu a migração dos leitores do contador
antigo somente depois de ativar o roteador, embora o descarte nesse ponto já impeça o
consumidor de continuar contando ou registrando esses eventos. Suas verificações de entrega
dos pedidos próprios e DLQ também ocorreriam após ativar o caminho novo, sem condição
explícita de contenção e recuperação para uma perda nesse intervalo. O autor e revisões
independentes Sol xhigh conferiram as respostas contra a fonte. Os prompts chegaram uma vez
por modelo, as amostras e skills ficaram intactas e nenhuma etapa de escrita ocorreu. Uma
tentativa guiada por modelo não mede taxa de sucesso nem demonstra que o parágrafo novo
causou qualquer melhora. Os principais achados e pareceres estão resumidos neste brief e no
plano; o relatório local detalhado e as respostas normalizadas foram removidos a seu pedido.
Os rastros nativos detalhados continuam em diretório temporário e precisarão de preservação
durável ou nova comprovação para uma futura auditoria final. **A validação completa com Sonnet e
Terra e E2 seguem pendentes; T2 continua adiado.**

Em **24/09/2026**, o
[teste seguinte com contrato de saída](../history/decision-to-architecture-flow-pre-condensation.md#completed-execution-bounded-output-contract-trial)
também terminou em **HOLD para Sonnet 5/xhigh e Opus 5/xhigh**, após uma tentativa nova
por modelo e revisão independente Sol xhigh. O Sonnet identificou a obrigação de avanço dos
registros, mas sua sequência retirou a checagem antiga antes de comprovar a entrega dos
pedidos próprios e o caminho da DLQ pelo roteador; ainda presumiu testes inexistentes no
cenário. O Opus passou a exigir a validação dessas garantias antes da retirada, mas propôs
operar os dois filtros de cliente ao mesmo tempo sem definir uma troca segura e deixou a
reescrita final do registro depois da auditoria, sem repeti-la. Ele também reabriu como
opção uma checagem defensiva no consumidor que D1 já retirou dali. Nenhum avançou para a
redação dos documentos. As fontes e skills não mudaram; no braço Opus, o cliente Claude
criou apenas uma autorização local de leitura no cenário isolado, registrada como diferença
de inventário e não como edição da fonte. O contrato de saída melhorou parte da cobertura,
mas não resolveu a passagem das regras para a ordem final. **E2 e a validação do fluxo
completo seguem pendentes; T2 continua adiado.**

Em **24/09/2026**, a nova
[rodada com Opus e Sonnet](../history/decision-to-architecture-flow-pre-condensation.md#completed-diagnostic-sonnet-and-opus-failure-localization-trial)
terminou sem liberar a redação. O Opus 5/xhigh identificou as garantias do texto original,
mas contradisse sua própria condição de migrar os usuários do contador antigo antes de
retirá-lo e colocou a validação do novo fluxo depois da retirada de proteções do consumidor.
O Sonnet 5/xhigh, com uma instrução geral para inventariar ações observáveis, passou a
preservar explicitamente o avanço dos registros descartados; ainda assim, criou uma
exigência de **pelo menos** uma linha de log onde D1 só fixou **no máximo** uma, não
validou todo o caminho pelo roteador e deixou o plano com escopo apenas no consumidor.
As duas extrações foram barradas pelo Sol xhigh. Os cenários e as skills ficaram intactos;
nenhum dos modelos chegou ao registro dos documentos.

Um Opus separado analisou as quatro extrações e concluiu que as regras essenciais já estão
nas skills, enquanto a síntese do modelo e a passagem da tabela para a ordem de execução
falharam; a apresentação densa de algumas regras pode contribuir. Aceitei essa conclusão
como diagnóstico limitado, não como prova de causa: houve uma tentativa por condição. O
analista considerou excessiva parte da reprovação do próprio Opus por encontrar a expressão
“corte atômico”. Uma conferência Sol xhigh adicional confirmou que essa expressão cobre
filtro e evidência, mas não exige validar **todas** as garantias antes da retirada; o HOLD
permanece, com a redação do achado mais precisa. O registro original do Terra contém as
leituras por arquivo, embora o pacote entregue a esse analista não as incluísse.

O teste seguinte, já concluído e descrito acima, congelou uma mudança mínima: exigir que cada
garantia cujo dono ou caminho muda tenha responsável, verificação observável e condição
de transição antes da retirada, e fazer a conferência citar também os trechos que possam
contrariar seus achados. Os mesmos critérios D18/D22 continuam valendo. Isso ainda não
aprovou alterações nas skills; **T2 segue adiado**, o fluxo completo continua sem aprovação
e **E2 permanece pendente**.

Você pediu testar **Terra e Sonnet antes de adotar a recomendação**. A
[rodada guiada](../history/decision-to-architecture-flow-pre-condensation.md#completed-execution-guided-terra-and-sonnet-trial)
fornece a lista de skills e separa extração, conferência independente e registro. Cada modelo
terá uma tentativa; só uma extração aceita poderá avançar para a redação. A preparação e a
revisão prévia terminaram. **O Sonnet falhou na extração, confirmado pelo Sol xhigh:** ele citou
o offset antigo, mas não exigiu claramente a preservação e a validação do avanço da fila antes
de retirar a proteção atual. Leu integralmente as sete skills e os templates; a ajuda explícita
não resolveu essa falha nesta tentativa. A conferência bloqueou a redação e nenhum arquivo do
ambiente de teste foi alterado. O Terra abriu corretamente, mas durante a abertura surgiu
uma entrada do diretório do teste na lista global de locais confiáveis. A diferença foi
registrada e a falha de preservação permaneceu. Após você esclarecer que essa mudança do
cliente não deveria parar o teste, a extração prosseguiu na mesma sessão. **O Terra também foi
barrado pela conferência independente:** preservou a confirmação/avanço como obrigação futura,
mas não exigiu validar o novo caminho antes de retirar a proteção atual, nem reconciliou o
escopo antigo do plano com o roteador. Nenhum dos dois modelos avançou para a redação nesta
rodada. Os critérios permanecem os mesmos, mas esta ajuda explícita
distingue a rodada do teste original. Nenhuma skill será instalada ou alterada por esse teste;
T2 continua adiado e a auditoria final E2 continua pendente.

Sua instrução de continuar foi executada como uma
[conferência independente da extração](../history/decision-to-architecture-flow-pre-condensation.md#completed-diagnostic-independent-extraction-gate-on-preserved-artifacts).
O Sol xhigh bloqueou a saída real do Sonnet, que identificava uma regra no texto antigo sem
mantê-la obrigatória no desenho futuro. Também bloqueou os três exemplos defeituosos e aceitou
o exemplo completo. Assim, a conferência detectou a perda antes de qualquer redação nesta rodada.
Ela usou a saída preservada e controles; não houve nova chamada ao Sonnet nem alteração das
skills. Uma justificativa adicional sobre logs foi considerada excessiva e não foi adotada;
o bloqueio permanece sustentado pelas falhas de preservação, validação e validade do registro.
Isso sustenta a utilidade de conferir a extração, mas não prova que a etapa seguinte escreverá
os documentos corretamente. Depois do bloqueio pela cota do Sol, o **Opus 5/high confirmou essa
avaliação**, sem achado impeditivo. Após eu apontar a omissão, ele completou a leitura das skills
aplicáveis. Registrei as ressalvas: os controles cobrem uma única garantia, não demonstram confiabilidade e não validam
o fluxo completo. O próprio teste também omitiu skills aplicáveis; essa falha continua registrada.
**E4 está resolvido.** O parecer e a complementação estão no
[plano](../history/decision-to-architecture-flow-pre-condensation.md#independent-result-conformance-completed);
não substituem a auditoria final E2. Nenhuma skill instalada foi alterada nesta rodada.

Em **23/09/2026**, você autorizou testar a recomendação de concentrar o procedimento de registro
e conferir explicitamente cada garantia do documento original até a nova arquitetura e o plano.
As duas tentativas do
[experimento](../history/decision-to-architecture-flow-pre-condensation.md#coverage-experiment-results-and-limits)
terminaram, com Sonnet 5/xhigh e os mesmos critérios. **A recomendação não demonstrou resolver
a falha.** Com as skills atuais, o modelo preservou a confirmação/avanço na arquitetura, mas
omitiu sua validação como pré-requisito no plano. Com a proposta, fez a tabela pedida, porém
agrupou todo o fluxo antigo como “alterado” e perdeu essa garantia na tabela, na arquitetura
e no plano. **O Sol xhigh conferiu e confirmou essa avaliação.** Acrescentou dois erros menores
de indicação de responsável e numeração dos passos na tabela; nenhum altera a reprovação.

Os documentos certos foram atualizados e as ações ficaram no escopo em ambas as tentativas.
As fontes e evidências protegidas foram preservadas. O cliente injetou duas ferramentas adicionais
na sessão da proposta; essa diferença foi conferida antes da tarefa e limita a comparação.
Nenhuma delas foi usada. Uma tentativa por versão não prova que a proposta causou a piora.
**Não adotei a proposta nem alterei as skills instaladas.** A tabela, sozinha, não foi suficiente
para conferir as garantias do texto original. A hipótese agora em avaliação é conferir a
extração independentemente antes de redigir; ainda não há demonstração de solução completa.
T2 continua adiado; experimentar a proposta não equivale a aprovar sua instalação.

Situação conferida em **22/09/2026**: a revisão das quatro skills centrais e a comparação de modelos
terminaram. Foram encontrados dois defeitos textuais e riscos de compreensão por repetição e
excesso de exceções. A regra de preservar garantias existentes já é explícita.

Terra xhigh, Sol high e Opus high preservaram a obrigação de confirmação/avanço que o Sonnet havia
perdido na tentativa anterior. Nenhum passou em todos os critérios. Esses exercícios pediam uma
tabela de análise; não aprovaram o fluxo completo de escrever o registro, derivar o plano e
atualizar o brief. Os [resultados e limites](../history/decision-to-architecture-flow-pre-condensation.md#comparative-extraction-results)
permanecem no plano, sem repetir seu histórico aqui.

Há **um item aberto neste brief: E2**, sobre a auditoria independente final. T3 foi resolvido
pela continuação do teste do Terra e E4 foi resolvido
com a conferência do Opus high. As validações do fluxo completo abaixo continuam pendentes.
**T1 foi decidido: fazer as duas
correções pontuais. T2 foi decidido: adiar a reorganização ampla.** As duas decisões foram
[registradas no plano](../history/decision-to-architecture-flow-pre-condensation.md#completed-execution-t1-corrections-and-t2-deferral),
sem registro pendente. **T1 foi executado**: as duas correções passaram pela revisão prévia, pelas
verificações focadas e pela conferência independente do resultado com Sol xhigh. Isso conclui as
correções textuais, sem aprovar o fluxo completo dos modelos. A reorganização ampla continua
adiada; as decisões anteriores continuam registradas.

A rodada do fluxo completo após T1 foi revisada pelo Sol xhigh. O **Sonnet 5/xhigh terminou
reprovado**: omitiu a garantia de confirmação/avanço no registro e sua validação antes de retirar
a proteção antiga no plano. Recebeu as quatro skills e o template corrigido integralmente;
os documentos certos foram atualizados e não houve alteração de código ou efeito proibido.
Os critérios e a tentativa original foram preservados.

Na rodada anterior, o Terra ficou suspenso porque faltava o catálogo de ferramentas no registro
da sessão e apareceu uma alteração de configuração cuja autoria não foi estabelecida. Essa
tentativa e sua falha de preservação continuam registradas.

As evidências anteriores, as 21 fontes comuns e os critérios foram preservados. A rodada terminou
sem aprovação completa. Os resultados e suas limitações estão registrados no
[plano](../history/decision-to-architecture-flow-pre-condensation.md#post-t1-batch-results-and-limits);
a falha do Sonnet e a suspensão do Terra não foram descartadas.

**A captura foi corrigida e o Terra xhigh executou a tarefa original uma vez**, depois da revisão
com Sol xhigh. Foram preservadas as requisições reais, as ferramentas e todas as ações. O resultado
também foi **reprovado**: faltam a garantia de confirmação/avanço no novo registro e sua validação
antes de retirar a proteção antiga no plano. Além disso, a lista dos arquivos ficou apenas nas
notas da sessão, embora o critério exija que apareça na resposta destinada ao usuário.

Os documentos certos foram atualizados e as ações registradas ficaram dentro do escopo. Contudo,
a configuração global mudou entre a conferência anterior e a posterior ao teste: apenas o modelo
padrão do cliente foi trocado. Todas as requisições continuaram usando Terra/xhigh; a autoria e o
momento exato da mudança são desconhecidos. Essa falha de preservação permanece separada das
falhas de conteúdo. Não houve nova tentativa nem alteração das skills ou dos critérios.

O Sol xhigh conferiu e confirmou essa avaliação, sem aprovar o fluxo completo. O Terra recebeu
as skills centrais integralmente, mas não leu o template de arquitetura corrigido
em T1. Portanto, esta tentativa também não demonstra o efeito daquela correção. Os
[resultados e limites](../history/decision-to-architecture-flow-pre-condensation.md#terra-task-result-after-capture-repair)
estão no plano. T2 continua adiado.

## O que falta para encerrar o trabalho já autorizado

| Pendência | O que precisa existir para encerrá-la |
| --- | --- |
| Validação do fluxo completo | Evidência aceita de que os modelos registram a decisão nos documentos certos, preservam todas as garantias e propõem uma transição segura. As obrigações de Sonnet e Terra continuam separadas; nenhum substitui a falha do outro. |
| Revalidação e auditoria do autor | Conferência final das regras, documentos, resultados e efeitos das ferramentas, com cada requisito do plano sustentado por evidência. Uma garantia não pode desaparecer nem surgir uma regra que você não decidiu. |
| Auditoria independente e fechamento | Parecer E2 sobre a versão final e suas evidências. Só depois de resolver todos os requisitos obrigatórios cabe concluir o plano e este brief. |

As duas primeiras pendências correspondem às validações e ao fechamento já previstos no plano;
**não são pedidos para autorizar novamente o mesmo trabalho**. A autorização anterior D24 permite
os testes necessários, com hipótese ou correção revisada, critérios definidos antes da rodada e
preservação de cada falha. Não permite repetir sem obter informação nova nem reduzir os critérios.

O ponto concreto ainda não demonstrado é a transição: quando a conferência sai de um componente e
vai para outro, o plano precisa exigir que o novo caminho de confirmação e avanço seja localizado
e validado antes de retirar a proteção antiga. Provar somente que o novo filtro descarta mensagens
não demonstra que a fila continuará avançando. As correções de T1 melhoram as instruções, mas
ainda não demonstraram resolver essa falha dos modelos.

Os rastros antigos do Codex mantêm suas limitações originais; não foram reinterpretados como
aprovados. Na tentativa atual, a nova captura resolveu a falta da entrada e do contexto completo,
incluindo ferramentas e a sequência de requisições. O impedimento concreto agora é obter validação
aceita do comportamento, preservando também o ambiente. Repetir o mesmo teste sem uma hipótese
nova não resolve essa pendência e não está previsto como próximo passo automático.

## Glossário

| Termo | O que é |
| --- | --- |
| skill | Pacote de instruções carregado pelo agente para um tipo de tarefa. |
| registro de arquitetura | Documento que define o desenho aprovado e as regras que o sistema deve cumprir. |
| garantia | Comportamento que deve continuar obrigatório, mesmo quando seu responsável muda. |
| confirmação/avanço | Concluir o consumo de uma mensagem para que a leitura da fila continue, inclusive após um descarte. |
| transição segura | Sequência de mudança que mantém as garantias durante a troca de componentes, e não apenas no desenho final. |
| auditoria do autor | Conferência completa feita por esta sessão, responsável pelas alterações e pela avaliação dos testes. |
| D18 e D22 anteriores | Obrigações de validação com Sonnet e Terra; as tentativas foram executadas, mas não forneceram aprovação completa. |
| D24 anterior | Sua autorização já registrada para testes necessários adicionais, com finalidade definida e os mesmos limites de segurança e avaliação. |
| D20.2 anterior | Sua decisão de conservar a antiga quarta rodada do caso grande apenas como histórico, sem usá-la para fechar a validação. |
| E2 | Auditoria final independente, herdada do brief anterior; mantém o mesmo número para evitar confusão. |
| `registro pendente` | Marca usada quando uma decisão sua ainda não chegou a todos os documentos que devem registrá-la. |

## Trabalho que posso fazer com sua autorização

### T3 — Continuar o teste do Terra com a mudança de configuração registrada

**Estado:** resolvido — a extração ocorreu uma vez, com a diferença de configuração registrada.

**O que é:** a abertura da sessão Terra acrescentou o diretório isolado do teste à lista de
locais confiáveis do Codex. O modelo e o esforço estão corretos e ele não chamou ferramentas.
A conferência inicial dos hashes isolou essa entrada; não estabeleceu, por si só, qual processo
escreveu o arquivo. A extração terminou na mesma sessão depois da continuação.

**Por que importa:** o protocolo exigia configuração intacta. Seu `AGENTS.md` manda consultar
você antes de mudar a estratégia quando uma premissa necessária falha. A continuação concreta
já passou pela revisão técnica e conserva essa falha no resultado.

**Opções:** fazer a primeira extração na mesma sessão, com o mesmo pedido e essa diferença
registrada; não fazer e encerrar o Terra sem resultado de conteúdo nesta rodada; ou adiar e
manter a extração suspensa.

**Recomendação:** fazer. A diferença está identificada e restrita ao próprio ambiente de teste;
continuar permite observar o comportamento do Terra. Mesmo se o conteúdo estiver correto, a
rodada não poderá receber aprovação geral sem ressalva. Não haverá repetição, restauração da
configuração, redução dos critérios ou alteração das skills.

**Resultado:** você esclareceu que a entrada automática de confiança não deveria interromper
o teste. A extração prosseguiu uma vez; o Sol xhigh e o autor a barraram por falta de uma
condição de transição segura. Nenhum documento do ambiente de teste foi redigido. A falha
original de preservação da configuração continua registrada no
[plano](../history/decision-to-architecture-flow-pre-condensation.md#completed-execution-guided-terra-and-sonnet-trial).

### T1 — Corrigir os dois defeitos textuais encontrados

**Estado:** decidido

**Decisão:** fazer as duas correções pontuais descritas neste item: limitar o gatilho de criação
dos arquivos de compatibilidade na `documentation` ao escopo autorizado e esclarecer no template
da `architecture-records` onde ficam as garantias preservadas. Registrada no
[plano de implementação](../history/decision-to-architecture-flow-pre-condensation.md#completed-execution-t1-corrections-and-t2-deferral),
dono do escopo e da sequência de execução. As skills são os alvos da mudança. A execução foi
autorizada; as duas correções estão concluídas, com revisão prévia, verificações focadas e
conferência independente do resultado. As evidências e seus limites estão no plano.

**A pergunta para você:** fazer as duas correções pontuais, não fazer ou adiar.

**O que foi corrigido:** os textos identificados na
[revisão das skills](../history/decision-to-architecture-flow-pre-condensation.md#skill-source-review):

- Na `documentation`, a obrigação de criar arquivos de compatibilidade ficou limitada aos
  trabalhos autorizados que tratam dessas instruções. Antes, a simples presença de um arquivo
  de instruções na raiz disparava a regra até numa revisão somente leitura, embora a autorização
  superior continuasse proibindo a escrita.
- No template da `architecture-records`, o texto agora manda preservar as regras nas seções
  normativas apropriadas e esclarece que excluir uma mudança não exclui as garantias existentes.
  Antes, a palavra “aqui”, dentro de Non-goals, deixava sua localização ambígua.

**Por que importa:** remove uma obrigação com alcance excessivo e uma ambiguidade confirmada.
Por exemplo, revisar um documento não deve, por essa regra, virar uma tarefa de configurar
instruções para três clientes. A correção do template também evita que uma regra preservada
pareça pertencer ao que o novo registro exclui.

**O que acontece em cada resposta:**

- **Fazer:** registrar o escopo no plano, obter a revisão exigida e aplicar as duas correções,
  conferindo suas relações com as outras skills e os critérios existentes.
- **Não fazer:** conservar os textos e registrar o motivo. Os achados continuam conhecidos;
  essa escolha, sozinha, não aprova as skills nem dispensa a avaliação de fechamento.
- **Adiar:** manter os achados pendentes e preservar a versão atual; não declarar as correções
  concluídas enquanto não houver uma decisão posterior.

**Custo e risco:** alterações localizadas em dois arquivos, com revisão e verificações focadas.
O principal risco é mudar sem querer o alcance das autorizações ou das garantias; a revisão deve
conferir exatamente esses limites. Não há estimativa monetária de novas rodadas nesta proposta.

**Recomendação:** fazer. São defeitos identificáveis no texto, independentemente de qual modelo
teve melhor resposta. Sua correção não deve ser apresentada como solução já comprovada para a
falha de transição dos testes.

### T2 — Reorganizar agora as skills para separar as fases do trabalho

**Estado:** decidido

**Decisão:** adiar a reorganização ampla das skills. Reconsiderá-la depois de tratar T1 e obter
informação útil sobre a falha de transição, conforme a opção de adiamento deste item.
Registrada no
[plano de implementação](../history/decision-to-architecture-flow-pre-condensation.md#completed-execution-t1-corrections-and-t2-deferral),
dono do escopo e da sequência de execução. A reorganização ampla permanece adiada.

**A pergunta para você:** fazer a reorganização ampla agora, não fazer ou adiar.

**O que é:** separar com mais clareza as instruções de analisar uma decisão, registrá-la,
implementar a mudança e fechar o trabalho; reduzir regras repetidas entre as skills. Hoje, uma
lista comum exige descontar várias exceções para descobrir quais conferências valem naquela fase.

**Por que importa:** pode reduzir o esforço de compreensão e manutenção. Porém, ainda não foi
demonstrado que essa organização causou a falha do Sonnet. Mudar muitos trechos ao mesmo tempo
também dificulta saber qual alteração melhorou ou piorou o comportamento.

**O que acontece em cada resposta:**

- **Fazer:** preparar uma proposta separada, com correspondência entre cada regra antiga e sua
  posição nova, revisão independente e validação das fases afetadas antes de alegar melhora.
- **Não fazer:** manter a organização atual; continuar com as correções pontuais e as obrigações
  de validação já aprovadas, conforme suas decisões sobre elas.
- **Adiar:** reconsiderar depois de tratar T1 e obter informação útil sobre a falha de transição,
  sem transformar uma hipótese de usabilidade em uma reformulação obrigatória agora.

**Custo e risco:** maior que T1, porque afeta vários textos e suas relações. Pode introduzir
contradições ou retirar uma exigência aprovada durante a simplificação; também exige mais revisão
e validação. O tamanho, por si só, não prova que a skill esteja errada.

**Recomendação:** adiar a reorganização ampla. Manter esta proposta separada das correções
pontuais permite avaliar cada mudança e preserva todos os critérios atuais. T2 não é uma nova
exigência obrigatória para encerrar o plano existente.

## Depende de outra sessão

### E4 — Concluir a conferência pontual bloqueada pela cota do Sol

**Estado:** resolvido — parecer recebido e ressalvas tratadas no registro da avaliação.
O identificador E3 já foi usado e resolvido no brief anterior, por isso não é reutilizado.

**Rota escolhida:** após a recomendação explícita de usar Opus high, você instruiu continuar.
A troca de revisor foi registrada no
[plano](../history/decision-to-architecture-flow-pre-condensation.md#independent-extraction-gate-results-and-limits).
Não há registro pendente. O Opus 5/high concluiu a conferência e emitiu `SUPPORTED`, sem
achado impeditivo. Após uma complementação para carregar três skills que havia omitido, manteve
o parecer. Registrei essa falha de procedimento e as nove ressalvas sobre a avaliação no
[resultado da revisão](../history/decision-to-architecture-flow-pre-condensation.md#independent-result-conformance-completed).

**O que foi conferido:** minha avaliação do teste de extração. O teste já terminou:
a revisão bloqueou a saída defeituosa do Sonnet e os três controles errados, e aceitou o controle
completo. O pacote contém as fontes, respostas, critérios, evidências e minha discordância de
uma justificativa adicional. A cota interrompeu a conferência desse pacote pelo Sol xhigh.

**Resultado e limite:** os cinco resultados e a preservação das evidências foram confirmados.
Os controles errados tratam todos da mesma garantia; não demonstram que a conferência detectará
qualquer erro ou evitará rejeições excessivas. O teste e o revisor omitiram leituras obrigatórias,
e a complementação não apaga essas falhas. Nenhum resultado anterior foi corrigido ou repetido.
Isso conclui apenas a avaliação desta rodada; a validação do fluxo completo e E2 continuam
pendentes. A revisão foi somente leitura e o custo monetário não foi medido.

### E2 — Receber a auditoria independente da versão final

**Estado:** aberto — mesma dependência do brief anterior, sem nova autorização solicitada.

**O que é, em termos práticos:** depois de terminar as correções, obter a validação exigida e
conferir meu próprio trabalho, outra sessão de IA lê os arquivos finais e os resultados. Ela
verifica se o que foi entregue realmente cumpre o que você decidiu e o que o plano exige.
Sua entrega é um parecer com os problemas encontrados, ou a confirmação de que não encontrou
pendências obrigatórias.

**Exemplo:** o registro diz que mensagens descartadas precisam permitir o avanço da fila, mas o
plano manda retirar a proteção antiga antes de validar quem fará essa confirmação no lugar dela.
O revisor deve apontar essa lacuna, mesmo que os arquivos estejam bem escritos e os verificadores
de formatação tenham passado.

**Por que outra sessão:** esta sessão escreveu alterações e avaliou os testes. Posso e devo
conferir tudo novamente, mas isso é a auditoria do autor. A revisão independente precisa de um
contexto novo, para reduzir a chance de repetir as mesmas suposições. As revisões anteriores
examinaram propostas ou experimentos; o E2 examina o conjunto final entregue.

**O que você terá de fazer:** quando o trabalho estiver pronto para essa etapa, eu preparo um
prompt completo com o plano, os arquivos e as evidências. Pela rota atual, você abre uma conversa
nova de revisão, cola esse prompt e depois traz o parecer para cá. O revisor apenas lê e relata;
eu trato os achados que precisarem de correção. Você não precisa redigir o pedido técnico.
Essa rota já está registrada em
[E2 no brief anterior](decision-to-architecture-flow.md#e2--receber-a-auditoria-independente-de-fechamento-após-as-rodadas).

**Quando fazer:** depois das correções, da validação exigida e da minha auditoria. Essas etapas
incluem T1, agora concluído, mas a validação do fluxo completo e a auditoria final do autor ainda
estão pendentes. Não é necessário abrir outra sessão agora.

**O que encerra E2:** receber o parecer final independente e resolver os achados obrigatórios.
Se houver correções, revalidar o que elas afetarem e obter a conferência final exigida pelo plano.
Receber um parecer que reprova o trabalho não basta para fechar esta dependência.

**O que bloqueia:** declarar o plano concluído e movê-lo para a pasta de trabalhos concluídos.
As correções e os testes anteriores a essa revisão continuam sendo trabalho a realizar.

## Sem ação necessária agora

- As decisões anteriores continuam registradas. Criar este briefing não altera nem reabre essas
  escolhas, inclusive D20.2 e a autorização de testes D24.
- O recebimento do Sonnet e a abertura do Claude interativo já foram resolvidos. Isso não
  converte suas tentativas reprovadas em aprovação.
- A comparação solicitada com Terra, Sol e Opus terminou. Nova rodada precisa ter finalidade
  definida dentro da autorização existente; não há repetição automática deste diagnóstico.
- O brief anterior permanece como referência das decisões. As atualizações da discussão passam
  a ocorrer aqui; o plano continua sendo o mesmo.
