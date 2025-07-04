import streamlit as st
from pvt.z_factor import calculate_z_factor
from pvt.dca import fit_decline_curve, plot_decline_curve
from pvt.correlations import hall_yarborough_z_factor, dranchuk_abu_kassem_z_factor, calculate_uncertainty_z_factor
from pvt.mbal import MaterialBalance
import pandas as pd
import matplotlib.pyplot as plt
import io
import numpy as np
from geology.model3d import GeologicalModel3D
import tempfile
import os
from geology.reservoir_characterization import ReservoirCharacterization
from geology.geostatistics import Geostatistics
from geology.petrophysics import PetrophysicalMapping
from geology.sensitivity import SensitivityAnalysis
from geology.flow_simulation import FlowSimulation
from geology.flow_history_matching import FlowHistoryMatching
from geology.uncertainty_analysis import UncertaintyAnalysis
from geology.production_optimization import ProductionOptimization
from production_analysis import ProductionAnalysis
from reserves_evaluation import ReservesEvaluation

st.title("Gaia Genesis - Reservatórios")

# =========================
# 1. Cálculo de Z-Factor
# =========================
st.header("Cálculo de Z-Factor")

# Seleção da correlação
correlation = st.selectbox(
    "Selecione a correlação",
    ["Standing & Katz", "Hall-Yarborough", "Dranchuk-Abu-Kassem"]
)

pressure = st.number_input("Pressão (psia)", value=1000.0)
temperature = st.number_input("Temperatura (°R)", value=520.0)
composition = {
    "C1": st.number_input("C1 (fração molar)", value=0.8),
    "C2": st.number_input("C2 (fração molar)", value=0.1),
    "C3": st.number_input("C3 (fração molar)", value=0.05),
    "C4": st.number_input("C4 (fração molar)", value=0.03),
    "C5": st.number_input("C5 (fração molar)", value=0.02)
}

# Normalizar composição
total = sum(composition.values())
composition = {k: v/total for k, v in composition.items()}

# Análise de incertezas
show_uncertainty = st.checkbox("Mostrar análise de incertezas")
n_samples = st.slider("Número de amostras para Monte Carlo", 100, 10000, 1000) if show_uncertainty else 1000

if st.button("Calcular Z-Factor"):
    # Calcular Z-Factor base
    if correlation == "Hall-Yarborough":
        z = hall_yarborough_z_factor(pressure, temperature)
    elif correlation == "Dranchuk-Abu-Kassem":
        z = dranchuk_abu_kassem_z_factor(pressure, temperature)
    else:  # Standing & Katz
        z = calculate_z_factor(pressure, temperature, composition)
    
    st.write(f"Z-Factor: {z:.4f}")
    
    if show_uncertainty:
        z_mean, z_std, z_ci = calculate_uncertainty_z_factor(
            pressure, temperature, composition,
            correlation.lower().replace(" & ", "_").replace("-", "_"),
            n_samples
        )
        st.write(f"Média: {z_mean:.4f}")
        st.write(f"Desvio Padrão: {z_std:.4f}")
        st.write(f"Intervalo de Confiança (95%): [{z_ci[0]:.4f}, {z_ci[1]:.4f}]")

    # Plot Z-Factor vs Pressão para uma faixa de pressões
    pressures = np.linspace(100, pressure, 50)
    z_values = []
    z_uncertainty = []
    
    for p in pressures:
        if correlation == "Hall-Yarborough":
            z = hall_yarborough_z_factor(p, temperature)
        elif correlation == "Dranchuk-Abu-Kassem":
            z = dranchuk_abu_kassem_z_factor(p, temperature)
        else:  # Standing & Katz
            z = calculate_z_factor(p, temperature, composition)
        z_values.append(z)
        
        if show_uncertainty:
            z_mean, z_std, _ = calculate_uncertainty_z_factor(
                p, temperature, composition,
                correlation.lower().replace(" & ", "_").replace("-", "_"),
                n_samples
            )
            z_uncertainty.append(z_std)
    
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(pressures, z_values, marker='o', label='Z-Factor')
    
    if show_uncertainty:
        ax.fill_between(pressures,
                       np.array(z_values) - np.array(z_uncertainty),
                       np.array(z_values) + np.array(z_uncertainty),
                       alpha=0.2, label='Incerteza (±1σ)')
    
    ax.set_xlabel("Pressão (psia)")
    ax.set_ylabel("Z-Factor")
    ax.set_title(f"Z-Factor vs. Pressão ({correlation})")
    ax.grid(True)
    ax.legend()
    st.pyplot(fig)

    # Exportar gráfico em PNG
    buf = io.BytesIO()
    fig.savefig(buf, format="png")
    st.download_button(
        label="Baixar gráfico PNG",
        data=buf.getvalue(),
        file_name=f"zfactor_vs_pressao_{correlation.lower().replace(' & ', '_').replace('-', '_')}.png",
        mime="image/png"
    )

# =========================
# 2. Análise de Curvas de Declínio (DCA)
# =========================
st.header("Análise de Curvas de Declínio (DCA)")
dca_file = st.file_uploader("Carregue os dados de produção (CSV ou Excel)", type=["csv", "xlsx"], key="dca_file")
if dca_file is not None:
    if dca_file.name.endswith('.csv'):
        df_dca = pd.read_csv(dca_file)
    else:
        df_dca = pd.read_excel(dca_file)
    
    st.write("Prévia dos dados de produção:")
    st.dataframe(df_dca.head())
    
    # Seleção de colunas
    time_col = st.selectbox("Selecione a coluna de tempo (dias)", df_dca.columns)
    rate_col = st.selectbox("Selecione a coluna de taxa de produção", df_dca.columns)
    
    # Tipo de declínio
    decline_type = st.selectbox(
        "Selecione o tipo de declínio",
        ["hyperbolic", "exponential", "harmonic"]
    )
    
    if st.button("Ajustar Curva de Declínio"):
        time = df_dca[time_col].values
        rate = df_dca[rate_col].values
        
        # Ajustar curva
        qi, Di, b = fit_decline_curve(time, rate, decline_type)
        
        # Mostrar resultados
        st.write(f"Taxa inicial (qi): {qi:.2f}")
        st.write(f"Taxa de declínio (Di): {Di:.4f}")
        if decline_type == "hyperbolic":
            st.write(f"Expoente de declínio (b): {b:.4f}")
        
        # Plotar curva
        fig, ax = plot_decline_curve(time, rate, qi, Di, b, decline_type)
        st.pyplot(fig)
        
        # Exportar gráfico
        buf = io.BytesIO()
        fig.savefig(buf, format="png")
        st.download_button(
            label="Baixar gráfico PNG",
            data=buf.getvalue(),
            file_name="curva_declinio.png",
            mime="image/png"
        )

# =========================
# 3. Interpolação de Propriedades PVT
# =========================
st.header("Interpolação de Propriedades PVT")
uploaded_file = st.file_uploader("Faça upload da tabela PVT (CSV ou Excel)", type=["csv", "xlsx"])
if uploaded_file is not None:
    if uploaded_file.name.endswith('.csv'):
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file)
    st.write("Prévia dos dados importados:")
    st.dataframe(df.head())

    interp_p = st.number_input("Pressão para interpolação (psia)", value=1000.0, key="interp_p")
    interp_t = st.number_input("Temperatura para interpolação (°R)", value=520.0, key="interp_t")

    from scipy.interpolate import griddata
    # Densidade
    if {'Pressão', 'Temperatura', 'Densidade'}.issubset(df.columns):
        points = df[['Pressão', 'Temperatura']].values
        values = df['Densidade'].values
        interp_value = griddata(points, values, [(interp_p, interp_t)], method='linear')
        st.write(f"Densidade interpolada: {interp_value[0]:.4f}")
    # Viscosidade
    if {'Pressão', 'Temperatura', 'Viscosidade'}.issubset(df.columns):
        points = df[['Pressão', 'Temperatura']].values
        values = df['Viscosidade'].values
        interp_value = griddata(points, values, [(interp_p, interp_t)], method='linear')
        st.write(f"Viscosidade interpolada: {interp_value[0]:.4f}")
    # Compressibilidade
    if {'Pressão', 'Temperatura', 'Compressibilidade'}.issubset(df.columns):
        points = df[['Pressão', 'Temperatura']].values
        values = df['Compressibilidade'].values
        interp_value = griddata(points, values, [(interp_p, interp_t)], method='linear')
        st.write(f"Compressibilidade interpolada: {interp_value[0]:.4f}")

    # Aviso se faltar colunas
    if not (
        {'Pressão', 'Temperatura', 'Densidade'}.issubset(df.columns) or
        {'Pressão', 'Temperatura', 'Viscosidade'}.issubset(df.columns) or
        {'Pressão', 'Temperatura', 'Compressibilidade'}.issubset(df.columns)
    ):
        st.warning("O arquivo deve conter as colunas: Pressão, Temperatura e pelo menos uma de Densidade, Viscosidade ou Compressibilidade.")

# =========================
# 4. Estimativa Volumétrica Simples (OOIP/OGIP)
# =========================
st.header("Estimativa Volumétrica Simples")

tab_ooip, tab_ogip = st.tabs(["OOIP (Óleo)", "OGIP (Gás)"])

with tab_ooip:
    st.subheader("Cálculo de OOIP (Óleo Original em Lugar)")
    area = st.number_input("Área do reservatório (ac)", value=640.0, min_value=0.0)
    espessura = st.number_input("Espessura média (ft)", value=50.0, min_value=0.0)
    porosidade = st.number_input("Porosidade (fração)", value=0.2, min_value=0.0, max_value=1.0)
    so = st.number_input("Saturação de óleo (fração)", value=0.7, min_value=0.0, max_value=1.0)
    bo = st.number_input("Fator de volume de formação do óleo (bbl/STB)", value=1.2, min_value=0.1)
    if st.button("Calcular OOIP"):
        # Fórmula clássica: OOIP = 7758 * A * h * φ * So / Bo
        ooip = 7758 * area * espessura * porosidade * so / bo
        st.success(f"OOIP: {ooip:,.0f} STB")

with tab_ogip:
    st.subheader("Cálculo de OGIP (Gás Original em Lugar)")
    area_g = st.number_input("Área do reservatório (ac)", value=640.0, min_value=0.0, key="area_g")
    espessura_g = st.number_input("Espessura média (ft)", value=50.0, min_value=0.0, key="espessura_g")
    porosidade_g = st.number_input("Porosidade (fração)", value=0.2, min_value=0.0, max_value=1.0, key="porosidade_g")
    sg = st.number_input("Saturação de gás (fração)", value=0.8, min_value=0.0, max_value=1.0, key="sg")
    bg = st.number_input("Fator de volume de formação do gás (ft³/SCF)", value=0.005, min_value=0.0001, key="bg")
    if st.button("Calcular OGIP"):
        # Fórmula clássica: OGIP = 43560 * A * h * φ * Sg / Bg
        ogip = 43560 * area_g * espessura_g * porosidade_g * sg / bg
        st.success(f"OGIP: {ogip:,.0f} SCF")

# =========================
# 5. Visualização Básica de Curvas PVT
# =========================
st.header("Visualização de Curvas PVT")
pvt_file = st.file_uploader("Carregue uma tabela PVT para plotar curvas (CSV ou Excel)", type=["csv", "xlsx"], key="pvt_plot")
if pvt_file is not None:
    if pvt_file.name.endswith('.csv'):
        df_plot = pd.read_csv(pvt_file)
    else:
        df_plot = pd.read_excel(pvt_file)
    st.write("Prévia dos dados importados:")
    st.dataframe(df_plot.head())

    colunas_plot = st.multiselect("Selecione as colunas para plotar (eixo Y)", [c for c in df_plot.columns if c.lower() != "pressão"])
    if colunas_plot:
        fig2, ax2 = plt.subplots()
        for col in colunas_plot:
            ax2.plot(df_plot['Pressão'], df_plot[col], marker='o', label=col)
        ax2.set_xlabel("Pressão (psia)")
        ax2.set_ylabel("Propriedade")
        ax2.set_title("Curvas PVT")
        ax2.legend()
        st.pyplot(fig2)

        buf2 = io.BytesIO()
        fig2.savefig(buf2, format="png")
        st.download_button(
            label="Baixar gráfico PNG",
            data=buf2.getvalue(),
            file_name="curvas_pvt.png",
            mime="image/png"
        )

# =========================
# 5. Balanço de Materiais (MBAL)
# =========================
st.header("Balanço de Materiais (MBAL)")

# Seleção do tipo de reservatório
reservoir_type = st.selectbox(
    "Tipo de Reservatório",
    ["Óleo", "Gás"],
    key="mbal_type"
)

# Upload de dados históricos
st.subheader("Dados Históricos")
history_file = st.file_uploader("Carregue o arquivo com dados históricos (CSV ou Excel)", type=["csv", "xlsx"], key="mbal_history")
if history_file is not None:
    if history_file.name.endswith('.csv'):
        df_history = pd.read_csv(history_file)
    else:
        df_history = pd.read_excel(history_file)
    
    st.write("Prévia dos dados históricos:")
    st.dataframe(df_history.head())
    
    # Seleção de colunas
    date_col = st.selectbox("Coluna de data", df_history.columns)
    pressure_col = st.selectbox("Coluna de pressão (psia)", df_history.columns)
    if reservoir_type == "Óleo":
        oil_prod_col = st.selectbox("Coluna de produção de óleo (STB)", df_history.columns)
        gas_prod_col = st.selectbox("Coluna de produção de gás (Mscf)", df_history.columns)
    else:
        gas_prod_col = st.selectbox("Coluna de produção de gás (Mscf)", df_history.columns)
    water_prod_col = st.selectbox("Coluna de produção de água (STB)", df_history.columns)
    
    # Upload de dados PVT
    st.subheader("Dados PVT")
    pvt_file = st.file_uploader("Carregue o arquivo com dados PVT (CSV ou Excel)", type=["csv", "xlsx"], key="mbal_pvt")
    if pvt_file is not None:
        if pvt_file.name.endswith('.csv'):
            df_pvt = pd.read_csv(pvt_file)
        else:
            df_pvt = pd.read_excel(pvt_file)
        
        st.write("Prévia dos dados PVT:")
        st.dataframe(df_pvt.head())
        
        # Seleção de colunas PVT
        pvt_pressure_col = st.selectbox("Coluna de pressão PVT (psia)", df_pvt.columns)
        if reservoir_type == "Óleo":
            bo_col = st.selectbox("Coluna de Bo (bbl/STB)", df_pvt.columns)
            rs_col = st.selectbox("Coluna de Rs (scf/STB)", df_pvt.columns)
            bg_col = st.selectbox("Coluna de Bg (bbl/Mscf)", df_pvt.columns)
        else:
            z_col = st.selectbox("Coluna de Z-Factor", df_pvt.columns)
            bg_col = st.selectbox("Coluna de Bg (bbl/Mscf)", df_pvt.columns)
        
        # Parâmetros do reservatório
        st.subheader("Parâmetros do Reservatório")
        Swi = st.number_input("Saturação inicial de água (fração)", value=0.2, min_value=0.0, max_value=1.0)
        cw = st.number_input("Compressibilidade da água (1/psi)", value=3e-6, format="%.2e")
        cf = st.number_input("Compressibilidade da formação (1/psi)", value=5e-6, format="%.2e")
        Bw = st.number_input("Fator de volume de formação da água (bbl/STB)", value=1.0)
        
        if reservoir_type == "Óleo":
            m = st.number_input("Razão gás-cap em lugar", value=0.0)
        
        if st.button("Calcular Balanço de Materiais"):
            # Inicializar objeto MBAL
            mbal = MaterialBalance(reservoir_type.lower())
            
            # Adicionar dados históricos
            for _, row in df_history.iterrows():
                mbal.add_pressure_point(row[pressure_col], row[date_col])
                if reservoir_type == "Óleo":
                    mbal.add_production_point(
                        oil_prod=row[oil_prod_col],
                        gas_prod=row[gas_prod_col],
                        water_prod=row[water_prod_col],
                        date=row[date_col]
                    )
                else:
                    mbal.add_production_point(
                        gas_prod=row[gas_prod_col],
                        water_prod=row[water_prod_col],
                        date=row[date_col]
                    )
            
            # Adicionar dados PVT
            for _, row in df_pvt.iterrows():
                if reservoir_type == "Óleo":
                    mbal.add_pvt_data(
                        pressure=row[pvt_pressure_col],
                        bo=row[bo_col],
                        bg=row[bg_col],
                        rs=row[rs_col]
                    )
                else:
                    mbal.add_pvt_data(
                        pressure=row[pvt_pressure_col],
                        bg=row[bg_col],
                        z=row[z_col]
                    )
            
            # Calcular balanço de materiais
            try:
                if reservoir_type == "Óleo":
                    N = mbal.solve_oil_mbal(m, 0, 0, 0, Bw, cw, cf, Swi)
                    st.success(f"OOIP estimado: {N:,.0f} STB")
                else:
                    G = mbal.solve_gas_mbal(0, 0, Bw, cw, cf, Swi)
                    st.success(f"OGIP estimado: {G:,.0f} Mscf")
                
                # Plotar histórico de pressão
                fig, ax = plt.subplots(figsize=(10, 6))
                dates = [p['date'] for p in mbal.pressure_history]
                pressures = [p['pressure'] for p in mbal.pressure_history]
                ax.plot(dates, pressures, marker='o')
                ax.set_xlabel("Data")
                ax.set_ylabel("Pressão (psia)")
                ax.set_title("Histórico de Pressão")
                ax.grid(True)
                plt.xticks(rotation=45)
                st.pyplot(fig)
                
            except Exception as e:
                st.error(f"Erro no cálculo do balanço de materiais: {str(e)}")

# Seção de Modelagem Geológica 3D
st.header("Modelagem Geológica 3D")

# Criar modelo
model = GeologicalModel3D()

# Parâmetros da malha
st.subheader("Parâmetros da Malha")
col1, col2 = st.columns(2)
with col1:
    nx = st.number_input("Número de células em X", min_value=10, value=50)
    ny = st.number_input("Número de células em Y", min_value=10, value=50)
    nz = st.number_input("Número de células em Z", min_value=10, value=50)
with col2:
    dx = st.number_input("Tamanho da célula em X (m)", min_value=1.0, value=10.0)
    dy = st.number_input("Tamanho da célula em Y (m)", min_value=1.0, value=10.0)
    dz = st.number_input("Tamanho da célula em Z (m)", min_value=1.0, value=10.0)

if st.button("Criar Malha"):
    model.create_grid(nx, ny, nz, dx, dy, dz)
    st.success("Malha criada com sucesso!")

# Adicionar poços
st.subheader("Adicionar Poços")
well_name = st.text_input("Nome do Poço")
col1, col2, col3 = st.columns(3)
with col1:
    x = st.number_input("Coordenada X (m)")
with col2:
    y = st.number_input("Coordenada Y (m)")
with col3:
    md = st.text_input("Medidas de Profundidade (m)", help="Separadas por vírgula")

if st.button("Adicionar Poço"):
    if well_name and x and y and md:
        try:
            md_values = np.array([float(d) for d in md.split(',')])
            model.add_well(well_name, x, y, md_values)
            st.success(f"Poço {well_name} adicionado com sucesso!")
        except ValueError:
            st.error("Formato inválido para medidas de profundidade")
    else:
        st.error("Preencha todos os campos")

# Carregar logs
st.subheader("Carregar Logs")
uploaded_file = st.file_uploader("Arquivo LAS", type=['las'])
if uploaded_file and well_name in model.wells:
    # Salvar arquivo temporariamente
    with tempfile.NamedTemporaryFile(delete=False, suffix='.las') as tmp:
        tmp.write(uploaded_file.getvalue())
        tmp_path = tmp.name
    
    try:
        model.load_well_log(well_name, tmp_path)
        st.success("Log carregado com sucesso!")
        
        # Mostrar propriedades disponíveis
        if model.wells[well_name]['properties']:
            st.write("Propriedades disponíveis:")
            st.write(list(model.wells[well_name]['properties'].keys()))
    except Exception as e:
        st.error(f"Erro ao carregar log: {str(e)}")
    finally:
        os.unlink(tmp_path)

# Interpolar propriedades
if model.wells and model.grid:
    st.subheader("Interpolar Propriedades")
    property_name = st.text_input("Nome da Propriedade")
    method = st.selectbox("Método de Interpolação", ['linear', 'cubic', 'nearest'])
    
    if st.button("Interpolar"):
        try:
            model.interpolate_property(property_name, method)
            st.success("Propriedade interpolada com sucesso!")
            
            # Mostrar estatísticas
            stats = model.calculate_statistics(property_name)
            st.write("Estatísticas:")
            st.write(stats)
        except ValueError as e:
            st.error(str(e))

# Visualizar modelo
if model.grid:
    st.subheader("Visualizar Modelo")
    property_name = st.text_input("Propriedade para Visualização", key="viz_prop")
    show_wells = st.checkbox("Mostrar Poços", value=True)
    show_surfaces = st.checkbox("Mostrar Superfícies", value=True)
    
    if st.button("Visualizar"):
        try:
            model.visualize(property_name, show_wells, show_surfaces)
        except Exception as e:
            st.error(f"Erro ao visualizar modelo: {str(e)}")

# Exportar modelo
if model.grid:
    st.subheader("Exportar Modelo")
    if st.button("Exportar para VTK"):
        try:
            model.export_to_vtk("modelo_geologico.vtk")
            st.success("Modelo exportado com sucesso!")
        except Exception as e:
            st.error(f"Erro ao exportar modelo: {str(e)}")

# Seção de Caracterização de Reservatórios
st.header("Caracterização de Reservatórios")

# Criar objeto de caracterização
char = ReservoirCharacterization()

# Upload de dados sísmicos
st.subheader("Dados Sísmicos")
seismic_file = st.file_uploader("Arquivo SEG-Y", type=['sgy', 'segy'])
if seismic_file:
    with tempfile.NamedTemporaryFile(delete=False, suffix='.sgy') as tmp:
        tmp.write(seismic_file.getvalue())
        tmp_path = tmp.name
    
    try:
        char.load_seismic_data(tmp_path)
        st.success("Dados sísmicos carregados com sucesso!")
    except Exception as e:
        st.error(f"Erro ao carregar dados sísmicos: {str(e)}")
    finally:
        os.unlink(tmp_path)

# Upload de dados de poço
st.subheader("Dados de Poço")
well_name = st.text_input("Nome do Poço", key="char_well")
las_file = st.file_uploader("Arquivo LAS", type=['las'], key="char_las")
tops_file = st.file_uploader("Arquivo de Topos (CSV)", type=['csv'], key="char_tops")

if well_name and las_file:
    with tempfile.NamedTemporaryFile(delete=False, suffix='.las') as tmp_las:
        tmp_las.write(las_file.getvalue())
        tmp_las_path = tmp_las.name
    
    tmp_tops_path = None
    if tops_file:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.csv') as tmp_tops:
            tmp_tops.write(tops_file.getvalue())
            tmp_tops_path = tmp_tops.name
    
    try:
        char.load_well_data(well_name, tmp_las_path, tmp_tops_path)
        st.success(f"Dados do poço {well_name} carregados com sucesso!")
        
        # Mostrar propriedades disponíveis
        if char.well_data[well_name]['logs'] is not None:
            st.write("Propriedades disponíveis:")
            st.write(list(char.well_data[well_name]['logs'].columns))
    except Exception as e:
        st.error(f"Erro ao carregar dados do poço: {str(e)}")
    finally:
        os.unlink(tmp_las_path)
        if tmp_tops_path:
            os.unlink(tmp_tops_path)

# Criação de mapas de propriedades
if char.well_data:
    st.subheader("Mapas de Propriedades")
    property_name = st.text_input("Nome da Propriedade", key="map_prop")
    method = st.selectbox("Método de Interpolação", ['linear', 'cubic', 'nearest', 'kriging'])
    resolution = st.slider("Resolução do Mapa", 50, 200, 100)
    
    if st.button("Criar Mapa"):
        try:
            char.create_property_map(property_name, method, resolution)
            st.success("Mapa criado com sucesso!")
            
            # Plotar mapa
            fig, ax = plt.subplots(figsize=(10, 8))
            im = ax.imshow(char.property_maps[property_name]['z'],
                          extent=[char.property_maps[property_name]['x'].min(),
                                 char.property_maps[property_name]['x'].max(),
                                 char.property_maps[property_name]['y'].min(),
                                 char.property_maps[property_name]['y'].max()],
                          origin='lower',
                          cmap='viridis')
            plt.colorbar(im, ax=ax, label=property_name)
            ax.set_xlabel("X")
            ax.set_ylabel("Y")
            ax.set_title(f"Mapa de {property_name}")
            st.pyplot(fig)
        except ValueError as e:
            st.error(str(e))

# Classificação de fácies
if len(char.well_data) > 1:
    st.subheader("Classificação de Fácies")
    properties = st.multiselect("Propriedades para Classificação",
                              options=list(char.well_data[list(char.well_data.keys())[0]]['logs'].columns))
    n_facies = st.slider("Número de Fácies", 2, 5, 3)
    
    if st.button("Classificar Fácies"):
        try:
            char.perform_facies_classification(properties, n_facies)
            st.success("Classificação de fácies realizada com sucesso!")
            
            # Mostrar resultados
            for well_name, data in char.well_data.items():
                if 'facies' in data:
                    st.write(f"Poço {well_name}: Fácies {data['facies']}")
        except ValueError as e:
            st.error(str(e))

# Integração sísmica-poço
if char.seismic_data and char.well_data:
    st.subheader("Integração Sísmica-Poço")
    well_property = st.selectbox("Propriedade do Poço",
                               options=list(char.well_data[list(char.well_data.keys())[0]]['logs'].columns))
    seismic_attribute = st.selectbox("Atributo Sísmico",
                                   options=['amplitude', 'frequency', 'phase'])
    
    if st.button("Integrar Dados"):
        try:
            results = char.integrate_seismic_well_data(well_property, seismic_attribute)
            st.success("Integração realizada com sucesso!")
            
            # Mostrar correlação
            st.write(f"Correlação: {results['correlation']:.4f}")
            
            # Plotar gráfico de dispersão
            fig, ax = plt.subplots(figsize=(8, 6))
            ax.scatter(results['seismic_values'], results['well_values'])
            ax.set_xlabel("Valor Sísmico")
            ax.set_ylabel(f"Valor de {well_property}")
            ax.set_title("Correlação Sísmica-Poço")
            st.pyplot(fig)
        except ValueError as e:
            st.error(str(e))

# Cálculo de parâmetros do reservatório
if char.well_data:
    st.subheader("Parâmetros do Reservatório")
    if st.button("Calcular Parâmetros"):
        try:
            results = char.calculate_reservoir_parameters()
            
            # Criar DataFrame com resultados
            df_results = pd.DataFrame.from_dict(results, orient='index')
            st.write("Resultados por poço:")
            st.dataframe(df_results)
            
            # Exportar resultados
            if st.button("Exportar Resultados"):
                char.export_results("parametros_reservatorio.csv")
                st.success("Resultados exportados com sucesso!")
        except Exception as e:
            st.error(f"Erro ao calcular parâmetros: {str(e)}")

# Seção de Geoestatística
st.header("Geoestatística")

# Criar objeto de geoestatística
geo = Geostatistics()

# Upload de dados
st.subheader("Dados")
data_file = st.file_uploader("Arquivo de dados (CSV)", type=['csv'])
if data_file:
    df = pd.read_csv(data_file)
    st.write("Prévia dos dados:")
    st.dataframe(df.head())
    
    # Seleção de colunas
    col1, col2 = st.columns(2)
    with col1:
        x_col = st.selectbox("Coluna X", df.columns)
        y_col = st.selectbox("Coluna Y", df.columns)
    with col2:
        z_col = st.selectbox("Coluna Z", df.columns)
        value_col = st.selectbox("Coluna de Valor", df.columns)
        
    if st.button("Carregar Dados"):
        try:
            geo.load_data(df, x_col, y_col, z_col, value_col)
            st.success("Dados carregados com sucesso!")
        except Exception as e:
            st.error(f"Erro ao carregar dados: {str(e)}")

# Análise de variograma
if geo.data is not None:
    st.subheader("Análise de Variograma")
    col1, col2 = st.columns(2)
    with col1:
        n_lags = st.slider("Número de Lags", 5, 20, 10)
        max_lag = st.number_input("Distância Máxima", value=float(np.max([
            np.max(geo.data['x']) - np.min(geo.data['x']),
            np.max(geo.data['y']) - np.min(geo.data['y']),
            np.max(geo.data['z']) - np.min(geo.data['z'])
        ])))
    with col2:
        model_type = st.selectbox("Tipo de Modelo", ['spherical', 'exponential', 'gaussian'])
        nugget = st.number_input("Efeito Pepita", value=0.0)
        
    if st.button("Calcular Variograma"):
        try:
            geo.calculate_variogram(n_lags, max_lag)
            geo.fit_variogram_model(model_type, nugget)
            st.success("Variograma calculado com sucesso!")
            
            # Plotar variograma
            fig = geo.plot_variogram()
            st.pyplot(fig)
        except Exception as e:
            st.error(f"Erro ao calcular variograma: {str(e)}")

# Krigagem
if geo.variogram is not None and 'model' in geo.variogram:
    st.subheader("Krigagem")
    col1, col2 = st.columns(2)
    with col1:
        nx = st.number_input("Número de pontos em X", min_value=10, value=50)
        ny = st.number_input("Número de pontos em Y", min_value=10, value=50)
    with col2:
        nz = st.number_input("Número de pontos em Z", min_value=10, value=50)
        method = st.selectbox("Método de Krigagem", ['simple', 'ordinary'])
        
    if st.button("Realizar Krigagem"):
        try:
            # Criar grade
            x = np.linspace(np.min(geo.data['x']), np.max(geo.data['x']), nx)
            y = np.linspace(np.min(geo.data['y']), np.max(geo.data['y']), ny)
            z = np.linspace(np.min(geo.data['z']), np.max(geo.data['z']), nz)
            grid_x, grid_y, grid_z = np.meshgrid(x, y, z)
            
            # Realizar krigagem
            results = geo.perform_kriging(grid_x, grid_y, grid_z, method)
            
            # Plotar resultados
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
            
            # Mapa de valores estimados
            im1 = ax1.imshow(results['predicted'][:, :, nz//2],
                            extent=[x.min(), x.max(), y.min(), y.max()],
                            origin='lower', cmap='viridis')
            plt.colorbar(im1, ax=ax1, label='Valor Estimado')
            ax1.set_title('Valores Estimados')
            ax1.set_xlabel('X')
            ax1.set_ylabel('Y')
            
            # Mapa de incerteza
            im2 = ax2.imshow(results['std'][:, :, nz//2],
                            extent=[x.min(), x.max(), y.min(), y.max()],
                            origin='lower', cmap='plasma')
            plt.colorbar(im2, ax=ax2, label='Incerteza')
            ax2.set_title('Incerteza')
            ax2.set_xlabel('X')
            ax2.set_ylabel('Y')
            
            st.pyplot(fig)
            
        except Exception as e:
            st.error(f"Erro ao realizar krigagem: {str(e)}")

# Análise de incerteza
if geo.kriging_model is not None:
    st.subheader("Análise de Incerteza")
    n_realizations = st.slider("Número de Realizações", 10, 1000, 100)
    
    if st.button("Calcular Incerteza"):
        try:
            results = geo.calculate_uncertainty(n_realizations)
            
            # Plotar resultados
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
            
            # Histograma dos valores
            ax1.hist(results['mean'], bins=30, density=True)
            ax1.set_title('Distribuição dos Valores')
            ax1.set_xlabel('Valor')
            ax1.set_ylabel('Frequência')
            
            # Intervalo de confiança
            ax2.plot(results['mean'], label='Média')
            ax2.fill_between(range(len(results['mean'])),
                           results['p10'], results['p90'],
                           alpha=0.3, label='P10-P90')
            ax2.set_title('Intervalo de Confiança')
            ax2.set_xlabel('Ponto')
            ax2.set_ylabel('Valor')
            ax2.legend()
            
            st.pyplot(fig)
            
            # Mostrar estatísticas
            st.write("Estatísticas:")
            st.write({
                'Média': np.mean(results['mean']),
                'Desvio Padrão': np.mean(results['std']),
                'P10': np.mean(results['p10']),
                'P90': np.mean(results['p90'])
            })
            
        except Exception as e:
            st.error(f"Erro ao calcular incerteza: {str(e)}")

# Exportar resultados
if geo.data is not None:
    st.subheader("Exportar Resultados")
    if st.button("Exportar para S-GeMS"):
        try:
            geo.export_to_sgems("dados_sgems.txt")
            st.success("Dados exportados com sucesso!")
        except Exception as e:
            st.error(f"Erro ao exportar dados: {str(e)}")

# Seção de Mapeamento Petrofísico
st.header("Mapeamento Petrofísico")

# Criar objeto de mapeamento
petro = PetrophysicalMapping()

# Upload de dados de poço
st.subheader("Dados de Poço")
well_name = st.text_input("Nome do Poço", key="petro_well")
data_file = st.file_uploader("Arquivo de dados petrofísicos (CSV)", type=['csv'], key="petro_data")

if well_name and data_file:
    df = pd.read_csv(data_file)
    st.write("Prévia dos dados:")
    st.dataframe(df.head())
    
    # Seleção de colunas
    col1, col2 = st.columns(2)
    with col1:
        depth_col = st.selectbox("Coluna de Profundidade", df.columns)
        x_col = st.selectbox("Coluna X", df.columns)
        y_col = st.selectbox("Coluna Y", df.columns)
    with col2:
        property_cols = st.multiselect("Colunas de Propriedades", 
                                     [col for col in df.columns if col not in [depth_col, x_col, y_col]])
        
    if st.button("Carregar Dados do Poço"):
        try:
            # Preparar dados
            depth = df[depth_col].values
            properties = {col: df[col].values for col in property_cols}
            
            # Carregar dados
            petro.load_well_data(well_name, depth, properties)
            st.success(f"Dados do poço {well_name} carregados com sucesso!")
            
            # Calcular e mostrar correlações
            petro.calculate_correlations()
            fig = petro.plot_correlation_matrix()
            st.pyplot(fig)
            
        except Exception as e:
            st.error(f"Erro ao carregar dados: {str(e)}")

# Criação de mapas
if petro.well_data:
    st.subheader("Criação de Mapas")
    col1, col2 = st.columns(2)
    with col1:
        property_name = st.selectbox("Propriedade para Mapeamento",
                                   options=property_cols)
        method = st.selectbox("Método de Interpolação",
                            ['kriging', 'linear', 'cubic', 'nearest'])
    with col2:
        resolution = st.slider("Resolução do Mapa", 50, 200, 100)
        depth_index = st.slider("Índice de Profundidade", 0, 100, 50)
        
    if st.button("Criar Mapa"):
        try:
            # Criar mapa
            petro.create_property_map(property_name, method, resolution)
            
            # Plotar mapa
            fig = petro.plot_property_map(property_name, depth_index)
            st.pyplot(fig)
            
            # Mostrar estatísticas
            stats = petro.calculate_statistics(property_name)
            st.write("Estatísticas:")
            st.write(stats)
            
        except Exception as e:
            st.error(f"Erro ao criar mapa: {str(e)}")

# Exportar mapas
if petro.property_maps:
    st.subheader("Exportar Mapas")
    if st.button("Exportar Mapas"):
        try:
            petro.export_maps("mapa_petrofisico")
            st.success("Mapas exportados com sucesso!")
        except Exception as e:
            st.error(f"Erro ao exportar mapas: {str(e)}")

# Seção de Análise de Sensitividade
st.header("Análise de Sensitividade e Incertezas")

# Criar objeto de análise
sens = SensitivityAnalysis()

# Definição de parâmetros
st.subheader("Definição de Parâmetros")

# Adicionar parâmetros
param_name = st.text_input("Nome do Parâmetro")
col1, col2 = st.columns(2)
with col1:
    distribution = st.selectbox("Distribuição", ['normal', 'uniform', 'lognormal'])
with col2:
    if distribution == 'normal':
        mean = st.number_input("Média")
        std = st.number_input("Desvio Padrão")
        params = {'mean': mean, 'std': std}
    elif distribution == 'uniform':
        min_val = st.number_input("Mínimo")
        max_val = st.number_input("Máximo")
        params = {'min': min_val, 'max': max_val}
    else:  # lognormal
        mean = st.number_input("Média")
        std = st.number_input("Desvio Padrão")
        params = {'mean': mean, 'std': std}

if st.button("Adicionar Parâmetro"):
    if param_name and params:
        sens.add_parameter(param_name, distribution, params)
        st.success(f"Parâmetro {param_name} adicionado com sucesso!")
    else:
        st.error("Preencha todos os campos")

# Mostrar parâmetros adicionados
if sens.parameters:
    st.write("Parâmetros adicionados:")
    for name, param in sens.parameters.items():
        st.write(f"- {name}: {param['distribution']} {param['params']}")

# Análise de sensitividade
if sens.parameters:
    st.subheader("Análise de Sensitividade")
    n_samples = st.slider("Número de Amostras", 100, 10000, 1000)
    
    if st.button("Gerar Amostras"):
        try:
            sens.generate_samples(n_samples)
            st.success("Amostras geradas com sucesso!")
        except Exception as e:
            st.error(f"Erro ao gerar amostras: {str(e)}")
            
    if sens.samples is not None:
        # Definir função do modelo
        st.write("Defina a função do modelo:")
        model_code = st.text_area("Código Python", """
def model_function(params):
    # Exemplo: OOIP = 7758 * A * h * φ * So / Bo
    A = params[0]  # Área
    h = params[1]  # Espessura
    phi = params[2]  # Porosidade
    So = params[3]  # Saturação de óleo
    Bo = params[4]  # Fator de volume de formação
    
    return 7758 * A * h * phi * So / Bo
""")
        
        if st.button("Executar Análise"):
            try:
                # Executar análise
                exec(model_code)
                sens.run_analysis(model_function)
                
                # Plotar resultados
                fig = sens.plot_sensitivity_indices()
                st.pyplot(fig)
                
                # Mostrar métricas
                metrics = sens.calculate_uncertainty_metrics(sens.results)
                st.write("Métricas de Incerteza:")
                st.write(metrics)
                
            except Exception as e:
                st.error(f"Erro ao executar análise: {str(e)}")

# Análise de incerteza
if sens.parameters:
    st.subheader("Análise de Incerteza")
    n_samples_mc = st.slider("Número de Amostras Monte Carlo", 100, 10000, 1000, key="mc_samples")
    
    if st.button("Plotar Incerteza"):
        try:
            fig = sens.plot_uncertainty(n_samples_mc)
            st.pyplot(fig)
        except Exception as e:
            st.error(f"Erro ao plotar incerteza: {str(e)}")

# Análise tornado
if sens.parameters:
    st.subheader("Análise Tornado")
    base_case = st.number_input("Caso Base")
    
    if st.button("Plotar Tornado"):
        try:
            # Gerar resultados para cada parâmetro
            results = {}
            for name in sens.parameters.keys():
                # Simular variação de ±20%
                results[name] = base_case * 1.2
                
            fig = sens.plot_tornado(base_case, results)
            st.pyplot(fig)
        except Exception as e:
            st.error(f"Erro ao plotar tornado: {str(e)}")

# Exportar resultados
if sens.sensitivity_indices is not None:
    st.subheader("Exportar Resultados")
    if st.button("Exportar Análise"):
        try:
            sens.export_results("analise_sensitividade.csv")
            st.success("Resultados exportados com sucesso!")
        except Exception as e:
            st.error(f"Erro ao exportar resultados: {str(e)}")

# Seção de Simulação de Fluxo
st.header("Simulação de Fluxo Multifásico")

# Selecionar tipo de malha
mesh_type = st.selectbox(
    "Tipo de Malha",
    ["Estruturada", "Não Estruturada"]
)

if mesh_type == "Estruturada":
    # Parâmetros da malha estruturada
    col1, col2 = st.columns(2)
    with col1:
        nx = st.number_input("Número de células em X", 1, 100, 10)
        ny = st.number_input("Número de células em Y", 1, 100, 10)
        nz = st.number_input("Número de células em Z", 1, 100, 10)
    with col2:
        dx = st.number_input("Tamanho da célula em X (ft)", 1.0, 1000.0, 100.0)
        dy = st.number_input("Tamanho da célula em Y (ft)", 1.0, 1000.0, 100.0)
        dz = st.number_input("Tamanho da célula em Z (ft)", 1.0, 1000.0, 100.0)
        
    # Criar objeto de simulação
    sim = FlowSimulation(
        mesh_type='structured',
        nx=nx, ny=ny, nz=nz,
        dx=dx, dy=dy, dz=dz
    )
else:
    # Upload de pontos para malha não estruturada
    points_file = st.file_uploader("Upload de pontos (CSV)", type=['csv'])
    if points_file is not None:
        points = pd.read_csv(points_file)
        sim = FlowSimulation(
            mesh_type='unstructured',
            points=points
        )
    else:
        st.warning("Por favor, faça upload do arquivo de pontos")
        st.stop()

# Configurar mecanismos de empuxo
st.subheader("Mecanismos de Empuxo")

# Cap de Gás
st.write("### Empuxo por Cap de Gás")
use_gas_cap = st.checkbox("Usar empuxo por cap de gás")
if use_gas_cap:
    gas_cap_props = {
        'initial_pressure': st.number_input("Pressão inicial do cap (psia)", 1000.0, 10000.0, 3000.0),
        'initial_gas_saturation': st.number_input("Saturação inicial de gás", 0.0, 1.0, 0.8),
        'gas_oil_contact': st.number_input("Profundidade do contato gás-óleo (ft)", 0.0, 10000.0, 5000.0),
        'gas_cap_volume': st.number_input("Volume do cap de gás (ft³)", 1e6, 1e9, 1e7)
    }
    sim.set_drive_mechanism('gas_cap', gas_cap_props)

# Aquífero
st.write("### Empuxo por Aquífero")
use_aquifer = st.checkbox("Usar empuxo por aquífero")
if use_aquifer:
    aquifer_type = st.selectbox(
        "Tipo de aquífero",
        ["pot", "fetkovich", "carter-tracy"]
    )
    aquifer_props = {
        'type': aquifer_type,
        'initial_pressure': st.number_input("Pressão inicial do aquífero (psia)", 1000.0, 10000.0, 3000.0),
        'water_oil_contact': st.number_input("Profundidade do contato água-óleo (ft)", 0.0, 10000.0, 6000.0),
        'aquifer_volume': st.number_input("Volume do aquífero (ft³)", 1e6, 1e9, 1e8),
        'aquifer_compressibility': st.number_input("Compressibilidade do aquífero (1/psi)", 1e-7, 1e-5, 3e-6),
        'water_compressibility': st.number_input("Compressibilidade da água (1/psi)", 1e-7, 1e-5, 3e-6),
        'aquifer_porosity': st.number_input("Porosidade do aquífero", 0.01, 0.4, 0.2),
        'aquifer_permeability': st.number_input("Permeabilidade do aquífero (md)", 1.0, 1000.0, 100.0)
    }
    sim.set_drive_mechanism('aquifer', aquifer_props)

# Gás em Solução
st.write("### Empuxo por Gás em Solução")
use_solution_gas = st.checkbox("Usar empuxo por gás em solução")
if use_solution_gas:
    solution_gas_props = {
        'initial_gas_oil_ratio': st.number_input("Razão gás-óleo inicial (scf/STB)", 100.0, 2000.0, 500.0),
        'bubble_point_pressure': st.number_input("Pressão de bolha (psia)", 1000.0, 5000.0, 2500.0)
    }
    sim.set_drive_mechanism('solution_gas', solution_gas_props)

# Upload de propriedades do reservatório
st.subheader("Propriedades do Reservatório")
reservoir_file = st.file_uploader("Upload de propriedades (CSV)", type=['csv'])
if reservoir_file is not None:
    reservoir_data = pd.read_csv(reservoir_file)
    porosity_col = st.selectbox("Coluna de porosidade", reservoir_data.columns)
    permeability_col = st.selectbox("Coluna de permeabilidade", reservoir_data.columns)
    depth_col = st.selectbox("Coluna de profundidade", reservoir_data.columns)
    
    if st.button("Carregar propriedades"):
        sim.set_reservoir_properties(
            reservoir_data[porosity_col].values,
            reservoir_data[permeability_col].values,
            reservoir_data[depth_col].values
        )
        st.success("Propriedades carregadas com sucesso!")

# Upload de condições iniciais
st.subheader("Condições Iniciais")
initial_conditions_file = st.file_uploader("Upload de condições iniciais (CSV)", type=['csv'])
if initial_conditions_file is not None:
    initial_data = pd.read_csv(initial_conditions_file)
    pressure_col = st.selectbox("Coluna de pressão", initial_data.columns)
    temperature_col = st.selectbox("Coluna de temperatura", initial_data.columns)
    saturation_cols = st.multiselect("Colunas de saturação", initial_data.columns)
    
    if st.button("Carregar condições iniciais"):
        saturation = {}
        for phase, col in zip(['oil', 'water', 'gas'], saturation_cols):
            saturation[phase] = initial_data[col].values
            
        sim.set_initial_conditions(
            initial_data[pressure_col].values,
            initial_data[temperature_col].values,
            saturation
        )
        st.success("Condições iniciais carregadas com sucesso!")

# Upload de dados PVT
st.subheader("Dados PVT")
pvt_file = st.file_uploader("Upload de dados PVT (CSV)", type=['csv'])
if pvt_file is not None:
    pvt_data = pd.read_csv(pvt_file)
    if st.button("Carregar dados PVT"):
        sim.set_pvt_data(pvt_data)
        st.success("Dados PVT carregados com sucesso!")

# Configuração da simulação
st.subheader("Configuração da Simulação")
sim_type = st.selectbox(
    "Tipo de Simulação",
    ["Black Oil", "Composicional", "Térmico"]
)
dt = st.number_input("Passo de tempo (dias)", 0.1, 100.0, 1.0)
n_steps = st.number_input("Número de passos", 1, 1000, 100)

if st.button("Executar Simulação"):
    try:
        if sim_type == "Black Oil":
            results = sim.run_black_oil_simulation(dt, n_steps)
        elif sim_type == "Composicional":
            results = sim.run_compositional_simulation(dt, n_steps)
        else:
            results = sim.run_thermal_simulation(dt, n_steps)
            
        # Plotar resultados
        fig = sim.plot_results(results)
        st.pyplot(fig)
        
        # Exportar resultados
        if st.button("Exportar Resultados"):
            sim.export_results("resultados_simulacao.csv")
            st.success("Resultados exportados com sucesso!")
            
    except Exception as e:
        st.error(f"Erro na simulação: {str(e)}")

# Seção de Ajuste de Histórico
st.header("Ajuste de Histórico (History Matching)")

# Upload de dados históricos
st.subheader("Dados Históricos")
history_file = st.file_uploader("Upload de dados históricos (CSV)", type=['csv'])
if history_file is not None:
    history_data = pd.read_csv(history_file)
    st.write("Prévia dos dados históricos:")
    st.dataframe(history_data.head())
    
    # Seleção de colunas
    time_col = st.selectbox("Coluna de tempo", history_data.columns)
    pressure_col = st.selectbox("Coluna de pressão", history_data.columns)
    production_cols = {}
    for phase in ['oil', 'water', 'gas']:
        col = st.selectbox(f"Coluna de produção de {phase}", history_data.columns)
        production_cols[phase] = col
        
    # Criar objeto de ajuste de histórico
    hm = FlowHistoryMatching(sim)
    
    # Carregar dados históricos
    hm.load_historical_data(
        history_data,
        time_col=time_col,
        pressure_col=pressure_col,
        production_cols=production_cols
    )
    
    # Seleção de parâmetros para ajuste
    st.subheader("Parâmetros para Ajuste")
    
    # Parâmetros do reservatório
    if st.checkbox("Ajustar parâmetros do reservatório"):
        hm.add_reservoir_parameters()
        
    # Parâmetros de permeabilidade relativa
    if st.checkbox("Ajustar parâmetros de permeabilidade relativa"):
        hm.add_relative_permeability_parameters()
        
    # Parâmetros de pressão capilar
    if st.checkbox("Ajustar parâmetros de pressão capilar"):
        hm.add_capillary_pressure_parameters()
        
    # Parâmetros de aquífero
    if st.checkbox("Ajustar parâmetros de aquífero"):
        hm.add_aquifer_parameters()
        
    # Parâmetros de cap de gás
    if st.checkbox("Ajustar parâmetros de cap de gás"):
        hm.add_gas_cap_parameters()
        
    # Parâmetros de gás em solução
    if st.checkbox("Ajustar parâmetros de gás em solução"):
        hm.add_solution_gas_parameters()
        
    # Configuração da otimização
    st.subheader("Configuração da Otimização")
    optimization_method = st.selectbox(
        "Método de otimização",
        ["differential_evolution", "nelder-mead"]
    )
    
    max_iterations = st.number_input("Número máximo de iterações", 10, 1000, 100)
    population_size = st.number_input("Tamanho da população", 10, 100, 20)
    
    # Pesos para cada tipo de dado
    st.write("Pesos para cada tipo de dado:")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        pressure_weight = st.number_input("Pressão", 0.0, 10.0, 1.0)
    with col2:
        oil_weight = st.number_input("Óleo", 0.0, 10.0, 1.0)
    with col3:
        water_weight = st.number_input("Água", 0.0, 10.0, 1.0)
    with col4:
        gas_weight = st.number_input("Gás", 0.0, 10.0, 1.0)
        
    weights = {
        'pressure': pressure_weight,
        'oil': oil_weight,
        'water': water_weight,
        'gas': gas_weight
    }
    
    if st.button("Executar Ajuste de Histórico"):
        try:
            # Executar otimização
            hm.run_optimization(
                method=optimization_method,
                max_iterations=max_iterations,
                population_size=population_size,
                weights=weights
            )
            
            # Executar análise de sensibilidade
            hm.run_sensitivity_analysis()
            
            # Plotar resultados
            st.write("### Resultados do Ajuste")
            
            # Plotar histórico vs simulado
            simulated = hm.run_simulation()
            fig_match = hm.plot_history_match(simulated)
            st.pyplot(fig_match)
            
            # Plotar sensibilidade
            fig_sens = hm.plot_sensitivity()
            st.pyplot(fig_sens)
            
            # Plotar correlações
            fig_corr = hm.plot_parameter_correlations()
            st.pyplot(fig_corr)
            
            # Mostrar parâmetros otimizados
            st.write("### Parâmetros Otimizados")
            for name, param in hm.parameters.items():
                st.write(f"{name}: {param['value']:.4f} ({param['description']})")
                
            # Exportar resultados
            if st.button("Exportar Resultados"):
                hm.export_results("resultados_ajuste_historico.csv")
                st.success("Resultados exportados com sucesso!")
                
        except Exception as e:
            st.error(f"Erro no ajuste de histórico: {str(e)}")

# Seção de Análise de Incertezas
st.header("Análise de Incertezas e Otimização Automática")

# Criar objeto de análise de incertezas
ua = UncertaintyAnalysis(hm)

# Configuração da análise
st.subheader("Configuração da Análise")
analysis_type = st.selectbox(
    "Tipo de Análise",
    ["Análise de Incertezas", "Otimização Automática", "Análise de Sensitividade"]
)

if analysis_type == "Análise de Incertezas":
    n_samples = st.slider("Número de amostras", 100, 10000, 1000)
    
    if st.button("Executar Análise de Incertezas"):
        try:
            # Executar análise
            results = ua.run_uncertainty_analysis(n_samples)
            
            # Plotar resultados
            st.write("### Resultados da Análise de Incertezas")
            
            # Distribuição dos erros
            fig_unc = ua.plot_uncertainty_results()
            st.pyplot(fig_unc)
            
            # Índices de Sobol
            st.write("### Índices de Sobol")
            sobol_indices = results['sobol_indices']
            
            # Criar DataFrame com índices
            df_sobol = pd.DataFrame({
                'Parâmetro': list(sobol_indices.keys()),
                'S1': [ind['S1'] for ind in sobol_indices.values()],
                'ST': [ind['ST'] for ind in sobol_indices.values()]
            })
            st.dataframe(df_sobol)
            
            # Plotar índices
            fig_sobol, ax = plt.subplots(figsize=(10, 6))
            df_sobol.plot(x='Parâmetro', y=['S1', 'ST'], kind='bar', ax=ax)
            ax.set_title('Índices de Sobol')
            ax.set_xlabel('Parâmetro')
            ax.set_ylabel('Índice')
            ax.grid(True)
            plt.xticks(rotation=45, ha='right')
            st.pyplot(fig_sobol)
            
        except Exception as e:
            st.error(f"Erro na análise de incertezas: {str(e)}")
            
elif analysis_type == "Otimização Automática":
    col1, col2 = st.columns(2)
    with col1:
        method = st.selectbox(
            "Método de otimização",
            ["differential_evolution", "nelder-mead"]
        )
        n_runs = st.number_input("Número de execuções", 1, 20, 5)
    with col2:
        population_size = st.number_input("Tamanho da população", 10, 100, 20)
        max_iterations = st.number_input("Número máximo de iterações", 10, 1000, 100)
        
    if st.button("Executar Otimização Automática"):
        try:
            # Executar otimização
            results = ua.run_automatic_optimization(
                method=method,
                n_runs=n_runs,
                population_size=population_size,
                max_iterations=max_iterations
            )
            
            # Plotar resultados
            st.write("### Resultados da Otimização Automática")
            
            # Evolução do erro
            fig_opt = ua.plot_optimization_results()
            st.pyplot(fig_opt)
            
            # Melhor solução
            best_run = min(results, key=lambda x: x['error'])
            st.write("### Melhor Solução")
            st.write(f"Execução: {best_run['run']}")
            st.write(f"Erro: {best_run['error']:.4f}")
            st.write("Parâmetros:")
            for name, value in best_run['parameters'].items():
                st.write(f"- {name}: {value:.4f}")
                
        except Exception as e:
            st.error(f"Erro na otimização automática: {str(e)}")
            
else:  # Análise de Sensitividade
    n_samples = st.slider("Número de amostras por parâmetro", 10, 500, 100)
    
    if st.button("Executar Análise de Sensitividade"):
        try:
            # Executar análise
            results = ua.run_parameter_sensitivity(n_samples)
            
            # Plotar resultados
            st.write("### Resultados da Análise de Sensitividade")
            
            # Sensitividade dos parâmetros
            fig_sens = ua.plot_sensitivity_results()
            st.pyplot(fig_sens)
            
            # Detalhes por parâmetro
            st.write("### Detalhes por Parâmetro")
            for name, result in results.items():
                st.write(f"#### {name}")
                st.write(f"Sensitividade: {result['sensitivity']:.4f}")
                
                # Plotar curva de sensitividade
                fig, ax = plt.subplots(figsize=(8, 4))
                ax.plot(result['values'], result['errors'])
                ax.set_title(f'Sensitividade de {name}')
                ax.set_xlabel('Valor do Parâmetro')
                ax.set_ylabel('Erro')
                ax.grid(True)
                st.pyplot(fig)
                
        except Exception as e:
            st.error(f"Erro na análise de sensitividade: {str(e)}")

# Exportar resultados
if st.button("Exportar Resultados"):
    try:
        ua.export_results("resultados_incertezas.csv")
        st.success("Resultados exportados com sucesso!")
    except Exception as e:
        st.error(f"Erro ao exportar resultados: {str(e)}")

# Seção de Previsão de Produção e Otimização
st.header("Previsão de Produção e Otimização")

# Criar objeto de otimização
opt = ProductionOptimization(sim)

# Seleção do tipo de análise
analysis_type = st.selectbox(
    "Tipo de Análise",
    ["Previsão de Produção", "Análise de Cenários", "Otimização de Malha", "Planejamento EOR"]
)

if analysis_type == "Previsão de Produção":
    st.subheader("Previsão de Produção")
    
    # Método de previsão
    forecast_method = st.selectbox(
        "Método de Previsão",
        ["Simulação", "Curvas de Declínio"]
    )
    
    # Parâmetros da previsão
    forecast_period = st.number_input("Período de Previsão (dias)", 30, 3650, 365)
    dt = st.number_input("Passo de Tempo (dias)", 1.0, 30.0, 1.0)
    
    if forecast_method == "Curvas de Declínio":
        st.write("### Parâmetros das Curvas de Declínio")
        
        # Óleo
        st.write("#### Óleo")
        oil_qi = st.number_input("Taxa Inicial (bbl/d)", 100.0, 10000.0, 1000.0)
        oil_di = st.number_input("Taxa de Declínio (1/dia)", 0.0001, 0.1, 0.01)
        oil_b = st.number_input("Expoente de Declínio", 0.0, 2.0, 0.0)
        
        # Água
        st.write("#### Água")
        water_qi = st.number_input("Taxa Inicial (bbl/d)", 100.0, 10000.0, 1000.0)
        water_di = st.number_input("Taxa de Declínio (1/dia)", 0.0001, 0.1, 0.01)
        water_b = st.number_input("Expoente de Declínio", 0.0, 2.0, 0.0)
        
        # Gás
        st.write("#### Gás")
        gas_qi = st.number_input("Taxa Inicial (Mscf/d)", 100.0, 10000.0, 1000.0)
        gas_di = st.number_input("Taxa de Declínio (1/dia)", 0.0001, 0.1, 0.01)
        gas_b = st.number_input("Expoente de Declínio", 0.0, 2.0, 0.0)
        
        decline_curves = {
            'oil': {'qi': oil_qi, 'Di': oil_di, 'b': oil_b},
            'water': {'qi': water_qi, 'Di': water_di, 'b': water_b},
            'gas': {'qi': gas_qi, 'Di': gas_di, 'b': gas_b}
        }
    else:
        decline_curves = None
        
    if st.button("Executar Previsão"):
        try:
            # Executar previsão
            forecast = opt.forecast_production(
                forecast_period,
                dt,
                decline_curves
            )
            
            # Plotar resultados
            fig = opt.plot_forecast()
            st.pyplot(fig)
            
            # Mostrar métricas
            metrics = opt._calculate_scenario_metrics(forecast)
            st.write("### Métricas")
            st.write(metrics)
            
        except Exception as e:
            st.error(f"Erro na previsão: {str(e)}")
            
elif analysis_type == "Análise de Cenários":
    st.subheader("Análise de Cenários")
    
    # Número de cenários
    n_scenarios = st.number_input("Número de Cenários", 1, 10, 3)
    
    scenarios = []
    for i in range(n_scenarios):
        st.write(f"### Cenário {i+1}")
        
        # Configurações do cenário
        forecast_period = st.number_input(
            f"Período de Previsão (dias) - Cenário {i+1}",
            30, 3650, 365
        )
        dt = st.number_input(
            f"Passo de Tempo (dias) - Cenário {i+1}",
            1.0, 30.0, 1.0
        )
        
        # Poços
        n_wells = st.number_input(
            f"Número de Poços - Cenário {i+1}",
            1, 20, 5
        )
        wells = []
        for j in range(n_wells):
            st.write(f"#### Poço {j+1}")
            well_type = st.selectbox(
                f"Tipo do Poço {j+1}",
                ["produtor", "injetor"],
                key=f"well_type_{i}_{j}"
            )
            x = st.number_input(
                f"Posição X (ft) - Poço {j+1}",
                0.0, float(sim.mesh.dimensions[0]),
                key=f"well_x_{i}_{j}"
            )
            y = st.number_input(
                f"Posição Y (ft) - Poço {j+1}",
                0.0, float(sim.mesh.dimensions[1]),
                key=f"well_y_{i}_{j}"
            )
            wells.append({
                'type': well_type,
                'x': x,
                'y': y
            })
            
        # Mecanismos de empuxo
        drive_mechanisms = {}
        if st.checkbox(f"Usar Cap de Gás - Cenário {i+1}"):
            drive_mechanisms['gas_cap'] = {
                'initial_pressure': st.number_input(
                    f"Pressão Inicial do Cap (psia) - Cenário {i+1}",
                    1000.0, 10000.0, 3000.0
                ),
                'initial_gas_saturation': st.number_input(
                    f"Saturação Inicial de Gás - Cenário {i+1}",
                    0.0, 1.0, 0.8
                )
            }
            
        if st.checkbox(f"Usar Aquífero - Cenário {i+1}"):
            drive_mechanisms['aquifer'] = {
                'type': st.selectbox(
                    f"Tipo de Aquífero - Cenário {i+1}",
                    ["pot", "fetkovich", "carter-tracy"]
                ),
                'initial_pressure': st.number_input(
                    f"Pressão Inicial do Aquífero (psia) - Cenário {i+1}",
                    1000.0, 10000.0, 3000.0
                )
            }
            
        # EOR
        eor = None
        if st.checkbox(f"Usar EOR - Cenário {i+1}"):
            eor_type = st.selectbox(
                f"Tipo de EOR - Cenário {i+1}",
                ["waterflood", "gas_injection", "chemical", "thermal"]
            )
            eor = {'type': eor_type}
            
        scenarios.append({
            'forecast_period': forecast_period,
            'dt': dt,
            'wells': wells,
            'drive_mechanisms': drive_mechanisms,
            'eor': eor
        })
        
    if st.button("Executar Análise de Cenários"):
        try:
            # Executar análise
            results = opt.run_scenario_analysis(scenarios)
            
            # Plotar comparação
            fig = opt.plot_scenario_comparison()
            st.pyplot(fig)
            
            # Mostrar métricas
            st.write("### Métricas por Cenário")
            for name, result in results.items():
                st.write(f"#### {name}")
                st.write(result['metrics'])
                
        except Exception as e:
            st.error(f"Erro na análise de cenários: {str(e)}")
            
elif analysis_type == "Otimização de Malha":
    st.subheader("Otimização de Malha de Poços")
    
    # Restrições
    constraints = {
        'n_wells': st.number_input("Número Total de Poços", 2, 20, 5),
        'forecast_period': st.number_input("Período de Previsão (dias)", 30, 3650, 365),
        'dt': st.number_input("Passo de Tempo (dias)", 1.0, 30.0, 1.0),
        'max_iterations': st.number_input("Número Máximo de Iterações", 10, 1000, 100),
        'population_size': st.number_input("Tamanho da População", 10, 100, 20),
        'oil_price': st.number_input("Preço do Óleo ($/bbl)", 20.0, 200.0, 60.0),
        'gas_price': st.number_input("Preço do Gás ($/Mscf)", 1.0, 10.0, 3.0),
        'water_cost': st.number_input("Custo da Água ($/bbl)", 1.0, 10.0, 2.0),
        'discount_rate': st.number_input("Taxa de Desconto (%/ano)", 5.0, 20.0, 10.0) / 100
    }
    
    if st.button("Otimizar Malha"):
        try:
            # Executar otimização
            results = opt.optimize_well_pattern(constraints)
            
            # Plotar malha otimizada
            fig = opt.plot_well_pattern()
            st.pyplot(fig)
            
            # Mostrar resultados
            st.write("### Resultados da Otimização")
            st.write(f"NPV: ${results['npv']:,.2f}")
            st.write("Poços:")
            for i, well in enumerate(results['wells']):
                st.write(f"Poço {i+1}:")
                st.write(f"- Tipo: {well['type']}")
                st.write(f"- Posição: ({well['x']:.1f}, {well['y']:.1f})")
                
        except Exception as e:
            st.error(f"Erro na otimização: {str(e)}")
            
else:  # Planejamento EOR
    st.subheader("Planejamento de Recuperação (EOR)")
    
    # Tipo de EOR
    eor_type = st.selectbox(
        "Tipo de EOR",
        ["waterflood", "gas_injection", "chemical", "thermal"]
    )
    
    # Restrições comuns
    constraints = {
        'forecast_period': st.number_input("Período de Previsão (dias)", 30, 3650, 365),
        'dt': st.number_input("Passo de Tempo (dias)", 1.0, 30.0, 1.0),
        'n_injectors': st.number_input("Número de Poços Injetores", 1, 10, 3),
        'n_producers': st.number_input("Número de Poços Produtores", 1, 10, 3),
        'injection_rate': st.number_input("Taxa de Injeção (bbl/d)", 1000.0, 10000.0, 5000.0)
    }
    
    # Restrições específicas
    if eor_type == "waterflood":
        constraints['water_quality'] = st.selectbox(
            "Qualidade da Água",
            ["água doce", "água salgada", "água produzida"]
        )
    elif eor_type == "gas_injection":
        constraints['gas_composition'] = {
            'C1': st.number_input("C1 (%)", 0.0, 100.0, 80.0) / 100,
            'C2': st.number_input("C2 (%)", 0.0, 100.0, 10.0) / 100,
            'C3': st.number_input("C3 (%)", 0.0, 100.0, 5.0) / 100,
            'C4+': st.number_input("C4+ (%)", 0.0, 100.0, 5.0) / 100
        }
    elif eor_type == "chemical":
        constraints['chemical_type'] = st.selectbox(
            "Tipo de Químico",
            ["polímero", "surfactante", "alcalino"]
        )
        constraints['concentration'] = st.number_input(
            "Concentração (%)",
            0.1, 10.0, 1.0
        )
        constraints['slug_size'] = st.number_input(
            "Tamanho do Slug (PV)",
            0.1, 1.0, 0.3
        )
    else:  # thermal
        constraints['steam_quality'] = st.number_input(
            "Qualidade do Vapor (%)",
            50.0, 100.0, 80.0
        )
        constraints['injection_temperature'] = st.number_input(
            "Temperatura de Injeção (°F)",
            200.0, 600.0, 400.0
        )
        
    if st.button("Planejar EOR"):
        try:
            # Executar planejamento
            results = opt.plan_eor(eor_type, constraints)
            
            # Plotar resultados
            fig = opt.plot_forecast()
            st.pyplot(fig)
            
            # Mostrar métricas
            st.write("### Métricas")
            st.write(results['metrics'])
            
            # Mostrar configuração
            st.write("### Configuração")
            if eor_type == "waterflood":
                st.write(f"Taxa de Injeção: {results['injection_rate']} bbl/d")
                st.write(f"Qualidade da Água: {results['water_quality']}")
            elif eor_type == "gas_injection":
                st.write(f"Taxa de Injeção: {results['injection_rate']} Mscf/d")
                st.write("Composição do Gás:")
                for comp, frac in results['gas_composition'].items():
                    st.write(f"- {comp}: {frac*100:.1f}%")
            elif eor_type == "chemical":
                st.write(f"Tipo de Químico: {results['chemical_type']}")
                st.write(f"Concentração: {results['concentration']}%")
                st.write(f"Tamanho do Slug: {results['slug_size']} PV")
            else:  # thermal
                st.write(f"Qualidade do Vapor: {results['steam_quality']}%")
                st.write(f"Temperatura de Injeção: {results['injection_temperature']}°F")
                
        except Exception as e:
            st.error(f"Erro no planejamento EOR: {str(e)}")

def production_analysis_page():
    st.title("Análise de Produção")
    
    # Inicializar analisador
    analyzer = ProductionAnalysis()
    
    # Upload de dados
    st.header("Upload de Dados")
    uploaded_file = st.file_uploader("Carregar dados históricos (CSV)", type=['csv'])
    
    if uploaded_file is not None:
        data = pd.read_csv(uploaded_file)
        
        # Configuração das colunas
        st.subheader("Configuração das Colunas")
        time_col = st.selectbox("Coluna de Tempo", data.columns)
        rate_cols = {}
        for phase in ['oil', 'water', 'gas']:
            col = st.selectbox(f"Coluna de Taxa de {phase}", data.columns)
            rate_cols[phase] = col
        pressure_col = st.selectbox("Coluna de Pressão (opcional)", [''] + list(data.columns))
        
        # Carregar dados
        analyzer.load_historical_data(
            data,
            time_col=time_col,
            rate_cols=rate_cols,
            pressure_col=pressure_col if pressure_col else None
        )
        
        # Análise de Curvas de Declínio
        st.header("Análise de Curvas de Declínio")
        phase = st.selectbox("Fase para Análise", ['oil', 'water', 'gas'])
        decline_type = st.selectbox("Tipo de Declínio", ['exponential', 'hyperbolic', 'harmonic'])
        n_samples = st.number_input("Número de Amostras para Incerteza", min_value=100, value=1000)
        
        if st.button("Ajustar Curva de Declínio"):
            results = analyzer.fit_decline_curves(
                phase=phase,
                decline_type=decline_type,
                n_samples=n_samples
            )
            
            # Mostrar parâmetros
            st.subheader("Parâmetros do Ajuste")
            for param, value in results['parameters'].items():
                st.write(f"{param}: {value:.4f}")
                
            # Plotar curva
            fig = analyzer.plot_decline_curves(phase)
            st.pyplot(fig)
            
        # Balanço de Materiais
        st.header("Balanço de Materiais")
        if pressure_col:
            # Upload de dados PVT
            pvt_file = st.file_uploader("Carregar dados PVT (CSV)", type=['csv'])
            
            if pvt_file is not None:
                pvt_data = pd.read_csv(pvt_file)
                
                # Configuração do reservatório
                st.subheader("Configuração do Reservatório")
                reservoir_type = st.selectbox("Tipo de Reservatório", ['oil', 'gas'])
                initial_pressure = st.number_input("Pressão Inicial (psi)", value=3000.0)
                initial_temperature = st.number_input("Temperatura Inicial (°F)", value=150.0)
                
                # Saturações iniciais
                st.subheader("Saturações Iniciais")
                initial_saturation = {}
                for phase in ['oil', 'water', 'gas']:
                    sat = st.number_input(f"Saturação de {phase}", min_value=0.0, max_value=1.0, value=0.0)
                    initial_saturation[phase] = sat
                    
                # Propriedades da rocha
                st.subheader("Propriedades da Rocha")
                rock_properties = {}
                for prop in ['Bo_initial', 'Rs_initial', 'Bw_initial', 'cw', 'cf']:
                    value = st.number_input(prop, value=1.0)
                    rock_properties[prop] = value
                    
                if st.button("Calcular Balanço de Materiais"):
                    results = analyzer.calculate_material_balance(
                        pvt_data=pvt_data,
                        reservoir_type=reservoir_type,
                        initial_pressure=initial_pressure,
                        initial_temperature=initial_temperature,
                        initial_saturation=initial_saturation,
                        rock_properties=rock_properties
                    )
                    
                    # Mostrar resultados
                    st.subheader("Resultados do Balanço de Materiais")
                    if reservoir_type == 'oil':
                        st.write(f"OOIP: {results['OOIP']:.0f} STB")
                    else:
                        st.write(f"OGIP: {results['OGIP']:.0f} Mscf")
                        
                    # Plotar resultados
                    fig = analyzer.plot_material_balance()
                    st.pyplot(fig)
                    
        # Previsão com Incerteza
        st.header("Previsão com Incerteza")
        forecast_period = st.number_input("Período de Previsão (dias)", min_value=30, value=365)
        dt = st.number_input("Passo de Tempo (dias)", min_value=1, value=30)
        
        if st.button("Realizar Previsão"):
            forecast = analyzer.forecast_with_uncertainty(
                forecast_period=forecast_period,
                dt=dt,
                n_samples=n_samples
            )
            
            # Plotar previsão
            fig = analyzer.plot_forecast()
            st.pyplot(fig)
            
            # Exportar resultados
            if st.button("Exportar Resultados"):
                analyzer.export_results("resultados_analise.csv")
                st.success("Resultados exportados com sucesso!")

def reserves_evaluation_page():
    st.title("Avaliação de Reservas e Análise Econômica")
    
    # Inicializar avaliador
    evaluator = ReservesEvaluation()
    
    # Upload de dados
    st.header("Upload de Dados")
    uploaded_file = st.file_uploader("Carregar dados de produção (CSV)", type=['csv'])
    
    if uploaded_file is not None:
        data = pd.read_csv(uploaded_file)
        
        # Configuração das colunas
        st.subheader("Configuração das Colunas")
        time_col = st.selectbox("Coluna de Tempo", data.columns)
        rate_cols = {}
        for phase in ['oil', 'water', 'gas']:
            col = st.selectbox(f"Coluna de Taxa de {phase}", data.columns)
            rate_cols[phase] = col
        pressure_col = st.selectbox("Coluna de Pressão (opcional)", [''] + list(data.columns))
        
        # Carregar dados
        evaluator.load_production_data(
            data,
            time_col=time_col,
            rate_cols=rate_cols,
            pressure_col=pressure_col if pressure_col else None
        )
        
        # Cálculo de Reservas
        st.header("Cálculo de Reservas")
        
        # Parâmetros das curvas de declínio
        st.subheader("Parâmetros das Curvas de Declínio")
        decline_curves = {}
        for phase in ['oil', 'water', 'gas']:
            st.write(f"#### {phase.capitalize()}")
            qi = st.number_input(f"Taxa Inicial (bbl/d/Mscf/d) - {phase}", value=1000.0)
            Di = st.number_input(f"Taxa de Declínio (1/dia) - {phase}", value=0.1)
            b = st.number_input(f"Expoente de Declínio - {phase}", value=0.0)
            decline_curves[phase] = {'qi': qi, 'Di': Di, 'b': b}
            
        # Limite econômico
        economic_limit = st.number_input("Limite Econômico (bbl/d/Mscf/d)", value=50.0)
        
        # Níveis de confiança
        st.subheader("Níveis de Confiança")
        confidence_levels = {
            'P1': st.number_input("P1 (Proved)", min_value=0.0, max_value=1.0, value=0.9),
            'P2': st.number_input("P2 (Probable)", min_value=0.0, max_value=1.0, value=0.5),
            'P3': st.number_input("P3 (Possible)", min_value=0.0, max_value=1.0, value=0.1)
        }
        
        if st.button("Calcular Reservas"):
            reserves = evaluator.calculate_reserves(
                decline_curves=decline_curves,
                economic_limit=economic_limit,
                confidence_levels=confidence_levels
            )
            
            # Mostrar resultados
            st.subheader("Resultados do Cálculo de Reservas")
            for category, phases in reserves.items():
                st.write(f"### {category}")
                for phase, value in phases.items():
                    st.write(f"- {phase.capitalize()}: {value:,.0f} bbl/Mscf")
                    
            # Plotar distribuição
            fig = evaluator.plot_reserves_distribution()
            st.pyplot(fig)
            
        # Análise Econômica
        st.header("Análise Econômica")
        
        # Parâmetros econômicos
        st.subheader("Parâmetros Econômicos")
        col1, col2 = st.columns(2)
        with col1:
            oil_price = st.number_input("Preço do Óleo ($/bbl)", value=60.0)
            gas_price = st.number_input("Preço do Gás ($/Mscf)", value=3.0)
            opex = st.number_input("OPEX ($/bbl)", value=10.0)
        with col2:
            capex = st.number_input("CAPEX ($)", value=1000000.0)
            discount_rate = st.number_input("Taxa de Desconto (%/ano)", value=10.0)
            tax_rate = st.number_input("Taxa de Impostos", min_value=0.0, max_value=1.0, value=0.34)
            
        if st.button("Calcular Métricas Econômicas"):
            metrics = evaluator.calculate_economic_metrics(
                oil_price=oil_price,
                gas_price=gas_price,
                opex=opex,
                capex=capex,
                discount_rate=discount_rate,
                tax_rate=tax_rate
            )
            
            # Mostrar resultados
            st.subheader("Métricas Econômicas")
            st.write(f"- NPV: ${metrics['npv']:,.2f}")
            st.write(f"- ROI: {metrics['roi']:.1f}%")
            st.write(f"- Payback: {metrics['payback']:.1f} anos")
            
            # Plotar métricas
            fig = evaluator.plot_economic_metrics()
            st.pyplot(fig)
            
        # Análise de Cenários
        st.header("Análise de Cenários")
        
        # Caso base
        st.subheader("Caso Base")
        base_case = {
            'oil_price': oil_price,
            'gas_price': gas_price,
            'opex': opex,
            'capex': capex,
            'discount_rate': discount_rate,
            'tax_rate': tax_rate
        }
        
        # Cenários
        n_scenarios = st.number_input("Número de Cenários", min_value=1, value=3)
        scenarios = []
        
        for i in range(n_scenarios):
            st.write(f"### Cenário {i+1}")
            col1, col2 = st.columns(2)
            with col1:
                oil_price_scen = st.number_input(f"Preço do Óleo ($/bbl) - Cenário {i+1}", value=oil_price)
                gas_price_scen = st.number_input(f"Preço do Gás ($/Mscf) - Cenário {i+1}", value=gas_price)
                opex_scen = st.number_input(f"OPEX ($/bbl) - Cenário {i+1}", value=opex)
            with col2:
                capex_scen = st.number_input(f"CAPEX ($) - Cenário {i+1}", value=capex)
                discount_rate_scen = st.number_input(f"Taxa de Desconto (%/ano) - Cenário {i+1}", value=discount_rate)
                tax_rate_scen = st.number_input(f"Taxa de Impostos - Cenário {i+1}", min_value=0.0, max_value=1.0, value=tax_rate)
                
            scenarios.append({
                'oil_price': oil_price_scen,
                'gas_price': gas_price_scen,
                'opex': opex_scen,
                'capex': capex_scen,
                'discount_rate': discount_rate_scen,
                'tax_rate': tax_rate_scen
            })
            
        if st.button("Executar Análise de Cenários"):
            results = evaluator.run_scenario_analysis(base_case, scenarios)
            
            # Mostrar resultados
            st.subheader("Resultados dos Cenários")
            for name, metrics in results.items():
                st.write(f"### {name}")
                st.write(f"- NPV: ${metrics['npv']:,.2f}")
                st.write(f"- ROI: {metrics['roi']:.1f}%")
                st.write(f"- Payback: {metrics['payback']:.1f} anos")
                
        # Geração de Relatórios
        st.header("Geração de Relatórios")
        
        if st.button("Gerar Relatório Técnico"):
            report = evaluator.generate_technical_report()
            st.markdown(report)
            
            # Download do relatório
            st.download_button(
                label="Baixar Relatório Técnico",
                data=report,
                file_name="relatorio_tecnico.md",
                mime="text/markdown"
            )
            
        if st.button("Gerar Resumo Executivo"):
            summary = evaluator.generate_executive_summary()
            st.markdown(summary)
            
            # Download do resumo
            st.download_button(
                label="Baixar Resumo Executivo",
                data=summary,
                file_name="resumo_executivo.md",
                mime="text/markdown"
            )

if __name__ == "__main__":
    st.set_page_config(page_title="Gaia Genesis", layout="wide")
    
    # Menu lateral
    menu = st.sidebar.selectbox(
        "Menu",
        ["Simulação de Fluxo", "History Matching", "Análise de Produção", "Avaliação de Reservas"]
    )
    
    if menu == "Simulação de Fluxo":
        flow_simulation_page()
    elif menu == "History Matching":
        history_matching_page()
    elif menu == "Análise de Produção":
        production_analysis_page()
    else:
        reserves_evaluation_page()