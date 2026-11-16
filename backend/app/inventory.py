# T05 / T12: Inventory history. Owner: Karnani Shresthkumar.
# Every Stock change goes through change_stock(), which writes an inventory_log row in the same
# transaction as the change (docs/database.md). The caller commits or rolls back both together,
# so the log can never disagree with the Stock it describes.
from .extensions import db
from .models import InventoryLog, Product

SALE, RESTOCK, RETURN, CORRECTION, CANCEL = "SALE", "RESTOCK", "RETURN", "CORRECTION", "CANCEL"
REASONS = (SALE, RESTOCK, RETURN, CORRECTION, CANCEL)
# Reasons a Manager may give for a hand edit. SALE and CANCEL are written only by the order code.
MANUAL_REASONS = (RESTOCK, RETURN, CORRECTION)
NOTE_MAX = 500


def change_stock(product, change, reason, *, user_id=None, order=None, note=None):
    """Add `change` (negative to remove) to the product's Stock and log it. Returns the log row.

    `order` is the Order object, not its id, so a SALE can be logged before the new Order is flushed.
    """
    if reason not in REASONS:
        raise ValueError(f"unknown inventory reason {reason!r}")
    if change == 0:
        raise ValueError("a stock change can't be zero")
    before = product.stock_qty
    after = before + change
    if after < 0:
        raise ValueError(f"stock of product {product.product_id} would go below zero")
    product.stock_qty = after
    entry = InventoryLog(
        product_id=product.product_id, user_id=user_id, order=order,
        before_qty=before, change_qty=change, after_qty=after, reason=reason, note=note,
    )
    db.session.add(entry)
    return entry


def return_order_stock(order, user_id=None, note=None):
    """A cancelled Order's items go back on the shelf: one CANCEL row per Order Line."""
    ids = sorted({line.product_id for line in order.lines})
    if not ids:
        return
    # Row locks in a fixed order, as place_order() does, so a sale and a cancel can't lose an update.
    locked = Product.query.filter(Product.product_id.in_(ids)).order_by(Product.product_id) \
        .populate_existing().with_for_update().all()
    products = {p.product_id: p for p in locked}
    for line in order.lines:
        change_stock(products[line.product_id], line.quantity, CANCEL, user_id=user_id, order=order, note=note)
