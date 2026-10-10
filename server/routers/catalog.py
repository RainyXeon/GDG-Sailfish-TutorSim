from fastapi import APIRouter, Depends, HTTPException, status

import data
import schemas
from deps import get_current_user

router = APIRouter(prefix="/catalog", tags=["catalog"], dependencies=[Depends(get_current_user)])


@router.get("/misconceptions", response_model=list[schemas.MisconceptionSummary])
def list_misconceptions():
    return [
        schemas.MisconceptionSummary(id=m["id"], chuyen_de=m["chuyen_de"], ten_loi=m["ten_loi"])
        for m in data.MISCONCEPTIONS
    ]


@router.get("/misconceptions/{misconception_id}", response_model=schemas.MisconceptionDetail)
def get_misconception(misconception_id: str):
    m = data.find_misconception(misconception_id)
    if m is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Misconception not found")
    return schemas.MisconceptionDetail(
        id=m["id"], chuyen_de=m["chuyen_de"], ten_loi=m["ten_loi"],
        bai_toan=m["bai_toan"], loi_giai_sai=m["loi_giai_sai"],
    )


@router.get("/personas", response_model=list[schemas.PersonaOut])
def list_personas():
    return [schemas.PersonaOut(key=k, description=v) for k, v in data.PERSONAS.items()]
