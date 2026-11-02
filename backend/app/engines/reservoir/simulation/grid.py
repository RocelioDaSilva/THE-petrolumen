from __future__ import annotations

import numpy as np


class Grid3D:
    def __init__(
        self, nx: int, ny: int, nz: int, dx: float, dy: float, dz: float
    ) -> None:
        dimensions = (nx, ny, nz)
        cell_sizes = (dx, dy, dz)
        if any(value <= 0 for value in dimensions):
            raise ValueError("Grid dimensions must be positive.")
        if any(value <= 0 for value in cell_sizes):
            raise ValueError("Cell dimensions must be positive.")

        self.nx = nx
        self.ny = ny
        self.nz = nz
        self.dx = dx
        self.dy = dy
        self.dz = dz
        self.shape = (nx * ny * nz,)

    def add_lgr(self, **region: object) -> None:
        raise NotImplementedError("Local grid refinement is not implemented.")

    def get_total_cells(self) -> int:
        return self.nx * self.ny * self.nz

    def get_cell_neighbors(self, cell: int) -> list[int]:
        if cell < 0 or cell >= self.get_total_cells():
            raise IndexError("Cell index is outside the grid.")

        i, j, k = np.unravel_index(cell, (self.nx, self.ny, self.nz))
        neighbors = []
        for di, dj, dk in (
            (-1, 0, 0),
            (1, 0, 0),
            (0, -1, 0),
            (0, 1, 0),
            (0, 0, -1),
            (0, 0, 1),
        ):
            neighbor = (i + di, j + dj, k + dk)
            if (
                0 <= neighbor[0] < self.nx
                and 0 <= neighbor[1] < self.ny
                and 0 <= neighbor[2] < self.nz
            ):
                neighbors.append(
                    int(np.ravel_multi_index(neighbor, (self.nx, self.ny, self.nz)))
                )
        return neighbors

    def calculate_transmissibilities(self, permeability: np.ndarray) -> np.ndarray:
        values = np.asarray(permeability, dtype=float).reshape(-1)
        if values.size != self.get_total_cells():
            raise ValueError("Permeability must contain one value per grid cell.")
        if not np.all(np.isfinite(values)) or np.any(values <= 0):
            raise ValueError("Permeability values must be finite and positive.")

        transmissibilities = np.zeros((values.size, values.size), dtype=float)
        areas = (self.dy * self.dz, self.dx * self.dz, self.dx * self.dy)
        distances = (self.dx, self.dy, self.dz)

        for cell in range(values.size):
            i, j, k = np.unravel_index(cell, (self.nx, self.ny, self.nz))
            for axis, offset in enumerate(
                ((-1, 0, 0), (1, 0, 0), (0, -1, 0), (0, 1, 0), (0, 0, -1), (0, 0, 1))
            ):
                neighbor_index = (i + offset[0], j + offset[1], k + offset[2])
                if not (
                    0 <= neighbor_index[0] < self.nx
                    and 0 <= neighbor_index[1] < self.ny
                    and 0 <= neighbor_index[2] < self.nz
                ):
                    continue
                neighbor = int(
                    np.ravel_multi_index(neighbor_index, (self.nx, self.ny, self.nz))
                )
                direction = axis // 2
                harmonic_permeability = (
                    2 * values[cell] * values[neighbor]
                    / (values[cell] + values[neighbor])
                )
                value = (
                    harmonic_permeability
                    * areas[direction]
                    / distances[direction]
                )
                transmissibilities[cell, neighbor] = value
                transmissibilities[neighbor, cell] = value

        return transmissibilities
