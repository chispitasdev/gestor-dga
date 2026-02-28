"""Router FastAPI para importacion de datos desde CSV/Excel."""

from __future__ import annotations

import tempfile
from pathlib import Path

from fastapi import APIRouter, HTTPException, UploadFile

from src.dga.infrastructure.api.dependencies import import_service
from src.dga.infrastructure.api.schemas import ImportResponse

router = APIRouter(prefix="/api/import", tags=["Importacion"])


@router.post("/{transformer_id}", response_model=ImportResponse)
async def import_file(
    transformer_id: int, file: UploadFile
) -> ImportResponse:
    """Importa muestras desde un archivo CSV o Excel.

    Sube el archivo y lo procesa para insertar las muestras
    asociadas al transformador indicado.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="No se envio archivo.")

    suffix = Path(file.filename).suffix.lower()
    if suffix not in (".csv", ".xlsx", ".xls"):
        raise HTTPException(
            status_code=400,
            detail=f"Formato no soportado: '{suffix}'. Use .csv o .xlsx",
        )

    # Guardar archivo temporal
    with tempfile.NamedTemporaryFile(
        delete=False, suffix=suffix
    ) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name

    try:
        result = import_service.import_from_file(tmp_path, transformer_id)
        return ImportResponse(
            total_rows=result.total_rows,
            imported=result.imported,
            skipped=result.skipped,
            errors=result.errors,
        )
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        Path(tmp_path).unlink(missing_ok=True)
