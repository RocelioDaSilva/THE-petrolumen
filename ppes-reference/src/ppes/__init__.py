"""PPES â€” Petroleum Production Engineering Software.

Source book: Guo, Lyons & Ghalambor (2007).

Each module ``chNN_xxx`` corresponds to chapter NN of the book.
Each public function's docstring cites the book equation and page.
"""
__version__ = "0.1.0"

from . import (
    units, solvers,
    ch02_pvt, ch03_ipr, ch04_tpr, ch05_choke, ch06_nodal,
    ch07_forecast, ch08_decline, ch09_tubing, ch10_separation,
    ch11_transport, ch12_rod_pump, ch13_gas_lift, ch14_other_lift,
    ch15_diagnostics, ch16_acidizing, ch17_fracturing, ch18_optimization,
)

__all__ = [
    "units", "solvers",
    "ch02_pvt", "ch03_ipr", "ch04_tpr", "ch05_choke", "ch06_nodal",
    "ch07_forecast", "ch08_decline", "ch09_tubing", "ch10_separation",
    "ch11_transport", "ch12_rod_pump", "ch13_gas_lift", "ch14_other_lift",
    "ch15_diagnostics", "ch16_acidizing", "ch17_fracturing", "ch18_optimization",
]