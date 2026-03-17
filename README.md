# P2P com Balanceamento de Carga Dinâmico

Sistema distribuído autônomo que demonstra balanceamento de carga horizontal em arquitetura P2P. Cada nó Master gerencia uma Farm de Workers; ao atingir saturação (requisições pendentes acima do threshold), negocia com Masters vizinhos o empréstimo de Workers via protocolo de conversa consensual.

## Documentação

- [Protocolo de comunicação](docs/PROTOCOLO.md) – canal, TASKs e fluxos
- [Arquitetura](docs/ARQUITETURA.md) – visão geral e diagramas
- [Payloads](docs/PAYLOADS.md) – mensagens JSON oficiais
- [Guia de testes](docs/TESTES.md) – como rodar o projeto e executar testes automatizados e manuais

## Requisitos

- Python 3.11+
- Dependências: ver `requirements.txt`

## Instalação

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Variáveis de ambiente

| Variável | Descrição | Exemplo |
|----------|-----------|---------|
| `MASTER_HOST` | Host do Master | `0.0.0.0` |
| `MASTER_PORT` | Porta do Master | `8000` |
| `WORKER_HOST` | Host do Worker | `0.0.0.0` |
| `WORKER_PORT` | Porta do Worker | `8001` |
| `THRESHOLD` | Limite de requisições pendentes para saturação | `10` |
| `NEIGHBOR_MASTERS` | Lista de Masters vizinhos (URLs separadas por vírgula) | `http://localhost:8002` |
| `SERVER_UUID` | UUID do Master (gerado automaticamente se omitido) | opcional |

## Execução

### Master

```bash
uvicorn src.master.app:app --host 0.0.0.0 --port 8000
```

Ou com variáveis:

```bash
THRESHOLD=10 NEIGHBOR_MASTERS=http://localhost:8002 uvicorn src.master.app:app --host 0.0.0.0 --port 8000
```

### Worker

O Worker precisa do endereço do Master para se registrar:

```bash
python -m src.worker.main --master-url http://localhost:8000 --port 8001
```

### Simulador de carga

Envia requisições ao Master em intervalos configuráveis:

```bash
python -m src.simulator.main --master-url http://localhost:8000 --rps 5 --duration 60
```

- `--master-url`: URL base do Master
- `--rps`: requisições por segundo (default 5)
- `--duration`: duração em segundos (default 60; 0 = infinito)

### Métricas do Master

- `GET /metrics` – retorna requisições pendentes, threshold e estado da Farm (para inspeção de carga e saturação).

## Estrutura do projeto

```
projeto-p2p/
├── docs/
├── src/
│   ├── master/
│   ├── worker/
│   ├── protocol/
│   └── simulator/
├── tests/
├── requirements.txt
└── README.md
```

## Testes

Instale as dependências e rode os testes automatizados:

```bash
pip install -r requirements.txt
pytest
```

Para testes manuais (Master, Worker, simulador e cenário com dois Masters), consulte o [Guia de testes](docs/TESTES.md).

## Interoperabilidade

O sistema comunica com outras implementações (ex.: de outras equipes) exclusivamente pelo protocolo documentado em `docs/`. Não há dependência de implementação interna; apenas os payloads e fluxos em PROTOCOLO.md e PAYLOADS.md devem ser respeitados. Detalhes em [docs/INTEROPERABILIDADE.md](docs/INTEROPERABILIDADE.md).
