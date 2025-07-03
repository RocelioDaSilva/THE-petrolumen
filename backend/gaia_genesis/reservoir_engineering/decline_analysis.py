from typing import List, Any, Tuple, Dict
import numpy as np
import pandas as pd
from scipy.optimize import curve_fit
import logging

logger = logging.getLogger(__name__)

# Define decline curve models
def exponential_decline(t: np.ndarray, qi: float, di: float) -> np.ndarray:
    """Exponential decline model."""
    return qi * np.exp(-di * t)

class AdvancedDeclineAnalysis:
    def __init__(self):
        self.models: Dict[str, Any] = {}
        self.best_model_name: str = ""
        self.params: Dict[str, np.ndarray] = {}

    def fit_models(self, time: np.ndarray, rate: np.ndarray) -> Dict[str, Any]:
        """Fits various decline curve models (Exponential, Hyperbolic, Harmonic) to production data."""
        if len(time) != len(rate):
            raise ValueError("Time and rate arrays must have the same length.")
        if len(time) < 2:
            raise ValueError("At least two data points are required to fit a model.")

        # Initial parameter guesses (can be improved with more sophisticated methods)
        q_initial_guess = rate[0]
        d_initial_guess = -np.log(rate[1]/rate[0]) / (time[1]-time[0]) if rate[0] > 0 and rate[1] > 0 else 0.01

        try:
            # For simplicity, only implementing exponential decline
            # In a real scenario, you'd try multiple models (Hyperbolic, Harmonic)
            # and select the best one based on some criteria (e.g., R-squared, AIC)
            popt_exp, pcov_exp = curve_fit(
                exponential_decline,
                time,
                rate,
                p0=[q_initial_guess, d_initial_guess],
                bounds=([0, 0], [np.inf, 1.]) # qi > 0, 0 < di < 1 (annual)
            )
            self.params['exponential'] = popt_exp
            self.models['exponential'] = {
                'qi': popt_exp[0],
                'Di': popt_exp[1],
                'type': 'Exponential'
            }
            self.best_model_name = 'exponential' # Defaulting to exponential
            logger.info(f"Fitted Exponential Decline: qi={popt_exp[0]:.2f}, Di={popt_exp[1]:.4f}")
            return self.models
        except RuntimeError as e:
            logger.error(f"Could not fit exponential decline curve: {e}", exc_info=True)
            return {"error": "Could not fit model due to numerical issues."}
        except Exception as e:
            logger.exception(f"An unexpected error occurred during model fitting: {e}")
            return {"error": f"An unexpected error occurred during model fitting: {str(e)}"}


    def predict_future(self, months: int) -> pd.DataFrame:
        """Predicts future production based on the best fitted model."""
        empty_df = pd.DataFrame({'Time_Months': [], 'Predicted_Rate': []})
        if not self.best_model_name or self.best_model_name not in self.params:
            logger.warning("Models not fitted yet or best model not selected. Call fit_models first.")
            return empty_df

        future_time = np.arange(1, months + 1)

        try:
            if self.best_model_name == 'exponential':
                qi, di = self.params['exponential']
                # Ensure qi and di are non-negative before prediction to avoid math errors with exp or log if they were negative
                if qi < 0 or di < 0:
                    logger.error(f"Invalid model parameters for exponential decline: qi={qi}, di={di}. Cannot predict.")
                    return empty_df
                predicted_rate = exponential_decline(future_time, qi, di / 12.0) # Assuming Di is annual, convert to monthly
            # Add other models (hyperbolic, harmonic) here if implemented
            # elif self.best_model_name == 'hyperbolic':
            #     qi, di, b = self.params['hyperbolic']
            #     predicted_rate = hyperbolic_decline(future_time, qi, di / 12.0, b)
            else:
                logger.warning(f"Model type {self.best_model_name} not implemented for prediction.")
                return empty_df
            return pd.DataFrame({'Time_Months': future_time, 'Predicted_Rate': predicted_rate})
        except (ArithmeticError, ValueError) as e:
            logger.error(f"Error during future prediction calculation for model {self.best_model_name}: {e}", exc_info=True)
            return empty_df
        except Exception as e:
            logger.exception(f"An unexpected error occurred during future prediction: {e}")
            return empty_df


    def plot_decline_curves(self, time: np.ndarray, rate: np.ndarray) -> str:
        """Generates plots of decline curves.
        In a real scenario, this might return a Plotly figure object or save to a file.
        For now, it returns a message.
        """
        if not self.best_model_name:
            return "Models not fitted yet. Cannot generate plot."

        # Placeholder for plotting logic
        # import plotly.graph_objects as go
        # fig = go.Figure()
        # fig.add_trace(go.Scatter(x=time, y=rate, mode='markers', name='Actual Production'))
        #
        # if self.best_model_name == 'exponential' and 'exponential' in self.params:
        #     qi_exp, di_exp = self.params['exponential']
        #     rate_pred_exp = exponential_decline(time, qi_exp, di_exp)
        #     fig.add_trace(go.Scatter(x=time, y=rate_pred_exp, mode='lines', name='Exponential Fit'))
        #
        # fig.update_layout(title='Decline Curve Analysis', xaxis_title='Time', yaxis_title='Rate')
        # return fig.to_json() # Or fig.show(), or save to file

        return f"Plot generation for {self.best_model_name} model would happen here."

    def generate_report(self, well_name: str, output_path: str) -> str:
        """Creates a PDF report of the analysis.
        For now, it returns a message indicating the action.
        """
        if not self.best_model_name:
            return f"Models for {well_name} not fitted. Cannot generate report."

        report_content = f"Decline Curve Analysis Report for Well: {well_name}\n"
        report_content += f"Best Fit Model: {self.best_model_name.capitalize()}\n"

        if self.best_model_name in self.params:
            params = self.params[self.best_model_name]
            if self.best_model_name == 'exponential':
                report_content += f"  Initial Rate (qi): {params[0]:.2f}\n"
                report_content += f"  Decline Rate (Di): {params[1]:.4f} (annual)\n"

        # In a real scenario, you would use a library like ReportLab or FPDF to create a PDF
        # and include plots and more detailed analysis.
        try:
            with open(output_path, 'w') as f:
                f.write(report_content)
            logger.info(f"Report for {well_name} generated at {output_path}")
            return f"Report for {well_name} generated at {output_path}"
        except IOError as e:
            logger.error(f"IOError when generating report for {well_name} at {output_path}: {e}", exc_info=True)
            return f"Error: Could not write report to {output_path}"
        except Exception as e:
            logger.exception(f"An unexpected error occurred during report generation for {well_name}: {e}")
            return f"Unexpected error generating report for {well_name}"

# Example Usage (optional, for testing)
if __name__ == '__main__':
    # Configure basic logging for the example
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(name)s - %(message)s')

    # Sample production data (time in months, rate in bbl/day)
    time_data = np.array([0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]) # months
    rate_data = np.array([1000, 900, 810, 729, 656, 590, 531, 478, 430, 387, 348, 313]) # bbl/day

    dca = AdvancedDeclineAnalysis()

    # Fit models
    fit_results = dca.fit_models(time_data, rate_data)
    print("Fit Results:", fit_results)

    if "error" not in fit_results:
        # Predict future production for the next 12 months
        future_predictions = dca.predict_future(months=12)
        print("\nFuture Predictions (next 12 months):\n", future_predictions)

        # Generate plot (placeholder message)
        plot_message = dca.plot_decline_curves(time_data, rate_data)
        print("\nPlotting Message:", plot_message)

        # Generate report (placeholder action)
        report_message = dca.generate_report(well_name="Well-001", output_path="decline_report_Well-001.txt")
        print("\nReport Generation Message:", report_message)
    else:
        print(f"Skipping prediction and reporting due to fitting error: {fit_results.get('error')}")

