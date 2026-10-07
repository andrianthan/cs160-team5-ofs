// OFS UI Prototype — shared fake data & helpers.
// Not real persistence: everything lives in localStorage, cleared any time via clearAll().

const OFS = (() => {
  // `icon` is a Phosphor icon slug (ph-<slug>), rendered via <i class="ph ph-<slug>">.
  const PRODUCTS = [
    { id: "p1", name: "Organic Bananas (bunch)", category: "Produce", price: 2.49, weightLb: 1.5, stock: 40, icon: "plant" },
    { id: "p2", name: "Heirloom Tomatoes (2 lb)", category: "Produce", price: 5.99, weightLb: 2, stock: 22, icon: "carrot" },
    { id: "p3", name: "Baby Spinach (box)", category: "Produce", price: 3.49, weightLb: 0.5, stock: 30, icon: "leaf" },
    { id: "p4", name: "Free-Range Eggs (dozen)", category: "Dairy", price: 6.49, weightLb: 1.6, stock: 18, icon: "egg" },
    { id: "p5", name: "Whole Milk (1 gal)", category: "Dairy", price: 5.29, weightLb: 8.6, stock: 15, icon: "drop" },
    { id: "p6", name: "Sourdough Loaf", category: "Bakery", price: 6.99, weightLb: 1.2, stock: 12, icon: "bread" },
    { id: "p7", name: "Organic Rolled Oats (5 lb)", category: "Pantry", price: 8.99, weightLb: 5, stock: 25, icon: "bowl-food" },
    { id: "p8", name: "Spring Water (24-pack)", category: "Pantry", price: 7.99, weightLb: 30, stock: 10, icon: "drop-half-bottom" },
  ];

  const CATEGORY_ICON = { Produce: "carrot", Dairy: "drop", Bakery: "bread", Pantry: "package" };

  const USERS = {
    customer: { role: "Customer", email: "customer@ofs.test", password: "demo", name: "Jamie Lin" },
    employee: { role: "Employee", email: "employee@ofs.test", password: "demo", name: "Sam Rivera" },
    manager:  { role: "Manager",  email: "manager@ofs.test",  password: "demo", name: "Dana Park" },
  };

  // Seed data — copied into shared storage on first load, then mutated from there.
  // Both apps read/write through getOrders/setOrders etc so a real end-to-end
  // flow (Placed -> Planned -> Out for Delivery -> Delivered/Failed) is visible
  // on both the Storefront and the Staff Dashboard.
  const SEED_ORDERS = [
    { id: "OFS-1030", customer: "Ana Torres", customerEmail: "ana@example.test", status: "Delivered",      weightLb: 9.0,  fee: 0,  total: 21.40, placedAt: "Yesterday", tripId: null },
    { id: "OFS-1028", customer: "Liam Chen", customerEmail: "liam@example.test", status: "Delivery Failed", weightLb: 15.5, fee: 0,  total: 39.90, placedAt: "Yesterday", tripId: null },
  ];

  const SEED_ROBOTS = [
    { id: "R1",
      status: "Idle",
      location: {
        lat: 37.3352,
        lng: -121.8811
      },
      progress: 0,
      etaMinutes: null
    },
    { id: "R2",
      status: "Idle",
      location: {
        lat: 37.3352,
        lng: -121.8811
      },
      progress: 0,
      etaMinutes: null
    },
  ];

  const SEED_TRIPS = [];

  const TRIP_MAX_ORDERS = 10; // BR-2
  const TRIP_MAX_WEIGHT = 200; // BR-2

  const DELIVERY_ZONE_HINT = "downtown san jose"; // address must mention this (case-insensitive) to validate

  // ---- storage helpers ----
  // localStorage on file:// pages is shared across every ofs-prototype file
  // opened in the same browser, which is what lets the Storefront and the
  // Staff Dashboard see the same orders/trips/robots. The "storage" event
  // fires in *other* open tabs whenever one tab writes, so if you keep both
  // apps open side by side they update live without a manual refresh.
  const KEY = "ofs_proto_v1";
  function load() {
    try { return JSON.parse(localStorage.getItem(KEY)) || {}; } catch { return {}; }
  }
  function save(state) {
    try { localStorage.setItem(KEY, JSON.stringify(state)); } catch {}
  }
  function get(key, fallback) {
    const s = load();
    return key in s ? s[key] : fallback;
  }
  function set(key, value) {
    const s = load();
    s[key] = value;
    save(s);
  }
  function clearAll() {
    try { localStorage.removeItem(KEY); } catch {}
  }
  function onChange(cb) {
    window.addEventListener("storage", (e) => { if (e.key === KEY) cb(); });
  }

  // ---- shared collections (orders / trips / robots) ----
  function getOrders() { return get("orders", null) || (set("orders", SEED_ORDERS), SEED_ORDERS.slice()); }
  function setOrders(list) { set("orders", list); }
  function getTrips() { return get("trips", null) || (set("trips", SEED_TRIPS), SEED_TRIPS.slice()); }
  function setTrips(list) { set("trips", list); }
  function getRobots() { return get("robots", null) || (set("robots", SEED_ROBOTS), SEED_ROBOTS.slice()); }
  function setRobots(list) { set("robots", list); }

  function nextOrderId() {
    return "OFS-" + Math.floor(1100 + Math.random() * 8899);
  }
  function nextTripId() {
    const trips = getTrips();
    const n = trips.length + 201;
    return "T-" + n;
  }

  // Delivery Planning: place a newly-Prepared order onto an open Trip,
  // respecting BR-2 (10 Orders / 200 lb per Trip) and BR-6 (oldest first —
  // here, first-open-trip-first since this is a single-store demo).
  function assignOrderToTrip(order) {
    const trips = getTrips();
    let trip = trips.find(t => t.status === "Planning"
      && t.orderIds.length < TRIP_MAX_ORDERS
      && t.weightLb + order.weightLb <= TRIP_MAX_WEIGHT);
    if (!trip) {
      trip = { id: nextTripId(), robot: null, orderIds: [], weightLb: 0, status: "Planning", createdAt: Date.now() };
      trips.push(trip);
    }
    trip.orderIds.push(order.id);
    trip.weightLb += order.weightLb;
    setTrips(trips);
    return trip.id;
  }

  // ---- domain helpers ----
  function calcWeight(cart) {
    return cart.reduce((sum, line) => {
      const p = PRODUCTS.find(p => p.id === line.id);
      return sum + (p ? p.weightLb * line.qty : 0);
    }, 0);
  }
  function calcSubtotal(cart) {
    return cart.reduce((sum, line) => {
      const p = PRODUCTS.find(p => p.id === line.id);
      return sum + (p ? p.price * line.qty : 0);
    }, 0);
  }
  function calcFee(weightLb) {
    return weightLb >= 20 ? 10 : 0; // BR-1
  }
  function isOverweight(weightLb) {
    return weightLb > 200; // BR-3
  }
  function money(n) {
    return "$" + n.toFixed(2);
  }
  function toast(msg, kind = "info") {
    const host = document.getElementById("toast-host");
    if (!host) return;
    const el = document.createElement("div");
    const styles = {
      info: { bg: "bg-brand-900", icon: "info" },
      error: { bg: "bg-red-600", icon: "warning-circle" },
      success: { bg: "bg-brand-700", icon: "check-circle" },
    };
    const s = styles[kind] || styles.info;
    el.className = `${s.bg} text-white text-sm px-4 py-2.5 rounded-2xl shadow-lg flex items-center gap-2 animate-[fadein_.15s_ease-out]`;
    el.innerHTML = `<i class="ph ph-${s.icon} text-base shrink-0" aria-hidden="true"></i><span>${msg}</span>`;
    host.appendChild(el);
    setTimeout(() => el.remove(), 3200);
  }

  return {
    PRODUCTS, USERS, DELIVERY_ZONE_HINT, TRIP_MAX_ORDERS, TRIP_MAX_WEIGHT, CATEGORY_ICON,
    get, set, clearAll, onChange,
    getOrders, setOrders, getTrips, setTrips, getRobots, setRobots,
    nextOrderId, assignOrderToTrip,
    calcWeight, calcSubtotal, calcFee, isOverweight, money, toast,
  };
})();
