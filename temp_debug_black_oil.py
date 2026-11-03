import numpy as np
from backend.app.engines.reservoir.simulation.black_oil_simulator import BlackOilSimulator

sim = BlackOilSimulator()
sim.setup_grid(2,2,1,50,50,10)
sim.set_rock_properties(np.array([0.2,0.2,0.2,0.2]), np.array([100,100,100,100]), 0)
sim.set_fluid_properties({"water_viscosity":1,"oil_viscosity":2,"gas_viscosity":0.02})
sim.initialize(3000,{"water":np.array([0.2,0.2,0.2,0.2]),"gas":np.array([0,0,0,0])})
print('before', sim.pressure, sim.saturations)
try:
    sim.run_timestep(1)
    print('after pressure', sim.pressure)
    print('after water', sim.saturations['water'])
    print('after gas', sim.saturations['gas'])
    print('check finite', np.all(np.isfinite(sim.pressure)), np.any(sim.pressure <= 0), np.all(np.isfinite(sim.saturations['water'])), np.any(sim.saturations['water'] < 0), np.any(sim.saturations['gas'] < 0), np.any(sim.saturations['water'] + sim.saturations['gas'] > 1))
except Exception as e:
    import traceback; traceback.print_exc()
