"""Streamlit UI -- 11 functional tabs."""
import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

from ppes import (ch02_pvt as pvt, ch03_ipr as ipr,
                   ch04_tpr as tpr, ch05_choke as chk,
                   ch06_nodal as nod, ch08_decline as dec,
                   ch09_tubing as tub, ch10_separation as sep,
                   ch11_transport as tr, ch13_gas_lift as gl,
                   ch17_fracturing as fx)

st.set_page_config(page_title="PPES", layout="wide")
st.title("Petroleum Production Engineering Software")
st.caption("Derived from Guo, Lyons & Ghalambor (2007)")

tabs = st.tabs([
    "PVT", "IPR", "TPR", "Choke", "Nodal", "Decline",
    "Tubing", "Separator", "Pipeline", "Gas Lift", "Fracturing",
])

# Tab 0: PVT
with tabs[0]:
    st.header("Fluid PVT (Ch. 2)")
    c1, c2 = st.columns(2)
    with c1:
        p = st.number_input("p [psia]", value=4475.0, key="p_p")
        t = st.number_input("T [F]", value=140.0, key="p_t")
        api = st.number_input("API", value=35.0, key="p_api")
        rs = st.number_input("R_s [scf/stb]", value=600.0, key="p_rs")
        gg = st.number_input("gamma_g", value=0.77, key="p_gg")
    with c2:
        st.metric("gamma_o", f"{141.5/(api+131.5):.4f}")
        st.metric("rho_o [lbm/ft3]",
                   f"{pvt.rho_o(p, t, api, rs, gg):.2f}")
        st.metric("B_o [rb/stb]",
                   f"{pvt.bo_standing(t, api, rs, gg):.4f}")
        st.metric("mu_od [cp]", f"{pvt.mu_dead_oil(api, t):.3f}")

# Tab 1: IPR
with tabs[1]:
    st.header("Reservoir Deliverability (Ch. 3)")
    qmax = st.number_input("q_max [stb/d]", value=618.0, key="ipr_q")
    pbar = st.number_input("p_bar [psia]", value=5651.0, key="ipr_p")
    pwf = np.linspace(0, pbar, 50)
    q = [ipr.vogel_rate(qmax, x, pbar) for x in pwf]
    fig, ax = plt.subplots()
    ax.plot(q, pwf); ax.set_xlabel("q"); ax.set_ylabel("p_wf")
    ax.set_title("Vogel IPR")
    st.pyplot(fig)

# Tab 2: TPR
with tabs[2]:
    st.header("Wellbore Performance (Ch. 4)")
    if st.button("Run Poettmann-Carpenter"):
        pbh = tpr.poettmann_carpenter_bhp(
            phf=500, t_head_F=100, t_bh_F=150, d_in=1.66,
            depth_ft=5000, q_liq=2000, wc=0.25, glr=1000,
            api=30, gamma_w=1.05, gamma_g=0.65)
        st.metric("p_wf [psia]", f"{pbh:.0f}",
                   help="Book Example 4.2 = 1,699 psia")

# Tab 3: Choke
with tabs[3]:
    st.header("Choke Performance (Ch. 5)")
    gg_c = st.number_input("gamma_g", value=0.6, key="c_gg")
    pu = st.number_input("p_up [psia]", value=800.0, key="c_pu")
    pd = st.number_input("p_dn [psia]", value=200.0, key="c_pd")
    tu = st.number_input("T_up [F]", value=75.0, key="c_tu")
    d2 = st.number_input("d_choke [in]", value=1.0, key="c_d2")
    k = st.number_input("k", value=1.3, key="c_k")
    rc = chk.critical_ratio(k)
    regime = "sonic" if pd/pu < rc else "subsonic"
    st.write(f"Critical ratio = {rc:.3f}; regime = **{regime}**")
    A2 = np.pi*(d2/2)**2
    if regime == "sonic":
        q = chk.q_sonic_gas(0.62, A2, pu, tu+460, gg_c, k)
    else:
        q = chk.q_subsonic_gas(0.62, A2, pu, pd, tu+460, gg_c, k)
    st.metric("q [Mscf/day]", f"{q:.0f}")

# Tab 4: Nodal
with tabs[4]:
    st.header("Nodal Analysis (Ch. 6)")
    qmax_n = st.number_input("q_max", value=978.0, key="n_q")
    pbar_n = st.number_input("p_bar", value=3000.0, key="n_p")
    def tpr_fn(q):
        return 500 + 0.0005*q
    try:
        q_op, p_op = nod.operating_point_oil_vogel(
            qmax_n, pbar_n, tpr_fn)
        st.metric("Operating q", f"{q_op:.1f}")
        st.metric("Operating p_wf", f"{p_op:.1f}")
    except ValueError:
        st.error("No intersection")

# Tab 5: Decline
with tabs[5]:
    st.header("Decline Analysis (Ch. 8)")
    model = st.radio("Model", ["Exponential", "Harmonic",
                                 "Hyperbolic"])
    qi = st.number_input("q_i", value=100.0, key="d_q")
    b = st.number_input("b", value=0.05, key="d_b")
    t_arr = np.linspace(0, 120, 200)
    if model == "Exponential":
        q_arr = [dec.exponential_rate(qi, b, x) for x in t_arr]
    elif model == "Harmonic":
        q_arr = [dec.harmonic_rate(qi, b, x) for x in t_arr]
    else:
        a = st.number_input("a", value=1.5, key="d_a")
        q_arr = [dec.hyperbolic_rate(qi, a, b, x) for x in t_arr]
    fig, ax = plt.subplots()
    ax.plot(t_arr, q_arr)
    ax.set_xlabel("time"); ax.set_ylabel("q")
    st.pyplot(fig)

# Tab 6: Tubing
with tabs[6]:
    st.header("Tubing Design (Ch. 9)")
    pc = st.number_input("p_c [psi]", value=7675.3, key="tb_pc")
    sa = st.number_input("S_A [psi]", value=35320.0, key="tb_sa")
    ym = st.number_input("Y_m [psi]", value=55000.0, key="tb_ym")
    try:
        pcc = tub.collapse_biaxial(pc, sa, ym)
        st.metric("p_cc [psi]", f"{pcc:.0f}")
    except Exception as e:
        st.error(str(e))

# Tab 7: Separator
with tabs[7]:
    st.header("Separator Sizing (Ch. 10)")
    D = st.number_input("D [ft]", value=20/12, key="sep_D")
    K = st.number_input("K", value=0.205, key="sep_K")
    p_s = st.number_input("p [psia]", value=800.0, key="sep_p")
    T_s = st.number_input("T [F]", value=80.0, key="sep_T")
    z_s = st.number_input("z", value=0.8427, key="sep_z")
    ggs = st.number_input("gamma_g", value=0.7, key="sep_gg")
    rl = st.number_input("rho_l [lbm/ft3]", value=46.11, key="sep_rl")
    try:
        qg = sep.gas_capacity(D, K, p_s, T_s, z_s, ggs, rl)
        st.metric("Gas capacity [MMscfd]", f"{qg:.2f}")
    except Exception as e:
        st.error(str(e))

# Tab 8: Pipeline
with tabs[8]:
    st.header("Pipeline (Ch. 11 / 18)")
    p1 = st.number_input("p1 [psia]", value=1000.0, key="pl_p1")
    p2 = st.number_input("p2 [psia]", value=800.0, key="pl_p2")
    d = st.number_input("d [in]", value=6.0, key="pl_d")
    L = st.number_input("L [ft]", value=52800.0, key="pl_L")
    ggp = st.number_input("gamma_g", value=0.7, key="pl_gg")
    TR = st.number_input("T [R]", value=520.0, key="pl_T")
    try:
        q_w = tr.weymouth_horizontal(None, p1, p2, d, L, ggp, TR)
        st.metric("Weymouth q [scfd]", f"{q_w:.0f}")
    except Exception as e:
        st.error(str(e))

# Tab 9: Gas Lift
with tabs[9]:
    st.header("Gas Lift (Ch. 13)")
    pd_g = st.number_input("Dome [psi]", value=817.0, key="gl_pd")
    St = st.number_input("Spring [psi]", value=0.0, key="gl_St")
    R = st.number_input("R", value=0.2562, key="gl_R")
    pt = st.number_input("Tubing [psi]", value=424.0, key="gl_pt")
    try:
        po = gl.valve_opening_pressure(pd_g, St, R, pt)
        pc2 = gl.valve_closing_pressure(pd_g, St, R)
        st.metric("Opening [psig]", f"{po:.0f}")
        st.metric("Closing [psig]", f"{pc2:.0f}")
        st.metric("Spread [psi]", f"{po-pc2:.0f}")
    except Exception as e:
        st.error(str(e))

# Tab 10: Fracturing
with tabs[10]:
    st.header("Hydraulic Fracturing (Ch. 17)")
    rho_f = st.number_input("Overburden [lbm/ft3]", value=165.0,
                              key="f_rho")
    H = st.number_input("Depth [ft]", value=10000.0, key="f_H")
    alpha = st.number_input("Biot", value=0.72, key="f_al")
    pp = st.number_input("Pore [psi]", value=3800.0, key="f_pp")
    nu = st.number_input("Poisson", value=0.25, key="f_nu")
    stect = st.number_input("Tectonic [psi]", value=2000.0, key="f_st")
    T0 = st.number_input("Tensile [psi]", value=1000.0, key="f_T0")
    sv = fx.overburden(rho_f, H)
    pbd = fx.breakdown_pressure(sv, alpha, pp, nu, stect, T0)
    st.metric("Breakdown [psi]", f"{pbd:.0f}")
    Sf = st.number_input("S_f", value=-6.82, key="f_Sf")
    re = st.number_input("r_e [ft]", value=1490.0, key="f_re")
    rw = st.number_input("r_w [ft]", value=0.328, key="f_rw")
    fold = fx.fold_of_increase(re, rw, Sf)
    st.metric("J/J_o", f"{fold:.2f}")
