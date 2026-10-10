# Validação realizada em 09/10/2026

- Frontend: `cd frontend && npm ci && npm run build` passou; TypeScript e Vite 5.4.21 geraram a versão de produção. Não há script de lint. Layout não foi inspecionado em navegador automatizado nesta execução.
- Backend: `cd backend && .venv/bin/python -m pytest -q`: **22 testes passaram**. Cobertura: health, ausência inicial de dados, POST válido, UTC, leitura após POST, stale aos 10 s, recuperação, DHT null/null com vibração, limites/tipos/coerência, NaN/Infinity, POST inválido sem renovar frescor, CORS permitido/rejeitado.
- HTTP real local com Uvicorn e curl: health 200, waiting, POST simulado 201, GET online, stale sem perder valores e POST de falha DHT com transições preservadas. O servidor temporário foi encerrado, apagando as leituras simuladas.
- `git diff --check` passou.
- Firmware: Arduino CLI/toolchain não disponível no PATH; **não compilado nem gravado**. Não houve teste físico dos sensores/reconexão Wi-Fi nesta execução. Procedimento está no README.

O Python padrão 3.14 não possuía ensurepip; o venv foi criado com `/home/gabriel/.pyenv/versions/3.11.9/bin/python`. Instalação de dependências, build e testes exigiram execução fora do sandbox por bloqueios de rede/processos/porta local.

`npm ci` informou dois avisos de segurança nas dependências existentes (um moderado e um alto). A stack e o lockfile foram preservados; não foi executado `npm audit fix --force`. Pytest informou um aviso de depreciação da integração TestClient/httpx na versão instalada de Starlette; os testes passaram.
