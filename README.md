# MS-Monitor

Monitoramento local de um mini-silo: DHT22 e SW-420 → Heltec WiFi LoRa 32 V2 → Wi-Fi/HTTP POST → FastAPI → GET periódico pelo dashboard React/TypeScript/Vite/Bootstrap.

Identificadores, comentários, mensagens seriais e contrato da API usam inglês. A interface apresenta textos, datas e números em português brasileiro (`pt-BR`) para uso em sala de aula. As rotas são `POST /api/readings` e `GET /api/readings/latest`. Após atualizar de uma versão com rotas em português, reinicie a API e o frontend e compile/grave novamente o firmware com a URL atualizada no `config.h`.

Esta etapa apresenta temperatura, umidade e contagem de transições. IA e controle de ventilador ainda não estão integrados. Transições não indicam intensidade, frequência mecânica, RPM, batidas nem estado do ventilador.

## API no Ubuntu

Requer Python 3.11 ou superior com suporte a venv. Se `python3 -m venv` informar falta de ensurepip, instale o pacote `python3-venv` correspondente ao seu Python pelo gerenciador do Ubuntu, ou use um interpretador que já tenha venv funcional.

```bash
cd /home/gabriel/workspace/MS-monitor/backend
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m pytest -q
python -m uvicorn app:app --host 0.0.0.0 --port 8000 --workers 1
```

No ambiente desta implementação, o interpretador funcional foi `/home/gabriel/.pyenv/versions/3.11.9/bin/python`; ele pode substituir `python3` na criação do venv.

A API guarda apenas uma última leitura global em memória, sem histórico ou banco. Reiniciar apaga a leitura. Use **um único worker**; esta etapa pressupõe um dispositivo. `/health` informa saúde da API independentemente de haver ESP32 conectado. Com a API ligada, consulte o contrato interativo em `http://localhost:8000/docs`.

## Frontend

Em outro terminal:

```bash
cd /home/gabriel/workspace/MS-monitor/frontend
npm ci
cp .env.example .env.local
npm run dev -- --host 0.0.0.0 --port 5173 --strictPort
```

Abra `http://localhost:5173`. `.env.local` define `VITE_API_URL=http://localhost:8000`. Reinicie Vite após alterar o ambiente. Para acessar no celular, use `http://LAPTOP_IP:5173`, configure `VITE_API_URL=http://LAPTOP_IP:8000` e inicie a API com a origem correspondente:

```bash
cd /home/gabriel/workspace/MS-monitor/backend
CORS_ORIGINS='http://localhost:5173,http://127.0.0.1:5173,http://LAPTOP_IP:5173' .venv/bin/python -m uvicorn app:app --host 0.0.0.0 --port 8000 --workers 1
```

Substitua `LAPTOP_IP` pelo IP LAN real. CORS aceita uma lista de origens separadas por vírgula; cada origem inclui esquema e porta, sem barra final. Se usar outra porta ou `npm run preview`, ajuste as origens. CORS afeta o navegador, não o POST da ESP32.

```bash
cd /home/gabriel/workspace/MS-monitor/frontend
npm run build
```

Não há script de lint no projeto. O build verifica TypeScript e gera `dist/`. O polling espera a requisição terminar antes de agendar a próxima em 2,5 s, tem timeout de 4 s e cancela timers/requisições ao desmontar. Sem leitura, mostra “—”. Na falha de rede preserva os valores anteriores e os marca como desatualizados. DHT com falha não oculta vibração. O layout e o espaço reservado para histórico foram preservados; não foi acrescentado gráfico ou endpoint de histórico.

## Rede e firmware

Notebook e ESP32 precisam alcançar um ao outro na LAN; redes de convidados podem isolar clientes. Para descobrir o IPv4 do notebook:

```bash
cd /home/gabriel/workspace/MS-monitor
hostname -I
ip -4 addr show
cp firmware/ms_monitor/config.example.h firmware/ms_monitor/config.h
```

Escolha o IP da interface Wi-Fi/Ethernet conectada à ESP32, sem usar IP de loopback/VPN. Edite `config.h` com SSID, senha, `DEVICE_ID` e `API_URL=http://LAPTOP_IP:8000/api/readings`. O arquivo é ignorado pelo Git. Não use `localhost` no ESP32. `0.0.0.0` é endereço de escuta do servidor, não destino. Não publique esta API na internet. Se houver firewall, permita a porta TCP 8000 (e 5173 para acesso ao frontend) somente na rede local; nenhum firewall ou permissão do sistema é alterado pelo projeto.

Hardware: **Heltec WiFi LoRa 32 V2, ESP32-D0WDQ6, micro-USB**. DHT22/AM2302: 3V3/GND/DAT GPIO 17. SW-420: 3V3/GND/DO GPIO 22. Não use GPIO 21, que controla Vext. Alimentação USB; sem motor, relé ou LoRa.

Na Arduino IDE 2.3.10:

1. Use o core **esp32 by Espressif Systems 3.3.12**, já testado no hardware do projeto.
2. Pelo gerenciador de bibliotecas, instale **DHT sensor library**, **Adafruit Unified Sensor** e **ArduinoJson 7.x** (biblioteca adicional para JSON confiável).
3. Abra `firmware/ms_monitor/ms_monitor.ino`. Selecione **Heltec WiFi LoRa 32(V2)**, não V3/S3, e a porta USB observada (exemplo `/dev/ttyUSB0`, configurável).
4. Clique em Verificar/Compilar, depois em Upload quando desejar gravar a placa.
5. Abra o Monitor Serial em **115200 baud**. Veja leituras locais, IP obtido e HTTP 201 ou código de falha, sem senha nos logs.

Para diagnóstico independente da rede, abra `firmware/sensor_test/sensor_test.ino`, baseline equivalente ao sketch serial fornecido. Os `.ino` são compilados e gravados na placa; não são executados pelo frontend/backend.

Se Arduino CLI já estiver instalado com core e bibliotecas, a compilação pode ser feita a partir da raiz (não faz upload):

```bash
cd /home/gabriel/workspace/MS-monitor
arduino-cli compile --fqbn esp32:esp32:heltec_wifi_lora_32_V2 firmware/sensor_test
arduino-cli compile --fqbn esp32:esp32:heltec_wifi_lora_32_V2 firmware/ms_monitor
arduino-cli monitor --port /dev/ttyUSB0 --config baudrate=115200
```

O firmware usa ISR CHANGE e contador protegido por trava. Fecha a janela aproximadamente a cada 2,5 s e transmite a duração real, incluindo atrasos da rede. Reconexão Wi-Fi é temporizada (10 s), sem espera infinita. HTTP usa timeout de conexão 700 ms e leitura 1000 ms; libera recursos e não mantém fila ou reinicia por erro. Continua lendo e registrando localmente sem Wi-Fi/API. A biblioteca DHT pode bloquear interrupções brevemente: a contagem é demonstrativa, não um instrumento preciso de vibração. `uptime_ms` é tempo desde o boot, com rollover de `millis()`; não é horário civil.

Referências: [definições oficiais de placas Espressif](https://github.com/espressif/arduino-esp32/blob/master/boards.txt) e [serialização ArduinoJson 7](https://arduinojson.org/v7/api/json/serializejson/).

## Teste HTTP explicitamente simulado

Com a API ligada, execute em outro terminal na raiz. Este payload é **simulado**, não uma leitura física; não existe gerador automático na aplicação:

```bash
cd /home/gabriel/workspace/MS-monitor
curl -fsS http://localhost:8000/health
curl -fsS http://localhost:8000/api/readings/latest
curl -i -X POST http://localhost:8000/api/readings -H 'Content-Type: application/json' --data '{"device_id":"simulated-curl","uptime_ms":15000,"window_ms":2500,"temperature_c":24.8,"humidity_pct":59.2,"dht_ok":true,"vibration_do":0,"vibration_transitions":44}'
curl -fsS http://localhost:8000/api/readings/latest
```

POST deve retornar 201; GET passa de `waiting` para `online`. Pare os POSTs e aguarde 10 s: GET retorna `stale`, preservando valores, enquanto `/health` segue saudável. Para testar DHT com falha, mantendo vibração:

```bash
curl -i -X POST http://localhost:8000/api/readings -H 'Content-Type: application/json' --data '{"device_id":"simulated-curl","uptime_ms":17500,"window_ms":2500,"temperature_c":null,"humidity_pct":null,"dht_ok":false,"vibration_do":1,"vibration_transitions":86}'
```

Reinicie a API após os testes para apagar a leitura simulada antes de conectar o dispositivo real.

Para verificar no hardware: desligue a ESP32 mantendo a API ligada (dashboard deve marcar dados antigos após 10 s); desconecte o DAT do DHT com cuidado (deve enviar null/null e manter telemetria de vibração); restaure o sensor; interrompa e restaure o Wi-Fi (serial continua lendo e retorna a HTTP 201 ao reconectar). Pare e reinicie a API para conferir “API inacessível” e recuperação. Nunca confunda falha do DHT com falha da API ou ausência do dispositivo.
