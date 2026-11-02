import numpy as np
from typing import Dict, List, Optional
import multiprocessing as mp
from scipy.sparse.linalg import spsolve
from scipy.sparse import csr_matrix
try:
    import cupy as cp
    from cupyx.scipy.sparse import csr_matrix as cp_csr_matrix
    from cupyx.scipy.sparse.linalg import cg as cp_cg
except ImportError:
    cp = None

class ParallelEngine:
    """Parallel computation engine supporting both CPU and GPU"""
    
    def __init__(self, use_gpu: bool = False):
        self.use_gpu = use_gpu and cp is not None
        self.n_cores = mp.cpu_count()
        self.pool = mp.Pool(self.n_cores) if not use_gpu else None
        
    def decompose_domain(self, grid_shape: tuple, n_blocks: int):
        """Decompose simulation domain for parallel execution"""
        nx, ny, nz = grid_shape
        
        # Simple domain decomposition along longest axis
        if nx >= ny and nx >= nz:
            block_size = nx // n_blocks
            return [(i*block_size, min((i+1)*block_size, nx), 0, ny, 0, nz)
                    for i in range(n_blocks)]
        elif ny >= nx and ny >= nz:
            block_size = ny // n_blocks
            return [(0, nx, i*block_size, min((i+1)*block_size, ny), 0, nz)
                    for i in range(n_blocks)]
        else:
            block_size = nz // n_blocks
            return [(0, nx, 0, ny, i*block_size, min((i+1)*block_size, nz))
                    for i in range(n_blocks)]
            
    def solve_linear_system(self, matrix: np.ndarray, rhs: np.ndarray,
                          solver: str = "direct", tol: float = 1e-10,
                          max_iter: int = 1000):
        """Solve linear system in parallel"""
        if self.use_gpu:
            return self._solve_gpu(matrix, rhs, solver, tol, max_iter)
        else:
            return self._solve_cpu(matrix, rhs, solver, tol, max_iter)
            
    def _solve_gpu(self, matrix: np.ndarray, rhs: np.ndarray,
                  solver: str, tol: float, max_iter: int):
        """GPU-accelerated linear solver"""
        if cp is None:
            raise RuntimeError("CUDA not available")
            
        # Transfer to GPU
        matrix_gpu = cp_csr_matrix(matrix)
        rhs_gpu = cp.array(rhs)
        
        if solver == "direct":
            # Use cuSPARSE direct solver
            solution_gpu = cp.linalg.solve(matrix_gpu.tocsc(), rhs_gpu)
        else:
            # Use iterative solver
            solution_gpu, info = cp_cg(matrix_gpu, rhs_gpu, 
                                     tol=tol, maxiter=max_iter)
            
        # Transfer back to CPU
        return cp.asnumpy(solution_gpu)
        
    def _solve_cpu(self, matrix: np.ndarray, rhs: np.ndarray,
                  solver: str, tol: float, max_iter: int):
        """Multi-threaded CPU solver"""
        # Convert to sparse format
        matrix_sparse = csr_matrix(matrix)
        
        if solver == "direct":
            # Parallel direct solver (if available)
            return spsolve(matrix_sparse, rhs)
        else:
            # Split system into blocks
            n = len(rhs)
            block_size = n // self.n_cores
            blocks = [(i*block_size, min((i+1)*block_size, n))
                     for i in range(self.n_cores)]
            
            # Solve blocks in parallel
            def solve_block(block):
                start, end = block
                local_matrix = matrix_sparse[start:end, :]
                local_rhs = rhs[start:end]
                return spsolve(local_matrix, local_rhs)
                
            solutions = self.pool.map(solve_block, blocks)
            
            # Combine solutions
            return np.concatenate(solutions)
            
    def matrix_vector_product(self, matrix: np.ndarray, 
                            vector: np.ndarray) -> np.ndarray:
        """Parallel matrix-vector multiplication"""
        if self.use_gpu:
            matrix_gpu = cp.array(matrix)
            vector_gpu = cp.array(vector)
            result_gpu = cp.dot(matrix_gpu, vector_gpu)
            return cp.asnumpy(result_gpu)
        else:
            # Split computation across cores
            n = len(vector)
            block_size = n // self.n_cores
            blocks = [(i*block_size, min((i+1)*block_size, n))
                     for i in range(self.n_cores)]
            
            def multiply_block(block):
                start, end = block
                return np.dot(matrix[start:end, :], vector)
                
            results = self.pool.map(multiply_block, blocks)
            return np.concatenate(results)
            
    def synchronize(self):
        """Synchronize parallel processes"""
        if self.use_gpu:
            cp.cuda.Stream.null.synchronize()
            
    def __del__(self):
        """Cleanup"""
        if self.pool is not None:
            self.pool.close()
            self.pool.join()
