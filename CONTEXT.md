# OFS On-Demand Food Delivery

Online grocery ordering and robot delivery for OFS, a local organic food retailer chain in Downtown San Jose. This glossary is the shared language for every Team 5 document, diagram, and line of code.

## People

**Customer**:
A person who registers with OFS, buys Products online, and receives them at a delivery address.
_Avoid_: User, client, buyer, shopper

**Employee**:
Authorized OFS store staff who update Product information, prepare Orders, load Robots, and approve Dispatch.
_Avoid_: Worker, clerk, associate

**Manager**:
OFS store staff with every Employee permission plus adding or removing Products, pausing deliveries, overriding Orders, and viewing Reports.
_Avoid_: Admin, owner, supervisor

**Staff**:
Collective term for Employees and Managers.
_Avoid_: Internal user, backoffice

## Catalog

**Product**:
A food or grocery item OFS sells, with a category, price, weight in pounds, description, and availability.
_Avoid_: Item, SKU, good

**Stock**:
The quantity of a Product currently available to sell.
_Avoid_: Inventory count, quantity on hand

**Inventory**:
The full set of Products and their Stock, including the history of changes.
_Avoid_: Catalog database, warehouse

## Ordering

**Cart**:
The Customer's in-progress selection of Products before checkout; it is saved for later.
_Avoid_: Basket, bag

**Order**:
One paid Customer checkout: a set of Order Lines, a validated delivery address, and a payment. An Order exists only after payment succeeds.
_Avoid_: Purchase, transaction, sale

**Order Line**:
One Product and its quantity inside a Cart or Order.
_Avoid_: Line item, cart item

**Order Weight**:
The total weight in pounds of every Order Line in an Order.
_Avoid_: Package weight, shipping weight

**Delivery Fee**:
$0 when Order Weight is under 20 lb; $10 when Order Weight is 20 lb or more.
_Avoid_: Shipping cost, surcharge

**Overweight Order**:
An Order whose Order Weight exceeds 200 lb; it cannot fit on a Robot, so checkout blocks it and Delivery Planning sends any that slip through to Manual Review.
_Avoid_: Bulk order, oversized order

**Preparation Queue**:
Orders on a planned Trip waiting for an Employee to retrieve, scan, and load them onto the Robot.
_Avoid_: Order queue, backlog

**Order Status**:
Where an Order is in its life: Placed → Planned → Out for Delivery → Delivered; or Delivery Failed, Manual Review, Cancelled.
_Avoid_: State, stage, progress

**Manual Review**:
An Order held for Staff attention because its address failed validation or it cannot fit a Trip.
_Avoid_: Exception queue, flagged order

## Delivery

**Delivery Zone**:
The Downtown San Jose area OFS delivers to; a delivery address outside it is rejected at checkout.
_Avoid_: Service area, coverage area, range

**Robot**:
A self-driving OFS delivery vehicle that carries up to 10 Orders and 200 lb per Trip.
_Avoid_: Vehicle, car, driver, drone

**Trip**:
One Robot run from the store through 1–10 Order delivery addresses and back.
_Avoid_: Batch, route, run, delivery

**Delivery Planning**:
Grouping Placed Orders into Trips, oldest Order first, adding the nearest Orders that keep the Trip within 10 Orders and 200 lb.
_Avoid_: Batching, scheduling

**Route**:
The ordered sequence of stops a Robot follows on a Trip, chosen to minimize travel time given current traffic.
_Avoid_: Path, directions, itinerary

**Dispatch**:
An Employee confirming a Robot is correctly loaded and sending it out on its Trip. A Trip is dispatched once full (10 Orders or 200 lb) or 30 minutes after its oldest Order was Placed, whichever comes first.
_Avoid_: Sending, launch

**Robot Queue**:
Planned Trips waiting for a Robot to become available.
_Avoid_: Trip backlog, waitlist

**Late Delivery**:
A delivery that reaches the Customer after the estimated arrival time shown to them.
_Avoid_: Delay, overdue order

**Delivery Failed**:
The Order Status when a Robot cannot hand an Order to the Customer at its stop; the Order returns to the store and Staff are notified.
_Avoid_: Missed delivery, undeliverable

**Delivery Pause**:
A Manager-set switch that temporarily stops new deliveries from being accepted.
_Avoid_: Disable deliveries, shutdown

## Management

**Report**:
A Manager view that summarizes sales, Product demand, Inventory history, or delivery performance over a chosen period.
_Avoid_: Analytics, dashboard, stats

**Order Override**:
A Manager changing or cancelling an Order after it was Placed.
_Avoid_: Admin edit, force update
