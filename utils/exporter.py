import io
import re
import pandas as pd

def export_as_csv(df: pd.DataFrame) -> bytes:
    """Exports DataFrame to CSV bytes."""
    return df.to_csv(index=False).encode('utf-8')

def export_as_xlsx(df: pd.DataFrame) -> bytes:
    """Exports DataFrame to XLSX (Excel) bytes."""
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='CleanedData')
    return output.getvalue()

def export_as_xls(df: pd.DataFrame) -> bytes:
    """Exports DataFrame to XLS bytes using openpyxl engine."""
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='CleanedData')
    return output.getvalue()

def export_as_xml(df: pd.DataFrame) -> bytes:
    """Exports DataFrame to XML bytes by strictly sanitizing XML tag names."""
    clean_df = df.copy()
    
    sanitized_cols = []
    for col in clean_df.columns:
        # Step 1: Alpha-numeric aur underscore ke ilawa baki sab (colons, spaces, etc.) replace karo
        clean_col = re.sub(r'[^a-zA-Z0-9_]', '_', str(col).strip())
        
        # Step 2: XML tags number se start nahi ho sakte, toh prefix add karo
        if clean_col and clean_col[0].isdigit():
            clean_col = f"col_{clean_col}"
            
        # Step 3: Empty string handle karo
        if not clean_col:
            clean_col = "unnamed_col"
            
        sanitized_cols.append(clean_col)
        
    clean_df.columns = sanitized_cols
    
    xml_data = clean_df.to_xml(index=False)
    return xml_data.encode('utf-8')