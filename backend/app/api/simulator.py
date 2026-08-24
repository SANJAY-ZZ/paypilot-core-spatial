from fastapi import APIRouter, status
from backend.app.schemas.simulation import SimulationRequest, SimulationResponse
from backend.app.services.simulation_engine import simulation_engine

router = APIRouter(prefix="/simulate", tags=["Simulator"])


@router.post("", response_model=SimulationResponse, status_code=status.HTTP_200_OK)
def run_simulation(request: SimulationRequest):
    """
    Simulate financial outcomes, expected conversions, campaign costs, net gains,
    and Guardian compliance before deploying a merchant campaign.
    """
    return simulation_engine.simulate(request)
