"""
ECD calculator skeleton
Usage: python ecd_calc.py
"""
import math

G = 9.80665

def pressure_from_density(rho, depth):
    # Pa
    return rho * G * depth

if __name__ == '__main__':
    rho = 1200  # kg/m3
    depth = 3000  # m
    p = pressure_from_density(rho, depth)
    print(f'Pressure (Pa): {p:.2e}, Pressure (bar): {p/1e5:.2f}')
