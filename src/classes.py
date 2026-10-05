# =======================================================================
# CLASSES
# =======================================================================
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np
import pandas as pd

class Batch:
    def __init__(self, batch_id, ph_opt, temperature_opt):
        self.batch_id = batch_id
        self.ph_opt = ph_opt
        self.temperature_opt = temperature_opt

    def display_info(self):
        print(f"Batch ID: {self.batch_id:4d} | "
              f"Optimal pH: {self.ph_opt:4.1f} | "
              f"Optimal Temperature: {self.temperature_opt:4.1f} C")

class BioprocessMonitor:
    def __init__(self, filepath, ph_lims, temperature_lims):
        self.filepath = filepath
        self.ph_lims = ph_lims
        self.temperature_lims = temperature_lims
        self.df = pd.read_csv(filepath)


    def extract_batch(self, batch_id):
        return self.df[self.df["batch_id"] == batch_id].copy()

    def optimal_ph_mask(self, df_batch):
        lower_limit = self.ph_lims[0] ##array of limits in constants.py
        upper_limit = self.ph_lims[1]
        above_lower = df_batch["pH"] >= lower_limit
        below_upper = df_batch["pH"] <= upper_limit
        ph_mask = above_lower & below_upper ##only true if both are true
        return ph_mask


    def optimal_temperature_mask(self, df_batch):
        lower_limit = self.temperature_lims[0]
        upper_limit = self.temperature_lims[1]
        above_lower = df_batch["temperature_C"] >= lower_limit
        below_upper = df_batch["temperature_C"] <= upper_limit
        temperature_mask= above_lower & below_upper
        return temperature_mask


    def get_n_batches(self):
        batch_column = self.df["batch_id"]
        unique_count = batch_column.nunique()
        return int(unique_count)


    def export_dashboard(self, batch_id, filepath):
        df_batch = self.extract_batch(batch_id)
        fig, axes = plt.subplots(2, 2, figsize=(12, 10))

        ## Concentration vs Time
        ax_conc = axes[0, 0]
        ax_conc.scatter(df_batch["time_h"], df_batch["C_glucose_g_L^-1"], label="Glucose", color="blue", marker="o")
        ax_conc.scatter(df_batch["time_h"], df_batch["C_biomass_g_L^-1"], label="Biomass", color="darkorange", marker="s")
        ax_conc.scatter(df_batch["time_h"], df_batch["C_product_g_L^-1"], label="Product", color="purple", marker="^")
        ax_conc.set_title(f"Concentrations vs Time (Batch {batch_id})")
        ax_conc.set_xlabel("Time (h)")
        ax_conc.set_ylabel("Concentration (g/L)")
        ax_conc.legend()
        ax_conc.grid(True, alpha=0.5)

        ## Temperature vs Time
        ax_temp = axes[0, 1]
        temp_mask = self.optimal_temperature_mask(df_batch)
        ax_temp.scatter(df_batch.loc[temp_mask, "time_h"], df_batch.loc[temp_mask, "temperature_C"], color="green", marker="o", label="Optimal")
        ax_temp.scatter(df_batch.loc[~temp_mask, "time_h"], df_batch.loc[~temp_mask, "temperature_C"], color="red", marker="x", label="Non-optimal")
        ax_temp.set_title("Temperature vs Time")
        ax_temp.set_xlabel("Time (h)")
        ax_temp.set_ylabel("Temperature (°C)")
        ax_temp.legend()
        ax_temp.grid(True, alpha=0.5)

        ## pH vs Time
        ax_ph = axes[1, 0]
        ph_mask = self.optimal_ph_mask(df_batch)
        ax_ph.scatter(df_batch.loc[ph_mask, "time_h"], df_batch.loc[ph_mask, "pH"], color="green", marker="o", label="Optimal")
        ax_ph.scatter(df_batch.loc[~ph_mask, "time_h"], df_batch.loc[~ph_mask, "pH"], color="red", marker="x", label="Non-optimal")
        ax_ph.set_title("pH vs Time")
        ax_ph.set_xlabel("Time (h)")
        ax_ph.set_ylabel("pH")
        ax_ph.legend()
        ax_ph.grid(True, alpha=0.5)

        ## Dissolved Oxygen vs Time
        ax_DO=axes[1, 1]
        ax_DO.scatter(df_batch["time_h"], df_batch["DO_percent"], color="navy", marker="o")
        ax_DO.set_title("Dissolved Oxygen vs Time")
        ax_DO.set_xlabel("Time (h)")
        ax_DO.set_ylabel("Dissolved Oxygen (%)")
        ax_DO.grid(True, alpha=0.5)

        for ax in axes.flat:
            ax.xaxis.set_major_locator(ticker.MultipleLocator(6))

        fig.tight_layout()

        fig.savefig(filepath, dpi=300)
        plt.close(fig)

    def export_summary(self, filepath):
        summary_rows = []
        batch_col = self.df["batch_id"]
        raw_unique_ids = batch_col.unique()
        unique_batch_ids = sorted(raw_unique_ids)
        for b_id in unique_batch_ids:
            df_b = self.extract_batch(b_id)
            if df_b.empty:
                continue
            ph_mask = self.optimal_ph_mask(df_b)
            temp_mask = self.optimal_temperature_mask(df_b)
            ph_prop = ph_mask.mean()
            temp_prop = temp_mask.mean()
            ph_pct_raw = ph_prop * 100
            temp_pct_raw = temp_prop * 100
            ph_optimal_percent = round(ph_pct_raw, 2)
            temperature_optimal_percent = round(temp_pct_raw, 2)
            df_b_sorted = df_b.sort_values(by="time_h")
            final_row = df_b_sorted.iloc[-1]
            c_product_final = final_row["C_product_g_L^-1"]
            row_dict = {
                "batch_id": b_id,
                "ph_optimal_percent": ph_optimal_percent,
                "temperature_optimal_percent": temperature_optimal_percent,
                "C_product_g_L^-1_final": c_product_final
            }
            summary_rows.append(row_dict)
        summary_df = pd.DataFrame(summary_rows)
        summary_df.to_csv(filepath, index=False)