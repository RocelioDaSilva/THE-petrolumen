# 02. Canvas do MVP

## 1. Objetivo
Este documento resume a lógica do produto em uma visão enxuta, buscando responder com clareza: para quem o PetroLúmen será útil, qual problema resolve, como será entregue e o que deve entrar na primeira versão.

## 2. Lean canvas

### Problema
- dados técnicos espalhados em ferramentas e arquivos;
- cálculos repetitivos e pouco automatizados;
- baixa transparência metodológica em workflows de engenharia;
- dificuldade de comparar cenários de produção, reservatório e perfuração;
- dependência de processos manuais e pouco rastreáveis.

### Segmentos de clientes
- empresas de óleo e gás;
- consultorias de engenharia;
- equipes de reservatórios e perfuração;
- instituições acadêmicas;
- profissionais independentes e analistas técnicos.

### Proposta de valor
Uma plataforma para análise técnica integrada de petróleo e reservatórios, com cálculos verificáveis, visualizações e suporte à comparação de cenários em um único ambiente.

### Solução
- motores de cálculos para PVT, perfuração, reservatórios e produção;
- visualização de resultados e gráficos;
- parsing e classificação de dados de poço;
- análise de cenários operacionais e económicos;
- interface para uso por engenharia aplicada.

### Métricas de produto
- número de cálculos executados por sessão;
- taxa de sucesso de workflows;
- tempo de execução por tipo de análise;
- taxa de adoção por disciplina;
- número de cenários comparados por usuário.

### Vantagem injusta
- rigor técnico e transparência metodológica;
- arquitetura modular e expansível;
- foco em código aberto e integração técnica;
- potencial para evolução com IA e automação.

### Canais
- GitHub / repositório aberto;
- demonstrações técnicas;
- apresentações para clientes e parceiros;
- documentação e onboarding;
- networking com instituições e laboratórios de engenharia.

### Estrutura de custos
- desenvolvimento de software;
- manutenção de infraestrutura;
- documentação e validação técnica;
- suporte a testes e benchmark;
- evolução de módulos e integração.

### Fluxo de receitas
- licenciamento do software;
- serviços de customização e integração;
- assinatura para uso institucional;
- projetos de consultoria e modelagem;
- módulos premium de análise e IA.

### MVP recomendado
O MVP deve incluir:
1. cálculo de PVT e material balance;
2. análise nodal;
3. geologia e visualização básica de malha;
4. importação e leitura de .las;
5. economia de produção;
6. dashboard de cenários e resultados.

### Critérios de sucesso do MVP
- execução estável dos módulos principais;
- interface funcional e clara;
- qualidade de resultados aceitável para decisão técnica;
- testes e documentação suficientes para validação.

---

## 3. Decisão de escopo
O MVP não deve incluir, na primeira fase:
- simulação composicional complexa;
- autenticação avançada de usuários;
- integração com DB empresarial robusta;
- IA aplicada a todos os workflows;
- modelos de produção completamente auto-operados.

O foco é provar utilidade real e qualidade técnica antes de escalar funcionalidade.
