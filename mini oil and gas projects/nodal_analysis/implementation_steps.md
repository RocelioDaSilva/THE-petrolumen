# Nodal Analysis — Implementation Steps

1. Criar ambiente virtual e instalar dependências:

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r ../requirements.txt
```

2. Colocar parâmetros de exemplo em `data/nodal_example.csv` (parâmetros: `qi`, `pr`, `p_surf`, `a`, `b`).
3. Executar:

```bash
python nodal_analysis.py
```

4. Validar gráfico IPR/TPR e o ponto de operação; refatorar funções para aceitar input CSV.
5. Adicionar testes para a função `residual(q)` e documentação dos parâmetros.
