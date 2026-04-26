"""
Geomechanical Coupling Module

This module provides capabilities for coupling geomechanics with reservoir simulation,
including stress/strain calculations, porosity/permeability updates, and fracture modeling.
"""

import numpy as np
from typing import Dict, List, Tuple  # Removed Optional, Union, Any
from scipy.sparse import csr_matrix, lil_matrix
from scipy.sparse.linalg import spsolve

# import numba # Unused


class GeomechanicalModel:
    def __init__(
        self, grid_dims: Tuple[int, int, int], properties: Dict[str, np.ndarray]
    ):
        """
        Initialize geomechanical model.

        Args:
            grid_dims: Grid dimensions (nx, ny, nz)
            properties: Dictionary of rock mechanical properties
        """
        self.nx, self.ny, self.nz = grid_dims
        self.n_cells = self.nx * self.ny * self.nz
        self.properties = properties

        # Initialize stress and strain tensors
        self.stress = {
            "xx": np.zeros(self.n_cells),
            "yy": np.zeros(self.n_cells),
            "zz": np.zeros(self.n_cells),
            "xy": np.zeros(self.n_cells),
            "yz": np.zeros(self.n_cells),
            "xz": np.zeros(self.n_cells),
        }

        self.strain = {
            "xx": np.zeros(self.n_cells),
            "yy": np.zeros(self.n_cells),
            "zz": np.zeros(self.n_cells),
            "xy": np.zeros(self.n_cells),
            "yz": np.zeros(self.n_cells),
            "xz": np.zeros(self.n_cells),
        }

        self.displacement = {
            "x": np.zeros(self.n_cells),
            "y": np.zeros(self.n_cells),
            "z": np.zeros(self.n_cells),
        }

        # Initialize failure criteria
        self.failure_criterion = (
            "mohr_coulomb"  # 'mohr_coulomb', 'drucker_prager', 'hoek_brown'
        )
        self.failure_flag = np.zeros(self.n_cells, dtype=bool)

        # Initialize boundary conditions
        self.boundary_conditions = {
            "type": "fixed_stress",  # 'fixed_stress', 'fixed_strain', 'fixed_displacement'
            "values": {
                "top": {"xx": 0.0, "yy": 0.0, "zz": 0.0},
                "bottom": {"xx": 0.0, "yy": 0.0, "zz": 0.0},
                "left": {"xx": 0.0, "yy": 0.0, "zz": 0.0},
                "right": {"xx": 0.0, "yy": 0.0, "zz": 0.0},
                "front": {"xx": 0.0, "yy": 0.0, "zz": 0.0},
                "back": {"xx": 0.0, "yy": 0.0, "zz": 0.0},
            },
        }

        # Initialize coupling parameters
        self.coupling_method = "one_way"  # 'one_way', 'iterative', 'fully_coupled'
        self.biot_coefficient = properties.get("biot_coefficient", 1.0)
        self.convergence_tolerance = 1e-5
        self.max_iterations = 20

    def set_initial_stress(self, stress_gradient: Dict[str, float], depth: np.ndarray):
        """
        Set initial stress state based on depth and stress gradients.

        Args:
            stress_gradient: Dictionary with stress gradients (psi/ft)
            depth: Depth array for each cell (ft)
        """
        # Calculate initial stress based on depth
        for component in ["xx", "yy", "zz"]:
            if component in stress_gradient:
                self.stress[component] = depth * stress_gradient[component]

        # Default values for shear components
        for component in ["xy", "yz", "xz"]:
            self.stress[component] = np.zeros_like(depth)

    def update_stress_from_pressure(
        self, pressure: np.ndarray, pressure_prev: np.ndarray
    ):
        """
        Update stress state based on pressure changes.

        Args:
            pressure: Current pressure field
            pressure_prev: Previous pressure field
        """
        # Calculate pressure change
        delta_p = pressure - pressure_prev

        # Update total stress using Biot's coefficient
        for component in ["xx", "yy", "zz"]:
            self.stress[component] -= self.biot_coefficient * delta_p

    def solve_mechanics(self, pressure: np.ndarray, grid_geometry: Dict):
        """
        Solve geomechanical equations.

        Args:
            pressure: Current pressure field
            grid_geometry: Grid geometry information
        """
        # Extract properties
        _E = self.properties.get(
            "youngs_modulus", np.ones(self.n_cells) * 1e6
        )  # psi # noqa: F841
        _nu = self.properties.get(
            "poissons_ratio", np.ones(self.n_cells) * 0.25
        )  # noqa: F841

        # Assemble stiffness matrix and load vector
        K, f = self._assemble_system(pressure, grid_geometry)

        # Apply boundary conditions
        K, f = self._apply_boundary_conditions(K, f)

        # Solve for displacements
        u = spsolve(K, f)

        # Extract displacement components
        self.displacement["x"] = u[0::3]
        self.displacement["y"] = u[1::3]
        self.displacement["z"] = u[2::3]

        # Calculate strains and stresses
        self._calculate_strain_stress(grid_geometry)

        # Check failure criteria
        self._check_failure()

    def _assemble_system(self, pressure: np.ndarray, grid_geometry: Dict):
        """
        Assemble stiffness matrix and load vector.

        Args:
            pressure: Current pressure field
            grid_geometry: Grid geometry information

        Returns:
            Tuple of (stiffness_matrix, load_vector)
        """
        # This is a placeholder for the full implementation
        # In a real code, this would assemble the full 3D elasticity equations

        # Create empty stiffness matrix and load vector
        ndof = 3 * self.n_cells  # 3 DOFs per cell (ux, uy, uz)
        K = lil_matrix((ndof, ndof))
        f = np.zeros(ndof)

        # Apply pressure as body force
        for i in range(self.n_cells):
            # Apply pressure to load vector
            f[3 * i] = -self.biot_coefficient * pressure[i]  # x-component
            f[3 * i + 1] = -self.biot_coefficient * pressure[i]  # y-component
            f[3 * i + 2] = -self.biot_coefficient * pressure[i]  # z-component

        # Convert to CSR format for efficient solving
        K = K.tocsr()

        return K, f

    def _apply_boundary_conditions(self, K: csr_matrix, f: np.ndarray):
        """Apply boundary conditions to the system."""
        # This is a placeholder for the full implementation
        return K, f

    def _calculate_strain_stress(self, grid_geometry: Dict):
        """Calculate strain and stress from displacements."""
        # This is a placeholder for the full implementation
        pass

    def _check_failure(self):
        """Check failure criteria."""
        if self.failure_criterion == "mohr_coulomb":
            self._check_mohr_coulomb_failure()
        elif self.failure_criterion == "drucker_prager":
            self._check_drucker_prager_failure()

    def _check_mohr_coulomb_failure(self):
        """Check Mohr-Coulomb failure criterion."""
        # Extract principal stresses
        s1, s2, s3 = self._calculate_principal_stresses()

        # Get cohesion and friction angle
        c = self.properties.get("cohesion", np.ones(self.n_cells) * 1000.0)  # psi
        phi = np.radians(
            self.properties.get("friction_angle", np.ones(self.n_cells) * 30.0)
        )

        # Calculate failure criterion
        f_mc = (
            s1
            - s3 * (1 + np.sin(phi)) / (1 - np.sin(phi))
            - 2 * c * np.cos(phi) / (1 - np.sin(phi))
        )

        # Update failure flag
        self.failure_flag = f_mc > 0

    def _check_drucker_prager_failure(self):
        """Check Drucker-Prager failure criterion."""
        # Extract principal stresses
        s1, s2, s3 = self._calculate_principal_stresses()

        # Calculate mean stress
        p = (s1 + s2 + s3) / 3.0

        # Calculate deviatoric stress
        J2 = ((s1 - s2) ** 2 + (s2 - s3) ** 2 + (s3 - s1) ** 2) / 6.0
        q = np.sqrt(3 * J2)

        # Get cohesion and friction angle
        c = self.properties.get("cohesion", np.ones(self.n_cells) * 1000.0)  # psi
        phi = np.radians(
            self.properties.get("friction_angle", np.ones(self.n_cells) * 30.0)
        )

        # Calculate Drucker-Prager parameters
        alpha = 2 * np.sin(phi) / (np.sqrt(3) * (3 - np.sin(phi)))
        k = 6 * c * np.cos(phi) / (np.sqrt(3) * (3 - np.sin(phi)))

        # Calculate failure criterion
        f_dp = q + 3 * alpha * p - k

        # Update failure flag
        self.failure_flag = f_dp > 0

    def _calculate_principal_stresses(self):
        """Calculate principal stresses from stress tensor."""
        # For each cell, calculate eigenvalues of stress tensor
        s1 = np.zeros(self.n_cells)
        s2 = np.zeros(self.n_cells)
        s3 = np.zeros(self.n_cells)

        for i in range(self.n_cells):
            # Create stress tensor
            stress_tensor = np.array(
                [
                    [self.stress["xx"][i], self.stress["xy"][i], self.stress["xz"][i]],
                    [self.stress["xy"][i], self.stress["yy"][i], self.stress["yz"][i]],
                    [self.stress["xz"][i], self.stress["yz"][i], self.stress["zz"][i]],
                ]
            )

            # Calculate eigenvalues (principal stresses)
            eigenvalues = np.linalg.eigvalsh(stress_tensor)

            # Sort in descending order (s1 >= s2 >= s3)
            eigenvalues = np.sort(eigenvalues)[::-1]

            s1[i] = eigenvalues[0]
            s2[i] = eigenvalues[1]
            s3[i] = eigenvalues[2]

        return s1, s2, s3

    def update_porosity_permeability(
        self, initial_porosity: np.ndarray, initial_permeability: np.ndarray
    ):
        """
        Update porosity and permeability based on geomechanical effects.

        Args:
            initial_porosity: Initial porosity field
            initial_permeability: Initial permeability field

        Returns:
            Tuple of (updated_porosity, updated_permeability)
        """
        # Calculate volumetric strain
        vol_strain = self.strain["xx"] + self.strain["yy"] + self.strain["zz"]

        # Update porosity using volumetric strain
        updated_porosity = initial_porosity * (1.0 + vol_strain)

        # Apply porosity limits
        min_porosity = self.properties.get("min_porosity", 0.01)
        max_porosity = self.properties.get("max_porosity", 0.5)
        updated_porosity = np.clip(updated_porosity, min_porosity, max_porosity)

        # Update permeability using Kozeny-Carman relation
        m = self.properties.get("permeability_exponent", 3.0)
        updated_permeability = initial_permeability * (
            (updated_porosity / initial_porosity) ** m
        )

        # Apply permeability limits
        min_permeability = self.properties.get("min_permeability", 0.01)
        max_permeability = self.properties.get("max_permeability", 10000.0)
        updated_permeability = np.clip(
            updated_permeability, min_permeability, max_permeability
        )

        return updated_porosity, updated_permeability


class FractureModel:
    """Model for natural and hydraulic fractures."""

    def __init__(self, grid_dims: Tuple[int, int, int]):
        """
        Initialize fracture model.

        Args:
            grid_dims: Grid dimensions (nx, ny, nz)
        """
        self.nx, self.ny, self.nz = grid_dims
        self.n_cells = self.nx * self.ny * self.nz

        # Fracture properties
        self.fracture_aperture = np.zeros(self.n_cells)  # mm
        self.fracture_permeability = np.zeros(self.n_cells)  # md
        self.fracture_porosity = np.zeros(self.n_cells)
        self.fracture_orientation = np.zeros((self.n_cells, 3))  # normal vector
        self.fracture_density = np.zeros(self.n_cells)  # fractures per meter

        # Hydraulic fracture properties
        self.hf_cells = []  # Cells containing hydraulic fractures
        self.hf_properties = {}  # Properties of hydraulic fractures

    def add_natural_fractures(
        self, cells: List[int], properties: Dict[str, np.ndarray]
    ):
        """
        Add natural fractures to specified cells.

        Args:
            cells: List of cell indices
            properties: Dictionary of fracture properties
        """
        for i, cell in enumerate(cells):
            self.fracture_aperture[cell] = properties.get(
                "aperture", np.zeros(len(cells))
            )[i]
            self.fracture_permeability[cell] = properties.get(
                "permeability", np.zeros(len(cells))
            )[i]
            self.fracture_porosity[cell] = properties.get(
                "porosity", np.zeros(len(cells))
            )[i]
            self.fracture_orientation[cell] = properties.get(
                "orientation", np.zeros((len(cells), 3))
            )[i]
            self.fracture_density[cell] = properties.get(
                "density", np.zeros(len(cells))
            )[i]

    def add_hydraulic_fracture(
        self,
        origin: Tuple[int, int, int],
        half_length: float,
        height: float,
        width: float,
        orientation: str,
        properties: Dict,
    ):
        """
        Add a hydraulic fracture.

        Args:
            origin: Origin cell (i, j, k)
            half_length: Fracture half-length (ft)
            height: Fracture height (ft)
            width: Fracture width (in)
            orientation: Fracture orientation ('x', 'y', 'z')
            properties: Dictionary of fracture properties
        """
        # Convert origin to cell index
        i, j, k = origin
        origin_idx = i + j * self.nx + k * self.nx * self.ny

        # Add to hydraulic fracture list
        hf_id = len(self.hf_cells)
        self.hf_cells.append(origin_idx)

        # Store properties
        self.hf_properties[hf_id] = {
            "origin": origin,
            "half_length": half_length,
            "height": height,
            "width": width,
            "orientation": orientation,
            "permeability": properties.get("permeability", 1e5),  # md
            "porosity": properties.get("porosity", 0.5),
            "conductivity": properties.get(
                "conductivity", width * properties.get("permeability", 1e5)
            ),  # md-ft
        }

        # Mark cells intersected by the fracture
        self._mark_fracture_cells(hf_id)

    def _mark_fracture_cells(self, hf_id: int):
        """Mark cells intersected by a hydraulic fracture."""
        # This is a placeholder for the full implementation
        # In a real simulator, this would identify all cells intersected by the fracture
        # and update their properties accordingly
        pass

    def calculate_effective_permeability(self, matrix_permeability: np.ndarray):
        """
        Calculate effective permeability considering fractures.

        Args:
            matrix_permeability: Matrix permeability field

        Returns:
            Effective permeability field
        """
        # Simple model: effective perm = matrix perm + fracture contribution
        effective_permeability = matrix_permeability.copy()

        # Add contribution from natural fractures
        # Using cubic law: k_f = aperture^2 / 12
        fracture_contrib = (
            (self.fracture_aperture * 1e-3) ** 2 / 12 * 1e15 * self.fracture_density
        )
        effective_permeability += fracture_contrib

        # Add contribution from hydraulic fractures
        # This is a simplified approach - in reality, this would be more complex
        for hf_id, cells in enumerate(self.hf_cells):
            hf_props = self.hf_properties[hf_id]
            effective_permeability[cells] += hf_props["permeability"]

        return effective_permeability
