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

def hyperbolic_decline(t: np.ndarray, qi: float, di: float, b: float) -> np.ndarray:
    """Hyperbolic decline model.
    Requires 1 + b * Di * t > 0.
    b is the hyperbolic exponent.
    """
    # Add a small epsilon to prevent division by zero or log of zero if 1 + b * di * t is very close to 0
    # and to handle cases where it might be slightly negative due to floating point issues or bad fit.
    # However, curve_fit bounds should ideally prevent parameters that lead to this.
    denominator = 1 + b * di * t
    # Ensure denominator is positive to avoid issues with fractional exponent for negative bases
    denominator[denominator <= 0] = 1e-9 # Replace non-positive values with a small positive number
    return qi / np.power(denominator, 1.0 / b)

def harmonic_decline(t: np.ndarray, qi: float, di: float) -> np.ndarray:
    """Harmonic decline model (special case of hyperbolic with b=1)."""
    # Add a small epsilon to prevent division by zero if 1 + di * t is very close to 0
    denominator = 1 + di * t
    denominator[denominator <= 0] = 1e-9
    return qi / denominator

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
        # Ensure time difference is not zero and rates are positive for log
        if time[1] - time[0] > 1e-6 and rate[0] > 0 and rate[1] > 0 and rate[1] < rate[0] :
            d_initial_guess = -np.log(rate[1] / rate[0]) / (time[1] - time[0])
        else:
            d_initial_guess = 0.05 # A small default if initial points are problematic

        b_initial_guess = 0.5 # For hyperbolic

        fitted_models_sse = {}

        # --- Fit Exponential ---
        try:
            popt_exp, _ = curve_fit(
                exponential_decline, time, rate,
                p0=[q_initial_guess, d_initial_guess],
                bounds=([0, 0], [q_initial_guess * 2, 5.0]), # Max decline rate: 500% per unit time (e.g. year)
                maxfev=5000
            )
            self.params['exponential'] = popt_exp
            self.models['exponential'] = {'qi': popt_exp[0], 'Di': popt_exp[1], 'type': 'Exponential'}
            pred_exp = exponential_decline(time, *popt_exp)
            fitted_models_sse['exponential'] = np.sum((rate - pred_exp)**2)
            logger.info(f"Fitted Exponential: qi={popt_exp[0]:.2f}, Di={popt_exp[1]:.4f}, SSE={fitted_models_sse['exponential']:.2f}")
        except RuntimeError as e:
            logger.warning(f"Could not fit Exponential model: {e}")
        except Exception as e:
            logger.warning(f"Unexpected error fitting Exponential model: {e}", exc_info=True)

        # --- Fit Hyperbolic ---
        # Bounds: qi > 0, Di > 0, 0 < b < 1 (strictly hyperbolic)
        # Looser b bound (e.g. up to 2) can sometimes be useful but might become unstable or resemble exponential/harmonic
        try:
            popt_hyp, _ = curve_fit(
                hyperbolic_decline, time, rate,
                p0=[q_initial_guess, d_initial_guess, b_initial_guess],
                bounds=([0, 1e-9, 1e-9], [q_initial_guess * 2, 5.0, 0.9999]), # Di>0, 0<b<1
                maxfev=5000
            )
            self.params['hyperbolic'] = popt_hyp
            self.models['hyperbolic'] = {'qi': popt_hyp[0], 'Di': popt_hyp[1], 'b': popt_hyp[2], 'type': 'Hyperbolic'}
            pred_hyp = hyperbolic_decline(time, *popt_hyp)
            fitted_models_sse['hyperbolic'] = np.sum((rate - pred_hyp)**2)
            logger.info(f"Fitted Hyperbolic: qi={popt_hyp[0]:.2f}, Di={popt_hyp[1]:.4f}, b={popt_hyp[2]:.2f}, SSE={fitted_models_sse['hyperbolic']:.2f}")
        except RuntimeError as e:
            logger.warning(f"Could not fit Hyperbolic model: {e}")
        except Exception as e:
            logger.warning(f"Unexpected error fitting Hyperbolic model: {e}", exc_info=True)

        # --- Fit Harmonic ---
        # Bounds: qi > 0, Di > 0
        try:
            popt_harm, _ = curve_fit(
                harmonic_decline, time, rate,
                p0=[q_initial_guess, d_initial_guess],
                bounds=([0, 1e-9], [q_initial_guess * 2, 5.0]), # Di > 0
                maxfev=5000
            )
            self.params['harmonic'] = popt_harm
            self.models['harmonic'] = {'qi': popt_harm[0], 'Di': popt_harm[1], 'type': 'Harmonic'}
            pred_harm = harmonic_decline(time, *popt_harm)
            fitted_models_sse['harmonic'] = np.sum((rate - pred_harm)**2)
            logger.info(f"Fitted Harmonic: qi={popt_harm[0]:.2f}, Di={popt_harm[1]:.4f}, SSE={fitted_models_sse['harmonic']:.2f}")
        except RuntimeError as e:
            logger.warning(f"Could not fit Harmonic model: {e}")
        except Exception as e:
            logger.warning(f"Unexpected error fitting Harmonic model: {e}", exc_info=True)

        # Select best model based on lowest SSE
        if not fitted_models_sse:
            logger.error("No models could be fitted.")
            return {"error": "Could not fit any decline model."}

        self.best_model_name = min(fitted_models_sse, key=fitted_models_sse.get)
        logger.info(f"Best model selected: {self.best_model_name.capitalize()} with SSE={fitted_models_sse[self.best_model_name]:.2f}")

        return self.models # Return all fitted models info


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
                # Assuming Di is annual, convert to monthly for prediction step
                predicted_rate = exponential_decline(future_time, qi, di / 12.0)
            elif self.best_model_name == 'hyperbolic':
                qi, di, b = self.params['hyperbolic']
                if qi < 0 or di <= 0 or b <= 0 or b >=1: # Stricter b for pure hyperbolic
                     logger.error(f"Invalid model parameters for hyperbolic decline: qi={qi}, di={di}, b={b}. Cannot predict.")
                     return empty_df
                predicted_rate = hyperbolic_decline(future_time, qi, di / 12.0, b)
            elif self.best_model_name == 'harmonic':
                qi, di = self.params['harmonic']
                if qi < 0 or di <= 0:
                     logger.error(f"Invalid model parameters for harmonic decline: qi={qi}, di={di}. Cannot predict.")
                     return empty_df
                predicted_rate = harmonic_decline(future_time, qi, di / 12.0)
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
            elif self.best_model_name == 'hyperbolic':
                report_content += f"  Initial Rate (qi): {params[0]:.2f}\n"
                report_content += f"  Initial Decline Rate (Di): {params[1]:.4f} (annual)\n"
                report_content += f"  Hyperbolic Exponent (b): {params[2]:.2f}\n"
            elif self.best_model_name == 'harmonic':
                report_content += f"  Initial Rate (qi): {params[0]:.2f}\n"
                report_content += f"  Decline Rate (Di): {params[1]:.4f} (annual)\n"

            # Could also add SSE or other fit metrics here
            # sse = fitted_models_sse.get(self.best_model_name, float('nan')) # Need fitted_models_sse to be an instance var
            # report_content += f"  Sum of Squared Errors (SSE): {sse:.2f}\n"


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

