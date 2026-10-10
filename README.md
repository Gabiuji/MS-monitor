# MS-Monitor

Monitoramento de temperatura, umidade e vibração de um mini-silo com ESP32.

Os sensores enviam leituras por Wi-Fi para uma API local, exibidas em um dashboard em português.

## Tecnologias

- Frontend: React, TypeScript, Vite e Bootstrap.
- Backend: Python e FastAPI.
- Hardware: Heltec WiFi LoRa 32 V2, DHT22 e SW-420.

## Como executar

Requisitos: Node.js, Python 3.11+ com suporte a `venv` e Arduino IDE.

Execute os comandos a partir da raiz do repositório, em terminais separados.

### Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app:app --host 0.0.0.0 --port 8000 --workers 1
```

Documentação da API: http://localhost:8000/docs.

### Frontend

```bash
cd frontend
npm ci
cp .env.example .env.local
npm run dev -- --port 5173 --strictPort
```

Dashboard: http://localhost:5173. A URL da API pode ser alterada em `.env.local`.

### ESP32

1. Copie `firmware/ms_monitor/config.example.h` para `config.h` na mesma pasta.
2. Configure o Wi-Fi e a URL `http://IP_DO_COMPUTADOR:8000/api/readings`. O arquivo `config.h` não é versionado.
3. Na Arduino IDE, instale o core ESP32 3.3.12 e as bibliotecas **DHT sensor library**, **Adafruit Unified Sensor** e **ArduinoJson 7.x**.
4. Abra `firmware/ms_monitor/ms_monitor.ino`, selecione **Heltec WiFi LoRa 32(V2)** e grave na placa. Monitor Serial: **115200 baud**.

Use Wi-Fi de **2,4 GHz**, com a ESP32 e o computador acessíveis na mesma rede local. DHT22 no GPIO 17; SW-420 no GPIO 22; ambos alimentados em 3,3 V.

## Estado atual

A API mantém apenas a última leitura em memória; reiniciá-la apaga os dados. Histórico, IA e controle do ventilador ainda não estão implementados. A vibração é apresentada como contagem de transições do sinal.
