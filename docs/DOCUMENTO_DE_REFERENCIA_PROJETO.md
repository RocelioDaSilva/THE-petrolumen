# PetroLúmen
## Documento de Referência do Projeto

> Versão: 1.0  
> Data: 07/11/2026  
> Estado: Documento de referência técnico-económico e de arquitetura

---

## 1. Resumo Executivo

O PetroLúmen é uma plataforma de engenharia de petróleo e reservatórios concebida para unificar cálculo técnico, visualização de cenários e apoio à tomada de decisão em operações upstream, facilities e análise de produção. O projeto combina uma aplicação web moderna em React + TypeScript com um backend em FastAPI, oferecendo motores de cálculo para PVT, perfuração, geologia, reservatórios, petrofísica, facilities, economia e simulação.

A visão do projecto é transformar o conhecimento técnico de engenharia de petróleo num ambiente acessível, verificável e extensível, com foco em rigor matemático, transparência de metodologia e capacidade de evolução para workflows impulsionados por IA. A arquitetura está desenhada para que cada módulo possa ser validado independentemente e integrado de forma modular, sem depender de um único fornecedor ou de um ecossistema fechado.

Em termos de maturidade, o sistema já incorpora múltiplos módulos funcionais, incluindo cálculo de trajectórias de poço, análise nodal, material balance, classificação de fácies, cálculo de economia de produção, parsing de arquivos LAS e geração de visuais. O projeto já apresenta um conjunto robusto de capacidades técnicas, sendo um excelente ponto de partida para um produto de engenharia aplicada com uso industrial e académico.

---

## 2. Contexto e Motivação

A engenharia de petróleo exige a coordenação de dados geológicos, petrofísicos, de fluidos, de produção, de custos e de restrições operacionais. Em muitos contextos, estas atividades encontram-se fragmentadas entre ferramentas isoladas, processos manuais e relatórios dispersos. O resultado é uma perda de tempo, maior risco de erro, pouca rastreabilidade e dificuldades em comparar cenários.

O PetroLúmen nasce para resolver esse problema, propondo uma plataforma única que encapsula o ciclo de trabalho de engenharia:

- aquisição e tratamento de dados de poços;
- interpretação dos dados petrofísicos;
- modelação de fluidos e reservatórios;
- análise de desempenho de poços e campos;
- avaliação económica e de viabilidade;
- apoio à decisão em cenários de produção e desenvolvimento.

Esta abordagem facilita a interoperabilidade entre disciplinas e reduz a dependência de conhecimento disperso entre ficheiros, planilhas e scripts informais.

---

## 3. Objetivos do Projeto

### 3.1 Objetivo principal
Desenvolver uma plataforma de engenharia de petróleo e reservatórios com foco em cálculo científico, validação de metodologias e utilização em ambiente de investigação e negócio.

### 3.2 Objetivos operacionais
- Centralizar motores de cálculo em um ambiente de referência;
- manter critérios de validação e documentação das fórmulas usadas;
- permitir visualização rápida de cenários e resultados;
- integrar unidades de medida de forma consistente;
- apoiar workflows de exploração, desenvolvimento e produção;
- preparar a plataforma para integração com ferramentas de IA e automação de engenharia.

### 3.3 Objetivos estratégicos
- reduzir o custo de análise técnica;
- acelerar a comparação de cenários;
- aumentar a transparência metodológica;
- apoiar a comunicação técnico-comercial entre equipes de engenharia e gestão;
- construir uma base tecnológica escalável em direção a um produto de mercado.

---

## 4. Visão de Produto

O PetroLúmen não é apenas uma calculadora. É uma workbench de engenharia de reservatórios e petróleo, pensada para servir como base de um ambiente operacional de avaliação técnica e decisão.

A plataforma é pensada para:

- suportar múltiplos domínios técnicos;
- manter a lógica de cálculo separada da interface;
- permitir consulta a resultados em linguagem natural e formatos técnicos;
- preparar integrações futuras com simulação avançada, agentes de IA e fluxos automáticos.

O produto combina rigor científico com acessibilidade de uso, oferecendo uma forma prática de aplicar engenharia num ambiente digital, sem necessidade de depender exclusivamente de software proprietário ou de processos manualmente fragmentados.

---

## 5. Arquitetura do Sistema

### 5.1 Visão geral
A solução combina uma aplicação front-end em React 18 + TypeScript 5 + Vite com um backend em FastAPI e uma camada de motores de cálculo em TypeScript/Python, conforme o modelo do repositório atual.

A arquitetura do projeto pode ser entendida em 5 camadas principais:

1. Camada de apresentação
   - interface web e desktop;
   - visualizações de gráficos e dashboards;
   - componentes de entrada de dados e parâmetros.

2. Camada de aplicação e API
   - endpoints REST para cálculo e workflows;
   - validação de parâmetros;
   - orquestração de execução.

3. Camada de domínio técnico
   - PVT, perfuração, reservatório, petrofísica, facilities, economia;
   - fórmulas e correlações integradas;
   - validação por benchmarks e testes.

4. Camada de dados e contexto
   - unidades, conversões, registry de sessões e contexto de execução;
   - consistência de dados e gestão do estado de cenário.

5. Camada de extensão e futuro
   - integração com IA, agentes, simulação avançada e orquestração de jobs.

### 5.2 Componentes principais

- Frontend: React + TypeScript + Vite + Tailwind CSS
- Backend: FastAPI
- Cálculos e bibliotecas: TypeScript (módulos de engenharia) e Python (API/backend)
- Visualização: gráficos e painéis de análise
- Testes: golden tests, unit tests e validações de benchmark

---

## 6. Módulos Técnicos e Capacidades Atuais

A plataforma já integra múltiplos módulos relevantes para engenharia de petróleo. A tabela abaixo resume a capacidade atual principal:

| Área | Função principal | Estado atual |
|---|---|---|
| Perfuração | Trajectória de poço, hidráulica, rig loads, casing design, well control | Funcional e validado |
| Geologia | Geração de malha, volumes e visualização 3D | Funcional |
| PVT | Cálculo EOS, Z-factor, material balance | Funcional |
| Reservatório | Análise nodal, IPR/TPR, simulador black-oil | Funcional |
| Petrofísica | Interpretação de LAS, classificação de fácies | Funcional |
| Facilities | Separação de fases, capacidade de tanques, tratamento de água | Funcional |
| Economia | NPV, IRR, payback, sensibilidade fiscal | Funcional |
| Simulação | Workflow de simulação e preparação para módulos mais avançados | Em evolução |

### 6.1 Endpoints operacionais relevantes
A API atual expõe vários endpoints funcionando para cálculo e visualização. Entre os principais, destacam-se:

- `/api/engine/drilling/trajectory`
- `/api/engine/geology/grid`
- `/api/engine/petrophysics/facies/classify`
- `/api/engine/production/economics`
- `/api/engine/pvt/eos`
- `/api/engine/pvt/mbal`
- `/api/engine/reservoir/nodal`
- `/api/petrophysics/las/parse`
- `/api/simulate/black-oil`
- `/health`

Estes endpoints demonstram a existência de um core técnico coerente e utilizável, com foco em aplicações operacionais reais.

---

## 7. Engines e Metodologias Integradas

A documentação do projecto refere uma base de cálculo apoiada em metodologias consolidadas da indústria petrolífera e referências académicas. Os módulos do repositório incorporam abordagem baseada em:

- perfuração e hidráulica segundo padrões clássicos e bibliografia técnico-académica;
- PVT e propriedades de fluidos;
- material balance e análise nodal;
- petrofísica e classificação de fácies;
- análise económica de produção.

Além disso, a visão arquitetónica do sistema aponta para um horizonte futuro que inclui simulação mais realista e uso de ferramentas abertas e livres, como OPM Flow, JutulDarcy, MRST, pyResToolbox e outras bibliotecas de código aberto relacionadas a reservatórios e IA.

---

## 8. Integração com IA e Workflow de Engenharia Assistida

Uma das grandes vantagens do projecto é a sua capacidade de evoluir para workflows de engenharia assistida por IA. A arquitetura atual já sugere um caminho natural para a adoção de agentes e modelos generativos para tarefas como:

- interpretação automática de dados de poço;
- geração de cenários de produção;
- comparação automática de casos;
- análise de incertezas e sensibilidade;
- roteamento de cálculos para a biblioteca correta;
- geração de relatórios técnicos com base em dados e validação.

A reposição de um motor de IA deve ocorrer com rigor: as saídas do sistema devem continuar a ser verificáveis, auditáveis e transparentes em termos de metodologia.

---

## 9. Estado Atual do Projeto

### 9.1 Maturidade
O projecto encontra-se num estado de maturidade funcional e de validação técnica, com módulos implementados e testados, mas ainda com espaço para evolução em áreas como:

- persistência de dados;
- autenticação e autorização;
- publicação de simulação mais sofisticada;
- composição de workflows complexos;
- integração com base de dados estruturada e gestão de projetos.

### 9.2 Limitações conhecidas
A documentação do projeto identifica alguns limites relevantes:

- o simulador black-oil é ainda um modelo simplificado, com aproximações documentadas;
- os módulos de simulação mais avançados ainda estão em fase de amadurecimento;
- a ausência de camada de persistência limita a gestão de estado e histórico de execução;
- a plataforma ainda não possui mecanismo completo de controlo de acesso.

Estas limitações não invalidam o valor do projecto; antes, apontam para um caminho de evolução técnico e operacional claro.

---

## 10. Proposta de Valor

O PetroLúmen agrega valor em três frentes principais:

### 10.1 Valor técnico
- unifica engenharia e cálculo em um ambiente coeso;
- reduz erros por gestão manual de parâmetros e resultados;
- melhora a transparência das metodologias aplicadas.

### 10.2 Valor operacional
- acelera análise de cenário, comparações e decisões;
- apoia trabalho de equipe multidisciplinar;
- permite maior rapidez na avaliação de casos de produção e desenvolvimento.

### 10.3 Valor estratégico
- cria uma base para produto escalável e comercializável;
- transforma conhecimento técnico em plataforma reutilizável;
- abre caminho para inteligência artificial aplicada à engenharia petrolífera.

---

## 11. Roadmap Proposto

### Fase 1 — Base funcional
- estabilização de API e módulos core;
- consolidação de testes e validação matemática;
- revisão de unidades e consistência de dados.

### Fase 2 — Maturação de simulação
- melhoria do simulador de reservatórios;
- integração de workflows mais completos de material balance e produção;
- gestão de projetos e cenários.

### Fase 3 — Plataforma operativa
- persistência e histórico de casos;
- gestão de usuários e permissões;
- dashboards executivos e relatórios padronizados.

### Fase 4 — IA e automação
- agentes para interpretação e geração de análises;
- otimização de procedimentos técnicos;
- integração com simuladores externos e ferramentas open-source.

---

## 12. Conclusão

O PetroLúmen constitui uma solução estratégica e tecnicamente relevante para a engenharia de petróleo e reservatórios. O projecto combina uma base sólida de cálculos, um frontend atual, uma API funcional e uma visão arquitetónica clara para evolução. Não se trata apenas de um protótipo isolado, mas de uma plataforma com potencial para se tornar um ambiente completo de análise, simulação e apoio à decisão técnica.

A sua maior força está na combinação de rigor técnico, clareza metodológica e flexibilidade para crescer em direção a um ecossistema de engenharia ampliado, incluindo IA, agentes de software e integração de simuladores de código aberto.

Desta forma, o PetroLúmen não só resolve necessidades imediatas de cálculo e análise, como também constrói uma base sólida para um produto de engenharia petrolífera mais inteligente, integrado e escalável.

---

## 13. Referências Internas

- [README.md](../README.md)
- [docs/README.md](./README.md)
- [docs/ARCHITECTURE_VISION.md](./ARCHITECTURE_VISION.md)
- [docs/MODULE_STATUS.md](./MODULE_STATUS.md)

---

## 14. Assinatura do Documento

Documento preparado com base na análise do repositório e na documentação interna do projeto, com foco na descrição técnica, arquitetural e estratégica do PetroLúmen.
