# Protocolo de Comunicação P2P

## Canal e regras gerais

- **Canal**: API REST (FastAPI) para clientes, registro de Workers, tarefas e protocolo Master–Master. Opcionalmente TCP com JSON por linha para streams (Message Delimiter `\n`).
- **Formato**: JSON em todos os payloads.
- **Message Delimiter (TCP)**: Se usar stream TCP, cada mensagem JSON deve terminar com `\n`. O receptor lê até `\n` e faz parse do JSON.
- **Identificação**: `SERVER_UUID` identifica o Master em todas as mensagens; Workers e Masters vizinhos usam esse identificador para roteamento.

## Lista de TASK (tipos de mensagem)

| TASK | Direção | Descrição |
|------|---------|-----------|
| HEARTBEAT | Worker → Master | Worker pergunta se o Master está ativo |
| HEARTBEAT | Master → Worker | Resposta ALIVE |
| REGISTER | Worker → Master | Worker solicita registro na Farm |
| TASK_REQUEST | Master → Worker | Atribuição de tarefa ao Worker |
| TASK_RESULT | Worker → Master | Resultado da execução da tarefa |
| REDIRECT | Master → Worker | Ordem para se reportar a outro Master |
| HELP_REQUEST | Master → Master | Pedido de ajuda (saturação) |
| HELP_OFFER | Master → Master | Oferta de Workers disponíveis |
| HELP_ACCEPT | Master → Master | Aceite da oferta e confirmação |
| WORKER_RETURN | Master → Master / Worker | Devolução de Worker ao Master original |

## Fluxos

### Heartbeat Worker ↔ Master

1. Worker envia HEARTBEAT (payload 1.1) ao Master periodicamente.
2. Master responde HEARTBEAT com RESPONSE: "ALIVE" (payload 1.2).
3. Se o Worker não receber resposta em tempo hábil, pode considerar o Master indisponível.

### Registro de Worker

1. Worker envia REGISTER ao Master (SERVER_UUID, WORKER_ID, endpoint/host/porta).
2. Master responde com sucesso e inclui o Worker na Farm (próprios ou emprestados).

### Atribuição e resultado de tarefa

1. Master envia TASK_REQUEST ao Worker (task_id, payload da tarefa, ex.: tipo + parâmetros).
2. Worker executa (ex.: cálculo, sleep) e envia TASK_RESULT ao Master (task_id, resultado).

### Protocolo de conversa consensual Master–Master

1. **Pedido de ajuda**: Master saturado envia HELP_REQUEST aos Masters vizinhos (lista configurável), informando SERVER_UUID e carga atual.
2. **Oferta**: Master vizinho responde HELP_OFFER com quantidade (ou lista) de Workers que pode ceder.
3. **Aceite**: Master saturado envia HELP_ACCEPT ao vizinho escolhido (quantidade/identificadores dos Workers desejados).
4. **Coordenação**: Master que cede envia REDIRECT a cada Worker, informando host/porta (ou SERVER_UUID) do Master receptor. Workers se desregistram e se registram no novo Master.
5. **Devolução** (opcional): Quando a carga do Master receptor normalizar, ele pode enviar WORKER_RETURN ao Worker ou ao Master original para o Worker voltar.

### Redirecionamento de Worker

1. Master A (doador) envia REDIRECT ao Worker com dados do Master B (receptor): host, porta, SERVER_UUID.
2. Worker envia desregistro ao Master A (se aplicável).
3. Worker registra-se no Master B e passa a enviar HEARTBEAT e receber TASK_REQUEST apenas de B.
4. Quando B devolver o Worker, este recebe REDIRECT ou WORKER_RETURN de volta para A e repete o processo em sentido inverso.
