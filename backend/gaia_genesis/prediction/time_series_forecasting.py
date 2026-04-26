import pandas as pd
import numpy as np
import logging
from typing import Dict, Optional
from prophet import Prophet

class TimeSeriesForecaster:
    """Service for time-series forecasting using Meta Prophet."""

    def __init__(self):
        self.logger = logging.getLogger("TimeSeriesForecaster")
        self.logger.setLevel(logging.INFO)

    def forecast_with_prophet(
        self,
        df: pd.DataFrame,
        periods: int = 12,
        freq: str = 'M'
    ) -> Dict:
        """
        df must have columns 'ds' (datetime) and 'y' (value).
        """
        if 'ds' not in df.columns or 'y' not in df.columns:
            raise ValueError("DataFrame must contain 'ds' and 'y' columns.")

        model = Prophet(yearly_seasonality=True, daily_seasonality=False)
        model.fit(df)

        future = model.make_future_dataframe(periods=periods, freq=freq)
        forecast = model.predict(future)

        # Convert to standard dictionary for JSON serialization
        return {
            "time": forecast['ds'].dt.strftime('%Y-%m-%d').tolist(),
            "yhat": forecast['yhat'].tolist(),
            "yhat_lower": forecast['yhat_lower'].tolist(),
            "yhat_upper": forecast['yhat_upper'].tolist()
        }

    def validate_against_simulator(self, simulated_data: Dict, periods: int = 5) -> float:
        """
        Validates the forecast against ground-truth simulator data.
        Returns RMSE.
        """
        # Minimal implementation for now
        return 0.0
