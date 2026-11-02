
# PetroLúmen - Engenharia de Reservatórios

Aplicação desktop eficiente para Windows, integrando frontend moderno (React/Next.js), backend Python e empacotamento nativo com Tauri para o projeto PetroLúmen.

**Nota sobre o Backend Python:** Os exemplos de código Python neste README referem-se a módulos como `gaia_genesis.reservoir_engineering`. Esta é uma referência ao nome original do projeto Python. Se o backend Python (localizado em `../backend/` e gerenciado separadamente) também for renomeado para alinhar com "PetroLúmen", os nomes dos módulos e as importações nesses exemplos precisarão ser atualizados em conformidade pelo mantenedor do backend.

## Como rodar como aplicativo Windows

1. **Instale as dependências do frontend:**
   No diretório `petrolumen` (este diretório):
   ```bash
   # Se preferir usar npm:
   npm install
   # Ou, se preferir usar yarn:
   yarn install
   # Ou, se preferir usar pnpm:
   pnpm install
   ```
   > Certifique-se de usar apenas um gerenciador de pacotes por vez (npm, yarn ou pnpm) para evitar conflitos de dependências.

2. **Instale as dependências do backend Python:**
   O backend Python é um projeto separado e espera-se que esteja localizado em um diretório chamado `backend` ao lado deste diretório `petrolumen` (ou seja, `../backend/` a partir do diretório `petrolumen`).
   A estrutura esperada para o diretório `backend` é:
   ```
   your-main-project-folder/
   ├── petrolumen/  # Este repositório
   └── backend/     # Backend Python
       ├── main.py  # Ponto de entrada da aplicação FastAPI
       ├── requirements.txt
       └── gaia_genesis/  # Pacote principal do código Python
           └── ...
   ```
   Navegue até o diretório do backend e instale suas dependências:
   ```bash
   cd ../backend  # Ou o caminho para seu diretório de backend
   pip install -r requirements.txt
   ```

3. **Inicie o backend Python localmente:**
   A partir do diretório do backend (ex: `../backend/`), inicie seu servidor Python (FastAPI).
   ```bash
   # Estando no diretório do backend (ex: ../backend/)
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```
   O backend FastAPI estará disponível em `http://localhost:8000`. A aplicação frontend se comunicará com este backend para funcionalidades como upload de dados, análises, etc.

   **Nota Importante sobre o Backend:** Atualmente, a lógica de manipulação de dados no backend (especificamente em `backend/gaia_genesis/reservoir_engineering/data_management.py`) é um *placeholder*. Ela utiliza um armazenamento em memória e validações mínimas, implementado para demonstrar e testar o pipeline de comunicação API. Você precisará substituir esta lógica placeholder pela sua lógica de processamento e armazenamento de dados robusta e definitiva.

4. **Desenvolvimento do Frontend (Tauri):**
   Para rodar o frontend em modo de desenvolvimento com o Tauri (que inclui hot-reloading para a interface web):
   No diretório `petrolumen` (este diretório):
   ```bash
   # Se preferir usar npm:
   npm run tauri dev
   # Ou, se preferir usar yarn:
   yarn tauri dev
   # Ou, se preferir usar pnpm:
   pnpm tauri dev
   ```
   Isso abrirá a aplicação desktop. A interface web (Next.js) se conectará ao backend FastAPI iniciado no passo anterior.

5. **Build do frontend (para empacotamento):**
   No diretório `petrolumen` (este diretório):
   ```bash
   npm run build
   ```

6. **Empacote como app Windows com Tauri:**
   Ainda no diretório `petrolumen`:
   ```bash
   # Instale o Tauri CLI se necessário (se ainda não o fez globalmente)
   # cargo install tauri-cli
   # Rode o comando de build do Tauri (ele usará o `src-tauri` internamente)
   npm run desktop:build
   # Ou diretamente:
   # tauri build
   ```

O instalador `.exe` será gerado em `src-tauri/target/release/bundle`.

---

## Passo a passo para empacotar e distribuir o .exe (Windows)

### 1. Pré-requisitos
- Node.js e npm/yarn/pnpm instalados
- Python instalado (para o backend)
- Rust instalado ([https://rustup.rs](https://rustup.rs))
- Tauri CLI instalado globalmente:
  ```powershell
  cargo install tauri-cli
  ```

### 2. Instale as dependências do frontend
No diretório `petrolumen` (este diretório):
```powershell
npm install
# ou yarn install
# ou pnpm install
```
   > Certifique-se de que está no diretório `petrolumen` antes de executar este comando.
   > Use apenas um gerenciador de pacotes por vez (npm, yarn ou pnpm) para evitar conflitos de dependências.

### 3. Instale as dependências do backend
O backend Python é um projeto separado e espera-se que esteja localizado em um diretório chamado `backend` ao lado deste diretório `petrolumen` (ou seja, `../backend/` a partir daqui). Certifique-se de que ele contenha um arquivo `requirements.txt` e que a estrutura interna seja como descrito na seção "Como rodar como aplicativo Windows".
```powershell
cd ../backend # Ou o caminho para seu diretório de backend
pip install -r requirements.txt
```

### 4. Build do frontend
No diretório `petrolumen` (este diretório):
```powershell
npm run build
```

### 5. Build do Tauri (gera o .exe)
Ainda no diretório `petrolumen` (este diretório):
```powershell
# Se você tem o Tauri CLI instalado globalmente e configurado no seu PATH:
tauri build
# Ou use o script do package.json:
npm run desktop:build
```

### 6. Encontre o instalador
O instalador `.exe` estará em:
```
src-tauri/target/release/bundle/windows/
```

### 7. Distribua
Envie o `.exe` para seus usuários ou publique em um site.

---

## Automatizando com o script PowerShell

Você pode rodar tudo com:
```powershell
cd scripts
./build-windows.ps1
```
Esse script já faz o build do frontend e do Tauri automaticamente.

Biblioteca Python para análise e simulação de reservatórios de petróleo.

## Funcionalidades

### 1. Upload e Validação de Dados
- Suporte a múltiplos arquivos CSV por poço
- Validação automática de colunas e tipos de dados
- Feedback amigável em caso de erro
- Preview dos dados carregados

### 2. Modelos de Declínio
- Exponencial
- Hiperbólico
- Harmônico
- Comparação visual entre modelos
- Cálculo automático do melhor ajuste

### 3. Predição com IA
- XGBoost
- SVR
- Comparador de desempenho
- Otimização de hiperparâmetros
- Gráfico com faixa de incerteza

### 4. Visualização
- Gráficos interativos com Plotly
- Exportação como PNG/PDF
- Gráfico de resíduos
- Zoom e destaque de outliers

### 5. Diagnóstico e Relatório
- Geração automática de relatório PDF
- Parâmetros estimados
- Previsão futura
- Recomendações baseadas em IA
- Exportação para Excel

### 6. Banco de Dados
- PostgreSQL/TimescaleDB
- CRUD completo
- Consulta por campo/poço/data
- Cache de resultados

### 7. Interface e Acesso
- Autenticação JWT
- Painel administrativo
- Histórico de uploads
- Integração com frontend

### 8. Simulação de Reservatórios
- Modelagem de malhas estruturadas e corner-point
- Definição de propriedades petrofísicas (porosidade, permeabilidade)
- Modelagem de falhas geológicas
- Definição e gerenciamento de poços
- Simulação com modelos black-oil, composicional e térmico
- Visualização 3D interativa de malhas e propriedades
- Análise de sensibilidade de parâmetros
- Funcionalidades similares ao Navigator (Rock Flow Dynamics)

## Instalação

```bash
pip install -r requirements.txt
```

## Exemplos de Uso

### Upload e Validação de Dados

```python
from gaia_genesis.reservoir_engineering.data_management import DataUploader

uploader = DataUploader()

# Carrega dados de múltiplos arquivos
data = uploader.load_well_data(
    well_name="P1",
    csv_files=["dados_2020.csv", "dados_2021.csv"]
)

# Preview dos dados
preview = uploader.get_data_preview("P1", n_rows=5)
print(preview)

# Estatísticas
stats = uploader.get_well_statistics("P1")
print(stats)
```

### Análise de Declínio

```python
from gaia_genesis.reservoir_engineering.decline_analysis import AdvancedDeclineAnalysis

analyzer = AdvancedDeclineAnalysis()

# Ajusta modelos
models = analyzer.fit_models(time, rate)

# Previsão futura
future = analyzer.predict_future(months=24)

# Plota resultados
fig = analyzer.plot_decline_curves(time, rate)
fig.show()

# Gera relatório
analyzer.generate_report("P1", "relatorio.pdf")
```

### Predição com IA

```python
from gaia_genesis.reservoir_engineering.prediction import AIPrediction

predictor = AIPrediction()

# Prepara dados
X_train, X_test, y_train, y_test = predictor.prepare_data(
    data=df,
    target_column="q_oleo",
    feature_columns=["q_gas", "q_agua", "pressao"]
)

# Treina modelos
predictor.train_models(X_train, y_train, X_test, y_test)

# Faz previsões
predictions = predictor.predict(X_test)

# Plota resultados
fig = predictor.plot_predictions(X_test, y_test)
fig.show()

# Salva modelo
predictor.save_model("modelo.joblib")
```

### Banco de Dados

```python
from gaia_genesis.reservoir_engineering.database import DatabaseManager

db = DatabaseManager(
    host="localhost",
    port=5432,
    database="reservoir",
    user="user",
    password="pass"
)

# Conecta ao banco
db.connect()

# Cria tabelas
db.create_tables()

# Insere poço
well_id = db.insert_well(
    well_name="P1",
    field_name="Campo A",
    latitude=-23.5,
    longitude=-46.6
)

# Insere dados
db.insert_production_data(well_id, data)

# Consulta dados
well_data = db.get_well_data(
    well_name="P1",
    start_date="2020-01-01",
    end_date="2020-12-31"
)
```

### Simulação de Reservatórios

```python
from gaia_genesis.reservoir_engineering.flow_simulation import ReservoirSimulator
import numpy as np

# Inicializa simulador
simulator = ReservoirSimulator()

# Cria malha estruturada
simulator.create_structured_grid(20, 15, 10, dx=100, dy=100, dz=20)

# Adiciona propriedades
nx, ny, nz = simulator.grid['dims']
porosity = np.random.uniform(0.1, 0.3, (nx, ny, nz))
simulator.add_property('porosity', porosity)
permeability = porosity**3 * 1e4  # Correlação com porosidade
simulator.add_property('permeability', permeability)

# Adiciona poços
simulator.add_well(
    name="PROD-01",
    trajectory=[(5, 5, 0), (5, 5, 5), (10, 10, 8)],
    completions=[{'i': 10, 'j': 10, 'k': 8, 'diameter': 0.1}]
)

simulator.add_well(
    name="INJ-01",
    trajectory=[(15, 12, 0), (15, 12, 8)]
)
simulator.convert_well_type("INJ-01", "injector")

# Executa simulação
simulator.run_simulation(end_time=1825, time_step=30)  # 5 anos

# Visualiza resultados
simulator.plot_property_slice('porosity')
simulator.plot_3d_model()
simulator.plot_well_results("PROD-01")
simulator.plot_field_results()

# Análise de sensibilidade
sensitivity = simulator.run_sensitivity_analysis(
    parameter='porosity',
    values=[0.1, 0.15, 0.2, 0.25, 0.3],
    metric='cum_oil'
)
simulator.plot_sensitivity_results(sensitivity, 'porosity', 'cum_oil')
```

### Autenticação

```python
from gaia_genesis.reservoir_engineering.api import AuthManager

auth = AuthManager(
    secret_key="sua_chave_secreta",
    access_token_expire_minutes=30
)

# Conecta ao banco
auth.connect_db(
    host="localhost",
    port=5432,
    database="reservoir",
    user="user",
    password="pass"
)

# Cria usuário
user_id = auth.create_user(
    username="admin",
    email="admin@example.com",
    password="senha123",
    is_admin=True
)

# Autentica usuário
user = auth.authenticate_user("admin", "senha123")
if user:
    token = auth.create_access_token({"sub": user["username"]})
```

## Testes

```bash
pytest tests/
```

## Documentação

A documentação completa está disponível em [docs/](docs/).

## Contribuição

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/nova-feature`)
3. Commit suas mudanças (`git commit -am 'Adiciona nova feature'`)
4. Push para a branch (`git push origin feature/nova-feature`)
5. Crie um Pull Request

## Licença

Este projeto está licenciado sob a licença MIT - veja o arquivo [LICENSE](LICENSE) para detalhes.

---

## Component Documentation

To ensure clarity and maintainability of our frontend components, please follow these documentation practices:

### JSDoc/TSDoc Comments

*   All React components, especially those in `components/ui/` and shared components within `app/components/`, should have JSDoc/TSDoc comment blocks.
*   The comment block should provide a clear description of the component's purpose and general usage.
*   For components that accept props, their `Props` interface/type should be clearly defined. If not immediately obvious, complex or important props can be described using TSDoc annotations within the interface. Example:
    ```typescript
    export interface MyComponentProps {
      /** The title to display in the component. */
      title: string;
      /** Optional callback function for when the component is clicked. */
      onClick?: () => void;
      variant: "primary" | "secondary";
    }

    /**
     * MyComponent is a versatile component that displays a title and can be clicked.
     * It supports primary and secondary visual variants.
     */
    const MyComponent: React.FC<MyComponentProps> = ({ title, onClick, variant }) => {
      // ... component logic
    };
    ```
*   See `petrolumen/components/ui/button.tsx` and `petrolumen/components/ui/card.tsx` for examples.

### Storybook (Future Enhancement)

While not yet implemented, we plan to integrate [Storybook](https://storybook.js.org/) for developing and showcasing UI components in isolation. This will provide an interactive component library, making it easier to visualize different component states and props.

**Guidelines for Storybook (when implemented):**
*   Each UI component in `components/ui/` should have a corresponding Storybook story.
*   Stories should demonstrate various states and prop combinations of the component.

By consistently documenting our components, we can improve collaboration, ease onboarding for new developers, and make the codebase more understandable.
