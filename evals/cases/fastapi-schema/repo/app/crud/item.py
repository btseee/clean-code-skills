from sqlalchemy.orm import Session

from ..models.item import Item


def get_item(db: Session, item_id: int) -> Item | None:
    return db.get(Item, item_id)
