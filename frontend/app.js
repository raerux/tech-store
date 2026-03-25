const API_BASE = "http://127.0.0.1:8000";

let state = {
  token: localStorage.getItem("access_token") || null,
  user: JSON.parse(localStorage.getItem("user") || "null"),
  page: 1,
  next: null,
  previous: null,
  filters: {
    search: "",
    categoria: "",
    ordering: "-created_at",
    destaque: ""
  }
};

// ---------- Helpers ----------
function authHeaders() {
  return state.token ? { Authorization: `Bearer ${state.token}` } : {};
}

function formatBRL(value) {
  return Number(value).toFixed(2).replace(".", ",");
}

function showMessage(msg) {
  alert(msg);
}

// ---------- Auth ----------
async function login(email, password) {
  const res = await fetch(`${API_BASE}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password })
  });

  const data = await res.json();
  if (!res.ok) throw new Error(data?.message || "Erro no login");

  state.token = data.data.tokens.access;
  state.user = data.data.user;
  localStorage.setItem("access_token", state.token);
  localStorage.setItem("user", JSON.stringify(state.user));
  updateAuthUI();
  showMessage(`Bem-vindo(a), ${state.user.nome}!`);
}

async function register(email, password, nome) {
  const res = await fetch(`${API_BASE}/auth/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password, nome })
  });

  const data = await res.json();

  if (!res.ok) {
    const errors = data?.errors || data;
    if (errors?.email) throw new Error(`Email: ${errors.email.join(" | ")}`);
    if (errors?.password) throw new Error(`Senha: ${errors.password.join(" | ")}`);
    throw new Error("Erro ao cadastrar usuário.");
  }

  return data;
}

function logout() {
  state.token = null;
  state.user = null;
  localStorage.removeItem("access_token");
  localStorage.removeItem("user");
  updateAuthUI();
}

function updateAuthUI() {
  const btnLogout = document.getElementById("btnLogout");
  btnLogout.classList.toggle("hidden", !state.token);
}

// ---------- Categories ----------
async function loadCategories() {
  const res = await fetch(`${API_BASE}/categories`);
  const data = await res.json();

  const categories = Array.isArray(data) ? data : (data.results || []);
  const select = document.getElementById("categorySelect");
  select.innerHTML = `<option value="">Todas</option>`;

  categories.forEach(cat => {
    const opt = document.createElement("option");
    opt.value = cat.id;
    opt.textContent = cat.nome;
    select.appendChild(opt);
  });
}

// ---------- Products ----------
function buildProductsUrl() {
  const params = new URLSearchParams();
  params.set("page", state.page);
  params.set("ordering", state.filters.ordering);

  if (state.filters.search) params.set("search", state.filters.search);
  if (state.filters.categoria) params.set("categoria", state.filters.categoria);
  if (state.filters.destaque !== "") params.set("destaque", state.filters.destaque);

  return `${API_BASE}/products/?${params.toString()}`;
}

async function loadProducts() {
  const url = buildProductsUrl();
  const res = await fetch(url);
  const data = await res.json();

  const products = data.results || data;
  state.next = data.next || null;
  state.previous = data.previous || null;

  document.getElementById("pageInfo").textContent = `Página ${state.page}`;
  renderProducts(products);
}

function renderProducts(products) {
  const grid = document.getElementById("productsGrid");
  grid.innerHTML = "";

  if (!products.length) {
    grid.innerHTML = "<p>Nenhum produto encontrado.</p>";
    return;
  }

  products.forEach(product => {
    const div = document.createElement("div");
    div.className = "card";

    div.innerHTML = `
      <img src="${product.imagem_url || "https://picsum.photos/300/200"}" alt="${product.nome}" />
      <h4>${product.nome}</h4>
      <p>${product.descricao}</p>
      <p><strong>Categoria:</strong> ${product.categoria_nome || product.categoria}</p>
      <p><strong>Estoque:</strong> ${product.estoque}</p>
      <p class="price">R$ ${formatBRL(product.preco)}</p>
      <button data-id="${product.id}">Adicionar ao Carrinho</button>
    `;

    const btn = div.querySelector("button");
    btn.addEventListener("click", () => addToCart(product.id));

    grid.appendChild(div);
  });
}

// ---------- Cart ----------
async function addToCart(productId) {
  if (!state.token) {
    showMessage("Faça login para adicionar ao carrinho.");
    return;
  }

  const quantity = Number(prompt("Quantidade:", "1")) || 1;

  const res = await fetch(`${API_BASE}/cart/`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...authHeaders() },
    body: JSON.stringify({ product: productId, quantidade: quantity })
  });

  const data = await res.json();
  if (!res.ok) {
    showMessage(`Erro ao adicionar ao carrinho: ${JSON.stringify(data)}`);
    return;
  }

  showMessage("Produto adicionado ao carrinho!");
  loadCart();
}

async function loadCart() {
  if (!state.token) return;

  const res = await fetch(`${API_BASE}/cart/`, { headers: { ...authHeaders() } });
  const data = await res.json();
  const items = data.results || data;

  const container = document.getElementById("cartList");
  container.innerHTML = "";

  let total = 0;

  items.forEach(item => {
    const subtotal = Number(item.preco) * Number(item.quantidade);
    total += subtotal;

    const div = document.createElement("div");
    div.className = "cart-item";
    div.innerHTML = `
      <p><strong>${item.product_nome}</strong></p>
      <p>Qtd: ${item.quantidade}</p>
      <p>Preço: R$ ${formatBRL(item.preco)}</p>
      <p>Subtotal: R$ ${formatBRL(subtotal)}</p>
      <button data-act="inc">+1</button>
      <button data-act="dec">-1</button>
      <button data-act="del">Remover</button>
    `;

    div.querySelector('[data-act="inc"]').onclick = () => updateCartItem(item.id, item.quantidade + 1);
    div.querySelector('[data-act="dec"]').onclick = () => {
      if (item.quantidade > 1) updateCartItem(item.id, item.quantidade - 1);
    };
    div.querySelector('[data-act="del"]').onclick = () => deleteCartItem(item.id);

    container.appendChild(div);
  });

  document.getElementById("cartTotal").textContent = formatBRL(total);
}

async function updateCartItem(cartItemId, quantidade) {
  const res = await fetch(`${API_BASE}/cart/${cartItemId}/`, {
    method: "PUT",
    headers: { "Content-Type": "application/json", ...authHeaders() },
    body: JSON.stringify({ quantidade })
  });

  if (!res.ok) {
    const err = await res.json();
    showMessage(`Erro ao atualizar carrinho: ${JSON.stringify(err)}`);
    return;
  }
  loadCart();
}

async function deleteCartItem(cartItemId) {
  const res = await fetch(`${API_BASE}/cart/${cartItemId}/`, {
    method: "DELETE",
    headers: { ...authHeaders() }
  });

  if (!res.ok) {
    const err = await res.json();
    showMessage(`Erro ao remover item: ${JSON.stringify(err)}`);
    return;
  }
  loadCart();
}

// ---------- Orders ----------
async function checkout() {
  if (!state.token) {
    showMessage("Faça login para finalizar pedido.");
    return;
  }

  const res = await fetch(`${API_BASE}/orders`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...authHeaders() },
    body: JSON.stringify({})
  });

  const data = await res.json();
  if (!res.ok) {
    showMessage(`Erro no checkout: ${JSON.stringify(data)}`);
    return;
  }

  showMessage(`Pedido #${data.data.id} criado com sucesso! Total: R$ ${formatBRL(data.data.total)}`);
  loadCart();
  loadOrders();
}

async function loadOrders() {
  if (!state.token) {
    showMessage("Faça login para visualizar pedidos.");
    return;
  }

  const res = await fetch(`${API_BASE}/orders`, { headers: { ...authHeaders() } });
  const data = await res.json();
  const orders = data.results || data;

  const container = document.getElementById("ordersList");
  container.innerHTML = "";

  orders.forEach(order => {
    const details = document.createElement("details");
    details.className = "order-item";

    const itemsHtml = (order.items || [])
      .map(i => `<li>${i.product_nome} - ${i.quantidade} x R$ ${formatBRL(i.preco_unitario)}</li>`)
      .join("");

    details.innerHTML = `
      <summary>Pedido #${order.id} | ${order.status} | Total: R$ ${formatBRL(order.total)}</summary>
      <ul>${itemsHtml}</ul>
      <small>Criado em: ${new Date(order.created_at).toLocaleString("pt-BR")}</small>
    `;

    container.appendChild(details);
  });
}

// ---------- Register Modal ----------
const registerModal = document.getElementById("registerModal");
const btnOpenRegister = document.getElementById("btnOpenRegister");
const btnCancelRegister = document.getElementById("btnCancelRegister");
const btnDoRegister = document.getElementById("btnDoRegister");

function openRegisterModal() {
  registerModal.classList.remove("hidden");
  registerModal.style.display = "flex";
}

function closeRegisterModal() {
  registerModal.classList.add("hidden");
  registerModal.style.display = "none";
}

btnOpenRegister.addEventListener("click", openRegisterModal);
btnCancelRegister.addEventListener("click", closeRegisterModal);

// fecha ao clicar fora da caixa branca
registerModal.addEventListener("click", (e) => {
  if (e.target === registerModal) closeRegisterModal();
});

btnDoRegister.addEventListener("click", async () => {
  try {
    const nome = document.getElementById("registerNome").value.trim();
    const email = document.getElementById("registerEmail").value.trim();
    const password = document.getElementById("registerPassword").value.trim();

    if (!nome || !email || !password) {
      showMessage("Preencha nome, email e senha.");
      return;
    }

    await register(email, password, nome);

    // preenche login automaticamente
    document.getElementById("loginEmail").value = email;
    document.getElementById("loginPassword").value = password;

    // limpa modal
    document.getElementById("registerNome").value = "";
    document.getElementById("registerEmail").value = "";
    document.getElementById("registerPassword").value = "";

    closeRegisterModal();
    showMessage("Cadastro realizado! Agora clique em Login.");
  } catch (e) {
    showMessage(e.message || "Erro no cadastro.");
  }
});

// ---------- Events ----------
document.getElementById("btnLogin").addEventListener("click", async () => {
  try {
    const email = document.getElementById("loginEmail").value.trim();
    const password = document.getElementById("loginPassword").value.trim();

    if (!email || !password) {
      showMessage("Preencha email e senha para login.");
      return;
    }

    await login(email, password);
    await loadCart();
  } catch (e) {
    showMessage(e.message);
  }
});

document.getElementById("btnLogout").addEventListener("click", () => {
  logout();
  document.getElementById("cartList").innerHTML = "";
  document.getElementById("ordersList").innerHTML = "";
  document.getElementById("cartTotal").textContent = "0,00";
});

document.getElementById("btnSearch").addEventListener("click", () => {
  state.page = 1;
  state.filters.search = document.getElementById("searchInput").value.trim();
  loadProducts();
});

document.getElementById("btnApplyFilters").addEventListener("click", () => {
  state.page = 1;
  state.filters.categoria = document.getElementById("categorySelect").value;
  state.filters.ordering = document.getElementById("orderSelect").value;
  loadProducts();
});

document.getElementById("btnDestaques").addEventListener("click", () => {
  state.page = 1;
  state.filters.destaque = "true";
  loadProducts();
});

document.getElementById("btnAll").addEventListener("click", () => {
  state.page = 1;
  state.filters = { search: "", categoria: "", ordering: "-created_at", destaque: "" };
  document.getElementById("searchInput").value = "";
  document.getElementById("categorySelect").value = "";
  document.getElementById("orderSelect").value = "-created_at";
  loadProducts();
});

document.getElementById("prevPage").addEventListener("click", () => {
  if (!state.previous) return;
  state.page -= 1;
  loadProducts();
});

document.getElementById("nextPage").addEventListener("click", () => {
  if (!state.next) return;
  state.page += 1;
  loadProducts();
});

document.getElementById("btnRefreshCart").addEventListener("click", loadCart);
document.getElementById("btnCheckout").addEventListener("click", checkout);
document.getElementById("btnLoadOrders").addEventListener("click", loadOrders);

// ---------- Init ----------
(async function init() {
  updateAuthUI();
  closeRegisterModal(); // garante que inicia fechado
  await loadCategories();
  await loadProducts();
  if (state.token) await loadCart();
})();