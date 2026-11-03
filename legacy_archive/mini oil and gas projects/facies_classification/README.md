Classificação de Fácies (ML)

Objetivo
- Treinar um classificador (RandomForest / CNN) para prever fácies a partir de logs (gamma, resistividade, densidade, etc.).

Pré-requisitos
- `pip install -r ../requirements.txt`

Passos
1. Preparar dataset: CSV com registros de profundidade e atributos de logging + etiqueta de fácies.
2. Tratar dados: preencher valores ausentes, normalizar/standardize.
3. Treinar baseline com `RandomForestClassifier`.
4. Validar com cross-validation; reportar métricas (accuracy, f1 por classe).
5. (Opcional) Implementar CNN em janelas para classificação de fácies locais.

Arquivo principal: `facies_classification.py`