# Contrato HTTP local

`GET /health` → 200 `{"status":"ok"}`. Independe do dispositivo.

`POST /api/readings` → 201 com os campos enviados e `received_at` UTC, gerado no servidor. Payload inválido → 422; não substitui a última leitura aceita.

| Campo | Validação |
| --- | --- |
| device_id | string de 1–64 caracteres, letras ASCII, números, `_` e `-` |
| uptime_ms | inteiro ≥ 0, não representa horário civil |
| window_ms | inteiro > 0, duração real da janela |
| temperature_c | número finito entre -40 e 80 °C, ou null |
| humidity_pct | número finito entre 0 e 100 %, ou null |
| dht_ok | booleano; true exige ambos os valores, false exige ambos null |
| vibration_do | inteiro 0 ou 1, não booleano |
| vibration_transitions | inteiro ≥ 0 |
| probe_temperature_c | número finito entre 0 e 1024 °C, ou null |
| probe_ok | booleano no payload novo; true exige temperatura, false exige null |
| embedded_diagnosis | objeto opcional com o diagnóstico calculado na ESP32 |

Os campos anteriores à sonda continuam obrigatórios; campos extras e coerção de strings/bools em números são rejeitados. NaN e Infinity são rejeitados. `temperature_c` continua sendo a temperatura do ar (DHT22).

Para compatibilidade, payloads antigos podem omitir ambos os campos da sonda; POST e GET retornam `probe_temperature_c: null` e `probe_ok: null`. Quando enviados, os dois são obrigatórios juntos, e `probe_ok` deve ser booleano. `true` exige temperatura válida (inclusive zero); `false` exige temperatura null. Enviar status null explicitamente é inválido: a ausência é reservada ao firmware antigo. Falhas do DHT22 e da sonda são independentes.

`GET /api/readings/latest` → 200 com envelope:

```json
{"data":null,"device_status":"waiting","age_seconds":null}
```

Após POST, `data` contém os campos acima e `received_at` (ISO 8601 UTC); `age_seconds` é a idade calculada com relógio monotônico do servidor. `device_status` é `online` enquanto idade < 10 s e `stale` a partir de 10 s. Leituras antigas permanecem disponíveis. `online` significa POST recente, não prova de conectividade contínua ou funcionamento do DHT.

O envelope também inclui `diagnosis`, traduzido para exibição a partir de `data.embedded_diagnosis`: a API não executa o modelo. Firmware antigo sem o objeto recebe `source: "unavailable"` e `risk_level: "unavailable"`. O novo objeto exige `source: "esp32"`, `model_version`, `risk_level`, `risk_score`, `confidence` e `inference_us`; valores não finitos, fora de faixa ou inconsistentes com os sensores retornam 422. Score e confiança ficam entre 0 e 1; para `unavailable`, ambos são null. [Contrato e validação da IA embarcada](embedded-ai.md).

## Histórico e CSV

`GET /api/readings?limit=300` → 200 `{"data": [...]}`. Retorna as últimas leituras, da mais antiga para a mais recente. `limit` aceita inteiros de 1 a 3600 (padrão 300); valores inválidos retornam 422. Cada item contém os campos do POST e `received_at` em UTC. Não duplica dados por polling: cada POST aceito corresponde a uma linha.

`GET /api/readings/export` → download do CSV completo com cabeçalho, inclusive quando ainda não houver leituras. A exportação é uma cópia do arquivo até o instante do pedido; novos envios continuam sendo gravados para a próxima exportação.

O arquivo padrão é `backend/data/readings.csv`, independente do diretório de execução da API. É possível configurar outro destino com `READINGS_CSV_PATH`. A pasta é criada no primeiro POST aceito e é ignorada pelo Git. Falha de gravação retorna 503, sem atualizar a última leitura em memória. POSTs inválidos não são gravados.

Colunas: `received_at`, `device_id`, `uptime_ms`, `window_ms`, `temperature_c`, `humidity_pct`, `dht_ok`, `probe_temperature_c`, `probe_ok`, `vibration_do`, `vibration_transitions`, `ai_source`, `ai_model_version`, `ai_risk_level`, `ai_risk_score`, `ai_confidence`, `ai_inference_us`. O CSV usa vírgula como separador, ponto decimal e booleanos `true`/`false`; valores null ficam em branco, nunca zero. As colunas de IA contêm previsões, não rótulos experimentais confirmados. CSVs antigos são migrados no próximo POST, com cópia original `readings.before-embedded-*.csv` na mesma pasta e sem fabricar resultados para as linhas anteriores.

O histórico em memória é limitado às últimas 3600 leituras e é recuperado do CSV ao iniciar a API; o arquivo completo continua crescendo enquanto houver coleta. Reiniciar volta a `waiting` na última leitura até chegar um novo POST; o histórico anterior permanece disponível. Use um único worker e uma única instância da API por arquivo CSV. Para encerrar a coleta, pare a API; preserve uma cópia do arquivo antes de iniciar outra coleta.

O dashboard separa temperaturas (°C), umidade (%) e contagem de transições. Interrompe as linhas nas falhas dos sensores e em intervalos sem dados de 10 s ou mais; os pontos usam os horários reais de recebimento. A duração da janela de vibração continua registrada em `window_ms`.

Esta API não autentica clientes: uso exclusivo na LAN confiável durante esta etapa.
