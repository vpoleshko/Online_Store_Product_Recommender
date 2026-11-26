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
  recipesTitle: document.getElementById("recipes-title"),
  recipesNote: document.getElementById("recipes-note"),
  recipes: document.getElementById("recipes"),
  pipeline: document.getElementById("pipeline"),
};

const FEATURE_NAMES = {
  knn_sum: "co-purchase strength",
  knn_max: "strongest co-purchase link",
  knn_count: "cart items linked",
  knn_rank: "KNN rank",
  emb_centroid: "embedding similarity",
  emb_max: "closest cart item (embeddings)",
  emb_rank: "embedding rank",
  recipe_score: "recipe score",
  recipe_count: "recipes completed",
  recipe_share: "recipe coverage",
  log_pop: "popularity",
  same_aisle: "same aisle as cart",
  same_dept: "same department",
  cart_size: "cart size",
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

function renderModelRow(product) {
  const wrap = el("div", "model-row");

  const top = el("div", "model-top");
  top.append(el("span", "badge badge-model", `MODEL #${product.model_rank}`));
  top.append(el("span", "model-score", `score ${product.model_score.toFixed(2)}`));
  wrap.append(top);

  const bar = el("div", "score-bar");
  const fill = el("div", "score-fill");
  fill.style.width = `${Math.round((0.15 + 0.85 * product.score_bar) * 100)}%`;
  bar.append(fill);
  wrap.append(bar);

  if (product.knn_rank) {
    const moved = product.knn_rank - product.model_rank;
    const arrow = moved > 0 ? "▲" : moved < 0 ? "▼" : "=";
    const line = el("div", `moved ${moved > 0 ? "up" : moved < 0 ? "down" : ""}`);
    line.textContent = `KNN order #${product.knn_rank} → model #${product.model_rank} ${arrow}`;
    wrap.append(line);
  } else {
    wrap.append(el("div", "moved", "not in KNN list: added by other sources"));
  }

  return wrap;
}

function renderCard(product, { tags = [] } = {}) {
  const card = el("article", "card");

  if (product.model_rank) card.append(renderModelRow(product));

  const category = product.category || product.department || "Other";

  const tile = el("div", "tile");
const imagePath = getProductImage(product);

if (imagePath) {
  const img = document.createElement("img");

  img.src = imagePath;
  img.alt = product.name;
  img.loading = "lazy";

  img.onerror = () => {
    tile.replaceChildren();
    tile.textContent = EMOJI[category] || "🛒";
  };

  tile.append(img);
} else {
  tile.textContent = EMOJI[category] || "🛒";
}

card.append(tile);

  card.append(el("div", "name", product.name));
  card.append(el("div", "meta", category));

  for (const tag of tags) card.append(el("div", `tag tag-${tag.type}`, tag.text));

  if (product.signals && product.signals.length > 0) {
    const list = el("div", "signals");
    for (const signal of product.signals) {
      list.append(el("div", `signal signal-${signal.source}`, signal.text));
    }
    card.append(list);
  }

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

function renderGrid(container, products, tagsOf) {
  container.replaceChildren(...products.map((p) => renderCard(p, { tags: tagsOf ? tagsOf(p) : [] })));
}

function pipelineStep(className, title, lines) {
  const step = el("div", `step ${className}`);
  step.append(el("div", "step-title", title));
  for (const line of lines) step.append(el("div", "step-line", line));
  return step;
}

function renderPipeline(result) {
  const { pipeline, model } = result;
  const root = els.pipeline;
  root.replaceChildren();

  const flow = el("div", "flow");

  flow.append(pipelineStep("step-cart", "Your cart", [`${pipeline.cart_size} item(s)`]));
  flow.append(el("span", "arrow", "→"));

  const sources = el("div", "sources");
  sources.append(pipelineStep("step-knn", "Co-purchase KNN", [`${pipeline.from_knn} candidates`, "what is bought together"]));
  sources.append(pipelineStep("step-embedding", "Text embeddings", [`${pipeline.from_embeddings} candidates`, "what is similar"]));
  sources.append(pipelineStep("step-recipe", "Recipes", [`${pipeline.from_recipes} candidates`, "what completes a dish"]));
  flow.append(sources);
  flow.append(el("span", "arrow", "→"));

  const rule = model.active ? "step-model" : "step-warning";
  flow.append(
    pipelineStep(rule, model.name, [
      `re-ranks ${pipeline.candidates} candidates`,
      `${pipeline.skipped_by_rules} skipped by diversity rules`,
    ])
  );
  flow.append(el("span", "arrow", "→"));
  flow.append(pipelineStep("step-result", "Top picks", [`${result.products.length} products`]));
  root.append(flow);

  if (model.active) {
    const details = el("details", "model-details");
    details.append(el("summary", "", "How the model decides and how good it is"));

    const body = el("div", "model-details-body");

    const weights = el("div", "weights");
    weights.append(el("div", "weights-title", `What the ${model.trees} trees rely on`));
    for (const item of model.importance) {
      const row = el("div", "weight-row");
      row.append(el("span", "weight-name", FEATURE_NAMES[item.feature] || item.feature));
      const bar = el("div", "weight-bar");
      const fill = el("div", "weight-fill");
      fill.style.width = `${Math.round(item.share * 100)}%`;
      bar.append(fill);
      row.append(bar);
      row.append(el("span", "weight-value", `${Math.round(item.share * 100)}%`));
      weights.append(row);
    }
    body.append(weights);

    if (model.evaluation) {
      const table = el("table", "evaluation");
      const header = el("tr");
      ["Held-out test (3000 baskets)", "Precision@5", "NDCG@5"].forEach((h) => header.append(el("th", "", h)));
      table.append(header);
      for (const row of model.evaluation) {
        const tr = el("tr", row.model.startsWith("Hybrid") ? "evaluation-best" : "");
        tr.append(el("td", "", row.model));
        tr.append(el("td", "", row.precision_at_5.toFixed(3)));
        tr.append(el("td", "", row.ndcg_at_5.toFixed(3)));
        table.append(tr);
      }
      body.append(table);
    }

    details.append(body);
    root.append(details);
  } else {
    root.append(el("p", "warning", "The trained ranker is not loaded: showing the simple fallback blend."));
  }

  root.hidden = false;
}

function titleCase(text) {
  return text.replace(/\b[a-z]/g, (c) => c.toUpperCase());
}

function renderRecipe(recipe) {
  const card = el("article", "recipe");

  const head = el("div", "recipe-head");
  head.append(el("span", "badge badge-rule", "RULES"));
  head.append(el("h4", "", titleCase(recipe.name)));
  head.append(el("span", "recipe-meta", `${recipe.minutes} min · ★ ${recipe.rating.toFixed(1)} (${recipe.reviews})`));
  card.append(head);

  const progress = el("div", "progress");
  const bar = el("div", "progress-bar");
  bar.style.width = `${Math.round((recipe.have / recipe.total) * 100)}%`;
  progress.append(bar);
  card.append(progress);

  card.append(
    el(
      "p",
      "muted",
      recipe.have === recipe.total
        ? "You already have everything for this recipe"
        : `${recipe.have} of ${recipe.total} ingredients are in your order`
    )
  );

  const chips = el("div", "chips");
  const missing = [];

  for (const ingredient of recipe.ingredients) {
    if (ingredient.status === "staple") continue;

    if (ingredient.status === "missing" && ingredient.product) {
      const chip = el("button", "chip chip-missing", `+ ${ingredient.name}`);
      chip.title = `Add “${ingredient.product.name}” to the cart`;
      chip.addEventListener("click", () => {
        addToCart(ingredient.product);
        chip.disabled = true;
        chip.className = "chip chip-added";
        chip.textContent = `✓ ${ingredient.name}`;
      });
      chips.append(chip);
      missing.push({ ingredient, chip });
    } else {
      chips.append(el("span", `chip chip-${ingredient.status === "have" ? "have" : "other"}`,
        `${ingredient.status === "have" ? "✓ " : ""}${ingredient.name}`));
    }
  }
  card.append(chips);

  if (missing.length > 0) {
    const all = el("button", "ghost", `Add ${missing.length} missing to cart`);
    all.addEventListener("click", () => {
      missing.forEach(({ chip }) => chip.click());
      all.disabled = true;
    });
    card.append(all);
  }

  if (recipe.steps.length > 0) {
    const details = el("details", "steps");
    details.append(el("summary", "", "How to cook"));
    const list = el("ol");
    recipe.steps.forEach((step) => list.append(el("li", "", step.charAt(0).toUpperCase() + step.slice(1))));
    details.append(list);
    card.append(details);
  }

  return card;
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
    els.status.textContent = query ? "Semantic search: embeddings, word match and popularity" : "";
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
  els.recipes.replaceChildren();
  els.recipesTitle.hidden = true;
  els.recipesNote.hidden = true;
  els.pipeline.hidden = true;
  cart.clear();
  renderCart();
  els.order.showModal();

  try {
    const result = await api("/api/recommend", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ product_ids: ids, k: 10 }),
    });
    els.orderStatus.textContent = "";

    const scores = result.products.map((p) => p.model_score);
    const low = Math.min(...scores);
    const high = Math.max(...scores);
    result.products.forEach((p) => {
      p.score_bar = high > low ? (p.model_score - low) / (high - low) : 1;
    });

    renderPipeline(result);
    renderGrid(els.recs, result.products, (p) => p.reasons.slice(0, 1));

    els.recipesTitle.hidden = result.recipes.length === 0;
    els.recipesNote.hidden = result.recipes.length === 0;
    els.recipes.replaceChildren(...result.recipes.map(renderRecipe));
  } catch (error) {
    els.orderStatus.textContent = `Could not get recommendations: ${error.message}`;
  }
});

els.order.addEventListener("close", loadCatalog);

renderCart();
loadCatalog();
