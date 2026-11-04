"""FastAPI REST layer."""
from __future__ import annotations
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from . import ch02_pvt as pvt, ch03_ipr as ipr, ch08_decline as dec

app = FastAPI(title="PPES", version="0.1.0",
              description="Petroleum Production Engineering Software")


class OilPVTIn(BaseModel):
    p: float = Field(..., gt=0)
    t_F: float
    api: float = Field(..., gt=0, lt=100)
    rs: float = Field(..., ge=0)
    gamma_g: float = Field(..., gt=0, lt=2)


class VogelIn(BaseModel):
    qmax: float
    pwf: float
    pbar: float


@app.get("/health")
def health():
    return {"status": "ok", "version": "0.1.0"}


@app.post("/pvt/oil")
def api_pvt_oil(req: OilPVTIn):
    try:
        return {
            "gamma_o": 141.5 / (req.api + 131.5),
            "rho_o": pvt.rho_o(req.p, req.t_F, req.api, req.rs, req.gamma_g),
            "Bo": pvt.bo_standing(req.t_F, req.api, req.rs, req.gamma_g),
            "mu_od": pvt.mu_dead_oil(req.api, req.t_F),
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/ipr/vogel")
def api_vogel(req: VogelIn):
    return {"q": ipr.vogel_rate(req.qmax, req.pwf, req.pbar)}


@app.post("/decline/exponential")
def api_decline(qi: float, q1: float, q2: float,
                t1: float, t2: float, t: float):
    b = dec.exponential_b_from_ln(q1, q2, t1, t2)
    return {"b": b,
            "q_t": dec.exponential_rate(qi, b, t),
            "cum": dec.exponential_cum(qi, b, t)}