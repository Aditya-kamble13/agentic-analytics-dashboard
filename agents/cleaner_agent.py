import pandas as pd

class DataCleanerAgent:
    def __init__(self, df: pd.DataFrame):
        self.df = df

    def get_audit_summary(self) -> dict:
        """Returns basic metrics on data hygiene."""
        return {
            "total_rows": self.df.shape[0],
            "total_columns": self.df.shape[1],
            "null_count": int(self.df.isnull().sum().sum()),
            "duplicate_count": int(self.df.duplicated().sum())
        }

    def clean_missing_values(self) -> pd.DataFrame:
        """Smartly cleans missing values without wiping out legitimate data rows."""
        # 1. Dropping completely empty columns
        self.df = self.df.dropna(how='all', axis=1)

        # 2. Dropping useless 'Unnamed' columns that have >70% nulls
        unnamed_cols = [c for c in self.df.columns if 'Unnamed' in str(c)]
        for col in unnamed_cols:
            if self.df[col].isnull().sum() / len(self.df) > 0.5:
                self.df = self.df.drop(columns=[col])

        # 3. Filling missing text/categorical values with 'N/A' instead of deleting rows
        cat_cols = self.df.select_dtypes(include=['object', 'category']).columns
        for col in cat_cols:
            self.df[col] = self.df[col].fillna("N/A")

        # 4. Filling missing numeric columns with 0
        num_cols = self.df.select_dtypes(include=['number']).columns
        for col in num_cols:
            self.df[col] = self.df[col].fillna(0)

        # 5. Dropping rows that are completely empty across all remaining columns
        self.df = self.df.dropna(how='all', axis=0)

        return self.df

    def remove_duplicates(self) -> pd.DataFrame:
        """Purges duplicate rows."""
        self.df = self.df.drop_duplicates()
        return self.df