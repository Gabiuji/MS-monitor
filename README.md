# MS-Monitor

Protótipo de mini-silo agrícola equipado com uma ESP32 e sensores para
monitorar as condições de armazenamento de grãos.

O objetivo geral é desenvolver e testar uma inteligência artificial embarcada
capaz de classificar condições favoráveis ao desenvolvimento de fungos e
insetos em grãos armazenados. O sistema deverá usar as leituras de temperatura
do ambiente, umidade relativa do ar e temperatura no interior dos grãos para
produzir alertas preventivos sobre o risco de deterioração.

O resultado do modelo será uma **estimativa de risco**, e não uma confirmação
laboratorial de contaminação por fungos ou micotoxinas.

## Tecnologias

- Frontend: React, TypeScript, Vite e Bootstrap.
- Backend: Python e FastAPI.
- IA: Python, pandas e scikit-learn.
- Hardware: Heltec WiFi LoRa 32 V2, DHT22, SW-420 e termopar tipo K com MAX6675.

## Sensores e escopo da primeira versão

O protótipo possui quatro grandezas de medição:

- **Temperatura ambiente**, medida pelo DHT22;
- **Umidade relativa do ar**, medida pelo DHT22;
- **Temperatura dos grãos**, medida pelo termopar tipo K com MAX6675;
- **Vibração**, medida pelo SW-420.

Na primeira versão da inteligência artificial serão utilizadas somente:

1. temperatura ambiente;
2. umidade relativa do ar;
3. temperatura dos grãos medida pela sonda.

O sensor de vibração não fará parte do diagnóstico inicial. Ele poderá ser
incorporado em uma etapa futura, caso os experimentos mostrem que suas leituras
ajudam a identificar atividade de insetos ou anomalias mecânicas.

## Objetivo da inteligência artificial

O modelo deverá classificar as condições de armazenamento em níveis de risco,
por exemplo:

```text
baixo       -> condições sem sinais relevantes de deterioração
moderado    -> condições que exigem acompanhamento
alto        -> condições favoráveis à deterioração
crítico     -> condições que exigem ação imediata
```

As entradas poderão incluir, além das leituras instantâneas, variáveis
calculadas a partir do histórico:

- médias móveis;
- tendência de aumento ou redução da temperatura;
- diferença entre a temperatura dos grãos e a temperatura ambiente;
- tempo de armazenamento;
- tempo de permanência acima de determinados limites.

O treinamento é feito no computador. O firmware inclui um modelo compacto
para executar a inferência diretamente na ESP32, inclusive sem Wi-Fi. A API
recebe o resultado para exibição e coleta. A IA não substitui inspeções
físicas ou análises laboratoriais.

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

O histórico permite visualizar temperaturas, umidade e vibração e baixar o CSV
completo. Cada leitura aceita é salva em `backend/data/readings.csv`; a coleta
continua enquanto a API estiver ligada, mesmo sem o navegador aberto.

### ESP32

1. Copie `firmware/ms_monitor/config.example.h` para `config.h` na mesma pasta.
2. Configure o Wi-Fi e a URL `http://IP_DO_COMPUTADOR:8000/api/readings`. O arquivo `config.h` não é versionado.
3. Na Arduino IDE, instale o core ESP32 3.3.12 e as bibliotecas **DHT sensor library**, **Adafruit Unified Sensor**, **ArduinoJson 7.x** e **MAX6675 library** (Adafruit).
4. Abra `firmware/ms_monitor/ms_monitor.ino`, selecione **Heltec WiFi LoRa 32(V2)** e grave na placa. Monitor Serial: **115200 baud**.

Use Wi-Fi de **2,4 GHz**, com a ESP32 e o computador acessíveis na mesma rede local. DHT22 no GPIO 17; SW-420 no GPIO 22; ambos alimentados em 3,3 V.

MAX6675: SCK no GPIO 13, CS no GPIO 23 e SO no GPIO 39; alimentação em 3,3 V e GND comum. [Montagem e teste da sonda](docs/max6675.md).

### IA

O modelo embarcado está em `firmware/ms_monitor/risk_model.h` e é compilado
junto com o sketch. Usa temperatura ambiente, umidade, temperatura da sonda
e a diferença entre as temperaturas. O arquivo `.joblib` fica apenas no
computador para treinamento e comparação; não é executado na placa.

Após gravar o firmware atualizado, a serial mostra a classe e o tempo de
inferência. O dashboard identifica **Inferência na ESP32**. Firmware antigo
continua enviando sensores, mas não recebe um diagnóstico calculado pelo backend.
Consulte [IA embarcada: treinamento e validação](docs/embedded-ai.md).

## Estado atual

A API salva as leituras em CSV e recupera o histórico ao reiniciar. Use apenas
um worker. A última leitura e o estado de conexão aguardam um novo envio da ESP32.
O dashboard já apresenta as leituras principais e a integração inicial com os
sensores está estruturada. O dashboard também possui um card destacado para o
diagnóstico preventivo da IA, atualizado junto com o polling da última leitura.
O gráfico mostra até as últimas 3.600 leituras; o CSV preserva a coleta completa.
A validação do modelo com dados reais ainda está em desenvolvimento.

O dataset de degradação disponível em `data/dataset.json` será utilizado para
criar o baseline do classificador. A validação deverá priorizar divisões por
lote e por período de tempo, evitando resultados artificialmente otimistas
causados por misturar leituras do mesmo lote entre treinamento e teste.

O firmware inclui o classificador demonstrativo. A validação com dados reais,
o tempo de inferência e a memória disponível ainda precisam ser confirmados
fisicamente na ESP32 após o Upload.
