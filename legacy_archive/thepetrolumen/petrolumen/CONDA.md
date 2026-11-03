# Conda guidance (Windows / heavy packages)

For Windows or when installing heavy compiled packages (e.g. `petsc4py`, `pyvista`, `segyio`) we recommend using Conda (Miniconda/Anaconda).

Example steps:

```powershell
conda create -n petrolumen python=3.10 -y
conda activate petrolumen
# Install core packages from conda-forge
conda install -c conda-forge numpy pandas scipy scikit-learn xgboost plotly matplotlib seaborn python-dotenv uvicorn fastapi -y

# Install optional/compiled packages
conda install -c conda-forge pyvista segyio petsc4py gstools -y

# Finally install any remaining Python-only deps via pip
pip install -r requirements-dev.txt
```

If you prefer `pip` on Windows, consider using WSL or a Docker container to avoid native build issues.
