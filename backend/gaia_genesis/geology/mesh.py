import numpy as np
from scipy.spatial import Delaunay
import pyvista as pv
from typing import Dict, List, Tuple, Optional, Union  # Added Union


class Mesh:
    def __init__(self):
        """Inicializa o objeto de malha."""
        self.vertices: Optional[np.ndarray] = None  # Coordenadas dos vértices
        self.cells: Optional[np.ndarray] = None  # Conectividade das células
        self.cell_types: Optional[np.ndarray] = (
            None  # Tipos das células (hexaedro, tetraedro, etc)
        )
        self.volumes: Optional[np.ndarray] = None  # Volumes das células
        self.centroids: Optional[np.ndarray] = None  # Centróides das células
        self.faces: Optional[List[np.ndarray]] = None  # Faces das células
        self.face_areas: Optional[List[float]] = None  # Áreas das faces
        self.face_normals: Optional[List[np.ndarray]] = (
            None  # Vetores normais das faces
        )
        self.neighbors: Optional[List[List[int]]] = None  # Células vizinhas

    def create_structured_mesh(
        self, nx: int, ny: int, nz: int, dx: float, dy: float, dz: float
    ):
        """
        Cria uma malha estruturada cartesiana.

        Args:
            nx, ny, nz (int): Número de células em cada direção
            dx, dy, dz (float): Tamanho das células em cada direção
        """
        # Criar coordenadas dos vértices
        x = np.linspace(0, nx * dx, nx + 1)
        y = np.linspace(0, ny * dy, ny + 1)
        z = np.linspace(0, nz * dz, nz + 1)

        # Criar grade de pontos
        X, Y, Z = np.meshgrid(
            x, y, z, indexing="ij"
        )  # Use 'ij' indexing for consistency with typical loops
        self.vertices = np.column_stack((X.ravel(), Y.ravel(), Z.ravel()))

        # Criar células (hexaedros)
        # For a grid of (nx, ny, nz) cells, there are (nx+1, ny+1, nz+1) vertices.
        # Cell (i,j,k) uses vertex (i,j,k) as its origin (e.g., bottom-left-front corner)
        self.cells = []
        for k_idx in range(nz):  # z-direction cells
            for j_idx in range(ny):  # y-direction cells
                for i_idx in range(nx):  # x-direction cells
                    # Index of the first vertex of the cell (i,j,k)
                    # v000 = ( # F841: Unused
                    #     i_idx * (ny + 1) * (nz + 1) + j_idx * (nz + 1) + k_idx
                    # )  # This indexing seems off

                    # Corrected indexing for IJ (Cartesian style) meshgrid output
                    # (i,j,k) -> (i,j,k)
                    # (i+1,j,k) -> (i+1,j,k)
                    # (i,j+1,k) -> (i,j+1,k)
                    # (i+1,j+1,k) -> (i+1,j+1,k)
                    # (i,j,k+1) -> (i,j,k+1)
                    # (i+1,j,k+1) -> (i+1,j,k+1)
                    # (i,j+1,k+1) -> (i,j+1,k+1)
                    # (i+1,j+1,k+1) -> (i+1,j+1,k+1)

                    # Vertex indices assuming X, Y, Z from meshgrid(x,y,z, indexing='ij')
                    # X.shape = (nx+1, ny+1, nz+1)
                    # vertices.shape = ((nx+1)*(ny+1)*(nz+1), 3)
                    # Vertex (i,j,k) is at flat_index = k + (nz+1)*j + (nz+1)*(ny+1)*i

                    def idx_func(
                        i_param, j_param, k_param
                    ):  # Renamed params to avoid conflict
                        return (
                            k_param + (nz + 1) * j_param + (nz + 1) * (ny + 1) * i_param
                        )

                    v0 = idx_func(i_idx, j_idx, k_idx)
                    v1 = idx_func(i_idx + 1, j_idx, k_idx)
                    v2 = idx_func(i_idx, j_idx + 1, k_idx)
                    v3 = idx_func(i_idx + 1, j_idx + 1, k_idx)
                    v4 = idx_func(i_idx, j_idx, k_idx + 1)
                    v5 = idx_func(i_idx + 1, j_idx, k_idx + 1)
                    v6 = idx_func(i_idx, j_idx + 1, k_idx + 1)
                    v7 = idx_func(i_idx + 1, j_idx + 1, k_idx + 1)

                    # PyVista convention for HEXAHEDRON cell connectivity:
                    # List of 8 vertex indices.
                    # For a hexahedron cell, the connectivity is typically ordered.
                    # For example, using the VTK convention for VTK_HEXAHEDRON (similar to PyVista):
                    # (0,1,2,3) are bottom face, (4,5,6,7) are top face, ordered counter-clockwise from a point of view.
                    # Let's use a common ordering:
                    # Bottom face: v0, v1, v3, v2 (looking from -z)
                    # Top face:    v4, v5, v7, v6 (looking from -z)
                    # PyVista's format for a cell is [n_points, p0, p1, ..., pn-1]
                    # For add_mesh, it's just the connectivity list for cells.
                    # The order for PyVista HEXAHEDRON is:
                    # 0-1-2-3 (bottom face, e.g. z=0) then 4-5-6-7 (top face, e.g. z=1)
                    # (0,0,0), (1,0,0), (1,1,0), (0,1,0), (0,0,1), (1,0,1), (1,1,1), (0,1,1)
                    # This corresponds to: v0, v1, v3, v2, v4, v5, v7, v6
                    self.cells.append([v0, v1, v3, v2, v4, v5, v7, v6])

        self.cells = np.array(self.cells)
        self.cell_types = np.full(len(self.cells), pv.CellType.HEXAHEDRON)

        self._calculate_mesh_properties()

    def create_unstructured_mesh(
        self, points: np.ndarray, boundary_points: Optional[np.ndarray] = None
    ):
        """
        Cria uma malha não estruturada usando triangulação de Delaunay.
        Currently implemented for 2D points, creating 2D cells (triangles).
        For 3D tetrahedra from 3D points, Delaunay(points) would be used directly.

        Args:
            points (np.array): Pontos para criar a malha (n_points, 2 or 3 for x,y,z)
            boundary_points (np.array, optional): Pontos que definem o contorno (for 2D)
        """
        if points.shape[1] == 2:  # 2D points, create 2D mesh (triangles)
            tri = Delaunay(points)
            self.vertices = np.hstack(
                (points, np.zeros((points.shape[0], 1)))
            )  # Add z=0
            self.cells = tri.simplices  # These are triangles
            self.cell_types = np.full(len(self.cells), pv.CellType.TRIANGLE)
        elif points.shape[1] == 3:  # 3D points, create 3D mesh (tetrahedra)
            tri = Delaunay(points)
            self.vertices = points
            self.cells = tri.simplices  # These are tetrahedra
            self.cell_types = np.full(len(self.cells), pv.CellType.TETRA)
        else:
            raise ValueError("Points must have 2 or 3 columns (dimensions).")

        self._calculate_mesh_properties()  # This will need to handle both triangle and tetra volumes/centroids

    def _calculate_mesh_properties(self):
        """Calcula propriedades da malha."""
        if self.cells is None or self.vertices is None:
            return

        self.volumes = np.zeros(len(self.cells))
        for i, cell_conn in enumerate(self.cells):
            cell_vertices = self.vertices[cell_conn]
            cell_type = self.cell_types[i]

            if cell_type == pv.CellType.HEXAHEDRON:
                self.volumes[i] = self._calculate_hex_volume(cell_vertices)
            elif cell_type == pv.CellType.TETRA:
                self.volumes[i] = self._calculate_tet_volume(cell_vertices)
            elif cell_type == pv.CellType.TRIANGLE:  # 2D cell
                self.volumes[i] = self._calculate_tri_area(cell_vertices)  # Area for 2D
            # Add other cell types if supported

        self.centroids = np.zeros((len(self.cells), 3))
        for i, cell_conn in enumerate(self.cells):
            self.centroids[i] = np.mean(self.vertices[cell_conn], axis=0)

        # Faces, normals, neighbors are more complex and depend on full 3D topology
        # For now, these are simplified or might be placeholders if not fully robust for all mesh types.
        # self._calculate_faces()
        # self._calculate_neighbors()

    def _calculate_hex_volume(self, hex_vertices: np.ndarray) -> float:
        """Calcula volume de um hexaedro cartesiano (assumes dx, dy, dz from vertices)."""
        # Assuming vertices are ordered such that dx, dy, dz can be inferred
        # This is simple for a Cartesian cell. For a general hexahedron, it's more complex.
        # For PyVista HEXAHEDRON (0,1,2,3 bottom; 4,5,6,7 top)
        # v0=(x0,y0,z0), v1=(x1,y0,z0), v2=(x0,y1,z0), v4=(x0,y0,z1)
        # dx = |v1-v0|, dy = |v2-v0|, dz = |v4-v0| (for axis aligned)
        # A more general method for arbitrarily shaped hexahedra is to decompose into tets or use shoelace formula on faces + centroid.
        # PyVista cell.volume can be used if a PyVista grid is constructed first.
        # For simplicity, if it's from create_structured_mesh, dx, dy, dz are known.
        # This method might be overly simplified if vertices are not from an axis-aligned structured grid.
        # Let's use a robust method by decomposing into 2 tetrahedra (assuming a split) or using PyVista's internal.
        # Using a simple dx*dy*dz based on min/max of vertices for an axis-aligned assumption:
        min_coords = np.min(hex_vertices, axis=0)
        max_coords = np.max(hex_vertices, axis=0)
        dimensions = max_coords - min_coords
        return np.prod(dimensions)

    def _calculate_tet_volume(self, tet_vertices: np.ndarray) -> float:
        """Calcula volume de um tetraedro."""
        # v0, v1, v2, v3 are the vertices
        # Volume = 1/6 * | (v1-v0) . ((v2-v0) x (v3-v0)) |
        v0, v1, v2, v3 = (
            tet_vertices[0],
            tet_vertices[1],
            tet_vertices[2],
            tet_vertices[3],
        )
        return abs(np.dot(v1 - v0, np.cross(v2 - v0, v3 - v0))) / 6.0

    def _calculate_tri_area(self, tri_vertices: np.ndarray) -> float:
        """Calcula area de um triangulo (2D)."""
        v0, v1, v2 = tri_vertices[0], tri_vertices[1], tri_vertices[2]
        # Using cross product for 3D vertices (z=0 for 2D case)
        return 0.5 * np.linalg.norm(np.cross(v1 - v0, v2 - v0))

    # _calculate_faces and _calculate_neighbors are complex and depend heavily on robust topology.
    # PyVista handles this internally when creating a mesh object.
    # These methods are placeholder-level if retained.

    def to_pyvista(self) -> Optional[pv.UnstructuredGrid]:
        """Converte a malha para formato PyVista UnstructuredGrid."""
        if self.vertices is None or self.cells is None or self.cell_types is None:
            print(
                "Warning: Mesh data (vertices, cells, or cell_types) is not defined. Cannot convert to PyVista."
            )
            return None

        # PyVista expects cells in a specific format: [n_points_cell1, p0, p1, ..., n_points_cell2, p0, p1, ...]
        # For cells array that is (n_cells, n_verts_per_cell), need to prepend n_verts_per_cell to each row.

        cells_list = []
        for cell_conn in self.cells:
            cells_list.append(len(cell_conn))
            cells_list.extend(cell_conn)

        try:
            grid = pv.UnstructuredGrid(
                np.array(cells_list), self.cell_types, self.vertices
            )
            if self.volumes is not None:
                grid.cell_data["Volume"] = self.volumes
            if self.centroids is not None:
                # PyVista can calculate centroids too, but if we have them:
                # grid.cell_data['Centroid'] = self.centroids # This might not be right, centroids are points
                pass
            return grid
        except Exception as e:
            print(f"Error creating PyVista UnstructuredGrid: {e}")
            return None

    def plot(
        self,
        show_cells=True,
        show_vertices=False,
        scalar_property_name: Optional[str] = None,
        cell_data: Optional[np.ndarray] = None,
    ):
        """Plota a malha usando PyVista."""
        grid = self.to_pyvista()
        if grid is None:
            print("Cannot plot: PyVista grid conversion failed.")
            return

        if cell_data is not None and scalar_property_name is not None:
            if len(cell_data) == grid.n_cells:
                grid.cell_data[scalar_property_name] = cell_data
            else:
                print(
                    f"Warning: cell_data length ({len(cell_data)}) does not match number of cells ({grid.n_cells}). Not adding scalar data."
                )
                scalar_property_name = None  # Don't try to plot scalars

        plotter = pv.Plotter()

        if show_cells:
            plotter.add_mesh(grid, scalars=scalar_property_name, show_edges=True)
        if show_vertices:
            plotter.add_points(
                self.vertices, color="red", point_size=5
            )  # pv.PolyData needed for add_points

        plotter.show()


class Grid3D:
    """Sistema de grade 3D suportando geometria em pontos de canto e LGR"""

    def __init__(
        self,
        nx: int,
        ny: int,
        nz: int,
        dx: Union[float, np.ndarray],
        dy: Union[float, np.ndarray],
        dz: Union[float, np.ndarray],
    ):
        self.nx = nx
        self.ny = ny
        self.nz = nz

        # Allow dx, dy, dz to be arrays for variable spacing
        self.dx = dx if isinstance(dx, np.ndarray) else np.full(nx, dx)
        self.dy = dy if isinstance(dy, np.ndarray) else np.full(ny, dy)
        self.dz = dz if isinstance(dz, np.ndarray) else np.full(nz, dz)

        if not (len(self.dx) == nx and len(self.dy) == ny and len(self.dz) == nz):
            raise ValueError(
                "dx, dy, dz array lengths must match nx, ny, nz respectively if provided as arrays."
            )

        self.nodes: Optional[np.ndarray] = None
        self.cell_centers: Optional[np.ndarray] = None
        self.volumes: Optional[np.ndarray] = None
        self.faces: Dict = {}  # Stores face areas
        self.lgrs: List[Dict] = []

        self._initialize_cartesian_grid()

    def add_lgr(
        self,
        i_start: int,
        i_end: int,
        j_start: int,
        j_end: int,
        k_start: int,
        k_end: int,
        refinement: Tuple[int, int, int],
    ):
        """Adicionar região de refinamento de grade local"""
        # Validate LGR extents
        if not (
            0 <= i_start < i_end < self.nx
            and 0 <= j_start < j_end < self.ny
            and 0 <= k_start < k_end < self.nz
        ):
            raise ValueError("Invalid LGR extents.")

        lgr_nx = (i_end - i_start + 1) * refinement[0]
        lgr_ny = (j_end - j_start + 1) * refinement[1]
        lgr_nz = (k_end - k_start + 1) * refinement[2]

        # Calculate refined dx, dy, dz for the LGR region
        # This assumes parent cells within LGR region have uniform dx, dy, dz
        # For variable parent dx, dy, dz, this needs more complex handling
        parent_dx_region = self.dx[i_start : i_end + 1]
        parent_dy_region = self.dy[j_start : j_end + 1]
        parent_dz_region = self.dz[k_start : k_end + 1]

        # For simplicity, assume LGR dx,dy,dz are mean of parents divided by refinement
        # A more robust approach would handle individual parent cell sizes.
        lgr_dx_val = np.mean(parent_dx_region) / refinement[0]
        lgr_dy_val = np.mean(parent_dy_region) / refinement[1]
        lgr_dz_val = np.mean(parent_dz_region) / refinement[2]

        lgr_grid = Grid3D(
            nx=lgr_nx, ny=lgr_ny, nz=lgr_nz, dx=lgr_dx_val, dy=lgr_dy_val, dz=lgr_dz_val
        )
        # TODO: Position the LGR grid correctly in global coordinates

        lgr = {
            "parent_extent": (i_start, i_end, j_start, j_end, k_start, k_end),
            "refinement": refinement,
            "grid": lgr_grid,
        }
        self.lgrs.append(lgr)

    def get_cell_neighbors(self, i: int, j: int, k: int) -> List[Tuple[int, int, int]]:
        """Obter índices das células vizinhas"""
        neighbors = []
        for di, dj, dk in [
            (-1, 0, 0),
            (1, 0, 0),
            (0, -1, 0),
            (0, 1, 0),
            (0, 0, -1),
            (0, 0, 1),
        ]:
            ni, nj, nk = i + di, j + dj, k + dk
            if 0 <= ni < self.nx and 0 <= nj < self.ny and 0 <= nk < self.nz:
                neighbors.append((ni, nj, nk))
        return neighbors

    def get_cell_volume(self, i: int, j: int, k: int) -> float:
        """Obter volume da célula (base grid, LGR not fully implemented here for volume access)"""
        if self.volumes is not None:
            return self.volumes[i, j, k]
        return 0.0  # Should not happen if initialized

    def get_face_area(
        self, i: int, j: int, k: int, face_orientation: str
    ) -> float:  # face_orientation e.g. 'x-', 'x+', 'y-', 'y+', 'z-', 'z+'
        """Obter área da face da célula"""
        # This simplified version assumes Cartesian cells and doesn't account for LGR interface complexity yet.
        if face_orientation in ["x-", "x+"]:  # Faces normal to x-axis (YZ plane)
            return self.dy[j] * self.dz[k]
        elif face_orientation in ["y-", "y+"]:  # Faces normal to y-axis (XZ plane)
            return self.dx[i] * self.dz[k]
        elif face_orientation in ["z-", "z+"]:  # Faces normal to z-axis (XY plane)
            return self.dx[i] * self.dy[j]
        else:
            raise ValueError(
                f"Face inválida: {face_orientation}. Use 'x-', 'x+', 'y-', 'y+', 'z-', or 'z+'."
            )

    def _initialize_cartesian_grid(self):
        """Inicializar grade cartesiana regular"""
        # Node coordinates (cumulative sums of dx, dy, dz)
        x_nodes = np.concatenate(([0], np.cumsum(self.dx)))
        y_nodes = np.concatenate(([0], np.cumsum(self.dy)))
        z_nodes = np.concatenate(([0], np.cumsum(self.dz)))

        self.nodes = np.zeros((self.nx + 1, self.ny + 1, self.nz + 1, 3))
        for i in range(self.nx + 1):
            for j in range(self.ny + 1):
                for k in range(self.nz + 1):
                    self.nodes[i, j, k] = [x_nodes[i], y_nodes[j], z_nodes[k]]

        self.cell_centers = np.zeros((self.nx, self.ny, self.nz, 3))
        self.volumes = np.zeros((self.nx, self.ny, self.nz))
        for i in range(self.nx):
            for j in range(self.ny):
                for k in range(self.nz):
                    self.cell_centers[i, j, k] = [
                        x_nodes[i] + self.dx[i] / 2,
                        y_nodes[j] + self.dy[j] / 2,
                        z_nodes[k] + self.dz[k] / 2,
                    ]
                    self.volumes[i, j, k] = self.dx[i] * self.dy[j] * self.dz[k]

    # LGR related methods like _is_in_lgr, _get_lgr_cell_volume would need full implementation
    # if LGRs are to be actively used beyond just definition.

    @property
    def shape(self) -> Tuple[int, int, int]:
        """Obter dimensões da grade"""
        return (self.nx, self.ny, self.nz)

    @property
    def total_cells(self) -> int:
        """Obter número total de células (base grid, LGR needs full sum)"""
        # This is simplified, a full LGR implementation would sum cells from LGR grids too
        return self.nx * self.ny * self.nz
