# Protótipo de IA

Esta pasta contém o primeiro protótipo do classificador de risco do
MS-Monitor. O modelo usa apenas as grandezas previstas para a primeira versão:

- temperatura ambiente;
- umidade relativa do ar;
- temperatura dos grãos medida pela sonda.

O sensor de vibração permanece fora do modelo nesta etapa.

## Objetivo

Classificar as condições de armazenamento em quatro níveis:

```text
low, moderate, high, critical
```

O resultado representa uma **estimativa preventiva de risco** baseada nos
dados do modelo. Ele não confirma a presença de fungos, insetos ou micotoxinas.

## Preparação do ambiente

Os comandos abaixo devem ser executados a partir da raiz do projeto
`MS-Monitor`.

```bash
python -m venv ai/.venv
```

Ative o ambiente virtual e instale as dependências:

```bash
# Windows PowerShell
.\ai\.venv\Scripts\Activate.ps1
pip install -r ai/requirements.txt
```

## Treinamento do modelo

O dataset esperado é `data/dataset.json`. Execute:

```bash
python ai/train.py
```

O comando:

1. carrega e valida o dataset;
2. cria atributos derivados das três grandezas dos sensores;
3. separa lotes completos entre treinamento e teste;
4. treina um Random Forest com balanceamento de classes;
5. imprime as métricas por classe;
6. salva o modelo em `ai/artifacts/risk_model.joblib`;
7. salva as métricas em `ai/artifacts/metrics.json`.

Também é possível indicar os caminhos:

```bash
python ai/train.py --data data/dataset.json --output-dir ai/artifacts
```

O artefato `ai/artifacts/risk_model.joblib` e as métricas geradas são ignorados
pelo Git. Por isso, após clonar o projeto em outra máquina, é necessário
executar o treinamento novamente antes de iniciar o backend.

### Resultado atual

O treinamento executado com o dataset atual possui:

```text
Registros: 43.200
Lotes: 20
Accuracy: 0.9902
Balanced accuracy: 0.5000
Macro F1: 0.4975
```

Esses valores são apenas um baseline. A acurácia geral está alta, mas as
métricas balanceadas mostram que o modelo ainda não reconhece todas as classes
com qualidade suficiente. O dataset possui padrões artificiais e classes
desbalanceadas, portanto o resultado não representa ainda o desempenho esperado
com dados reais do mini-silo.

## Executar a IA no dashboard

A IA é executada no backend. O frontend não treina nem carrega o modelo
diretamente: ele consulta `GET /api/readings/latest`, e o backend acrescenta o
campo `diagnosis` à resposta.

### Terminal 1: preparar e iniciar o backend

Na raiz do projeto:

```powershell
python -m venv backend/.venv
.\backend\.venv\Scripts\Activate.ps1
pip install -r backend/requirements.txt
cd backend
python -m uvicorn app:app --host 0.0.0.0 --port 8000
```

Se o ambiente virtual do backend já existir:

```powershell
.\backend\.venv\Scripts\Activate.ps1
python -m uvicorn app:app --app-dir backend --host 0.0.0.0 --port 8000
```

O backend carrega o modelo em:

```text
ai/artifacts/risk_model.joblib
```

Se esse arquivo não existir, treine o modelo antes de iniciar o backend:

```powershell
.\backend\.venv\Scripts\python.exe ai/train.py --data data/dataset.json --output-dir ai/artifacts
```

### Terminal 2: iniciar o frontend

```powershell
cd frontend
npm install
npm run dev -- --port 5173 --strictPort
```

Acesse:

```text
http://localhost:5173
```

O card **Diagnóstico da IA** será atualizado junto com o polling da última
leitura, realizado pelo frontend a cada 2,5 segundos.

### Simular uma leitura sem a ESP32

Enquanto o hardware não estiver disponível, envie uma leitura de teste para o
backend. Execute este comando em outro terminal:

```powershell
$body = @{
  device_id = "simulated-dashboard"
  uptime_ms = 15000
  window_ms = 2500
  temperature_c = 29.2
  humidity_pct = 72.4
  dht_ok = $true
  vibration_do = 0
  vibration_transitions = 4
  probe_ok = $true
  probe_temperature_c = 28.1
} | ConvertTo-Json

Invoke-RestMethod `
  -Uri http://localhost:8000/api/readings `
  -Method Post `
  -ContentType "application/json" `
  -Body $body
```

Depois de enviar a leitura, atualize ou aguarde o dashboard. O card deverá
mostrar o nível de risco, o índice estimado, a confiança, os fatores
observados e o horário da análise.

Para consultar diretamente a resposta completa:

```powershell
Invoke-RestMethod http://localhost:8000/api/readings/latest | ConvertTo-Json -Depth 5
```

O diagnóstico exige as três entradas principais. Se `dht_ok` for falso ou
`probe_ok` não for verdadeiro, o dashboard exibirá o diagnóstico como
indisponível em vez de produzir uma classificação incompleta.

## Inferência manual

Também é possível executar uma inferência diretamente pela linha de comando,
sem iniciar o backend:

```bash
python ai/predict.py --model ai/artifacts/risk_model.joblib --temperature 29.2 --humidity 72.4 --grain-temperature 28.1
```

Exemplo de saída:

```json
{
  "risk_level": "low",
  "risk_score": 0.2086,
  "confidence": 0.7547,
  "probabilities": {
    "critical": 0.1446,
    "high": 0.0475,
    "low": 0.7386,
    "moderate": 0.0692
  }
}
```

O resultado pode ser diferente após um novo treinamento, pois o modelo é
recriado a partir do dataset local.

## Testes

Com o ambiente virtual do backend ativado, execute:

```powershell
python -m pytest backend/tests -q
```

Os testes atuais validam a API, o recebimento das leituras, as falhas
independentes dos sensores e a inclusão do diagnóstico no endpoint.

Nesta primeira versão, a inferência é executada em Python para validar o
modelo. A conversão para execução diretamente na ESP32 será avaliada depois da
validação com leituras reais, considerando memória, tempo de inferência e
formato de exportação.
