import numpy as np
from scipy.spatial import Delaunay
import pyvista as pv
from typing import Dict, List, Tuple, Optional

class Mesh:
    def __init__(self):
        """Inicializa o objeto de malha."""
        self.vertices = None  # Coordenadas dos vértices
        self.cells = None     # Conectividade das células
        self.cell_types = None  # Tipos das células (hexaedro, tetraedro, etc)
        self.volumes = None   # Volumes das células
        self.centroids = None # Centróides das células
        self.faces = None     # Faces das células
        self.face_areas = None # Áreas das faces
        self.face_normals = None # Vetores normais das faces
        self.neighbors = None # Células vizinhas
        
    def create_structured_mesh(self, nx, ny, nz, dx, dy, dz):
        """
        Cria uma malha estruturada cartesiana.
        
        Args:
            nx, ny, nz (int): Número de células em cada direção
            dx, dy, dz (float): Tamanho das células em cada direção
        """
        # Criar coordenadas dos vértices
        x = np.linspace(0, nx*dx, nx+1)
        y = np.linspace(0, ny*dy, ny+1)
        z = np.linspace(0, nz*dz, nz+1)
        
        # Criar grade de pontos
        X, Y, Z = np.meshgrid(x, y, z)
        self.vertices = np.column_stack((X.flatten(), Y.flatten(), Z.flatten()))
        
        # Criar células (hexaedros)
        self.cells = []
        for k in range(nz):
            for j in range(ny):
                for i in range(nx):
                    # Índices dos vértices do hexaedro
                    v0 = i + j*(nx+1) + k*(nx+1)*(ny+1)
                    v1 = v0 + 1
                    v2 = v0 + (nx+1)
                    v3 = v2 + 1
                    v4 = v0 + (nx+1)*(ny+1)
                    v5 = v1 + (nx+1)*(ny+1)
                    v6 = v2 + (nx+1)*(ny+1)
                    v7 = v3 + (nx+1)*(ny+1)
                    
                    self.cells.append([v0, v1, v2, v3, v4, v5, v6, v7])
        
        self.cells = np.array(self.cells)
        self.cell_types = np.full(len(self.cells), pv.CellType.HEXAHEDRON)
        
        # Calcular propriedades da malha
        self._calculate_mesh_properties()
        
    def create_unstructured_mesh(self, points, boundary_points=None):
        """
        Cria uma malha não estruturada usando triangulação de Delaunay.
        
        Args:
            points (np.array): Pontos para criar a malha
            boundary_points (np.array, optional): Pontos que definem o contorno
        """
        # Triangulação de Delaunay
        tri = Delaunay(points[:, :2])  # Usar apenas x,y para triangulação 2D
        
        # Criar células (tetraedros)
        self.vertices = points
        self.cells = tri.simplices
        self.cell_types = np.full(len(self.cells), pv.CellType.TETRA)
        
        # Calcular propriedades da malha
        self._calculate_mesh_properties()
        
    def _calculate_mesh_properties(self):
        """Calcula propriedades da malha."""
        # Calcular volumes das células
        self.volumes = np.zeros(len(self.cells))
        for i, cell in enumerate(self.cells):
            vertices = self.vertices[cell]
            if len(cell) == 8:  # Hexaedro
                self.volumes[i] = self._calculate_hex_volume(vertices)
            else:  # Tetraedro
                self.volumes[i] = self._calculate_tet_volume(vertices)
        
        # Calcular centróides
        self.centroids = np.zeros((len(self.cells), 3))
        for i, cell in enumerate(self.cells):
            self.centroids[i] = np.mean(self.vertices[cell], axis=0)
        
        # Calcular faces e suas propriedades
        self._calculate_faces()
        
        # Calcular vizinhos
        self._calculate_neighbors()
        
    def _calculate_hex_volume(self, vertices):
        """Calcula volume de um hexaedro."""
        # Dividir em 5 tetraedros e somar volumes
        tet_vertices = [
            [0, 1, 2, 4],  # Base inferior
            [1, 2, 3, 4],  # Base inferior
            [2, 3, 7, 4],  # Lado direito
            [3, 0, 4, 7],  # Lado esquerdo
            [4, 5, 6, 7]   # Base superior
        ]
        
        volume = 0
        for tet in tet_vertices:
            v = vertices[tet]
            volume += self._calculate_tet_volume(v)
            
        return volume
        
    def _calculate_tet_volume(self, vertices):
        """Calcula volume de um tetraedro."""
        v1 = vertices[1] - vertices[0]
        v2 = vertices[2] - vertices[0]
        v3 = vertices[3] - vertices[0]
        
        return abs(np.dot(np.cross(v1, v2), v3)) / 6
        
    def _calculate_faces(self):
        """Calcula faces e suas propriedades."""
        self.faces = []
        self.face_areas = []
        self.face_normals = []
        
        for i, cell in enumerate(self.cells):
            if len(cell) == 8:  # Hexaedro
                # 6 faces quadrangulares
                face_indices = [
                    [0, 1, 2, 3],  # Face inferior
                    [4, 5, 6, 7],  # Face superior
                    [0, 1, 5, 4],  # Face frontal
                    [2, 3, 7, 6],  # Face traseira
                    [0, 3, 7, 4],  # Face esquerda
                    [1, 2, 6, 5]   # Face direita
                ]
            else:  # Tetraedro
                # 4 faces triangulares
                face_indices = [
                    [0, 1, 2],
                    [0, 2, 3],
                    [0, 3, 1],
                    [1, 3, 2]
                ]
            
            for face in face_indices:
                vertices = self.vertices[cell[face]]
                self.faces.append(vertices)
                
                # Calcular área e normal
                if len(face) == 4:  # Face quadrangular
                    area, normal = self._calculate_quad_face_properties(vertices)
                else:  # Face triangular
                    area, normal = self._calculate_tri_face_properties(vertices)
                    
                self.face_areas.append(area)
                self.face_normals.append(normal)
                
    def _calculate_quad_face_properties(self, vertices):
        """Calcula área e normal de uma face quadrangular."""
        # Dividir em dois triângulos
        v1 = vertices[1] - vertices[0]
        v2 = vertices[2] - vertices[0]
        v3 = vertices[3] - vertices[0]
        
        # Calcular normais dos triângulos
        n1 = np.cross(v1, v2)
        n2 = np.cross(v2, v3)
        
        # Normal média
        normal = (n1 + n2) / 2
        normal = normal / np.linalg.norm(normal)
        
        # Área total
        area = (np.linalg.norm(n1) + np.linalg.norm(n2)) / 2
        
        return area, normal
        
    def _calculate_tri_face_properties(self, vertices):
        """Calcula área e normal de uma face triangular."""
        v1 = vertices[1] - vertices[0]
        v2 = vertices[2] - vertices[0]
        
        normal = np.cross(v1, v2)
        area = np.linalg.norm(normal) / 2
        normal = normal / np.linalg.norm(normal)
        
        return area, normal
        
    def _calculate_neighbors(self):
        """Calcula células vizinhas."""
        self.neighbors = [[] for _ in range(len(self.cells))]
        
        # Para cada face, encontrar células que compartilham a face
        for i, cell in enumerate(self.cells):
            for j, other_cell in enumerate(self.cells):
                if i != j:
                    # Verificar se compartilham vértices
                    shared_vertices = set(cell).intersection(set(other_cell))
                    if len(shared_vertices) >= 3:  # Compartilham uma face
                        self.neighbors[i].append(j)
                        
    def to_pyvista(self):
        """Converte a malha para formato PyVista."""
        grid = pv.UnstructuredGrid(self.vertices, self.cell_types, self.cells)
        return grid
        
    def plot(self, show_cells=True, show_vertices=False):
        """Plota a malha usando PyVista."""
        grid = self.to_pyvista()
        plotter = pv.Plotter()
        
        if show_cells:
            plotter.add_mesh(grid, show_edges=True)
        if show_vertices:
            plotter.add_mesh(pv.PolyData(self.vertices), color='red', point_size=10)
            
        plotter.show()
        
class Grid3D:
    """Sistema de grade 3D suportando geometria em pontos de canto e LGR"""
    
    def __init__(self, nx: int, ny: int, nz: int, 
                 dx: float, dy: float, dz: float):
        self.nx = nx
        self.ny = ny
        self.nz = nz
        self.dx = dx
        self.dy = dy
        self.dz = dz
        
        # Inicializar geometria da grade
        self.nodes = np.zeros((nx+1, ny+1, nz+1, 3))  # Pontos de canto
        self.cell_centers = np.zeros((nx, ny, nz, 3))  # Centros das células
        self.volumes = np.zeros((nx, ny, nz))          # Volumes das células
        self.faces = {}                                # Faces das células
        self.lgrs = []                                # Refinamentos de grade local
        
        self._initialize_cartesian_grid()
        
    def add_lgr(self, i_start: int, i_end: int,
                j_start: int, j_end: int,
                k_start: int, k_end: int,
                refinement: Tuple[int, int, int]):
        """Adicionar região de refinamento de grade local"""
        lgr = {
            "extent": (i_start, i_end, j_start, j_end, k_start, k_end),
            "refinement": refinement,
            "grid": self._create_refined_grid(
                i_start, i_end, j_start, j_end, k_start, k_end, refinement
            )
        }
        self.lgrs.append(lgr)
        
    def get_cell_neighbors(self, i: int, j: int, k: int) -> List[Tuple[int, int, int]]:
        """Obter índices das células vizinhas"""
        neighbors = []
        for di, dj, dk in [(-1,0,0), (1,0,0), (0,-1,0), (0,1,0), (0,0,-1), (0,0,1)]:
            ni, nj, nk = i + di, j + dj, k + dk
            if 0 <= ni < self.nx and 0 <= nj < self.ny and 0 <= nk < self.nz:
                neighbors.append((ni, nj, nk))
        return neighbors
        
    def get_cell_volume(self, i: int, j: int, k: int) -> float:
        """Obter volume da célula incluindo LGR se presente"""
        for lgr in self.lgrs:
            if self._is_in_lgr(i, j, k, lgr):
                return self._get_lgr_cell_volume(i, j, k, lgr)
        return self.volumes[i,j,k]
        
    def get_face_area(self, i: int, j: int, k: int, 
                      face: str) -> float:
        """Obter área da face da célula"""
        key = (i,j,k,face)
        if key not in self.faces:
            self.faces[key] = self._calculate_face_area(i,j,k,face)
        return self.faces[key]
        
    def _initialize_cartesian_grid(self):
        """Inicializar grade cartesiana regular"""
        # Definir coordenadas dos nós
        for i in range(self.nx + 1):
            for j in range(self.ny + 1):
                for k in range(self.nz + 1):
                    self.nodes[i,j,k] = [
                        i * self.dx,
                        j * self.dy,
                        k * self.dz
                    ]
        
        # Calcular centros e volumes das células
        for i in range(self.nx):
            for j in range(self.ny):
                for k in range(self.nz):
                    self.cell_centers[i,j,k] = [
                        (i + 0.5) * self.dx,
                        (j + 0.5) * self.dy,
                        (k + 0.5) * self.dz
                    ]
                    self.volumes[i,j,k] = self.dx * self.dy * self.dz
                    
    def _create_refined_grid(self, i1: int, i2: int,
                            j1: int, j2: int,
                            k1: int, k2: int,
                            refinement: Tuple[int, int, int]) -> 'Grid3D':
        """Criar grade refinada para região LGR"""
        nx_ref, ny_ref, nz_ref = refinement
        dx_ref = self.dx / nx_ref
        dy_ref = self.dy / ny_ref
        dz_ref = self.dz / nz_ref
        
        return Grid3D(
            (i2-i1+1) * nx_ref,
            (j2-j1+1) * ny_ref,
            (k2-k1+1) * nz_ref,
            dx_ref, dy_ref, dz_ref
        )
        
    def _is_in_lgr(self, i: int, j: int, k: int, 
                   lgr: Dict) -> bool:
        """Verificar se a célula está na região LGR"""
        i1,i2,j1,j2,k1,k2 = lgr["extent"]
        return (i1 <= i <= i2 and 
                j1 <= j <= j2 and 
                k1 <= k <= k2)
        
    def _get_lgr_cell_volume(self, i: int, j: int, k: int,
                            lgr: Dict) -> float:
        """Obter volume da célula na região LGR"""
        i1,i2,j1,j2,k1,k2 = lgr["extent"]
        nx_ref, ny_ref, nz_ref = lgr["refinement"]
        
        # Converter para coordenadas locais da LGR
        i_local = (i - i1) * nx_ref
        j_local = (j - j1) * ny_ref
        k_local = (k - k1) * nz_ref
        
        return lgr["grid"].volumes[i_local,j_local,k_local]
        
    def _calculate_face_area(self, i: int, j: int, k: int,
                            face: str) -> float:
        """Calcular área da face da célula"""
        if face in ['left', 'right']:
            return self.dy * self.dz
        elif face in ['front', 'back']:
            return self.dx * self.dz
        elif face in ['top', 'bottom']:
            return self.dx * self.dy
        else:
            raise ValueError(f"Face inválida: {face}")

    @property
    def shape(self) -> Tuple[int, int, int]:
        """Obter dimensões da grade"""
        return (self.nx, self.ny, self.nz)

    @property
    def total_cells(self) -> int:
        """Obter número total de células incluindo LGRs"""
        base_cells = self.nx * self.ny * self.nz
        lgr_cells = sum(
            lgr["grid"].total_cells for lgr in self.lgrs
        )
        return base_cells + lgr_cells