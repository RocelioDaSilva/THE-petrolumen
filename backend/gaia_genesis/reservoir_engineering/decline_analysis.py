import numpy as np
import pandas as pd
from scipy.optimize import curve_fit
import matplotlib.pyplot as plt
# For PDF report generation, FPDF or ReportLab could be used.
# For simplicity, we'll just sketch out the structure.
# from fpdf import FPDF # Example, if FPDF is chosen

class AdvancedDeclineAnalysis:
    def __init__(self, time: np.ndarray, rate: np.ndarray):
        if len(time) != len(rate):
            raise ValueError("Time and rate arrays must have the same length.")
        if not isinstance(time, np.ndarray):
            time = np.array(time)
        if not isinstance(rate, np.ndarray):
            rate = np.array(rate)

        self.time = time
        self.rate = rate
        self.models = {}
        self.params = {}
        self.predictions = {}

    @staticmethod
    def exponential_decline(t, qi, di):
        """Exponential decline curve model."""
        return qi * np.exp(-di * t)

    @staticmethod
    def hyperbolic_decline(t, qi, di, b):
        """Hyperbolic decline curve model."""
        # Ensure b is not too close to 0 or 1 for stability, or handle those cases
        if b <= 0 or b > 1: # b > 1 is technically possible but often constrained to 0-1
             # print(f"Warning: b value {b} is outside typical 0-1 range for hyperbolic.")
             pass # Allow it, but be mindful
        return qi / (1 + b * di * t)**(1 / b)

    @staticmethod
    def harmonic_decline(t, qi, di):
        """Harmonic decline curve model (special case of hyperbolic with b=1)."""
        return qi / (1 + di * t)

    def fit_models(self, p0_exp=None, p0_hyp=None, p0_harm=None):
        """
        Fits various decline curve models to the production data.
        p0_exp: initial guess for exponential parameters [qi, di]
        p0_hyp: initial guess for hyperbolic parameters [qi, di, b]
        p0_harm: initial guess for harmonic parameters [qi, di]
        """
        # Ensure rate is positive for fitting, log-transform can also be an option
        valid_indices = self.rate > 0
        if not np.any(valid_indices):
            print("No positive rate data available for fitting.")
            return

        time_fit = self.time[valid_indices]
        rate_fit = self.rate[valid_indices]

        # Default initial guesses if not provided
        qi_guess = rate_fit[0] if len(rate_fit) > 0 else 1.0
        di_guess = 0.1 # A small initial decline rate

        if p0_exp is None:
            p0_exp = [qi_guess, di_guess]
        if p0_hyp is None:
            p0_hyp = [qi_guess, di_guess, 0.5] # b_guess = 0.5 for hyperbolic
        if p0_harm is None:
            p0_harm = [qi_guess, di_guess]

        try:
            params_exp, _ = curve_fit(self.exponential_decline, time_fit, rate_fit, p0=p0_exp, maxfev=5000)
            self.params['exponential'] = {'qi': params_exp[0], 'di': params_exp[1]}
            self.models['exponential'] = lambda t: self.exponential_decline(t, *params_exp)
            print(f"Exponential fit successful. Params: {self.params['exponential']}")
        except RuntimeError:
            print("Could not fit exponential decline model.")
            self.params['exponential'] = None

        try:
            # Bounds for hyperbolic 'b' can be important: (0, 1] is common
            params_hyp, _ = curve_fit(self.hyperbolic_decline, time_fit, rate_fit, p0=p0_hyp, bounds=([0, 0, 0], [np.inf, np.inf, 1.0]), maxfev=5000)
            self.params['hyperbolic'] = {'qi': params_hyp[0], 'di': params_hyp[1], 'b': params_hyp[2]}
            self.models['hyperbolic'] = lambda t: self.hyperbolic_decline(t, *params_hyp)
            print(f"Hyperbolic fit successful. Params: {self.params['hyperbolic']}")
        except RuntimeError:
            print("Could not fit hyperbolic decline model.")
            self.params['hyperbolic'] = None
        except ValueError as ve:
            print(f"ValueError during hyperbolic fit (possibly bounds): {ve}")
            self.params['hyperbolic'] = None


        try:
            params_harm, _ = curve_fit(self.harmonic_decline, time_fit, rate_fit, p0=p0_harm, maxfev=5000)
            self.params['harmonic'] = {'qi': params_harm[0], 'di': params_harm[1]}
            self.models['harmonic'] = lambda t: self.harmonic_decline(t, *params_harm)
            print(f"Harmonic fit successful. Params: {self.params['harmonic']}")
        except RuntimeError:
            print("Could not fit harmonic decline model.")
            self.params['harmonic'] = None

    def predict_future(self, future_time: np.ndarray, model_name: str = 'hyperbolic') -> np.ndarray:
        """Predicts future production based on a specified fitted model."""
        if model_name not in self.models or self.models[model_name] is None:
            raise ValueError(f"Model '{model_name}' is not fitted or failed to fit.")

        prediction = self.models[model_name](future_time)
        self.predictions[model_name] = {'time': future_time, 'rate': prediction}
        return prediction

    def plot_decline_curves(self, future_time_extrapolation: np.ndarray = None, title="Decline Curve Analysis", file_path=None):
        """
        Generates plots of actual data and fitted decline curves.
        future_time_extrapolation: Optional array of future time points for plotting predictions.
        """
        plt.figure(figsize=(10, 6))
        plt.scatter(self.time, self.rate, label='Actual Production Data', color='black', marker='o')

        plot_time = self.time
        if future_time_extrapolation is not None:
            # Ensure plot_time covers both historical and future if provided
            plot_time = np.unique(np.concatenate((self.time, future_time_extrapolation)))


        for name, model_func in self.models.items():
            if model_func and self.params[name]: # Check if model was fitted
                params = self.params[name]
                if name == 'exponential':
                    rate_pred = self.exponential_decline(plot_time, params['qi'], params['di'])
                elif name == 'hyperbolic':
                    rate_pred = self.hyperbolic_decline(plot_time, params['qi'], params['di'], params['b'])
                elif name == 'harmonic':
                    rate_pred = self.harmonic_decline(plot_time, params['qi'], params['di'])
                else:
                    continue
                plt.plot(plot_time, rate_pred, label=f'{name.capitalize()} Fit')

        plt.xlabel('Time')
        plt.ylabel('Rate')
        plt.title(title)
        plt.legend()
        plt.grid(True)

        if file_path:
            plt.savefig(file_path)
            print(f"Plot saved to {file_path}")
        else:
            plt.show()

    def generate_report(self, well_name: str, output_path: str):
        """
        Creates a PDF report of the analysis.
        This is a placeholder for actual PDF generation logic.
        """
        print(f"Generating report for well {well_name} to {output_path}...")
        # Example: Using FPDF (would require `pip install fpdf2`)
        # pdf = FPDF()
        # pdf.add_page()
        # pdf.set_font("Arial", size=12)
        # pdf.cell(200, 10, txt=f"Decline Curve Analysis Report for {well_name}", ln=1, align="C")

        # Add summary of parameters
        # pdf.ln(10)
        # pdf.set_font("Arial", 'B', size=10)
        # pdf.cell(200, 10, txt="Fitted Model Parameters:", ln=1)
        # pdf.set_font("Arial", size=10)
        # for model_name, params in self.params.items():
        #     if params:
        #         param_str = ", ".join([f"{k}: {v:.4f}" for k, v in params.items()])
        #         pdf.cell(200, 10, txt=f"{model_name.capitalize()}: {param_str}", ln=1)

        # Add plot (e.g., save plot to a temp file and add as image)
        # plot_file_temp = "temp_decline_plot.png"
        # self.plot_decline_curves(file_path=plot_file_temp, title=f"Decline Curves for {well_name}")
        # if os.path.exists(plot_file_temp):
        #     pdf.image(plot_file_temp, x=10, y=None, w=180)
        #     os.remove(plot_file_temp)

        # pdf.output(output_path, "F")
        print(f"Report generation for {well_name} is a placeholder. Actual PDF would be saved to {output_path}")
        # Placeholder action: create a dummy text file
        with open(output_path, 'w') as f:
            f.write(f"Decline Curve Analysis Report for {well_name}\n\n")
            f.write("Fitted Model Parameters:\n")
            for model_name, params in self.params.items():
                if params:
                    param_str = ", ".join([f"{k}: {v:.4f}" for k, v in params.items()])
                    f.write(f"{model_name.capitalize()}: {param_str}\n")
            f.write("\nPlot would be included here.\n")
        print(f"Dummy report saved to {output_path}")


# Example Usage:
if __name__ == '__main__':
    # Sample data
    time_data = np.array([0, 30, 60, 90, 120, 150, 180, 210, 240, 270, 300, 330, 360]) # days
    rate_data = np.array([1000, 850, 700, 600, 500, 430, 370, 320, 280, 250, 220, 200, 180]) # bbl/day

    dca = AdvancedDeclineAnalysis(time_data, rate_data)

    # Fit models
    # Providing initial guesses can help convergence
    qi_guess = rate_data[0]
    di_guess_exp = -np.log(rate_data[-1]/rate_data[0]) / time_data[-1] if rate_data[-1] > 0 else 0.01

    dca.fit_models(
        p0_exp=[qi_guess, di_guess_exp if di_guess_exp > 0 else 0.01],
        p0_hyp=[qi_guess, 0.005, 0.8], # qi, di, b
        p0_harm=[qi_guess, 0.001]
    )

    print("\nFitted Parameters:")
    for model_name, params in dca.params.items():
        if params:
            print(f"{model_name.capitalize()}: {params}")
        else:
            print(f"{model_name.capitalize()}: Fit failed.")

    # Predict future production using the hyperbolic model (if fitted)
    if 'hyperbolic' in dca.models and dca.models['hyperbolic']:
        future_time = np.array([390, 420, 450, 480, 510, 540]) # Future days
        future_prediction = dca.predict_future(future_time, model_name='hyperbolic')
        print(f"\nFuture Predictions (Hyperbolic) at times {future_time}:")
        for t, r in zip(future_time, future_prediction):
            print(f"Time: {t}, Predicted Rate: {r:.2f}")

    # Plot the results including future extrapolation
    time_extrapolation = np.arange(time_data[-1] + 30, time_data[-1] + 30*6, 30) # For plotting
    dca.plot_decline_curves(future_time_extrapolation=time_extrapolation, title="Well Production Decline Analysis")

    # Generate a report (placeholder)
    dca.generate_report(well_name="TestWell001", output_path="TestWell001_decline_report.pdf") # Will create a .txt file

    # Example of handling case with no positive data
    print("\n--- Testing with non-positive data ---")
    time_zeros = np.array([0,1,2])
    rate_zeros = np.array([0,0,0])
    dca_zeros = AdvancedDeclineAnalysis(time_zeros, rate_zeros)
    dca_zeros.fit_models() # Should print "No positive rate data available for fitting."

    # Example of only one data point (curve_fit might struggle or give warnings)
    print("\n--- Testing with single data point ---")
    time_one = np.array([0])
    rate_one = np.array([100])
    dca_one = AdvancedDeclineAnalysis(time_one, rate_one)
    dca_one.fit_models() # curve_fit will likely fail or give poor results

    # Example of data that is hard to fit for some models
    print("\n--- Testing with noisy/flat data ---")
    time_flat = np.array([0, 30, 60, 90])
    rate_flat = np.array([500, 501, 499, 500]) # Very flat, low decline
    dca_flat = AdvancedDeclineAnalysis(time_flat, rate_flat)
    dca_flat.fit_models(p0_hyp=[500, 0.0001, 0.5]) # May need careful p0 for hyperbolic
    dca_flat.plot_decline_curves(title="Flat Production Data")
    dca_flat.generate_report("FlatWell", "FlatWell_report.pdf")

```
