from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..crud.item import get_item
from ..dependencies import get_db
from ..schemas.item import ItemRead

router = APIRouter(prefix="/items")


@router.get("/{item_id}", response_model=ItemRead)
def read_item(item_id: int, db: Session = Depends(get_db)):
    item = get_item(db, item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    return item
