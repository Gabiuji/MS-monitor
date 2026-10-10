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

Todos os campos são obrigatórios; campos extras e coerção de strings/bools em números são rejeitados. NaN e Infinity são rejeitados.

`GET /api/readings/latest` → 200 com envelope:

```json
{"data":null,"device_status":"waiting","age_seconds":null}
```

Após POST, `data` contém os campos acima e `received_at` (ISO 8601 UTC); `age_seconds` é a idade calculada com relógio monotônico do servidor. `device_status` é `online` enquanto idade < 10 s e `stale` a partir de 10 s. Leituras antigas permanecem disponíveis. `online` significa POST recente, não prova de conectividade contínua ou funcionamento do DHT.

Uma leitura global em memória, um worker, sem persistência/histórico. Reinício volta a `waiting`. Esta API não autentica clientes: uso exclusivo na LAN confiável durante esta etapa.
