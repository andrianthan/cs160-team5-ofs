# T02 — PostgreSQL schema and migrations. Owner: Sharma Anuj.
# Tables per docs/part1 Architecture HLD §4 and docs/part2 LLD 6:
#   users, addresses, products, inventory_log, carts, order_lines, orders,
#   payments, robots, trips, trip_stops
#
# Import each model here once defined, e.g.:
#   from .user import User
#   from .product import Product
# so `from app.models import User` works and Flask-Migrate can see them.
from .user import User 