const EMOJI = {
  Meat: "🥩",
  Seafood: "🐟",
  Fruit: "🍎",
  Vegetables: "🥦",
  Produce: "🥬",
  Dairy: "🥛",
  Eggs: "🥚",
  Bakery: "🍞",
  Beverages: "🥤",
  Snacks: "🍿",
  Breakfast: "🥣",
  "Frozen Foods": "🧊",
  Pantry: "🥫",
  "Canned Goods": "🥫",
  Deli: "🥪",
  "Pasta & Grains": "🍝",
  Household: "🧽",
  "Personal Care": "🧴",
  "Baby Products": "🍼",
  "Pet Supplies": "🐶",
  "International Foods": "🌍",
  Alcohol: "🍷",
  "Bulk Foods": "📦",
  "Meat & Seafood": "🍽️"
};

const TAGS = {
  purchases: "Often bought together",
  similar: "Similar to your items",
};

const cart = new Map();

const els = {
  search: document.getElementById("search"),
  grid: document.getElementById("grid"),
  title: document.getElementById("catalog-title"),
  status: document.getElementById("status"),
  cartItems: document.getElementById("cart-items"),
  cartEmpty: document.getElementById("cart-empty"),
  cartCount: document.getElementById("cart-count"),
  buy: document.getElementById("buy"),
  order: document.getElementById("order"),
  orderSummary: document.getElementById("order-summary"),
  orderStatus: document.getElementById("order-status"),
  recs: document.getElementById("recs"),
};

async function api(path, options) {
  const response = await fetch(path, options);
  if (!response.ok) {
    throw new Error(`${response.status} ${await response.text()}`);
  }
  return response.json();
}

function hue(text) {
  let h = 0;
  for (const ch of text) h = (h * 31 + ch.charCodeAt(0)) % 360;
  return h;
}

function el(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}

function renderCard(product, { tag } = {}) {
  const card = el("article", "card");

  const category = product.category || product.department || "Other";

  const tile = el("div", "tile", EMOJI[category] || "🛒");
  tile.style.background = `hsl(${hue(category)} 70% 50% / 0.18)`;
  card.append(tile);

  card.append(el("div", "name", product.name));
  card.append(el("div", "meta", category));

  if (tag) card.append(el("div", "tag", tag));
  card.append(el("div", "spacer"));

  const button = el("button", "", cart.has(product.product_id) ? "In cart" : "Add to cart");
  button.disabled = cart.has(product.product_id);
  button.addEventListener("click", () => {
    addToCart(product);
    button.textContent = "In cart";
    button.disabled = true;
  });
  card.append(button);

  return card;
}

function renderGrid(container, products, tagOf) {
  container.replaceChildren(...products.map((p) => renderCard(p, { tag: tagOf ? tagOf(p) : null })));
}

function addToCart(product) {
  cart.set(product.product_id, product);
  renderCart();
}

function removeFromCart(productId) {
  cart.delete(productId);
  renderCart();
  loadCatalog();
}

function renderCart() {
  els.cartItems.replaceChildren(
    ...[...cart.values()].map((product) => {
      const item = el("li");
      item.append(el("span", "label", product.name));
      const remove = el("button", "", "✕");
      remove.setAttribute("aria-label", `Remove ${product.name}`);
      remove.addEventListener("click", () => removeFromCart(product.product_id));
      item.append(remove);
      return item;
    })
  );
  els.cartCount.textContent = cart.size;
  els.cartEmpty.hidden = cart.size > 0;
  els.buy.disabled = cart.size === 0;
}

async function loadCatalog() {
  const query = els.search.value.trim();
  els.status.textContent = "Loading…";
  try {
    const products = await api(query ? `/api/search?q=${encodeURIComponent(query)}&limit=24` : "/api/popular?limit=24");
    els.title.textContent = query ? `Results for “${query}”` : "Popular products";
    els.status.textContent = query ? "Semantic search by product embeddings" : "";
    renderGrid(els.grid, products);
  } catch (error) {
    els.status.textContent = `Could not load products: ${error.message}`;
  }
}

let timer;
els.search.addEventListener("input", () => {
  clearTimeout(timer);
  timer = setTimeout(loadCatalog, 300);
});

els.buy.addEventListener("click", async () => {
  const bought = [...cart.values()];
  const ids = bought.map((p) => p.product_id);

  els.orderSummary.textContent = `You bought: ${bought.map((p) => p.name).join(", ")}`;
  els.orderStatus.textContent = "Finding recommendations…";
  els.recs.replaceChildren();
  cart.clear();
  renderCart();
  els.order.showModal();

  try {
    const recs = await api("/api/recommend", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ product_ids: ids, k: 10 }),
    });
    els.orderStatus.textContent = "";
    renderGrid(els.recs, recs, (p) => TAGS[p.sources[0]]);
  } catch (error) {
    els.orderStatus.textContent = `Could not get recommendations: ${error.message}`;
  }
});

els.order.addEventListener("close", loadCatalog);

renderCart();
loadCatalog();
