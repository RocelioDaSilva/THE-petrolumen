"""Reproduce book Example 3.1 -- three-flow-regime IPR."""
import math
from ppes.report import Report
from ppes import ch03_ipr as ipr

k, h, bo, mu = 8.2, 53, 1.1, 1.7
re, rw, s, pbar = 2980, 0.328, 0, 5651

j_ss = k*h/(141.2*bo*mu*math.log(re/rw))
j_pss = k*h/(141.2*bo*mu*(math.log(re/rw) - 0.75))

rpt = Report("Example 3.1 -- Vertical Well IPR", "PPES")
rpt.add("Input data",
        data={"k [md]": k, "h [ft]": h, "B_o [rb/stb]": bo,
              "mu_o [cp]": mu, "r_e [ft]": re, "r_w [ft]": rw,
              "S": s, "p_bar [psia]": pbar})
rpt.add("Steady-state J*",
        body="Eq. 3.16, p. 3/33",
        data={"J*_ss [stb/d/psi]": j_ss},
        notes=["Book value 0.1806"])
rpt.add("Pseudo-steady J*",
        body="Eq. 3.17, p. 3/33",
        data={"J*_pss [stb/d/psi]": j_pss},
        notes=["Book value 0.1968"])

print(rpt.to_text())
rpt.to_pdf("example_3_1.pdf")
rpt.to_docx("example_3_1.docx")
