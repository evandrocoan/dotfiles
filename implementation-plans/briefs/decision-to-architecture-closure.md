# Brief de discussão: correções e fechamento das skills de arquitetura

**Estado:** em discussão

**Alimenta:**

- [plano de implementação existente](../active/decision-to-architecture-flow.md).

Documento de trabalho em português. Explica o que ainda precisa ser resolvido; não substitui o
plano nem autoriza execução. As escolhas e autorizações anteriores continuam no
[brief preservado](decision-to-architecture-flow.md). Este passa a ser o documento de discussão
atual, conforme seu pedido de um briefing novo. A dependência E2 conserva seu identificador.

## Resumo

Situação conferida em **22/09/2026**: a revisão das quatro skills centrais e a comparação de modelos
terminaram. Foram encontrados dois defeitos textuais e riscos de compreensão por repetição e
excesso de exceções. A regra de preservar garantias existentes já é explícita.

Terra xhigh, Sol high e Opus high preservaram a obrigação de confirmação/avanço que o Sonnet havia
perdido na tentativa anterior. Nenhum passou em todos os critérios. Esses exercícios pediam uma
tabela de análise; não aprovaram o fluxo completo de escrever o registro, derivar o plano e
atualizar o brief. Os [resultados e limites](../active/decision-to-architecture-flow.md#comparative-extraction-results)
permanecem no plano, sem repetir seu histórico aqui.

Há **um item aberto**: E2, sobre a auditoria independente final. **T1 foi decidido: fazer as duas
correções pontuais. T2 foi decidido: adiar a reorganização ampla.** As duas decisões foram
[registradas no plano](../active/decision-to-architecture-flow.md#current-execution-t1-corrections-and-t2-deferral),
sem registro pendente. **T1 foi executado**: as duas correções passaram pela revisão prévia, pelas
verificações focadas e pela conferência independente do resultado com Sol xhigh. Isso conclui as
correções textuais, sem aprovar o fluxo completo dos modelos. A reorganização ampla continua
adiada; as decisões anteriores continuam registradas.

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

Nos rastros do Codex, o corpo inicial da tarefa permanece criptografado. O texto enviado e a
correspondência entre os rastros foram preservados, mas sua entrega em texto claro segue não
verificada. Essa limitação de evidência também precisa ser resolvida para qualquer critério que
a exija; não vira aprovação por causa de uma resposta correta.

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

### T1 — Corrigir os dois defeitos textuais encontrados

**Estado:** decidido

**Decisão:** fazer as duas correções pontuais descritas neste item: limitar o gatilho de criação
dos arquivos de compatibilidade na `documentation` ao escopo autorizado e esclarecer no template
da `architecture-records` onde ficam as garantias preservadas. Registrada no
[plano de implementação](../active/decision-to-architecture-flow.md#current-execution-t1-corrections-and-t2-deferral),
dono do escopo e da sequência de execução. As skills são os alvos da mudança. A execução foi
autorizada; as duas correções estão concluídas, com revisão prévia, verificações focadas e
conferência independente do resultado. As evidências e seus limites estão no plano.

**A pergunta para você:** fazer as duas correções pontuais, não fazer ou adiar.

**O que foi corrigido:** os textos identificados na
[revisão das skills](../active/decision-to-architecture-flow.md#skill-source-review):

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
[plano de implementação](../active/decision-to-architecture-flow.md#current-execution-t1-corrections-and-t2-deferral),
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
