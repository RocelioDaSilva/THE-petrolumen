# A-main review notes

## `advanced_simulation.py`

Compared: A-main `thepetrolumen/thepetrolumen_new/backend/gaia_genesis/advanced_simulation.py` and canonical `backend/app/engines/reservoir/simulation/advanced_simulation.py`.

**No actionable differences found.** A-main and canonical expose the same `AdvancedSimulation` methods and engineering behavior. The only executable difference is naming the matrix-fracture transfer result `calculated_transfer` instead of `transfer`; the returned phase transfer values use the same shape-factor relation in both versions.

## `compositional_modeling.py`

Compared: A-main `thepetrolumen/thepetrolumen_new/backend/gaia_genesis/compositional_modeling.py` and canonical `backend/app/engines/reservoir/simulation/compositional_modeling.py`.

There are no A-main-only classes, functions, or additional phase-equilibrium formulas. Both versions contain the same Peng–Robinson EOS, cubic compressibility-factor calculation, Wilson K-value fallback, Rachford–Rice flash, phase-density calculation, and simplified viscosity estimates.

**Actionable implementation difference:** A-main's `PengRobinsonEOS.calculate_fugacity_coefficients` computes local gas constant and dimensionless EOS parameters before evaluating the standard Peng–Robinson component fugacity-coefficient expression:

\[
\ln \phi_i =
\frac{b_i}{b_m}(Z-1)-\ln(Z-B)
+ \frac{A}{2\sqrt{2}B}
\left(\frac{b_i}{b_m}-\frac{2\sum_j x_j a_{ij}}{a_m}\right)
\ln\left(\frac{Z+(1+\sqrt{2})B}{Z+(1-\sqrt{2})B}\right)
\]

It also skips the final logarithmic contribution when `B_param` is near zero. In canonical, the corresponding method refers to `R`, `A`, and `B` without defining them locally or at module scope, so a call reaches unresolved names rather than evaluating the fugacity coefficients. The A-main version's local `R_const`, `A_param`, and `B_param` calculations and small-`B_param` guard are the substantive items to review.

The other observed differences in this file are naming/formatting changes, not additional engineering functionality.
