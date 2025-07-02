# This file makes 'reservoir_engineering' a Python sub-package of 'gaia_genesis'.

# You can make specific classes or functions available when this sub-package is imported.
# This allows for easier access, e.g.,
# from gaia_genesis.reservoir_engineering import DataUploader

# Example of exposing key classes from the modules in this package:
from .data_management import DataUploader
from .decline_analysis import AdvancedDeclineAnalysis
from .prediction import AIPrediction
from .database import DatabaseManager
from .flow_simulation import ReservoirSimulator
from .api import AuthManager # Though 'api' might sometimes be structured separately

__all__ = [
    "DataUploader",
    "AdvancedDeclineAnalysis",
    "AIPrediction",
    "DatabaseManager",
    "ReservoirSimulator",
    "AuthManager"
]

# This allows a user to type:
# from gaia_genesis.reservoir_engineering import *
# (though explicit imports are generally preferred over *)
# and get all the names listed in __all__.
#
# Or more commonly:
# from gaia_genesis.reservoir_engineering import DataUploader
# client = DataUploader()
```
