// OFS Storefront — click-through prototype logic. No backend, no real payment.

const AUTH_KEY = "auth";
const CART_KEY = "cart";

function getAuth() { return OFS.get(AUTH_KEY, null); }
function setAuth(user) { OFS.set(AUTH_KEY, user); }
function getCart() { return OFS.get(CART_KEY, []); }
function setCart(cart) { OFS.set(CART_KEY, cart); renderCartBadge(); }

const PUBLIC_ROUTES = ["login", "register"];

// ---------- routing ----------
function currentRoute() {
  const hash = location.hash.replace(/^#\//, "") || "";
  return hash.split("/")[0] || (getAuth() ? "browse" : "login");
}

function render() {
  const route = currentRoute();
  const auth = getAuth();
  const nav = document.getElementById("nav");

  if (!auth && !PUBLIC_ROUTES.includes(route)) {
    location.hash = "#/login";
    return;
  }
  if (auth && PUBLIC_ROUTES.includes(route)) {
    location.hash = "#/browse";
    return;
  }

  nav.classList.toggle("hidden", !auth);
  if (auth) {
    document.getElementById("nav-user").textContent = auth.name;
    document.querySelectorAll("[data-nav]").forEach(el => {
      const active = el.dataset.nav === route;
      el.classList.toggle("bg-brand-50", active);
      el.classList.toggle("text-brand-700", active);
      el.classList.toggle("text-brand-900/60", !active);
    });
  }

  document.querySelectorAll("[data-route]").forEach(el => {
    el.dataset.active = String(el.dataset.route === route);
  });

  if (route === "browse") renderBrowse();
  if (route === "cart") renderCart();
  if (route === "checkout") renderCheckoutTotal();
  if (route === "track") renderTrack();
  renderCartBadge();
}

window.addEventListener("hashchange", render);

// ---------- login / register ----------
document.getElementById("login-form").addEventListener("submit", (e) => {
  e.preventDefault();
  const form = new FormData(e.target);
  const email = form.get("email").trim().toLowerCase();
  const password = form.get("password");
  const match = Object.values(OFS.USERS).find(u => u.role === "Customer" && u.email === email && u.password === password);
  const errEl = document.getElementById("login-error");
  if (!match) {
    errEl.querySelector("span").textContent = "Incorrect email or password.";
    errEl.classList.remove("hidden");
    return;
  }
  errEl.classList.add("hidden");
  setAuth(match);
  OFS.toast(`Welcome back, ${match.name.split(" ")[0]}`, "success");
  location.hash = "#/browse";
});

document.getElementById("register-form").addEventListener("submit", (e) => {
  e.preventDefault();
  const form = new FormData(e.target);
  const user = { role: "Customer", name: form.get("name"), email: form.get("email").trim().toLowerCase() };
  setAuth(user);
  OFS.toast(`Account created — welcome, ${user.name.split(" ")[0]}`, "success");
  location.hash = "#/browse";
});

document.getElementById("logout-btn").addEventListener("click", () => {
  setAuth(null);
  location.hash = "#/login";
});

// ---------- browse ----------
let activeCategory = "All";

function renderCategoryFilters() {
  const cats = ["All", ...new Set(OFS.PRODUCTS.map(p => p.category))];
  const host = document.getElementById("category-filters");
  host.innerHTML = cats.map(c => `
    <button data-cat="${c}" class="cat-btn px-3 py-1.5 rounded-full text-xs font-medium border transition-colors duration-200 cursor-pointer flex items-center gap-1.5
      ${c === activeCategory ? "bg-brand-600 text-white border-brand-600" : "bg-white text-brand-900/60 border-brand-200 hover:border-brand-400"}">
      ${c !== "All" ? `<i class="ph ph-${OFS.CATEGORY_ICON[c] || "package"} text-sm" aria-hidden="true"></i>` : ""}${c}
    </button>`).join("");
  host.querySelectorAll(".cat-btn").forEach(btn => {
    btn.addEventListener("click", () => { activeCategory = btn.dataset.cat; renderBrowse(); });
  });
}

function renderBrowse() {
  renderCategoryFilters();
  const cart = getCart();
  const products = activeCategory === "All" ? OFS.PRODUCTS : OFS.PRODUCTS.filter(p => p.category === activeCategory);
  document.getElementById("product-grid").innerHTML = products.map(p => {
    const inCart = cart.find(l => l.id === p.id);
    const outOfStock = p.stock <= 0;
    return `
    <div class="bg-white border border-brand-100 rounded-3xl p-4 flex flex-col gap-2 hover:shadow-md hover:shadow-brand-900/5 transition-shadow duration-200">
      <div class="w-10 h-10 rounded-2xl bg-brand-50 text-brand-700 flex items-center justify-center text-xl"><i class="ph ph-${p.icon}" aria-hidden="true"></i></div>
      <div class="font-medium text-sm leading-snug">${p.name}</div>
      <div class="text-xs text-brand-900/50">${p.weightLb} lb · ${p.category}</div>
      <div class="flex items-center justify-between mt-1">
        <span class="font-semibold">${OFS.money(p.price)}</span>
        ${outOfStock
          ? `<span class="text-xs text-red-600 font-medium">Out of stock</span>`
          : `<button data-add="${p.id}" class="text-xs font-medium bg-brand-600 hover:bg-brand-700 text-white rounded-full px-3 py-1.5 transition-colors duration-200 cursor-pointer">
              ${inCart ? `In cart (${inCart.qty})` : "Add"}
            </button>`}
      </div>
    </div>`;
  }).join("");

  document.querySelectorAll("[data-add]").forEach(btn => {
    btn.addEventListener("click", () => {
      const id = btn.dataset.add;
      const cart = getCart();
      const line = cart.find(l => l.id === id);
      if (line) line.qty += 1; else cart.push({ id, qty: 1 });
      setCart(cart);
      OFS.toast("Added to cart", "success");
      renderBrowse();
    });
  });
}

// ---------- cart ----------
function renderCart() {
  const cart = getCart();
  document.getElementById("cart-empty").classList.toggle("hidden", cart.length > 0);
  document.getElementById("cart-body").classList.toggle("hidden", cart.length === 0);
  if (cart.length === 0) return;

  document.getElementById("cart-lines").innerHTML = cart.map(line => {
    const p = OFS.PRODUCTS.find(p => p.id === line.id);
    return `
    <div class="bg-white border border-brand-100 rounded-2xl p-4 flex items-center gap-4">
      <div class="w-9 h-9 rounded-xl bg-brand-50 text-brand-700 flex items-center justify-center text-lg shrink-0"><i class="ph ph-${p.icon}" aria-hidden="true"></i></div>
      <div class="flex-1">
        <div class="font-medium text-sm">${p.name}</div>
        <div class="text-xs text-brand-900/50">${OFS.money(p.price)} · ${p.weightLb} lb each</div>
      </div>
      <div class="flex items-center gap-2">
        <button data-dec="${p.id}" aria-label="Decrease quantity" class="w-8 h-8 rounded-lg border border-brand-200 text-sm hover:bg-brand-50 cursor-pointer transition-colors duration-200">–</button>
        <span class="w-6 text-center text-sm">${line.qty}</span>
        <button data-inc="${p.id}" aria-label="Increase quantity" class="w-8 h-8 rounded-lg border border-brand-200 text-sm hover:bg-brand-50 cursor-pointer transition-colors duration-200">+</button>
      </div>
      <button data-remove="${p.id}" aria-label="Remove ${p.name}" class="text-brand-900/40 hover:text-red-600 text-sm cursor-pointer transition-colors duration-200"><i class="ph ph-trash" aria-hidden="true"></i></button>
    </div>`;
  }).join("");

  const weight = OFS.calcWeight(cart);
  const subtotal = OFS.calcSubtotal(cart);
  const fee = OFS.calcFee(weight);
  const overweight = OFS.isOverweight(weight);

  document.getElementById("sum-subtotal").textContent = OFS.money(subtotal);
  document.getElementById("sum-weight").textContent = weight.toFixed(1) + " lb";
  document.getElementById("sum-fee").textContent = OFS.money(fee);
  document.getElementById("sum-total").textContent = OFS.money(subtotal + fee);
  document.getElementById("fee-hint").textContent = fee > 0
    ? "Order is 20 lb or more — $10 Delivery Fee applies. (BR-1)"
    : "Under 20 lb — free delivery. (BR-1)";
  document.getElementById("overweight-banner").classList.toggle("hidden", !overweight);
  document.getElementById("checkout-btn").disabled = overweight;

  document.querySelectorAll("[data-inc]").forEach(b => b.addEventListener("click", () => bumpQty(b.dataset.inc, 1)));
  document.querySelectorAll("[data-dec]").forEach(b => b.addEventListener("click", () => bumpQty(b.dataset.dec, -1)));
  document.querySelectorAll("[data-remove]").forEach(b => b.addEventListener("click", () => {
    setCart(getCart().filter(l => l.id !== b.dataset.remove));
    renderCart();
  }));
}

function bumpQty(id, delta) {
  const cart = getCart();
  const line = cart.find(l => l.id === id);
  if (!line) return;
  line.qty += delta;
  const next = cart.filter(l => l.qty > 0);
  setCart(next);
  renderCart();
}

document.getElementById("checkout-btn").addEventListener("click", () => {
  location.hash = "#/checkout";
});

function renderCartBadge() {
  const cart = getCart();
  const count = cart.reduce((n, l) => n + l.qty, 0);
  const badge = document.getElementById("cart-badge");
  badge.textContent = count;
  badge.classList.toggle("hidden", count === 0);
  badge.classList.toggle("flex", count > 0);

  // Sticky bottom cart bar (Uber/DoorDash pattern): only on Browse, only with items.
  const bar = document.getElementById("sticky-cart-bar");
  const showBar = count > 0 && currentRoute() === "browse";
  bar.classList.toggle("hidden", !showBar);
  bar.classList.toggle("flex", showBar);
  if (showBar) {
    const subtotal = OFS.calcSubtotal(cart);
    document.getElementById("sticky-cart-text").textContent = `${count} item${count > 1 ? "s" : ""} · ${OFS.money(subtotal)}`;
  }
}

// ---------- checkout ----------
function renderCheckoutTotal() {
  document.getElementById("checkout-address").classList.remove("hidden");
  document.getElementById("checkout-payment").classList.add("hidden");
  document.getElementById("checkout-step-num").textContent = "1";
  document.getElementById("address-error").classList.add("hidden");
  document.getElementById("payment-error").classList.add("hidden");
  const cart = getCart();
  const weight = OFS.calcWeight(cart);
  const subtotal = OFS.calcSubtotal(cart);
  const fee = OFS.calcFee(weight);
  document.getElementById("checkout-total").textContent = OFS.money(subtotal + fee);
}

document.getElementById("validate-address-btn").addEventListener("click", () => {
  const street = document.getElementById("addr-street").value.trim();
  const errEl = document.getElementById("address-error");
  if (!street) {
    errEl.querySelector("span").textContent = "Enter a delivery address.";
    errEl.classList.remove("hidden");
    return;
  }
  const inZone = street.toLowerCase().includes(OFS.DELIVERY_ZONE_HINT);
  if (!inZone) {
    errEl.querySelector("span").textContent = "This address is outside the Downtown San Jose Delivery Zone. (BR-5)";
    errEl.classList.remove("hidden");
    return;
  }
  errEl.classList.add("hidden");
  document.getElementById("checkout-address").classList.add("hidden");
  document.getElementById("checkout-payment").classList.remove("hidden");
  document.getElementById("checkout-step-num").textContent = "2";
});

document.getElementById("back-to-address-btn").addEventListener("click", () => {
  document.getElementById("checkout-payment").classList.add("hidden");
  document.getElementById("checkout-address").classList.remove("hidden");
  document.getElementById("checkout-step-num").textContent = "1";
});

document.getElementById("pay-btn").addEventListener("click", () => {
  const card = document.getElementById("card-number").value.replace(/\s/g, "");
  const errEl = document.getElementById("payment-error");
  if (card === "4000000000000002") {
    errEl.querySelector("span").textContent = "Card declined. Try again or use a different card.";
    errEl.classList.remove("hidden");
    return;
  }
  if (card !== "4242424242424242") {
    errEl.querySelector("span").textContent = "Enter a valid test card number (see hint above).";
    errEl.classList.remove("hidden");
    return;
  }
  errEl.classList.add("hidden");

  const cart = getCart();
  const weight = OFS.calcWeight(cart);
  const fee = OFS.calcFee(weight);
  const subtotal = OFS.calcSubtotal(cart);
  const auth = getAuth();
  const orderId = OFS.nextOrderId();
  const order = {
    id: orderId,
    customer: auth.name,
    customerEmail: auth.email,
    status: "Placed",
    weightLb: weight,
    fee,
    total: subtotal + fee,
    placedAt: "Just now",
    tripId: null,
  };

  OFS.setOrders([order, ...OFS.getOrders()]);
  setCart([]);
  document.getElementById("addr-street").value = "";
  document.getElementById("card-number").value = "";
  OFS.toast(`Order ${orderId} placed!`, "success");
  location.hash = "#/track";
});

// ---------- track ----------
// Timeline pattern borrows from DoorDash (icon steps + filled progress line);
// the active-order hero card borrows from Uber (full-bleed map, floating ETA sheet).
const STATUS_STEPS = [
  { key: "Placed", icon: "receipt" },
  { key: "Planned", icon: "package" },
  { key: "Out for Delivery", icon: "robot" },
  { key: "Delivered", icon: "check-circle" },
];

function statusTimeline(status) {
  if (status === "Delivery Failed") {
    return `<div class="text-sm text-red-600 font-medium flex items-center gap-2">
      <i class="ph ph-warning-circle text-base" aria-hidden="true"></i>
      Delivery Failed — order returned to store, you've been notified. (BR-8)
    </div>`;
  }
  const idx = STATUS_STEPS.findIndex(s => s.key === status);
  return `<div class="flex items-center">${STATUS_STEPS.map((s, i) => `
    <div class="flex items-center ${i < STATUS_STEPS.length - 1 ? "flex-1" : ""}">
      <div class="flex flex-col items-center gap-1 shrink-0">
        <div class="w-7 h-7 rounded-full flex items-center justify-center text-xs ${i <= idx ? "bg-brand-600 text-white" : "bg-brand-100 text-brand-900/30"}">
          <i class="ph ph-${s.icon}" aria-hidden="true"></i>
        </div>
        <span class="text-[10px] ${i <= idx ? "text-brand-700 font-medium" : "text-brand-900/40"} text-center leading-tight w-14">${s.key}</span>
      </div>
      ${i < STATUS_STEPS.length - 1 ? `<div class="flex-1 h-0.5 -mt-4 ${i < idx ? "bg-brand-600" : "bg-brand-100"}"></div>` : ""}
    </div>`).join("")}</div>`;
}

function renderTrack() {
  const auth = getAuth();
  const orders = OFS.getOrders().filter(o => o.customerEmail === auth.email);
  const host = document.getElementById("track-list");


  if (orders.length === 0) {
    host.innerHTML = `<div class="text-brand-900/50 py-16 text-center border-2 border-dashed border-brand-200 rounded-3xl">
      <i class="ph ph-truck text-3xl mb-2 block" aria-hidden="true"></i>
      No orders yet. <a href="#/browse" class="text-brand-700 font-medium hover:underline">Go shopping →</a>
    </div>`;
    return;F
  }

  const active = orders.find(o => o.status === "Out for Delivery");
  const rest = orders.filter(o => o !== active);

  let activeTrip = null;
  let activeRobot = null;

  if (active && active.tripId) {
    activeTrip = OFS.getTrips().find(
        t => t.id === active.tripId
    );

    if (activeTrip && activeTrip.robot) {
      activeRobot = OFS.getRobots().find(
          r => r.id === activeTrip.robot
      );
    }
  }

  const robotProgress = activeRobot?.progress ?? 0;
  const robotLeft = Math.min(85, Math.max(15, 15 + robotProgress * 0.7));

  const heroCard = active ? `
    <div class="relative rounded-3xl overflow-hidden border border-brand-100 shadow-sm shadow-brand-900/5 mb-5">
      <div class="relative h-40 bg-brand-100" style="background-image: radial-gradient(circle, rgba(21,128,61,0.15) 1px, transparent 1px); background-size: 10px 10px;">
        <div class="map-dot absolute w-4 h-4 bg-brand-700 rounded-full border-2 border-white shadow" style="top: 38%; left: ${robotLeft}%;"></div>
        <div class="absolute w-2 h-2 bg-brand-900/30 rounded-full" style="top: 65%; left: 20%;" aria-hidden="true"></div>
        <div class="absolute top-3 left-3 bg-white/90 backdrop-blur text-xs font-medium text-brand-900 rounded-full px-3 py-1 flex items-center gap-1.5 shadow-sm">
          <i class="ph ph-robot text-brand-600" aria-hidden="true"></i> Robot en route
        </div>
      </div>
      <div class="bg-white p-4 flex items-center justify-between">
        <div>
          <div class="font-display font-semibold">${active.id}</div>
          <div class="text-xs text-brand-900/50">${active.weightLb.toFixed(1)} lb · ${OFS.money(active.total)}</div>
        </div>
        <div class="text-right">
          <div class="text-xs text-brand-900/50">Arriving in</div>
          <div class="font-display font-bold text-brand-700">
            ${activeRobot?.etaMinutes ?? "--"} min
          </div>
          <div class="text-xs text-brand-900/50 mt-1">
            ${activeRobot
              ? `${activeRobot.id} · ${activeRobot.status}`
              : "Waiting for robot"}
          </div>
        </div>
      </div>
      <div class="bg-white px-4 pb-4">${statusTimeline(active.status)}</div>
    </div>` : "";

  const cards = rest.map(o => `
    <div class="bg-white border border-brand-100 rounded-3xl p-5">
      <div class="flex items-center justify-between mb-4 flex-wrap gap-2">
        <div>
          <div class="font-semibold">${o.id}</div>
          <div class="text-xs text-brand-900/50">${o.placedAt} · ${o.weightLb.toFixed(1)} lb · ${OFS.money(o.total)}</div>
        </div>
      </div>
      ${statusTimeline(o.status)}
    </div>`).join("");

  host.innerHTML = heroCard + `<div class="space-y-4">${cards}</div>`;
}

// ---------- init ----------
render();

// If the Staff Dashboard is open in another tab and moves one of this
// customer's orders along (Prepared, Dispatched, Delivered...), reflect it
// here without needing a manual refresh.
OFS.onChange(() => { if (currentRoute() === "track") renderTrack(); if (currentRoute() === "cart") renderCart(); });
