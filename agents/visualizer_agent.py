import plotly.express as px
import pandas as pd

class VisualizerAgent:
    def __init__(self, df: pd.DataFrame):
        self.df = df

    def generate_dashboard_charts(self):
        """Categorical aur numerical columns ke basis par auto-charts return karta hai."""
        num_cols = self.df.select_dtypes(include=['number']).columns.tolist()
        cat_cols = self.df.select_dtypes(include=['object', 'category']).columns.tolist()

        fig_bar = None
        fig_pie = None

        if len(num_cols) > 0 and len(cat_cols) > 0:
            # Bar chart aggregate calculation
            cat_summary = self.df.groupby(cat_cols[0])[num_cols[0]].sum().reset_index()
            fig_bar = px.bar(
                cat_summary, 
                x=cat_cols[0], 
                y=num_cols[0], 
                color=cat_cols[0], 
                title=f"{num_cols[0]} Breakdown by {cat_cols[0]}"
            )

            # Pie chart distribution
            fig_pie = px.pie(
                self.df, 
                names=cat_cols[0], 
                values=num_cols[0], 
                hole=0.4, 
                title=f"{num_cols[0]} Share Ratio"
            )

        return fig_bar, fig_pie