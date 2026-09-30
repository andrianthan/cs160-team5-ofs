// OFS Staff Dashboard — click-through prototype logic.

const AUTH_KEY = "staffAuth";
const PAUSE_KEY = "deliveryPaused";
const STOCK_KEY = "stockOverrides"; // { [productId]: newStock }

function getAuth() { return OFS.get(AUTH_KEY, null); }
function setAuth(user) { OFS.set(AUTH_KEY, user); }
function isPaused() { return OFS.get(PAUSE_KEY, false); }
function setPaused(v) { OFS.set(PAUSE_KEY, v); }
function getStockOverrides() { return OFS.get(STOCK_KEY, {}); }
function setStock(id, qty) {
  const overrides = getStockOverrides();
  overrides[id] = qty;
  OFS.set(STOCK_KEY, overrides);
}
function stockFor(product) {
  const overrides = getStockOverrides();
  return id_in(overrides, product.id) ? overrides[product.id] : product.stock;
}
function id_in(obj, id) { return Object.prototype.hasOwnProperty.call(obj, id); }

function currentRoute() {
  const hash = location.hash.replace(/^#\//, "") || "";
  return hash.split("/")[0] || (getAuth() ? "queue" : "login");
}

function render() {
  const route = currentRoute();
  const auth = getAuth();
  const nav = document.getElementById("nav");

  if (!auth && route !== "login") { location.hash = "#/login"; return; }
  if (auth && route === "login") { location.hash = "#/queue"; return; }
  if (auth && route === "reports" && auth.role !== "Manager") {
    OFS.toast("Reports is Manager-only.", "error");
    location.hash = "#/queue";
    return;
  }

  nav.classList.toggle("hidden", !auth);
  if (auth) {
    document.getElementById("nav-user").textContent = auth.name;
    document.getElementById("nav-role").textContent = auth.role;
    const isManager = auth.role === "Manager";
    document.querySelectorAll("[data-manager-only]").forEach(el => {
      el.classList.toggle("hidden", !isManager);
      if (isManager) el.classList.add("inline-flex");
    });
    document.querySelectorAll("[data-nav]").forEach(el => {
      const active = el.dataset.nav === route;
      el.classList.toggle("bg-brand-50", active);
      el.classList.toggle("text-brand-700", active);
      el.classList.toggle("text-brand-900/60", !active);
    });
    renderPauseBtn();
  }

  document.querySelectorAll("[data-route]").forEach(el => {
    el.dataset.active = String(el.dataset.route === route);
  });

  if (route === "queue") renderQueue();
  if (route === "dispatch") renderDispatch();
  if (route === "inventory") renderInventory();
  if (route === "reports") renderReports();
}

window.addEventListener("hashchange", render);

// ---------- login ----------
document.getElementById("login-form").addEventListener("submit", (e) => {
  e.preventDefault();
  const form = new FormData(e.target);
  const email = form.get("email").trim().toLowerCase();
  const password = form.get("password");
  const match = Object.values(OFS.USERS).find(u => u.role !== "Customer" && u.email === email && u.password === password);
  const errEl = document.getElementById("login-error");
  if (!match) {
    errEl.querySelector("span").textContent = "Incorrect email or password.";
    errEl.classList.remove("hidden");
    return;
  }
  errEl.classList.add("hidden");
  setAuth(match);
  OFS.toast(`Welcome, ${match.name.split(" ")[0]} (${match.role})`, "success");
  location.hash = "#/queue";
});

document.getElementById("logout-btn").addEventListener("click", () => {
  setAuth(null);
  location.hash = "#/login";
});

document.getElementById("pause-btn").addEventListener("click", () => {
  setPaused(!isPaused());
  renderPauseBtn();
  OFS.toast(isPaused() ? "Delivery paused — checkout disabled for customers. (BR-9)" : "Delivery resumed.", isPaused() ? "error" : "success");
});

function renderPauseBtn() {
  const paused = isPaused();
  document.getElementById("pause-state").textContent = paused ? "Paused" : "Active";
  const btn = document.getElementById("pause-btn");
  btn.classList.toggle("border-red-300", paused);
  btn.classList.toggle("text-red-600", paused);
  btn.classList.toggle("bg-red-50", paused);
}

// ---------- prep queue ----------
function renderQueue() {
  const list = OFS.getOrders().filter(o => o.status === "Placed");
  const host = document.getElementById("queue-list");
  if (list.length === 0) {
    host.innerHTML = `<div class="text-brand-900/50 py-12 text-center border border-dashed border-brand-200 rounded-xl">Queue is empty. Orders placed on the Storefront show up here.</div>`;
    return;
  }
  host.innerHTML = list.map(o => `
    <div class="bg-white border border-brand-100 rounded-xl p-4 flex items-center justify-between flex-wrap gap-3">
      <div>
        <div class="font-medium text-sm">${o.id} <span class="text-brand-900/40 font-normal">· ${o.customer}</span></div>
        <div class="text-xs text-brand-900/50">${o.weightLb.toFixed(1)} lb · ${OFS.money(o.total)} · placed ${o.placedAt}</div>
      </div>
      <div class="flex items-center gap-2">
        <span class="text-xs font-medium px-2.5 py-1 rounded-full bg-gold-100 text-gold-800 flex items-center gap-1"><i class="ph ph-receipt" aria-hidden="true"></i>Placed</span>
        <button data-prep="${o.id}" class="text-xs font-medium bg-brand-600 hover:bg-brand-700 text-white rounded-xl px-3 py-1.5 transition-colors duration-200 cursor-pointer flex items-center gap-1.5"><i class="ph ph-check" aria-hidden="true"></i>Mark Prepared</button>
      </div>
    </div>`).join("");

  document.querySelectorAll("[data-prep]").forEach(btn => {
    btn.addEventListener("click", () => {
      const list = OFS.getOrders();
      const o = list.find(x => x.id === btn.dataset.prep);
      o.status = "Planned";
      o.tripId = OFS.assignOrderToTrip(o); // BR-2 / BR-6: adds to the open Trip, or opens a new one
      OFS.setOrders(list);
      OFS.toast(`${o.id} prepared — added to ${o.tripId}`, "success");
      renderQueue();
    });
  });
}

// ---------- dispatch ----------
function tripOrders(trip) {
  const all = OFS.getOrders();
  return trip.orderIds.map(id => all.find(o => o.id === id)).filter(Boolean);
}

function renderDispatch() {
  const trips = OFS.getTrips().filter(t => t.status !== "Completed");
  const host = document.getElementById("dispatch-list");
  if (trips.length === 0) {
    host.innerHTML = `<div class="text-brand-900/50 py-12 text-center border border-dashed border-brand-200 rounded-xl md:col-span-2">No Trips yet. Prepare an order in the Queue to open one.</div>`;
    return;
  }
  host.innerHTML = trips.map(t => {
    const orders = tripOrders(t);
    const overCount = t.orderIds.length > OFS.TRIP_MAX_ORDERS;
    const overWeight = t.weightLb > OFS.TRIP_MAX_WEIGHT;
    const robots = OFS.getRobots();
    const robot = robots.find(r => r.id === t.robot);
    const isDispatched = t.status === "Out for Delivery";

    return `
    <div class="bg-white border border-brand-100 rounded-3xl p-5 shadow-sm shadow-brand-900/5">
      <div class="flex items-center justify-between mb-3">
        <div class="font-display font-semibold">${t.id}</div>
        <span class="text-xs font-medium px-2.5 py-1 rounded-full flex items-center gap-1 ${isDispatched ? "bg-emerald-100 text-emerald-700" : "bg-brand-50 text-brand-900/60"}">
          ${isDispatched ? '<i class="ph ph-truck" aria-hidden="true"></i>' : ""}${t.status}
        </span>
      </div>

      <!-- Robot avatar row, Uber-driver-card style -->
      <div class="flex items-center gap-3 mb-4 p-3 rounded-2xl ${robot ? "bg-brand-50" : "bg-brand-50/50 border border-dashed border-brand-200"}">
        <div class="w-10 h-10 rounded-full ${robot ? "bg-brand-700" : "bg-brand-200"} text-white flex items-center justify-center text-lg shrink-0">
          <i class="ph ph-robot" aria-hidden="true"></i>
        </div>
        <div class="flex-1 text-sm">
          <div class="font-medium">${robot ? robot.id : "No Robot assigned"}</div>
          <div class="text-xs text-brand-900/50">${robot ? "Ready to load" : "Waiting in Robot Queue"}</div>
        </div>
      </div>

      <div class="text-sm text-brand-900/60 space-y-1 mb-3">
        <div class="flex items-center gap-1.5 ${overCount ? "text-red-600 font-medium" : ""}"><i class="ph ph-package" aria-hidden="true"></i>Orders: ${t.orderIds.length} / ${OFS.TRIP_MAX_ORDERS}</div>
        <div class="flex items-center gap-1.5 ${overWeight ? "text-red-600 font-medium" : ""}"><i class="ph ph-scales" aria-hidden="true"></i>Weight: ${t.weightLb.toFixed(1)} / ${OFS.TRIP_MAX_WEIGHT} lb</div>
      </div>
      <div class="text-xs text-brand-900/50 mb-3 space-y-1">
        ${orders.map(o => `<div class="flex items-center justify-between">
          <span>${o.id} · ${o.customer}</span>
          ${isDispatched && (o.status === "Out for Delivery") ? `
            <span class="flex gap-1">
              <button data-deliver="${o.id}" class="text-[11px] font-medium text-emerald-700 bg-emerald-50 hover:bg-emerald-100 rounded-full px-2.5 py-1 cursor-pointer transition-colors duration-200">Delivered</button>
              <button data-fail="${o.id}" class="text-[11px] font-medium text-red-700 bg-red-50 hover:bg-red-100 rounded-full px-2.5 py-1 cursor-pointer transition-colors duration-200">Failed</button>
            </span>` : `<span class="italic">${o.status}</span>`}
        </div>`).join("")}
      </div>
      ${!isDispatched ? `
        <button data-assign-robot="${t.id}" ${robot ? "disabled" : ""} class="w-full mb-2 text-xs font-medium border border-brand-200 hover:border-brand-500 disabled:opacity-40 disabled:cursor-not-allowed rounded-xl px-3 py-2 transition-colors duration-200 cursor-pointer flex items-center justify-center gap-1.5">
          <i class="ph ph-robot" aria-hidden="true"></i>${robot ? "Robot assigned" : "Assign next available Robot"}
        </button>
        <button data-dispatch="${t.id}" ${!robot ? "disabled" : ""} class="w-full text-xs font-medium bg-gold-600 hover:bg-gold-700 disabled:bg-brand-900/20 disabled:cursor-not-allowed text-white rounded-xl px-3 py-2 transition-colors duration-200 cursor-pointer flex items-center justify-center gap-1.5">
          <i class="ph ph-paper-plane-tilt" aria-hidden="true"></i>Confirm load & Dispatch
        </button>` : ""}
    </div>`;
  }).join("");

  document.querySelectorAll("[data-assign-robot]").forEach(btn => {
    btn.addEventListener("click", () => {
      const robots = OFS.getRobots();
      const idle = robots.find(r => r.status === "Idle");
      if (!idle) { OFS.toast("No Robot available — Trip stays in the Robot Queue.", "error"); return; }
      const trips = OFS.getTrips();
      const t = trips.find(x => x.id === btn.dataset.assignRobot);
      t.robot = idle.id;
      idle.status = "Reserved";
      OFS.setTrips(trips);
      OFS.setRobots(robots);
      renderDispatch();
    });
  });

  document.querySelectorAll("[data-dispatch]").forEach(btn => {
    btn.addEventListener("click", () => {
      const trips = OFS.getTrips();
      const t = trips.find(x => x.id === btn.dataset.dispatch);
      t.status = "Out for Delivery";
      const robots = OFS.getRobots();
      const robot = robots.find(r => r.id === t.robot);
      if (robot) robot.status = "Out for Delivery";
      const orders = OFS.getOrders();
      t.orderIds.forEach(id => { const o = orders.find(x => x.id === id); if (o) o.status = "Out for Delivery"; });
      OFS.setTrips(trips);
      OFS.setRobots(robots);
      OFS.setOrders(orders);
      OFS.toast(`${t.id} dispatched`, "success");
      renderDispatch();
    });
  });

  document.querySelectorAll("[data-deliver]").forEach(btn => btn.addEventListener("click", () => resolveStop(btn.dataset.deliver, "Delivered")));
  document.querySelectorAll("[data-fail]").forEach(btn => btn.addEventListener("click", () => resolveStop(btn.dataset.fail, "Delivery Failed")));
}

// Simulates a Robot reporting one stop's result (BR-8 on failure).
function resolveStop(orderId, result) {
  const orders = OFS.getOrders();
  const order = orders.find(o => o.id === orderId);
  order.status = result;
  OFS.setOrders(orders);
  OFS.toast(`${orderId} → ${result}`, result === "Delivered" ? "success" : "error");

  const trips = OFS.getTrips();
  const trip = trips.find(t => t.id === order.tripId);
  if (trip) {
    const stillOut = tripOrders(trip).some(o => o.status === "Out for Delivery");
    if (!stillOut) {
      trip.status = "Completed";
      const robots = OFS.getRobots();
      const robot = robots.find(r => r.id === trip.robot);
      if (robot) robot.status = "Idle"; // robot returns to store, ready for another Trip
      OFS.setRobots(robots);
    }
    OFS.setTrips(trips);
  }
  renderDispatch();
}

// ---------- inventory ----------
function renderInventory() {
  document.getElementById("inventory-body").innerHTML = OFS.PRODUCTS.map(p => {
    const stock = stockFor(p);
    const low = stock <= 15;
    return `
    <tr class="border-t border-brand-50 hover:bg-brand-50/40 transition-colors duration-200">
      <td class="px-4 py-3 flex items-center gap-2.5">
        <span class="w-7 h-7 rounded-lg bg-brand-50 text-brand-700 flex items-center justify-center text-sm shrink-0"><i class="ph ph-${p.icon}" aria-hidden="true"></i></span>
        ${p.name}
      </td>
      <td class="px-4 py-3 text-brand-900/50">${p.category}</td>
      <td class="px-4 py-3 text-right">${OFS.money(p.price)}</td>
      <td class="px-4 py-3 text-right">${p.weightLb} lb</td>
      <td class="px-4 py-3 text-right">
        <div class="inline-flex items-center gap-2">
          ${low ? `<span class="text-[10px] font-medium text-red-600 bg-red-50 rounded-full px-2 py-0.5 flex items-center gap-1"><i class="ph ph-warning" aria-hidden="true"></i>Low</span>` : ""}
          <button data-stock-dec="${p.id}" aria-label="Decrease stock" class="w-7 h-7 rounded-lg border border-brand-200 hover:bg-brand-50 text-xs cursor-pointer transition-colors duration-200">–</button>
          <span class="w-6 text-center">${stock}</span>
          <button data-stock-inc="${p.id}" aria-label="Increase stock" class="w-7 h-7 rounded-lg border border-brand-200 hover:bg-brand-50 text-xs cursor-pointer transition-colors duration-200">+</button>
        </div>
      </td>
    </tr>`;
  }).join("");

  document.querySelectorAll("[data-stock-inc]").forEach(b => b.addEventListener("click", () => {
    const p = OFS.PRODUCTS.find(x => x.id === b.dataset.stockInc);
    setStock(p.id, stockFor(p) + 1);
    renderInventory();
  }));
  document.querySelectorAll("[data-stock-dec]").forEach(b => b.addEventListener("click", () => {
    const p = OFS.PRODUCTS.find(x => x.id === b.dataset.stockDec);
    setStock(p.id, Math.max(0, stockFor(p) - 1));
    renderInventory();
  }));
}

// ---------- reports ----------
function renderReports() {
  const allOrders = OFS.getOrders();
  const delivered = allOrders.filter(o => o.status === "Delivered").length;
  const failed = allOrders.filter(o => o.status === "Delivery Failed").length;
  const total = allOrders.length;
  const successRate = (delivered + failed) ? Math.round((delivered / (delivered + failed)) * 100) : 0;
  const sales = allOrders.reduce((s, o) => s + o.total, 0);

  const tiles = [
    { label: "Sales (today)", value: OFS.money(sales), icon: "currency-dollar" },
    { label: "Orders (today)", value: total, icon: "receipt" },
    { label: "Delivery success rate", value: successRate + "%", icon: "check-circle" },
    { label: "Trip utilization", value: "82%", icon: "chart-line-up" },
  ];
  document.getElementById("reports-tiles").innerHTML = tiles.map(t => `
    <div class="bg-white border border-brand-100 rounded-3xl p-5 shadow-sm shadow-brand-900/5">
      <div class="w-9 h-9 rounded-xl bg-brand-50 text-brand-700 flex items-center justify-center text-base mb-3"><i class="ph ph-${t.icon}" aria-hidden="true"></i></div>
      <div class="text-xs text-brand-900/50 mb-1">${t.label}</div>
      <div class="text-2xl font-display font-bold">${t.value}</div>
    </div>`).join("");
}

// ---------- init ----------
render();

// If the Storefront (or another Staff tab) places/moves an order in another
// tab, reflect it here live without needing a manual refresh.
OFS.onChange(() => {
  const route = currentRoute();
  if (route === "queue") renderQueue();
  if (route === "dispatch") renderDispatch();
  if (route === "reports") renderReports();
});
