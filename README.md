# PetroLúmen - Plataforma Avançada de Engenharia de Petróleo

**PetroLúmen** é uma plataforma moderna e integrada de engenharia de petróleo e simulação de reservatórios desenvolvida em **React 18**, **TypeScript**, **Vite** e **Tailwind CSS**.

---

## 🚀 Módulos Integrados

1. **Dashboard Geral**: Painel de controle integrado com indicadores de integridade do sistema, simulações ativas, modelos calibrados de IA e histórico consolidado do campo.
2. **Simulação de Reservatórios**:
   - Solucionador numérico 1D IMPES de difusividade de pressão com poço produtor/injetor.
   - Malha Geocelular 3D interativa (nx: 8, ny: 8, nz: 4 = 256 blocos) com projeção isométrica, visualização de propriedades (Porosidade, Permeabilidade, Pressão, Sw, NTG) e filtros por camada Z.
3. **Análise de Declínio (DCA)**:
   - Ajuste empírico de Arps (Exponencial, Hiperbólico e Harmônico) e modelo não-convencional de Duong (Shale / Tight Gas).
   - Cálculo de EUR (Estimated Ultimate Recovery) e exportação de relatórios em PDF.
4. **Cálculos e Termodinâmica PVT**:
   - Fator de compressibilidade do gás Z (Hall-Yarborough / Standing-Katz).
   - Propriedades de fluido: FVF de óleo ($B_o$), FVF de gás ($B_g$), Solubilidade ($R_s$), Pressão de Bolha ($P_b$), viscosidade do óleo e gás.
   - Editor de frações molares para fluidos composicionais ($C_1$ a $C_7+$, $N_2$, $CO_2$).
   - Diagrama de envelope de fases P-T (Curvas de ponto de bolha, orvalho e ponto crítico).
   - Alternância dinâmica entre Sistema de Campo (psia, °F, bbl) e Sistema Internacional (kPa, °C, m³).
5. **Análise Nodal**:
   - Curvas de influxo IPR (Vogel e Darcy) combinadas com elevação na coluna VLP (Beggs & Brill).
   - Solução instantânea do ponto de operação ótimo ($q_{op}$ STB/d @ $P_{wf}$ psia).
6. **Rate Transient Analysis (RTA) & Balanço de Materiais**:
   - Flowing Material Balance (FMB) gás ($P/Z$ vs $G_p$) com estimativa de OGIP in-place e diagnóstico de mecanismos de drive.
7. **Avaliação Econômica e Reservas**:
   - Fluxo de caixa descontado, Valor Presente Líquido (VPL / NPV), Taxa Interna de Retorno (TIR / IRR), Payback e ROI.
8. **Analytics Avançado & Machine Learning**:
   - Treinamento supervisionado com algoritmos XGBoost, SVR e Redes Recorrentes LSTM.
   - Métricas de acurácia estatística ($R^2$, RMSE, MAE) e pesos de importância de features SHAP.
9. **Perfis de Poço (LAS Logs)**:
   - Visualizador multifaixa com Raio Gama (GR), Resistividade Profunda (RT), Densidade (RHOB) e Neutrão (NPHI).
10. **Conectores Comerciais**:
    - Gerenciamento de interfaces de comunicação com simuladores comerciais (ECLIPSE, tNavigator, CMG) e plataformas de dados (OSDU, Petrel).

---

## 🛠️ Tecnologias

- **Framework**: React 18 / TypeScript / Vite
- **Estilização**: Tailwind CSS com suporte a tema Claro/Escuro
- **Visualização de Dados**: Recharts & 3D Voxel Engine
- **Exportação de Relatórios**: jsPDF & html2canvas
- **Ícones**: Lucide React

---

## 💻 Como Executar

```bash
# Instalar dependências
npm install

# Iniciar servidor de desenvolvimento (Porta 3000)
npm run dev

# Compilar para produção
npm run build
```
