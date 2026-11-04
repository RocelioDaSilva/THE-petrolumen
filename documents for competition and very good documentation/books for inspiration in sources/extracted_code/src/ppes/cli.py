"""CLI entry point."""
import typer
from . import ch02_pvt as pvt, ch03_ipr as ipr, ch08_decline as dec

app = typer.Typer(help="PPES -- Petroleum Production Engineering")

@app.command()
def pvt_oil(p: float, t: float, api: float, rs: float,
            gamma_g: float):
    typer.echo(f"gamma_o = {141.5/(api+131.5):.4f}")
    typer.echo(f"rho_o   = {pvt.rho_o(p, t, api, rs, gamma_g):.3f}")
    typer.echo(f"B_o     = {pvt.bo_standing(t, api, rs, gamma_g):.4f}")

@app.command()
def vogel(qmax: float, pbar: float, pwf: float):
    typer.echo(f"q = {ipr.vogel_rate(qmax, pwf, pbar):.3f} stb/day")

@app.command()
def exp_decline(qi: float, q1: float, q2: float, t1: float,
                t2: float, t: float):
    b = dec.exponential_b_from_ln(q1, q2, t1, t2)
    typer.echo(f"b = {b:.6f}")
    typer.echo(f"q(t) = {dec.exponential_rate(qi, b, t):.3f}")
