import pandas as pd #type: ignore
from ydata_profiling import ProfileReport #type: ignore
import json

def generate_column_stats(df: pd.DataFrame) -> dict:
    """
    Generates lightweight stats for each column to enrich the semantic graph.
    Returns a dictionary mapping column names to their stats.
    """
    # Using minimal mode for speed
    try:
        profile = ProfileReport(df, minimal=True, sensitive=False)
        json_data = json.loads(profile.to_json())
        
        stats_map = {}
        variables = json_data.get('variables', {})
        
        for col_name, data in variables.items():
            stats_map[col_name] = {
                "type": data.get('type'),
                "n_distinct": data.get('n_distinct'),
                "missing_pct": data.get('p_missing'),
                # Add specific stats based on type
                "min": data.get('min') if 'min' in data else None,
                "max": data.get('max') if 'max' in data else None,
            }
        return stats_map
    except Exception as e:
        print(f"Profiling failed: {e}")
        return {}