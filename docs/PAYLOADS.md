# Payloads oficiais do protocolo

Todos os payloads são JSON. Campos em maiúsculas são obrigatórios na especificação.

## HEARTBEAT (oficial do plano do professor)

### 1.1 Worker → Servidor (Worker pergunta se o Servidor está ativo)

```json
{
  "SERVER_UUID": "<uuid do Master>",
  "TASK": "HEARTBEAT"
}
```

### 1.2 Servidor → Worker (Servidor responde que está ativo)

```json
{
  "SERVER_UUID": "<uuid do Master>",
  "TASK": "HEARTBEAT",
  "RESPONSE": "ALIVE"
}
```

## REGISTER (Worker → Master)

```json
{
  "SERVER_UUID": "<uuid do Master alvo>",
  "TASK": "REGISTER",
  "WORKER_ID": "<id único do Worker>",
  "HOST": "<host do Worker>",
  "PORT": <porta do Worker>
}
```

Resposta de sucesso (Master → Worker):

```json
{
  "SERVER_UUID": "<uuid do Master>",
  "TASK": "REGISTER",
  "RESPONSE": "OK",
  "WORKER_ID": "<id confirmado>"
}
```

## TASK_REQUEST (Master → Worker)

```json
{
  "SERVER_UUID": "<uuid do Master>",
  "TASK": "TASK_REQUEST",
  "TASK_ID": "<id da tarefa>",
  "PAYLOAD": { "type": "sleep", "seconds": 1 }
}
```

Tipos de payload de tarefa (exemplos): `{"type": "sleep", "seconds": N}`, `{"type": "compute", "expression": "..."}`.

## TASK_RESULT (Worker → Master)

```json
{
  "SERVER_UUID": "<uuid do Master>",
  "TASK": "TASK_RESULT",
  "TASK_ID": "<id da tarefa>",
  "RESULT": "<resultado ou status>"
}
```

## REDIRECT (Master → Worker)

```json
{
  "SERVER_UUID": "<uuid do Master que ordena>",
  "TASK": "REDIRECT",
  "TARGET_MASTER_HOST": "<host do novo Master>",
  "TARGET_MASTER_PORT": <porta>,
  "TARGET_MASTER_UUID": "<uuid do novo Master>"
}
```

## HELP_REQUEST (Master → Master)

```json
{
  "SERVER_UUID": "<uuid do Master saturado>",
  "TASK": "HELP_REQUEST",
  "PENDING_COUNT": <número de requisições pendentes>,
  "THRESHOLD": <threshold configurado>
}
```

## HELP_OFFER (Master → Master)

```json
{
  "SERVER_UUID": "<uuid do Master que oferece>",
  "TASK": "HELP_OFFER",
  "AVAILABLE_WORKERS": <número ou lista de Worker IDs>,
  "OFFER_COUNT": <quantidade que pode ceder>
}
```

## HELP_ACCEPT (Master → Master)

O Master que aceita (saturado) envia ao doador. REQUESTER_HOST e REQUESTER_PORT permitem ao doador saber para onde redirecionar os Workers.

```json
{
  "SERVER_UUID": "<uuid do Master que aceita (saturado)>",
  "TASK": "HELP_ACCEPT",
  "REQUESTER_UUID": "<uuid do Master que receberá os Workers>",
  "REQUESTER_HOST": "<host do Master receptor>",
  "REQUESTER_PORT": <porta do Master receptor>,
  "ACCEPTED_COUNT": <quantidade aceita>,
  "WORKER_IDS": ["<id1>", "<id2>"]
}
```

## WORKER_RETURN (devolução de Worker)

Master receptor ou Worker informa devolução:

```json
{
  "SERVER_UUID": "<uuid do Master atual do Worker>",
  "TASK": "WORKER_RETURN",
  "WORKER_ID": "<id do Worker>",
  "ORIGINAL_MASTER_UUID": "<uuid do Master original>"
}
```
