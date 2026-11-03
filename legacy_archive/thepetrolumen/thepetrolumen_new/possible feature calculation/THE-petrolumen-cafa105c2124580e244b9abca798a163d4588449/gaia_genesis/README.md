# Gaia Genesis - Reservoir Engineering Toolkit

Um toolkit Python para engenharia de reservatórios que fornece ferramentas para análise e simulação de reservatórios de petróleo e gás.

## Funcionalidades

### 1. Propriedades PVT
- Cálculo de fatores de volume de formação (Bo, Bg)
- Cálculo de viscosidades
- Cálculo de relação gás-óleo em solução (Rs)
- Cálculo de fator de compressibilidade (Z)

### 2. Simulação de Reservatório
- Simulação numérica 3D
- Gerenciamento de poços
- Simulação transiente e estacionária
- Propriedades da malha

### 3. Balanço de Materiais
- Cálculo de OGIP e STOIIP
- Método de Havlena-Odeh
- Suporte a diferentes mecanismos de produção

### 4. Testes de Poço
- Análise de build-up
- Análise de drawdown
- Cálculo de permeabilidade e skin
- Raio de investigação

### 5. Análise de Declínio
- Ajuste de curvas de declínio (Arps)
- Previsão de produção
- Cálculo de EUR
- Vida remanescente

### 6. Ajuste de Histórico
- Otimização de parâmetros
- Análise de sensibilidade
- Análise de incerteza

### 7. Visualização
- Mapas de saturação e pressão
- Performance de poços
- Seções transversais
- Visualização 3D

## Instalação

1. Clone o repositório:
```bash
git clone https://github.com/seu-usuario/gaia-genesis.git
cd gaia-genesis
```

2. Instale as dependências:
```bash
pip install -r requirements.txt
```

## Uso

Exemplo básico de uso:

```python
from gaia_genesis.reservoir_engineering import (
    PVTProperties,
    ReservoirSimulation,
    MaterialBalance,
    WellTesting,
    DeclineAnalysis,
    HistoryMatching,
    ReservoirVisualization
)

# Cálculo de propriedades PVT
pvt = PVTProperties()
bo = pvt.calculate_formation_volume_factor(
    pressure=3000,
    temperature=180,
    fluid_type='oil',
    api_gravity=35
)

# Simulação de reservatório
simulator = ReservoirSimulation(nx=50, ny=50, nz=10)
simulator.add_well(
    name='P1',
    i=25,
    j=25,
    k=0,
    well_type='producer',
    rate=1000
)

# Análise de declínio
decline = DeclineAnalysis()
params = decline.fit_arps(
    time=time_array,
    rate=rate_array,
    method='hyperbolic'
)
eur = decline.calculate_eur(params, economic_limit=100)

# Visualização
viz = ReservoirVisualization(simulator)
fig = viz.plot_saturation_map(layer=0)
```

## Contribuindo

Contribuições são bem-vindas! Por favor, leia o guia de contribuição antes de submeter um pull request.

## Licença

Este projeto está licenciado sob a licença MIT - veja o arquivo LICENSE para detalhes. 