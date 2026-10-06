# MS-Monitor

O **MS-Monitor** é um projeto de monitoramento para um mini-silo conectado a uma
ESP32. A proposta é acompanhar, em uma interface web, as condições internas do
silo e identificar situações que possam afetar o armazenamento.

## Objetivo

O sistema deverá coletar dados de sensores instalados no mini-silo e
disponibilizá-los para consulta em um dashboard. Os principais dados previstos
são:

- Temperatura;
- Umidade do ar;
- Vibração;
- Estado da ventilação;
- Estado de conexão da ESP32.

Além do monitoramento, a ESP32 poderá controlar um ventilador de acordo com
regras automáticas ou comandos enviados pela interface.

## Visão geral

O fluxo esperado do projeto é:

```text
Sensores do mini-silo
        |
        v
      ESP32
        |
        | Wi-Fi / HTTP
        v
      Backend
        |
        v
    Frontend web
```

A ESP32 será responsável pela leitura dos sensores e pelo acionamento do
hardware. O backend deverá receber, armazenar e disponibilizar as leituras. O
frontend apresentará os dados de forma clara e permitirá acompanhar o estado do
sistema.

## Estrutura atual

```text
MS-Monitor/
├── backend/                 # Serviços da API e regras de negócio
├── frontend/                # Interface web do monitoramento
│   ├── src/
│   │   ├── components/      # Componentes visuais reutilizáveis
│   │   ├── data/            # Dados simulados durante o desenvolvimento
│   │   ├── types/           # Tipos compartilhados do frontend
│   │   ├── App.tsx          # Dashboard principal
│   │   └── styles.css       # Estilos complementares ao Bootstrap
│   ├── package.json
│   └── vite.config.ts
└── README.md
```

## Frontend

O frontend está sendo desenvolvido com:

- **React**;
- **TypeScript**;
- **Vite**;
- **Bootstrap 5**;
- **Bootstrap Icons**.

O dashboard atual utiliza dados simulados e já possui:

- Cards de temperatura, umidade e vibração;
- Indicador de ventilação;
- Indicador de conexão com a ESP32;
- Status geral do sistema;
- Layout responsivo para desktop, tablet e celular;
- Controle visual para ativar ou desativar a ventilação.

O gráfico histórico está reservado para a próxima etapa, quando a API estiver
disponível.

## Como executar o frontend

É necessário ter o [Node.js](https://nodejs.org/) instalado.

```bash
cd frontend
npm install
npm run dev
```

Após iniciar o Vite, acesse o endereço informado no terminal, normalmente:

```text
http://localhost:5173
```

Para gerar a versão de produção:

```bash
npm run build
```

## API planejada

A integração deverá utilizar uma API HTTP. Alguns endpoints inicialmente
previstos são:

```http
GET /api/status
GET /api/readings?period=24h
POST /api/fan/toggle
```

Exemplo de resposta para o estado atual:

```json
{
  "device": "esp32-silo-01",
  "online": true,
  "timestamp": "2026-10-06T00:00:00Z",
  "temperature": 29.2,
  "humidity": 72.4,
  "vibration": 0.08,
  "fan": {
    "active": true,
    "mode": "automatic"
  }
}
```

No início, a atualização das leituras poderá ser feita por polling periódico.
Posteriormente, o projeto poderá evoluir para Server-Sent Events ou WebSocket,
caso seja necessário um acompanhamento em tempo real mais frequente.

## Próximas etapas

1. Criar a API do backend;
2. Definir o formato final das leituras da ESP32;
3. Substituir os dados simulados pela integração com a API;
4. Adicionar gráficos históricos;
5. Implementar limites configuráveis e alertas;
6. Adicionar persistência das leituras;
7. Implementar o firmware da ESP32;
8. Adicionar suporte a múltiplos silos, se necessário.

## Observações

O projeto está sendo desenvolvido de forma incremental. A prioridade inicial é
construir uma interface clara e confiável para o monitoramento, mantendo a
comunicação entre frontend, backend e ESP32 desacoplada para facilitar a
evolução do sistema.
