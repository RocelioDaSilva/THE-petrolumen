# PetroLúmen - Plataforma Avançada de Engenharia de Petróleo e Reservatórios

**PetroLúmen** é uma plataforma moderna, integrada e de alta performance para Engenharia de Petróleo, Perfuração, Instalações de Superfície e Simulação de Reservatórios, desenvolvida em **React 18**, **TypeScript 5**, **Vite 6** e **Tailwind CSS**.

---

## 🚀 Módulos Integrados

1. **Dashboard Geral**: Painel de controle central com indicadores em tempo real, estado de integridade do sistema, atalhos para módulos operacionais e resumo consolidado do campo.
2. **Engenharia de Perfuração & Operações de Poço**:
   - **Controle de Poço (Well Control)**: Cálculos de Well Control avançados, métodos Drillers Method e Wait & Weight, gradientes de fratura e pressão de poros.
   - **Hidráulica de Perfuração & Reologia**: Modelos de Bingham Plastic e Power Law, perdas de carga no circuito, ECD (Equivalent Circulating Density) e modelos de bit hydraulics (Bourgoyne et al. 1986).
   - **Fluidos de Perfuração & Análise de Retorta**: Ajustes de densidade do lama, composição óleo/água/sólidos e tratamentos com barita.
   - **Cimentação**: Cálculo de volumes de pasta, deslocamento, hidráulica e pressões hidrostáticas em operações de cimentação primária (Carter et al. 2023).
   - **Poço Preso (Stuck Pipe) & Força de Tração**: Análise de aprisionamento diferencial, estimativa de ponto livre (Free Point) e força de estiramento da coluna.
   - **Trajetória e Poços Direcionais**: Cálculo de dogleg severity (DLS), levantamentos direcionais (Minimum Curvature) e projeto de revestimento (Casing Collapse API 5C3).
   - **Operações de Carga da Sonda (Rig Loads & Ton-Miles)**: Cálculos de carga no gancho, fadiga de cabo de perfuração (Ton-Miles) e consumo de energia.
3. **Engenharia de Instalações de Superfície (Facilities)**:
   - **Dimensionamento de Separadores**: Separadores bifásicos e trifásicos horizontais/verticais (Arnold & Stewart 2008).
   - **Tratamento de Óleo e Água**: Dimensionamento de FWKO, tratadores eletrostáticos e tanques de flotação.
   - **Capacidade de Tanques**: Cálculo geométrico de volume de tanques cilíndricos horizontais e verticais.
4. **Simulação de Reservatórios**:
   - **Solucionador Numérico 1D IMPES**: Solução implícita de pressão com matriz tridiagonal e atualização explícita de saturação (água-óleo) com poços produtores/injetores.
   - **Malha Geocelular 3D Interativa**: Visualizador voxel de grade geocelular ($8 \times 8 \times 4 = 256$ blocos) com projeção isométrica, filtros de camadas e mapeamento de propriedades ($\phi$, $k$, $P$, $S_w$, $NTG$).
5. **Análise de Declínio (DCA)**:
   - Modelos empíricos de Arps (Exponencial, Hiperbólico e Harmônico) e modelo não-convencional de Duong (Shale / Tight Gas).
   - Estimativa de EUR (Estimated Ultimate Recovery) e exportação de relatórios executivos em PDF.
6. **Termodinâmica e Propriedades PVT**:
   - Correlações de fator $Z$ do gás (Hall-Yarborough / Standing-Katz), $B_o$, $B_g$, $R_s$, $P_b$ e viscosidades com sanitização estrita e fail-loudly em parâmetros não-físicos.
   - Editor de frações molares para misturas composicionais ($C_1$ a $C_7+$, $N_2$, $CO_2$) e diagrama P-T de envelope de fases.
   - Suporte universal a conversão instantânea entre Sistema de Campo (psia, °F, bbl) e Sistema Internacional (kPa, °C, m³).
7. **Análise Nodal & Elevação de Fluidos**:
   - Curvas IPR (Vogel e Darcy) combinadas com curvas VLP (Beggs & Brill).
   - Ponto de operação ótimo ($q_{op}$ vs $P_{wf}$).
8. **RTA & Balanço de Materiais**:
   - Flowing Material Balance (FMB) para gás ($P/Z$ vs $G_p$) com estimativa de OGIP.
9. **Avaliação Econômica**:
   - Fluxo de caixa descontado, VPL (NPV), Taxa Interna de Retorno (TIR / IRR), Payback e ROI.
10. **Analytics & Machine Learning**:
    - Algoritmos supervisionados (XGBoost, SVR, LSTM) com métricas de erro ($R^2$, RMSE, MAE) e importância de variáveis SHAP.
11. **Perfis de Poço (LAS Logs)**:
    - Visualizador de perfis de poço multifaixa (GR, RT, RHOB, NPHI) com parser robusto de arquivos LAS 2.0 para interpretação petrofísica.

---

## 🛠️ Tecnologias e Arquitetura

- **Frontend & Core Engine**: React 18, TypeScript 5.7, Vite 6.0
- **Roteamento & Carregamento Dinâmico**: Code-splitting 100% sob demanda com `React.lazy()` e `Suspense` acompanhado de skeletons visuais
- **Estilização**: Tailwind CSS 3.4 com tema Claro/Escuro persistido em `localStorage`
- **Isolamento de Estado**: `SessionRegistry` com tipagem estrita e guardas contra vazamento de estado
- **Tratamento de Erros**: `ErrorBoundary` desacoplado, internacionalizado (PT/EN) com diagnóstico em modo desenvolvimento
- **Visualização**: Recharts, Canvas 2D/3D Voxel Engine
- **Exportação**: jsPDF & html2canvas
- **Ícones**: Lucide React
- **Infraestrutura de Testes**: Vitest + Testing Library + Test Runner customizado para benchmarks de engenharia

---

## 💻 Como Executar e Testar

### Instalação de Dependências
```bash
npm install
```

### Servidor de Desenvolvimento
```bash
npm run dev
# Servidor disponível em http://localhost:3000
```

### Verificação de Tipos e Linting
```bash
npm run lint
```

### Execução de Todos os Testes (Benchmarks + Vitest)
```bash
npm test
# Executa simultaneamente:
# 1. 92 benchmarks físicos em 11 suítes de golden tests
# 2. 18 testes unitários de integração via Vitest
```

### Testes Individuais
```bash
# Executa apenas as 11 suítes de benchmarks de engenharia (92 testes)
npm run test:benchmarks

# Executa apenas a suíte de testes unitários Vitest (18 testes)
npm run test:unit
```

### Compilação de Produção & Empacotamento
```bash
# Build de produção
npm run build

# Cria pacote de distribuição pronto para release (petrolumen-release.zip)
npm run package
```

---

## 📄 Documentação

Toda a documentação técnica e relatórios de auditoria estão centralizados no diretório [`docs/`](./docs/):
- [Guia do Desenvolvedor (`docs/DEVELOPER_ONBOARDING.md`)](./docs/DEVELOPER_ONBOARDING.md)
- [Estado do Ambiente & Infraestrutura (`docs/ENVIRONMENT_STATE.md`)](./docs/ENVIRONMENT_STATE.md)
- [Auditoria do Estado Atual (`docs/audits/CURRENT_STATE_AUDIT.md`)](./docs/audits/CURRENT_STATE_AUDIT.md)
- [Instruções de Agentes & Princípios de Engenharia (`AGENTS.md`)](./AGENTS.md)
