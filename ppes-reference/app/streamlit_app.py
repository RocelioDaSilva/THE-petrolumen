"""PPES MVP â€” five highest-value flows from the book."""
import streamlit as st
import matplotlib.pyplot as plt
import numpy as np
from ppes import (ch02_pvt as pvt, ch03_ipr as ipr,
                  ch04_tpr as tpr, ch05_choke as chk,
                  ch06_nodal as nod, ch08_decline as dec)

st.set_page_config(page_title="PPES", layout="wide")
st.title("Petroleum Production Engineering Software")
st.caption("Based on Guo, Lyons & Ghalambor (2007)")

tabs = st.tabs(["PVT", "IPR", "TPR", "Choke", "Nodal", "Decline"])

with tabs[0]:
    st.header("Fluid PVT (Ch. 2)")
    c1, c2 = st.columns(2)
    with c1:
        p = st.number_input("p [psia]", value=4475.0)
        t = st.number_input("T [F]", value=140.0)
        api = st.number_input("API", value=35.0)
        rs = st.number_input("R_s [scf/stb]", value=600.0)
        gg = st.number_input("gamma_g", value=0.77)
    with c2:
        st.metric("gamma_o", f"{141.5/(api+131.5):.4f}")
        st.metric("rho_o [lbm/ft3]", f"{pvt.rho_o(p, t, api, rs, gg):.2f}")
        st.metric("B_o [rb/stb]", f"{pvt.bo_standing(t, api, rs, gg):.4f}")
        st.metric("mu_od [cp]", f"{pvt.mu_dead_oil(api, t):.3f}")

with tabs[1]:
    st.header("Reservoir Deliverability (Ch. 3)")
    qmax = st.number_input("q_max [stb/d]", value=618.0)
    pbar = st.number_input("p_bar [psia]", value=5651.0)
    pwf = np.linspace(0, pbar, 50)
    q = [ipr.vogel_rate(qmax, x, pbar) for x in pwf]
    fig, ax = plt.subplots()
    ax.plot(q, pwf)
    ax.set_xlabel("q [stb/d]")
    ax.set_ylabel("p_wf [psia]")
    ax.set_title("Vogel IPR")
    st.pyplot(fig)

with tabs[2]:
    st.header("Wellbore Performance (Ch. 4)")
    if st.button("Run Average T/z"):
        pbh = tpr.bhp_average_tz(800, 2000, 0.71, 2.259, 10000,
                                  0, 635, 0.9028, 0.017397)
        st.metric("p_wf [psia]", f"{pbh:.0f}",
                   help="Book Example 4.5 = 1,082 psia")

with tabs[3]:
    st.header("Choke Performance (Ch. 5)")
    gg_c = st.number_input("gamma_g", value=0.6, key="chk_gg")
    pu = st.number_input("p_up [psia]", value=800.0, key="chk_pu")
    pd = st.number_input("p_dn [psia]", value=200.0, key="chk_pd")
    tu = st.number_input("T_up [F]", value=75.0, key="chk_tu")
    d2 = st.number_input("d_choke [in]", value=1.0, key="chk_d2")
    k = st.number_input("k", value=1.3, key="chk_k")
    rc = chk.critical_ratio(k)
    regime = "sonic" if pd/pu < rc else "subsonic"
    st.write(f"Critical ratio = {rc:.3f}; regime = **{regime}**")
    A2 = np.pi*(d2/2)**2
    if regime == "sonic":
        q = chk.q_sonic_gas(0.62, A2, pu, tu+460, gg_c, k)
    else:
        q = chk.q_subsonic_gas(0.62, A2, pu, pd, tu+460, gg_c, k)
    st.metric("q [Mscf/day]", f"{q:.0f}")

with tabs[4]:
    st.header("Nodal Analysis (Ch. 6)")
    qmax_n = st.number_input("q_max", value=978.0, key="n_qmax")
    pbar_n = st.number_input("p_bar", value=3000.0, key="n_pbar")
    def tpr_func(q):
        return 500 + 0.0005*q
    try:
        q_op, p_op = nod.operating_point_oil_vogel(
            qmax_n, pbar_n, tpr_func)
        st.metric("Operating q", f"{q_op:.1f}")
        st.metric("Operating p_wf", f"{p_op:.1f}")
    except ValueError:
        st.error("No intersection found.")

with tabs[5]:
    st.header("Decline Analysis (Ch. 8)")
    model = st.radio("Model", ["Exponential", "Harmonic", "Hyperbolic"])
    qi = st.number_input("q_i", value=100.0)
    b = st.number_input("b", value=0.05)
    t_arr = np.linspace(0, 120, 200)
    if model == "Exponential":
        q_arr = [dec.exponential_rate(qi, b, x) for x in t_arr]
    elif model == "Harmonic":
        q_arr = [dec.harmonic_rate(qi, b, x) for x in t_arr]
    else:
        a = st.number_input("a", value=1.5)
        q_arr = [dec.hyperbolic_rate(qi, a, b, x) for x in t_arr]
    fig, ax = plt.subplots()
    ax.plot(t_arr, q_arr)
    ax.set_xlabel("time")
    ax.set_ylabel("q")
    st.pyplot(fig)