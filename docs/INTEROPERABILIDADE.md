# Interoperabilidade com outras equipes

Para que o sistema de outra equipe interopere com este, basta implementar o protocolo descrito em [PROTOCOLO.md](PROTOCOLO.md) e [PAYLOADS.md](PAYLOADS.md). Não é necessário conhecer a implementação interna.

## O que o Master deve expor

- **GET /info** – Retorno: `{"SERVER_UUID": "<uuid>"}`.
- **POST /heartbeat** – Body: `{"SERVER_UUID": "...", "TASK": "HEARTBEAT"}`. Resposta: `{"SERVER_UUID": "...", "TASK": "HEARTBEAT", "RESPONSE": "ALIVE"}`.
- **POST /workers/register** – Body: `{"SERVER_UUID": "...", "TASK": "REGISTER", "WORKER_ID": "...", "HOST": "...", "PORT": N}`. Resposta: `{"SERVER_UUID": "...", "TASK": "REGISTER", "RESPONSE": "OK", "WORKER_ID": "..."}`.
- **POST /help/request** – Body: HelpRequest (SERVER_UUID, TASK, PENDING_COUNT, THRESHOLD). Resposta: HelpOffer (SERVER_UUID, TASK, AVAILABLE_WORKERS, OFFER_COUNT, WORKER_IDS).
- **POST /help/accept** – Body: HelpAccept (incluindo REQUESTER_UUID, REQUESTER_HOST, REQUESTER_PORT, WORKER_IDS). O doador deve enviar REDIRECT a cada Worker em WORKER_IDS para o endereço REQUESTER_HOST:REQUESTER_PORT.

## O que o Worker deve expor

- **POST /execute** – Body: TaskRequest (SERVER_UUID, TASK, TASK_ID, PAYLOAD com type "sleep" ou "compute", seconds/expression). Resposta: TaskResult (SERVER_UUID, TASK, TASK_ID, RESULT).
- **POST /redirect** – Body: RedirectCommand (TARGET_MASTER_HOST, TARGET_MASTER_PORT, TARGET_MASTER_UUID). O Worker deve desregistrar do Master atual e registrar-se no novo Master nesse endereço.

## Fluxo que a outra equipe deve implementar

1. Worker obtém SERVER_UUID via GET /info do Master e regista-se com POST /workers/register.
2. Worker envia HEARTBEAT periódico ao Master (POST /heartbeat).
3. Master envia tarefas ao Worker via POST no endpoint /execute do Worker (HOST:PORT do registro).
4. Quando o Master doador recebe POST /help/accept, envia POST /redirect a cada Worker listado, com o endereço do Master receptor (REQUESTER_HOST, REQUESTER_PORT, REQUESTER_UUID).
5. Worker ao receber REDIRECT passa a usar o novo Master (registro e heartbeat no novo endereço).

Respeitando esses payloads e fluxos, qualquer implementação (outra linguagem ou framework) pode interconectar-se com esta.
