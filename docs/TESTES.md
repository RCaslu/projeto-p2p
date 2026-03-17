# Guia de testes – P2P com Balanceamento de Carga Dinâmico

Este documento descreve como rodar o projeto e executar testes automatizados e manuais para validar o sistema.

---

## 1. Pré-requisitos

- Python 3.9+ (recomendado 3.11+)
- Terminal com acesso à linha de comando

### 1.1. Ambiente virtual e dependências

No diretório raiz do projeto:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

No Windows:

```bash
.venv\Scripts\activate
pip install -r requirements.txt
```

---

## 2. Testes automatizados (pytest)

Os testes não exigem processos em execução; usam a aplicação via ASGI.

### 2.1. Executar todos os testes

```bash
pytest
```

Ou com saída detalhada:

```bash
pytest -v
```

### 2.2. Opções úteis

| Comando | Descrição |
|---------|-----------|
| `pytest tests/` | Roda apenas a pasta `tests/` |
| `pytest tests/test_protocol.py` | Roda só os testes de protocolo |
| `pytest tests/test_master.py` | Roda só os testes do Master |
| `pytest -v -k "heartbeat"` | Roda testes cujo nome contém "heartbeat" |
| `pytest --tb=short` | Exibe tracebacks resumidos em falhas |

### 2.3. O que cada arquivo testa

- **tests/test_protocol.py**  
  Modelos do protocolo (Pydantic): serialização de HEARTBEAT, REGISTER, HELP_REQUEST, HELP_OFFER, HELP_ACCEPT e payloads de tarefa (sleep/compute). Garante que os payloads oficiais estão corretos.

- **tests/test_master.py**  
  API do Master via cliente HTTP (ASGITransport):
  - **GET /info** – retorna SERVER_UUID
  - **POST /heartbeat** – request HEARTBEAT e resposta ALIVE
  - **POST /workers/register** – registro de Worker
  - **POST /tasks** – submissão de tarefa e retorno de task_id
  - **GET /metrics** – pending_count, threshold, workers_count, worker_ids
  - **POST /help/request** – pedido de ajuda e resposta HELP_OFFER

### 2.4. Resultado esperado

Ao final, deve aparecer algo como:

```
============================== 14 passed in 0.03s ==============================
```

Se algum teste falhar, o pytest mostra o nome do teste, o assert que falhou e o traceback.

---

## 3. Testes manuais e de integração

Para validar o sistema com processos reais (Master, Worker, simulador), use terminais separados.

### 3.1. Cenário 1: Apenas o Master

Objetivo: validar que o Master sobe e responde.

1. No terminal 1:

```bash
source .venv/bin/activate
uvicorn src.master.app:app --host 127.0.0.1 --port 8000
```

2. Em outro terminal (com o venv ativado):

```bash
curl http://127.0.0.1:8000/info
curl http://127.0.0.1:8000/metrics
```

Esperado: JSON com `SERVER_UUID` em `/info` e em `/metrics` campos `pending_count`, `threshold`, `workers_count`, `worker_ids`.

### 3.2. Cenário 2: Master + um Worker

Objetivo: Worker registra no Master e Master envia tarefas.

1. Subir o Master (terminal 1):

```bash
uvicorn src.master.app:app --host 127.0.0.1 --port 8000
```

2. Subir um Worker (terminal 2):

```bash
python -m src.worker.main --master-url http://127.0.0.1:8000 --port 8001
```

3. Verificar registro (terminal 3):

```bash
curl http://127.0.0.1:8000/metrics
```

Esperado: `workers_count` >= 1 e `worker_ids` não vazio.

4. Enviar uma tarefa:

```bash
curl -X POST http://127.0.0.1:8000/tasks -H "Content-Type: application/json" -d '{"type":"sleep","seconds":0}'
```

Esperado: resposta com `task_id`. Em seguida, conferir `/metrics`: o `pending_count` pode subir e depois baixar quando o Worker processar.

### 3.3. Cenário 3: Master + Worker + simulador de carga

Objetivo: simular várias requisições e observar distribuição e métricas.

1. Master no terminal 1 (como acima).
2. Worker no terminal 2 (como acima).
3. No terminal 3, rodar o simulador por alguns segundos:

```bash
python -m src.simulator.main --master-url http://127.0.0.1:8000 --rps 3 --duration 15
```

4. Durante a execução ou depois, consultar:

```bash
curl http://127.0.0.1:8000/metrics
```

Esperado: tarefas sendo processadas; `pending_count` e `worker_ids` coerentes com a carga.

### 3.4. Cenário 4: Dois Masters e empréstimo de Workers (consenso)

Objetivo: Master A saturado pede ajuda ao Master B; B cede Worker(s) a A.

1. Terminal 1 – Master A (porta 8000, vizinho = B):

```bash
THRESHOLD=3 NEIGHBOR_MASTERS=http://127.0.0.1:8002 MASTER_HOST=127.0.0.1 MASTER_PORT=8000 \
  uvicorn src.master.app:app --host 127.0.0.1 --port 8000
```

2. Terminal 2 – Master B (porta 8002):

```bash
THRESHOLD=3 MASTER_HOST=127.0.0.1 MASTER_PORT=8002 \
  uvicorn src.master.app:app --host 127.0.0.1 --port 8002
```

3. Terminal 3 – Worker 1 (registra em A):

```bash
python -m src.worker.main --master-url http://127.0.0.1:8000 --port 8001
```

4. Terminal 4 – Worker 2 (registra em B):

```bash
python -m src.worker.main --master-url http://127.0.0.1:8002 --port 8003
```

5. Terminal 5 – Simulador contra Master A para saturar:

```bash
python -m src.simulator.main --master-url http://127.0.0.1:8000 --rps 5 --duration 20
```

6. Verificar métricas dos dois Masters:

```bash
curl http://127.0.0.1:8000/metrics
curl http://127.0.0.1:8002/metrics
```

Esperado: quando A ficar acima do threshold (3), ele envia HELP_REQUEST a B; B responde HELP_OFFER; A envia HELP_ACCEPT; B envia REDIRECT ao Worker 2; Worker 2 passa a se registrar em A. Assim, em `/metrics` de A pode aparecer mais de um worker (próprio + emprestado).

---

## 4. Ordem recomendada para validar

1. Rodar **pytest** e garantir que os 14 testes passem.
2. Executar **Cenário 1** (só Master) e validar `/info` e `/metrics`.
3. Executar **Cenário 2** (Master + Worker), registrar Worker e enviar uma tarefa.
4. Executar **Cenário 3** (simulador) e observar carga e métricas.
5. (Opcional) Executar **Cenário 4** para validar o protocolo consensual e o redirecionamento de Workers.

---

## 5. Solução de problemas

- **"Address already in use"**  
  Outro processo está usando a porta. Troque a porta (ex.: 8000 → 8010) ou encerre o processo que a utiliza.

- **Worker não aparece em /metrics**  
  Confirme que o Master está em 127.0.0.1:8000 e que o Worker foi iniciado com `--master-url http://127.0.0.1:8000`. O Worker obtém SERVER_UUID via GET /info antes de registrar.

- **Testes falham com "MasterState not initialized"**  
  Os testes usam `Depends(get_state)` que lê `request.app.state.master_state`. Esse state é definido ao carregar o módulo do Master. Não é necessário subir o servidor para os testes; basta rodar `pytest` no diretório do projeto com o venv ativado.

- **Módulo ou import não encontrado**  
  Execute os comandos a partir da **raiz do projeto** (onde está `src/` e `requirements.txt`) e com o ambiente virtual ativado.

---

## 6. Resumo dos comandos

| Ação | Comando |
|------|---------|
| Instalar dependências | `pip install -r requirements.txt` |
| Rodar testes automatizados | `pytest` ou `pytest -v` |
| Iniciar Master | `uvicorn src.master.app:app --host 127.0.0.1 --port 8000` |
| Iniciar Worker | `python -m src.worker.main --master-url http://127.0.0.1:8000 --port 8001` |
| Rodar simulador | `python -m src.simulator.main --master-url http://127.0.0.1:8000 --rps 5 --duration 60` |
| Consultar métricas | `curl http://127.0.0.1:8000/metrics` |
