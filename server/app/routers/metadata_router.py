from __future__ import annotations

from fastapi import APIRouter

from app.schemas.conversion import OperationOut
from core.operations import OPERATIONS

router = APIRouter(prefix="/api", tags=["metadata"])


@router.get("/operations", response_model=list[OperationOut])
def operations() -> list[OperationOut]:
    return [OperationOut.from_spec(spec) for spec in OPERATIONS.values()]
