const apiRoot = "/api/v1/http";
const state = {
  accessToken: sessionStorage.getItem("accessToken"),
  refreshToken: sessionStorage.getItem("refreshToken"),
  currentUser: null,
  peer: null,
  socket: null,
};

const byId = (id) => document.getElementById(id);

function notify(message) {
  const notice = byId("notice");
  notice.textContent = message;
  notice.hidden = !message;
}

function persistTokens(tokens) {
  state.accessToken = tokens.access_token;
  state.refreshToken = tokens.refresh_token;
  sessionStorage.setItem("accessToken", state.accessToken);
  sessionStorage.setItem("refreshToken", state.refreshToken);
}

async function refreshAccess() {
  if (!state.refreshToken) return false;
  const response = await fetch(`${apiRoot}/auth/refresh`, {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({refresh_token: state.refreshToken}),
  });
  if (!response.ok) return false;
  persistTokens(await response.json());
  return true;
}

async function request(path, options = {}, retry = true) {
  const headers = new Headers(options.headers || {});
  if (state.accessToken) headers.set("Authorization", `Bearer ${state.accessToken}`);
  if (options.body && !(options.body instanceof FormData)) headers.set("Content-Type", "application/json");
  const response = await fetch(`${apiRoot}${path}`, {...options, headers});
  if (response.status === 401 && retry && await refreshAccess()) return request(path, options, false);
  if (!response.ok) {
    const error = await response.json().catch(() => ({detail: "Ошибка запроса"}));
    throw new Error(error.detail || "Ошибка запроса");
  }
  return response.status === 204 ? null : response.json();
}

function showAuthenticated(authenticated) {
  byId("auth").hidden = authenticated;
  byId("nav").hidden = !authenticated;
  if (authenticated) showView("feed");
}

async function showView(view) {
  byId("feed").hidden = view !== "feed";
  byId("chat").hidden = view !== "chat";
  if (view === "feed") await loadPosts();
  if (view === "chat") await loadUsers();
}

function postNode(post) {
  const article = document.createElement("article");
  article.className = "card";
  const own = state.currentUser?.id === post.author_id;
  article.innerHTML = `
    <div class="post-meta"><strong></strong><time></time></div>
    <p class="post-content"></p>
    <div class="post-actions">
      <button data-like>♥ <span></span></button>
      ${own ? "<button data-edit class='quiet'>Изменить</button><button data-delete class='quiet'>Удалить</button>" : ""}
    </div>`;
  article.querySelector("strong").textContent = post.author_name;
  article.querySelector("time").textContent = new Date(post.created_at).toLocaleString();
  article.querySelector(".post-content").textContent = post.content;
  article.querySelector("[data-like] span").textContent = post.likes_count;
  article.querySelector("[data-like]").onclick = async () => {
    const result = await request(`/posts/${post.id}/likes/toggle`, {method: "POST"});
    article.querySelector("[data-like] span").textContent = result.likes_count;
  };
  const edit = article.querySelector("[data-edit]");
  if (edit) edit.onclick = async () => {
    const content = prompt("Новый текст", post.content);
    if (!content) return;
    await request(`/posts/${post.id}`, {method: "PUT", body: JSON.stringify({content})});
    await loadPosts();
  };
  const remove = article.querySelector("[data-delete]");
  if (remove) remove.onclick = async () => {
    await request(`/posts/${post.id}`, {method: "DELETE"});
    await loadPosts();
  };
  return article;
}

async function loadPosts(query = "") {
  const data = await request(`/posts${query ? `?q=${encodeURIComponent(query)}` : ""}`);
  byId("posts").replaceChildren(...data.items.map(postNode));
}

async function loadUsers() {
  const users = await request("/users");
  byId("users").replaceChildren(...users.map((user) => {
    const button = document.createElement("button");
    button.textContent = user.name;
    button.onclick = () => selectPeer(user);
    return button;
  }));
}

function messageNode(message) {
  const node = document.createElement("div");
  node.className = `message${message.sender_id === state.currentUser.id ? " mine" : ""}`;
  node.textContent = message.content;
  return node;
}

async function selectPeer(peer) {
  state.peer = peer;
  byId("peer-name").textContent = peer.name;
  byId("message-form").hidden = false;
  const data = await request(`/messages/${peer.id}`);
  byId("messages").replaceChildren(...data.items.map(messageNode));
}

function connectMessages() {
  state.socket?.close();
  const scheme = location.protocol === "https:" ? "wss" : "ws";
  state.socket = new WebSocket(`${scheme}://${location.host}${apiRoot}/ws/messages`);
  state.socket.onmessage = (event) => {
    const message = JSON.parse(event.data);
    if (message.type !== "message.created" || !state.peer) return;
    const data = message.data;
    if ([data.sender_id, data.recipient_id].includes(state.peer.id)) {
      byId("messages").append(messageNode(data));
    }
  };
}

byId("login-form").onsubmit = async (event) => {
  event.preventDefault();
  const data = new FormData(event.currentTarget);
  const body = new URLSearchParams({username: data.get("email"), password: data.get("password")});
  try {
    const response = await fetch(`${apiRoot}/auth/login`, {method: "POST", body});
    if (!response.ok) throw new Error("Неверный email или пароль");
    const login = await response.json();
    persistTokens(login);
    state.currentUser = login.user;
    notify("");
    showAuthenticated(true);
    connectMessages();
  } catch (error) { notify(error.message); }
};

byId("register-form").onsubmit = async (event) => {
  event.preventDefault();
  const values = Object.fromEntries(new FormData(event.currentTarget));
  try {
    await request("/auth/register", {method: "POST", body: JSON.stringify(values)});
    notify("Аккаунт создан — теперь войдите");
    event.currentTarget.reset();
  } catch (error) { notify(error.message); }
};

byId("post-form").onsubmit = async (event) => {
  event.preventDefault();
  const content = new FormData(event.currentTarget).get("content");
  await request("/posts", {method: "POST", body: JSON.stringify({content})});
  event.currentTarget.reset();
  await loadPosts();
};

byId("search-form").onsubmit = async (event) => {
  event.preventDefault();
  await loadPosts(new FormData(event.currentTarget).get("q"));
};

byId("message-form").onsubmit = async (event) => {
  event.preventDefault();
  const content = new FormData(event.currentTarget).get("content");
  await request("/messages", {method: "POST", body: JSON.stringify({recipient_id: state.peer.id, content})});
  event.currentTarget.reset();
};

byId("logout").onclick = async () => {
  if (state.refreshToken) await request("/auth/logout", {method: "POST", body: JSON.stringify({refresh_token: state.refreshToken})}).catch(() => null);
  sessionStorage.clear();
  state.socket?.close();
  state.accessToken = state.refreshToken = state.currentUser = null;
  showAuthenticated(false);
};

document.querySelectorAll("[data-view]").forEach((button) => {
  button.onclick = () => showView(button.dataset.view).catch((error) => notify(error.message));
});

if (state.accessToken) {
  request("/users/me").then((user) => {
    state.currentUser = user;
    showAuthenticated(true);
    connectMessages();
  }).catch(() => showAuthenticated(false));
}
