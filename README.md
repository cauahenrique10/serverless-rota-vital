# Atividade individual 1 · Serverless (Rota Vital)

Infraestrutura de Software · ADS · CESAR School · 2026.2
Aluno: **<Cauã Henrique Melo Almeida>**

Função serverless que gera a guia de transporte de uma requisição do Rota Vital,
acionada por evento (`sam local invoke`) e por HTTP (`sam local start-api`).

## Caminho escolhido

**Caminho A: AWS SAM CLI local** (Docker + SAM CLI + Python 3.12), sem conta na AWS.

## Estrutura

```
template.yaml        # API POST /guias + Timeout em Globals
hello_world/app.py   # handler (lê o body, devolve a guia)
events/pedido.json   # evento gerado com sam local generate-event
events/demorar.json  # evento com "demorar": true (Passo 5)
evidencias/          # prints dos comandos e saídas
```

## Como rodar

```bash
sam --version
sam build

# Passo 3: invocação com evento (rodar 2x e anotar o tempo)
sam local invoke -e events/pedido.json

# Passo 4: HTTP
sam local start-api
curl -X POST http://127.0.0.1:3000/guias -H "Content-Type: application/json" \
  -d '{"requisicaoId":"R-002","hospital":"H-Caruaru"}'

# Passo 4 (parte 2): reaproveitando o ambiente
sam local start-api --warm-containers LAZY

# Passo 5: limite de tempo
curl -X POST http://127.0.0.1:3000/guias -H "Content-Type: application/json" \
  -d '{"requisicaoId":"R-003","demorar":true}'
# depois: Timeout 3 -> 10 em template.yaml, sam build e repetir
```

No Windows usei Git Bash / WSL.

## Medições

| Experimento | Resultado |
|---|---|
| `sam local invoke` #1 | 2.14 s |
| `sam local invoke` #2 | 1.18 s |
| `start-api` sem `--warm-containers`, 3 chamadas | invocacaoNesteAmbiente = 1, 1, 1 |
| `start-api --warm-containers LAZY`, 3 chamadas | invocacaoNesteAmbiente = 1, 2, 3 |
| `demorar: true` com Timeout 3 | HTTP 502 Bad Gateway (Function 'GuiaFunction' timed out after 3.00 seconds) |
| `demorar: true` com Timeout 10 | HTTP 201 Created (tempo: 5.08 s) |

## Respostas

**1. Por que a primeira invocação demorou mais que a segunda? O que acontece na fase de Init?**

Na primeira chamada não existe ambiente de execução pronto (cold start). O Lambda
precisa criar o ambiente (no SAM local, subir um container Docker), carregar o código,
iniciar o runtime do Python e executar o código que fica fora do handler (os `import`
e a criação da variável global `contador = 0`). Essas etapas formam a fase de Init e
só depois o `lambda_handler` roda. Em uma chamada seguinte, se o ambiente for
reaproveitado (warm), o Init é pulado e só o handler executa, por isso é mais rápida.
Obs.: o `sam local invoke` cria um container novo a cada execução, então as duas
invocações tendem a ter custo parecido; o ganho de reaproveitamento aparece
com `start-api --warm-containers`.

**2. O que `invocacaoNesteAmbiente` mostrou com e sem `--warm-containers`?**

Sem a flag, cada requisição usou um container novo e o campo veio sempre `1`
(o contador reinicia). Com `--warm-containers LAZY`, o container foi reaproveitado
e o valor cresceu (`1, 2, 3`). Conclusão: a variável global só sobrevive enquanto o
mesmo ambiente de execução continuar vivo, e isso não é garantido: o provedor pode
descartar o ambiente a qualquer momento, e requisições simultâneas usam ambientes
diferentes, cada um com seu contador. Portanto não se deve guardar estado importante
em variável global; ele deve ficar em um serviço externo (DynamoDB, S3, banco de dados).
Variável global serve no máximo como cache descartável.

**3. O que aconteceu com `demorar = true`? Qual o tempo máximo de uma execução no Lambda?**

A função dorme 5 s, mas o Timeout do template era 3 s; a plataforma interrompeu a
execução e devolveu erro de timeout (no `start-api`, o cliente recebe erro 5xx/502 e
o log mostra que a função excedeu 3 segundos). Com Timeout = 10 a função terminou e
respondeu 201 após ~5 s. No Lambda de verdade o tempo máximo por execução é de
**15 minutos (900 s)**. Trabalho mais longo deve ser quebrado em etapas menores
(Step Functions, filas SQS) ou movido para um serviço sem esse limite, como
containers (ECS/Fargate) ou AWS Batch.

**4. Custo de 1 milhão de execuções com 128 MB e 100 ms (us-east-1)**

- Requisições: 1.000.000 × US$ 0,20 / 1.000.000 = **US$ 0,20**
- Computação: 128 MB = 0,125 GB; 0,125 GB × 0,1 s = 0,0125 GB-s por execução
  → 1.000.000 × 0,0125 = 12.500 GB-s
  → 12.500 × US$ 0,0000166667 = **US$ 0,2083**
- **Total ≈ US$ 0,41** por milhão de execuções (sem considerar a faixa gratuita,
  que cobriria esse volume inteiro).

**5. Em que parte do Rota Vital uma função assim faria sentido, e em qual não?**

Faz sentido em tarefas curtas, sem estado e disparadas por evento ou requisição, com
demanda irregular: gerar a guia de transporte quando uma requisição de hemocomponentes
é criada, validar o pedido, enviar notificação ao hospital quando a guia é emitida.
Paga-se só quando há pedido e escala sozinha em picos.
Não faz sentido onde há processo longo ou contínuo (acima de 15 min), conexões
persistentes ou estado em memória, como o rastreamento em tempo real do veículo
durante o transporte, ou o banco de dados principal do estoque de bolsas, que
precisa ser um serviço persistente.

## Uso de IA

- **Ferramenta:** Claude (Anthropic).
- **Finalidade:** apoio para montar a estrutura do projeto, rascunhar o README e
  conferir a conta de custo.
- **Como validei:** executei os comandos no meu computador, conferi as saídas e
  medições reais (evidências na pasta `evidencias/`), reli e ajustei as respostas
  com o que observei e refiz a conta de custo à mão. (Declaração conforme PO-CESAR-021.)
