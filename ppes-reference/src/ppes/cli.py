"""Typer CLI."""
from __future__ import annotations
import typer
from . import ch02_pvt as pvt, ch03_ipr as ipr, ch08_decline as dec

app = typer.Typer(help="PPES â€” Petroleum Production Engineering Software")


@app.command()
def pvt_oil(p: float, t: float, api: float, rs: float, gamma_g: float):
    """Quick oil PVT (Ch. 2)."""
    gamma_o = 141.5 / (api + 131.5)
    typer.echo(f"gamma_o = {gamma_o:.4f}")
    typer.echo(f"rho_o   = {pvt.rho_o(p, t, api, rs, gamma_g):.3f} lbm/ft3")
    typer.echo(f"B_o     = {pvt.bo_standing(t, api, rs, gamma_g):.4f} rb/stb")
    typer.echo(f"mu_od   = {pvt.mu_dead_oil(api, t):.3f} cp")


@app.command()
def vogel(qmax: float, pbar: float, pwf: float):
    """Vogel IPR (Ch. 3)."""
    typer.echo(f"q = {ipr.vogel_rate(qmax, pwf, pbar):.3f} stb/day")


@app.command()
def exp_decline(qi: float, q1: float, q2: float,
                t1: float, t2: float, t: float):
    """Exponential decline (Ch. 8)."""
    b = dec.exponential_b_from_ln(q1, q2, t1, t2)
    typer.echo(f"b = {b:.6f}")
    typer.echo(f"q(t={t}) = {dec.exponential_rate(qi, b, t):.3f}")