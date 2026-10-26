import pandas as pd
import numpy as np
from gaia_genesis.prediction.time_series_forecasting import TimeSeriesForecaster


def test_prophet_forecasting_basic():
    """
    Test Meta Prophet forecasting on a simple trended dataset.
    """
    forecaster = TimeSeriesForecaster()

    # Create 2 years of monthly data
    dates = pd.date_range(start="2020-01-01", periods=24, freq="ME")
    # Linear trend + slight noise
    values = np.linspace(1000, 500, 24) + np.random.normal(0, 10, 24)

    df = pd.DataFrame({"ds": dates, "y": values})

    # Forecast 6 months ahead
    result = forecaster.forecast_with_prophet(df, periods=6, freq="ME")

    assert len(result["time"]) == 30  # 24 + 6
    assert len(result["yhat"]) == 30
    assert "yhat_lower" in result
    assert "yhat_upper" in result

    # The trend is decreasing, so the last forecast should be less than the first value
    assert result["yhat"][-1] < values[0]
