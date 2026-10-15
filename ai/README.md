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

Na raiz do projeto:

```bash
python -m venv ai/.venv
```

Ative o ambiente virtual e instale as dependências:

```bash
# Windows PowerShell
.\ai\.venv\Scripts\Activate.ps1
pip install -r ai/requirements.txt
```

## Treinamento

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

## Inferência

Depois do treinamento:

```bash
python ai/predict.py --model ai/artifacts/risk_model.joblib --temperature 29.2 --humidity 72.4 --grain-temperature 28.1
```

Exemplo de saída:

```json
{
  "risk_level": "high",
  "risk_score": 0.81,
  "probabilities": {
    "low": 0.03,
    "moderate": 0.06,
    "high": 0.81,
    "critical": 0.1
  }
}
```

Nesta primeira versão, a inferência é executada em Python para validar o
modelo. A conversão para execução diretamente na ESP32 será avaliada depois da
validação com leituras reais.
