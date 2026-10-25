# Revisão do relatório MS-Monitor

O relatório foi reescrito no template LaTeX fornecido, com base no enunciado do Grupo 03, no DOCX original e na implementação do projeto na revisão `07b1400`. A mudança de tema foi explicitada: a classificação de ventilação do enunciado não corresponde ao classificador térmico e higrométrico atualmente implementado. O documento não presume aprovação docente dessa mudança.

## Entrega e edição

- `Main.pdf`: relatório compilado para leitura.
- `Main.tex`: arquivo principal; capa e folha de rosto incluem os cinco integrantes.
- `capitulos/`: texto revisado, organizado em sete seções.
- `figuras/`: diagramas vetoriais editáveis em TikZ.
- `figuras/png/`: os quatro diagramas em PNG a 300 dpi, com fundo branco, margens recortadas e sem legendas externas, para inserção no Word. O arquivo `diagramas-png.zip` reúne essas imagens.
- `ExportarDiagramas.tex`: exportação dos mesmos diagramas em páginas individuais; pode ser compilado com `latexmk -pdf -outdir=build ExportarDiagramas.tex` e convertido em PNG com `pdftoppm` a 300 dpi.
- `referencias-relatorio.bib`: referências efetivamente utilizadas.
- `preambulo-relatorio.tex`: configuração ativa do relatório, preservando a classe do template.

O PDF do enunciado e o DOCX original foram preservados. Os arquivos de exemplo antigos do template que não são chamados por `Main.tex` também foram preservados; seu conteúdo não aparece no relatório final.

Para compilar, execute na pasta deste arquivo:

```bash
latexmk -pdf -outdir=build -interaction=nonstopmode -halt-on-error Main.tex
cp build/Main.pdf Main.pdf
```

O diretório `build/` contém apenas arquivos intermediários e está ignorado pelo Git. A compilação utiliza pdfLaTeX, BibTeX, TikZ e o estilo `abntex2-alf`.

A versão entregue tem **22 páginas**, quatro diagramas vetoriais e oito tabelas. A compilação foi concluída sem erros, referências indefinidas ou caixas excedendo as margens. Foram conferidos visualmente a paginação, os diagramas, as tabelas e as referências no PDF; o sumário foi ajustado para usar os destinos de navegação corretos da classe fornecida.

## Principais correções

| Ponto examinado | Tratamento na versão revisada |
| --- | --- |
| Tema do Grupo 03 no enunciado | Explicita a mudança de classificação de ventilação para monitoramento das condições de armazenamento, mantendo os entregáveis arquiteturais como referência. |
| Detecção de fungos | Apresentada como investigação futura, sem afirmar detecção, identificação de espécies, micotoxinas ou segurança sanitária comprovadas. |
| Uso de “diagnóstico”, “risco” e “confiança” | A classe é uma saída demonstrativa do dataset; o índice não é probabilidade calibrada de fungos, e a confiança é a maior probabilidade de classe. |
| Temperatura do grão | Qualificada como temperatura no ponto da sonda; uma única ponta não representa toda a massa armazenada. |
| Umidade | Distingue umidade relativa do ar de teor de água do grão e atividade de água. |
| Papel do SW-420 | Contagem de transições e leitura DO, sem atribuir intensidade, aceleração, RPM ou estado de ventilador. Não é entrada da IA atual. |
| Entradas do modelo | Quatro atributos: temperatura do ar, UR do ar, temperatura da sonda e diferença sonda menos ar. Não inclui tempo de armazenamento ou médias móveis. |
| Local de execução da IA | Treinamento em Python no computador e inferência C++ na ESP32; o arquivo `.joblib` não é executado na placa nem usado para inferir pela API atual. |
| Fluxo sem Wi-Fi | Classificação e serial antecedem a verificação da rede. Não há fila para recuperar posteriormente as leituras desse intervalo. |
| Disponibilidade da API | O firmware tenta o POST e interpreta o resultado; não faz uma consulta prévia para decidir se a API está disponível. |
| Falhas térmicas | DHT22 e sonda têm validade independente; a IA exige ambos válidos. A falha não deve reapresentar uma classe anterior como nova. |
| Periodicidade | 2500 ms é o intervalo nominal de ciclos; `window_ms` registra a janela real. Os 0,4 Hz não representam amostragem de uma forma de onda mecânica. |
| Alimentação | Distingue entrada USB de 5 V, barramento de 3,3 V e retorno GND. O termopar é passivo. |
| Lei de Ohm e consumo | Corrige a relação para `I = V/R`. Remove a soma de correntes hipotéticas e a potência correspondente como se caracterizassem a montagem. Consumo real permanece a medir. |
| Especificações | Usa referências dos componentes; resolução de 0,25 °C do MAX6675 não equivale à exatidão de todo o conjunto termopar/conversor. |
| Contrato JSON | Substitui a imagem com nomes incompatíveis por exemplo textual com campos reais em inglês e valores explicitamente ilustrativos. |
| CSV e horários | Distingue medições e previsões de rótulos experimentais; `received_at` é recebimento no servidor, e `uptime_ms` não é horário civil. |
| Interface web | Descreve os elementos implementados. Não afirma existir card específico de diferença térmica; ventilação permanece “Não avaliado”. |
| Avaliação do modelo | Expõe suporte por classe, acurácia balanceada, F1 macro e comparação com a previsão constante da classe majoritária. |
| Validação cruzada | O código usa a primeira divisão de cinco partições por lote; as métricas não são média de cinco rodadas. |
| Evidências físicas | Diferencia compilação registrada, testes de software, paridade nativa e ensaios na placa. Não inventa calibração, consumo ou duração física de inferência. |
| Escrita acadêmica | Remove repetição na apresentação, corrige identificação institucional e substitui formulações categóricas por conclusões vinculadas às evidências disponíveis. |

## Exame dos diagramas e imagens do DOCX

Foram examinadas visualmente as cinco imagens técnicas do documento, além das marcas institucionais. Os diagramas foram reconstruídos em TikZ para manter legibilidade e facilitar ajustes posteriores.

1. **Arquitetura original (`image4.png`):** misturava a estrutura atual com a proposta futura de ventilação. O novo diagrama separa o caminho térmico utilizado pela IA, a contagem de vibração, a saída serial e os serviços externos. A API recebe a classificação feita pela ESP32.
2. **Alimentação original (`image5.png`):** a representação do GND com sentido de emissão podia ser confundida com fonte de energia. O novo desenho mostra distribuição de 3,3 V e retorno comum, distinguindo alimentação de dados. Continua sendo diagrama funcional, não esquema elétrico completo.
3. **Fluxo original da IA (`image6.png`):** a ordem e os retornos do fluxo podiam sugerir dependência da rede e consulta antecipada da API. O novo fluxo mostra validade dos dois sensores térmicos, inferência local, serial e somente depois decisão sobre Wi-Fi e tentativa de POST.
4. **Classificador futuro de ventilação (`image7.png`):** não corresponde a uma função implementada. Foi excluído da arquitetura atual; não há motor ou acionamento no relatório revisado.
5. **Exemplo JSON (`image8.png`):** os campos da imagem não correspondiam ao contrato da API. Foi substituído por listagem editável com `embedded_diagnosis` e avisos explícitos sobre valores ilustrativos, inclusive o tempo de inferência.

Foi acrescentado um diagrama de treinamento, teste e exportação. A comparação Python–C++ recebe os dois preditores; não é apresentada como uma nova avaliação de generalização ou validação agronômica.

## Evidências computacionais verificadas

- Backend e IA: **87 testes aprovados**, com um aviso de descontinuação da integração Starlette/httpx.
- Frontend: **7 testes aprovados** e build TypeScript/Vite concluído.
- Paridade nativa: **43.200 registros**, nenhuma divergência de classe entre Python e C++; maior diferença de probabilidade de aproximadamente **3,01 × 10⁻⁸**.
- As dimensões de programa e variáveis globais citadas no texto provêm do registro anterior de compilação da Heltec V2 no projeto. Não foram apresentadas como nova gravação ou medição em hardware nesta revisão.

As verificações confirmam aspectos de implementação. Não demonstram detecção de fungos, calibração dos sensores ou desempenho de campo.

## Limites que afetam as conclusões

O teste do modelo contém 10.694 exemplos `low`, 106 `moderate` e nenhum `high` ou `critical`. A acurácia de 98,9907% é ligeiramente inferior aos 99,0185% de sempre prever `low`; o recall de `moderate` é zero. Portanto, esse resultado não sustenta alegação de detecção adequada das condições minoritárias.

O F1 macro exportado considera quatro rótulos, com zero para divisões indefinidas; a acurácia balanceada considera as duas classes presentes. Essa diferença foi explicada para evitar comparação incorreta dos indicadores.

A documentação local descreve a base como sintética. O material examinado não comprova rótulos microbiológicos obtidos dos grãos do mini-silo. O texto não atribui uma origem experimental ou licença ao dataset sem documentação disponível.

Permanecem a caracterizar: espécie e massa dos grãos, geometria do recipiente, posição dos sensores, especificações da montagem elétrica, instrumentos de referência, consumo e tempo de inferência na placa. O plano de testes identifica procedimentos e evidências para essas etapas. Os autores devem completar esses registros após ensaios e confirmar a adequação da mudança de tema com o docente antes da entrega.
