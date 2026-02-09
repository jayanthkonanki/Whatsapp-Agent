from fastapi import FastAPI, UploadFile, File, HTTPException #type: ignore
from xl_parser.parser import load_excel_to_graph
from xl_parser.schemas import ExtractionResponse
import uvicorn #type: ignore

app = FastAPI(title="Excel -> Semantic Graph Pipeline")

@app.post("/upload/excel", response_model=ExtractionResponse)
async def upload_excel(file: UploadFile = File(...)):
    """
    Accepts an Excel file, parses it into a Semantic Graph JSON, 
    and returns a structure ready for LLM consumption.
    """
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="Invalid file type. Please upload Excel.")
    
    try:
        content = await file.read()
        
        # Execute Pipeline
        semantic_tables = load_excel_to_graph(content, file.filename)
        
        return ExtractionResponse(
            filename=file.filename,
            tables=semantic_tables
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)