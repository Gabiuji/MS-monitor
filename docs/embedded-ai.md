# IA embarcada na ESP32

O firmware executa um Random Forest treinado previamente em Python e exportado para C++. O treinamento não ocorre na placa. O `.joblib` anterior continua disponível apenas como baseline de comparação no computador.

O firmware completo foi compilado com core **3.3.12** e FQBN **esp32:esp32:heltec_wifi_lora_32_V2**: **1.043.428 bytes de flash (31%)** e **48.824 bytes de variáveis globais (14%)**. Esse relatório não mede o heap livre ou a duração da inferência na placa; essas medições exigem o teste físico.

Fluxo: **sensores → inferência na ESP32 → POST com medições e diagnóstico → API / CSV → dashboard**. A API não classifica as leituras; apenas valida e apresenta o diagnóstico recebido. Sem Wi-Fi, a inferência e as mensagens seriais continuam funcionando, mas não existe fila de leituras offline.

## Modelo

- 32 árvores, profundidade máxima 6, mínimo de 5 amostras por folha, semente 42.
- Entradas: temperatura do ar, umidade relativa, temperatura da sonda e diferença sonda − ar; float32, sem horário ou médias móveis.
- Classificador treinado a partir dos rótulos do dataset; não são regras manuais de temperatura/umidade.
- Parâmetros gerados em `firmware/ms_monitor/risk_model.h`, identificados por uma versão com hash. O cabeçalho acompanha o repositório para permitir compilação sem treinamento adicional.
- Tabelas constantes do modelo: 102.496 bytes no compilador nativo. Não há alocação dinâmica no preditor; a compilação da placa verifica o uso total de flash/RAM.
- O índice de risco é uma soma ponderada das probabilidades de classe, não uma probabilidade calibrada de contaminação. A confiança corresponde à maior probabilidade de classe do modelo.

O relatório reproduzível está em [embedded-ai-metrics.json](embedded-ai-metrics.json). O split separa lotes completos. A acurácia geral é aproximadamente 98,99%, mas a balanced accuracy é aproximadamente 0,50 e o macro F1 das quatro classes é aproximadamente 0,249. O conjunto de teste não contém exemplos de risco alto/crítico e o reconhecimento de risco moderado é insuficiente. Portanto, esta versão demonstra inferência embarcada; não é um diagnóstico agrícola validado.

## Compilar e gravar

Abra `firmware/ms_monitor/ms_monitor.ino` na Arduino IDE. Mantenha `risk_model.h` e `embedded_inference.h` na mesma pasta. Use **Heltec WiFi LoRa 32(V2)** com core Espressif **3.3.12**, as bibliotecas já utilizadas pelos sensores e seu `config.h` local. Nenhuma biblioteca de IA adicional é necessária no Arduino.

Faça Verificar/Compilar e Upload. No Monitor Serial em **115200 baud**, procure a versão do modelo e uma linha como:

```text
AI (ESP32): low | Confidence: 0.800 | Inference: 123 us
```

Essa linha é apenas ilustrativa: classe, confiança e duração reais dependem das leituras e da placa. DHT22 ou sonda inválidos geram `unavailable`, com score/confiança null, sem reutilizar uma classificação anterior.

Reinicie também a API com o código atualizado. Firmware antigo é aceito para telemetria, mas o dashboard pede a atualização para receber o diagnóstico embarcado. O horário apresentado é o recebimento na API; `inference_us` mede somente a chamada local do preditor.

## Reproduzir o treinamento e a verificação

Com as dependências de `backend/requirements.txt` instaladas, execute a partir da raiz. Ajuste `--data` se o dataset estiver em outra pasta:

```bash
backend/.venv/bin/python ai/train_embedded.py --data data/dataset.json
backend/.venv/bin/python ai/verify_embedded.py --data data/dataset.json
```

O primeiro comando gera o cabeçalho e `ai/artifacts/embedded_risk_model.joblib`, preservando o `risk_model.joblib` anterior. O segundo requer `g++`, compila o preditor C++ e compara classes/probabilidades com o modelo Python em todo o dataset. Os pesos, a ordem das classes e os cortes das árvores são exportados; o cálculo dos atributos replica os floats dos sensores.

Verificação realizada com o dataset local: **43.200 amostras, zero divergências de classe e erro máximo de probabilidade de aproximadamente 3 × 10⁻⁸**. Essa comparação verifica a fidelidade da exportação, não a qualidade do diagnóstico.

Também passaram **84 testes** de API, CSV e IA, o build/TypeScript do frontend e seis cenários de renderização do card (origem, versão, duração, firmware antigo, indisponibilidade e dados desatualizados). A compilação para a placa passou sem Upload; as durações reais de inferência continuam pendentes de medição física.

## API e coleta

O POST inclui um campo opcional `embedded_diagnosis`:

```json
{
  "source": "esp32",
  "model_version": "embedded-rf-6b0d1696547d",
  "risk_level": "low",
  "risk_score": 0.12,
  "confidence": 0.8,
  "inference_us": 123
}
```

Exemplo simulado do objeto, não uma medição real. As demais medições continuam obrigatórias no payload. `risk_level` aceita `low`, `moderate`, `high`, `critical` ou `unavailable`; score e confiança ficam entre 0 e 1 ou ambos null quando indisponível. Resultado válido exige DHT22 e sonda válidos. A versão e o tempo de inferência são registrados no CSV.

Ao receber a primeira leitura após atualizar a API, um CSV com o formato anterior é estendido automaticamente com as colunas `ai_source`, `ai_model_version`, `ai_risk_level`, `ai_risk_score`, `ai_confidence` e `ai_inference_us`. Uma cópia original `readings.before-embedded-*.csv` é preservada na mesma pasta. Leituras anteriores não recebem diagnósticos fabricados. Use uma única instância da API por arquivo.

## Teste físico pendente

Após gravar a placa, confirme a identificação do modelo e a classificação na serial, desligue temporariamente o Wi-Fi e confira que a inferência continua. Verifique falhas independentes do DHT22 e da sonda; depois restaure a conexão e confira origem ESP32, versão e tempo de inferência na API, no dashboard e no CSV. Meça memória livre e tempo de inferência na placa antes de apresentar números experimentais. Nenhum Upload ou teste físico foi realizado automaticamente.
