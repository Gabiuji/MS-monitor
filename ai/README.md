# IA do MS-Monitor

O treinamento ocorre em Python; a inferência da versão atual ocorre na
**ESP32**, pelo modelo C++ incluído em `firmware/ms_monitor/risk_model.h`.
Não é necessário carregar um `.joblib` para iniciar a API.

O firmware usa temperatura do ar, umidade relativa, temperatura da sonda
e a diferença entre as temperaturas. Vibração não entra no classificador.
A API recebe o diagnóstico embarcado e o encaminha ao dashboard e ao CSV.

## Reproduzir a versão embarcada

Execute na raiz, após instalar `backend/requirements.txt`. Ajuste `--data`
se o dataset estiver em outra pasta:

```bash
backend/.venv/bin/python ai/train_embedded.py --data data/dataset.json
backend/.venv/bin/python ai/verify_embedded.py --data data/dataset.json
```

O treinamento gera o cabeçalho versionado e o artefato local
`ai/artifacts/embedded_risk_model.joblib`. A verificação exige `g++` e
compara o preditor C++ com o Python. O modelo já exportado acompanha o firmware;
não é necessário retreinar para compilá-lo.

A divisão de treinamento/teste mantém lotes separados. Esta versão é
demonstrativa: classes desbalanceadas e ausência de classes no conjunto de teste
limitam as conclusões sobre qualidade. As previsões não comprovam fungos,
insetos ou micotoxinas. O CSV da coleta contém previsões, não rótulos de verdade
para treinamento supervisionado.

Veja [procedimento de gravação, contrato e resultados](../docs/embedded-ai.md)
e [métricas por classe](../docs/embedded-ai-metrics.json).

## Baseline anterior para comparação offline

O modelo maior permanece disponível por estes comandos, mas não é usado pela
API nem pelo firmware:

```bash
backend/.venv/bin/python ai/train.py --data data/dataset.json
backend/.venv/bin/python ai/predict.py --model ai/artifacts/risk_model.joblib --temperature 29.2 --humidity 72.4 --grain-temperature 28.1
```

## Testes

```bash
cd backend
.venv/bin/python -m pytest tests ../ai/tests -q
```
