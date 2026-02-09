import pandas as pd
from io import BytesIO
from typing import List
from schemas import TableGraph, CellNode, ColumnMetadata
from profiler import generate_column_stats
from typing import List

def load_excel_to_graph(file_content: bytes, filename: str) -> List[TableGraph]:
    """
    Parses Excel (both .xls and .xlsx) into a Semantic Table Graph.
    Uses pandas.ExcelFile to automatically handle different Excel formats.
    """
    try:
        # UPDATED: Use pd.ExcelFile instead of openpyxl
        # This wrapper handles .xls, .xlsx, and .odf automatically
        xls = pd.ExcelFile(BytesIO(file_content))
    except Exception as e:
        # If pandas fails, it's likely not an Excel file at all (maybe CSV or text)
        raise ValueError(f"Could not read Excel file. Ensure it is a valid .xlsx or .xls file. Error: {str(e)}")

    parsed_tables = []

    for sheet_name in xls.sheet_names:
        # Parse the specific sheet
        df = pd.read_excel(xls, sheet_name=sheet_name)
        
        # Cleanup: Drop empty rows/cols
        df.dropna(how='all', inplace=True)
        df.dropna(axis=1, how='all', inplace=True)
        
        if df.empty:
            continue

        # 1. Get Statistical Profile
        col_stats = generate_column_stats(df)

        # 2. Build Column Metadata
        metadata_list = []
        for col in df.columns:
            col_str = str(col)
            stats = col_stats.get(col_str, {})
            metadata_list.append(ColumnMetadata(
                name=col_str,
                inferred_type=str(stats.get('type', 'unknown')), # Ensure string
                stats=stats
            ))

        # 3. Construct the Graph Nodes
        graph_nodes = []
        
        # Iterrows is slow for massive sheets, but fine for this semantic depth
        for idx, row in df.iterrows():
            # Excel 1-based index (approximate, +2 because header is usually row 1)
            row_id = idx + 2 
            
            for col_name in df.columns:
                val = row[col_name]
                if pd.isna(val):
                    continue
                
                # Determine basic type
                dtype = "text"
                if isinstance(val, (int, float)):
                    dtype = "numeric"
                elif isinstance(val, bool):
                    dtype = "boolean"

                # Create the Semantic Node
                node = CellNode(
                    coordinate=f"Row{row_id}:{col_name}",
                    value=val,
                    data_type=dtype,
                    context={
                        "associated_header": str(col_name),
                        "row_index": row_id,
                        "sheet": sheet_name
                    }
                )
                graph_nodes.append(node)

        # 4. Assemble the Table Graph
        table_graph = TableGraph(
            sheet_name=sheet_name,
            dimensions=f"{df.shape[0]} rows x {df.shape[1]} cols",
            columns=metadata_list,
            nodes=graph_nodes,
            summary=f"Table containing columns: {', '.join([str(c) for c in df.columns[:5]])}"
        )
        parsed_tables.append(table_graph)

    return parsed_tables