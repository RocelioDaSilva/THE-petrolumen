import numpy as np
from scipy.optimize import fsolve

class MaterialBalance:
    def __init__(self, reservoir_type='oil'):
        """
        Inicializa o objeto de balanço de materiais.
        
        Args:
            reservoir_type (str): Tipo de reservatório ('oil' ou 'gas')
        """
        self.reservoir_type = reservoir_type
        self.pressure_history = []
        self.production_history = []
        self.pvt_data = {}
        
    def add_pressure_point(self, pressure, date=None):
        """
        Adiciona um ponto de pressão ao histórico.
        
        Args:
            pressure (float): Pressão em psia
            date (str, optional): Data do ponto
        """
        self.pressure_history.append({'pressure': pressure, 'date': date})
        
    def add_production_point(self, oil_prod=None, gas_prod=None, water_prod=None, date=None):
        """
        Adiciona um ponto de produção ao histórico.
        
        Args:
            oil_prod (float, optional): Produção de óleo em STB
            gas_prod (float, optional): Produção de gás em Mscf
            water_prod (float, optional): Produção de água em STB
            date (str, optional): Data do ponto
        """
        self.production_history.append({
            'oil': oil_prod,
            'gas': gas_prod,
            'water': water_prod,
            'date': date
        })
        
    def add_pvt_data(self, pressure, bo=None, bg=None, rs=None, rv=None, z=None):
        """
        Adiciona dados PVT para uma pressão específica.
        
        Args:
            pressure (float): Pressão em psia
            bo (float, optional): Fator de volume de formação do óleo
            bg (float, optional): Fator de volume de formação do gás
            rs (float, optional): Razão de solubilidade
            rv (float, optional): Razão de vaporização
            z (float, optional): Fator de compressibilidade
        """
        self.pvt_data[pressure] = {
            'bo': bo,
            'bg': bg,
            'rs': rs,
            'rv': rv,
            'z': z
        }
        
    def calculate_oil_mbal(self, N, m, We, Wp, Gp, Bw, cw, cf, Swi):
        """
        Calcula o balanço de materiais para reservatório de óleo.
        
        Args:
            N (float): OOIP em STB
            m (float): Razão gás-cap em lugar
            We (float): Influxo de água em STB
            Wp (float): Produção de água em STB
            Gp (float): Produção de gás em Mscf
            Bw (float): Fator de volume de formação da água
            cw (float): Compressibilidade da água
            cf (float): Compressibilidade da formação
            Swi (float): Saturação inicial de água
        
        Returns:
            float: Erro do balanço de materiais
        """
        if len(self.pressure_history) < 2:
            raise ValueError("Necessário pelo menos dois pontos de pressão")
            
        p1 = self.pressure_history[0]['pressure']
        p2 = self.pressure_history[-1]['pressure']
        
        # Interpolar dados PVT
        bo1 = np.interp(p1, list(self.pvt_data.keys()), [d['bo'] for d in self.pvt_data.values()])
        bo2 = np.interp(p2, list(self.pvt_data.keys()), [d['bo'] for d in self.pvt_data.values()])
        rs1 = np.interp(p1, list(self.pvt_data.keys()), [d['rs'] for d in self.pvt_data.values()])
        rs2 = np.interp(p2, list(self.pvt_data.keys()), [d['rs'] for d in self.pvt_data.values()])
        bg1 = np.interp(p1, list(self.pvt_data.keys()), [d['bg'] for d in self.pvt_data.values()])
        bg2 = np.interp(p2, list(self.pvt_data.keys()), [d['bg'] for d in self.pvt_data.values()])
        
        # Calcular expansão do óleo
        Eo = (bo2 - bo1) + (rs1 - rs2) * bg1
        
        # Calcular expansão do gás
        Eg = bo1 * (bg2/bg1 - 1)
        
        # Calcular expansão da água e formação
        Efw = (cw * Swi + cf) / (1 - Swi) * (p1 - p2)
        
        # Calcular produção total
        Np = sum(p['oil'] for p in self.production_history if p['oil'] is not None)
        
        # Calcular balanço de materiais
        F = Np * (bo2 + (rs1 - rs2) * bg2) + Wp * Bw - We * Bw
        E = Eo + m * Eg + (1 + m) * Efw
        
        return F - N * E
        
    def calculate_gas_mbal(self, G, We, Wp, Bw, cw, cf, Swi):
        """
        Calcula o balanço de materiais para reservatório de gás.
        
        Args:
            G (float): OGIP em Mscf
            We (float): Influxo de água em STB
            Wp (float): Produção de água em STB
            Bw (float): Fator de volume de formação da água
            cw (float): Compressibilidade da água
            cf (float): Compressibilidade da formação
            Swi (float): Saturação inicial de água
        
        Returns:
            float: Erro do balanço de materiais
        """
        if len(self.pressure_history) < 2:
            raise ValueError("Necessário pelo menos dois pontos de pressão")
            
        p1 = self.pressure_history[0]['pressure']
        p2 = self.pressure_history[-1]['pressure']
        
        # Interpolar dados PVT
        z1 = np.interp(p1, list(self.pvt_data.keys()), [d['z'] for d in self.pvt_data.values()])
        z2 = np.interp(p2, list(self.pvt_data.keys()), [d['z'] for d in self.pvt_data.values()])
        bg1 = np.interp(p1, list(self.pvt_data.keys()), [d['bg'] for d in self.pvt_data.values()])
        bg2 = np.interp(p2, list(self.pvt_data.keys()), [d['bg'] for d in self.pvt_data.values()])
        
        # Calcular expansão do gás
        Eg = bg2 - bg1
        
        # Calcular expansão da água e formação
        Efw = (cw * Swi + cf) / (1 - Swi) * (p1 - p2)
        
        # Calcular produção total
        Gp = sum(p['gas'] for p in self.production_history if p['gas'] is not None)
        
        # Calcular balanço de materiais
        F = Gp * bg2 + Wp * Bw - We * Bw
        E = Eg + Efw
        
        return F - G * E
        
    def solve_oil_mbal(self, m, We, Wp, Gp, Bw, cw, cf, Swi):
        """
        Resolve o balanço de materiais para encontrar o OOIP.
        
        Args:
            m (float): Razão gás-cap em lugar
            We (float): Influxo de água em STB
            Wp (float): Produção de água em STB
            Gp (float): Produção de gás em Mscf
            Bw (float): Fator de volume de formação da água
            cw (float): Compressibilidade da água
            cf (float): Compressibilidade da formação
            Swi (float): Saturação inicial de água
        
        Returns:
            float: OOIP estimado em STB
        """
        def objective(N):
            return self.calculate_oil_mbal(N, m, We, Wp, Gp, Bw, cw, cf, Swi)
            
        N = fsolve(objective, 1e6)[0]
        return N
        
    def solve_gas_mbal(self, We, Wp, Bw, cw, cf, Swi):
        """
        Resolve o balanço de materiais para encontrar o OGIP.
        
        Args:
            We (float): Influxo de água em STB
            Wp (float): Produção de água em STB
            Bw (float): Fator de volume de formação da água
            cw (float): Compressibilidade da água
            cf (float): Compressibilidade da formação
            Swi (float): Saturação inicial de água
        
        Returns:
            float: OGIP estimado em Mscf
        """
        def objective(G):
            return self.calculate_gas_mbal(G, We, Wp, Bw, cw, cf, Swi)
            
        G = fsolve(objective, 1e9)[0]
        return G 