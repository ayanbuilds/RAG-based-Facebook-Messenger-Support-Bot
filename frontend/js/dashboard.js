// const API_BASE = "http://127.0.0.1:8000";
// const SUPABASE_URL = "https://ubuoxjcewqnaeelxdcom.supabase.co";
// const SUPABASE_ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InVidW94amNld3FuYWVlbHhkY29tIiwicm9sZSI6ImFub24iLCJpYXQiOjE3Njc4NTgzMzcsImV4cCI6MjA4MzQzNDMzN30.nhjABZl0MO3Im64V9ntHMYUBVqfqNsvijlOAMn3cQDw";


// if (localStorage.getItem("is_admin") !== "true") {
//   window.location.href = "login.html";
// }

// const sb = supabase.createClient(SUPABASE_URL, SUPABASE_ANON_KEY);

// const badgeEl = document.getElementById("badge");
// const convListEl = document.getElementById("conversations");
// const filterEl = document.getElementById("filter");
// const btnRefresh = document.getElementById("btnRefresh");

// const chatEl = document.getElementById("chat");
// const convIdEl = document.getElementById("convId");
// const btnOpen = document.getElementById("btnOpen");

// const btnNeedHuman = document.getElementById("btnNeedHuman");
// const btnBotActive = document.getElementById("btnBotActive");
// const btnResolved = document.getElementById("btnResolved");

// const replyEl = document.getElementById("reply");
// const btnSend = document.getElementById("btnSend");
// const rtStatus = document.getElementById("rtStatus");
// const btnLogout = document.getElementById("btnLogout");

// let msgChannel = null;
// let convChannel = null;
// let currentConversationId = null;

// btnLogout.addEventListener("click", () => {
//   localStorage.removeItem("is_admin");
//   window.location.href = "login.html";
// });

// function escapeHtml(str) {
//   return String(str).replace(/[&<>"']/g, (s) => ({
//     "&":"&amp;","<":"&lt;",">":"&gt;", "\"":"&quot;","'":"&#039;"
//   }[s]));
// }

// function addBubble(m) {
//   const div = document.createElement("div");
//   div.className = `bubble ${m.direction === "inbound" ? "left" : "right"}`;
//   div.innerHTML = `<div><b>${escapeHtml(m.sender_type)}</b>: ${escapeHtml(m.content)}</div>
//                    <div class="meta">${m.created_at || ""}</div>`;
//   chatEl.appendChild(div);
//   chatEl.scrollTop = chatEl.scrollHeight;
// }

// async function fetchConversations() {
//   const res = await fetch(`${API_BASE}/api/conversations`);
//   const data = await res.json();
//   return Array.isArray(data) ? data : [];
// }

// function renderConversations(list) {
//   convListEl.innerHTML = "";
//   const f = filterEl.value;

//   const filtered = list.filter(c => (f === "ALL" ? true : c.status === f));

//   for (const c of filtered) {
//     const item = document.createElement("div");
//     item.className = "list-item";
//     item.innerHTML = `
//       <div><b>#${c.id}</b> <span class="muted">${escapeHtml(c.status)}</span></div>
//       <div class="muted">Customer: ${c.customer_id}</div>
//     `;
//     item.addEventListener("click", () => {
//       convIdEl.value = c.id;
//       openConversation(String(c.id));
//     });
//     convListEl.appendChild(item);
//   }
// }

// async function refreshInbox() {
//   const convs = await fetchConversations();
//   const needsHumanCount = convs.filter(c => c.status === "NEEDS_HUMAN").length;
//   badgeEl.textContent = `Needs Human: ${needsHumanCount}`;
//   renderConversations(convs);
// }

// btnRefresh.addEventListener("click", refreshInbox);
// filterEl.addEventListener("change", refreshInbox);

// async function loadMessages(conversationId) {
//   chatEl.innerHTML = "";
//   const res = await fetch(`${API_BASE}/api/conversations/${conversationId}/messages`);
//   const data = await res.json();
//   (Array.isArray(data) ? data : []).forEach(addBubble);
// }

// function startMessageRealtime(conversationId) {
//   if (msgChannel) sb.removeChannel(msgChannel);

//   msgChannel = sb
//     .channel(`messages:${conversationId}`)
//     .on(
//       "postgres_changes",
//       {
//         event: "INSERT",
//         schema: "public",
//         table: "messages",
//         filter: `conversation_id=eq.${conversationId}`,
//       },
//       (payload) => {
//         const m = payload.new;
//         addBubble({
//           id: m.id,
//           direction: m.direction,
//           sender_type: m.sender_type,
//           content: m.content,
//           created_at: m.created_at,
//         });
//       }
//     )
//     .subscribe((status) => {
//       rtStatus.textContent = `Realtime: ${status}`;
//     });
// }

// function startConversationRealtime() {
//   if (convChannel) sb.removeChannel(convChannel);

//   convChannel = sb
//     .channel("conversations_changes")
//     .on(
//       "postgres_changes",
//       { event: "*", schema: "public", table: "conversations" },
//       () => {
//         // Any status change -> refresh inbox count/list
//         refreshInbox();
//       }
//     )
//     .subscribe();
// }

// async function openConversation(conversationId) {
//   currentConversationId = conversationId;
//   await loadMessages(conversationId);
//   startMessageRealtime(conversationId);
// }

// btnOpen.addEventListener("click", () => {
//   const id = convIdEl.value.trim();
//   if (!id) return;
//   openConversation(id);
// });

// async function setStatus(status) {
//   if (!currentConversationId) return;
//   await fetch(`${API_BASE}/api/admin/conversations/${currentConversationId}/status?status=${encodeURIComponent(status)}`, {
//     method: "POST",
//   });
//   await refreshInbox();
// }

// btnNeedHuman.addEventListener("click", () => setStatus("NEEDS_HUMAN"));
// btnBotActive.addEventListener("click", () => setStatus("BOT_ACTIVE"));
// btnResolved.addEventListener("click", () => setStatus("RESOLVED"));

// btnSend.addEventListener("click", async () => {
//   if (!currentConversationId) return;
//   const content = replyEl.value.trim();
//   if (!content) return;

//   await fetch(`${API_BASE}/api/admin/conversations/${currentConversationId}/reply?content=${encodeURIComponent(content)}`, {
//     method: "POST",
//   });

//   replyEl.value = "";
// });

// startConversationRealtime();
// refreshInbox();
//  upar wale code tak sab perfect just removed search bar

// ------------------------------------------------------------------------------------------------------------------------------------------------

// const API_BASE = "http://127.0.0.1:8000";
// const SUPABASE_URL = "https://ubuoxjcewqnaeelxdcom.supabase.co";
// const SUPABASE_ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InVidW94amNld3FuYWVlbHhkY29tIiwicm9sZSI6ImFub24iLCJpYXQiOjE3Njc4NTgzMzcsImV4cCI6MjA4MzQzNDMzN30.nhjABZl0MO3Im64V9ntHMYUBVqfqNsvijlOAMn3cQDw";
// ------------------------------------------------------------------------------------------------------------------------------------------------

// const { API_BASE, SUPABASE_URL, SUPABASE_ANON_KEY } = window.APP_CONFIG;
// const sb = supabase.createClient(SUPABASE_URL, SUPABASE_ANON_KEY);

// // -------------------------
// // Auth guard
// // -------------------------
// async function requireAuth() {
//   const { data } = await sb.auth.getSession();
//   if (!data.session) {
//     location.replace("login.html");
//     return null;
//   }
//   return data.session;
// }

// // Prevent bfcache/back-forward access
// window.addEventListener("pageshow", async () => {
//   await requireAuth();
// });

// // -------------------------
// // DOM elements (new layout)
// // -------------------------
// const badgeEl = document.getElementById("badge");
// const convListEl = document.getElementById("conversations");
// const filterEl = document.getElementById("filter");
// const searchEl = document.getElementById("search");
// const btnRefresh = document.getElementById("btnRefresh");

// const chatEl = document.getElementById("chat");
// const chatTitleEl = document.getElementById("chatTitle");
// const statusPillEl = document.getElementById("statusPill");
// const chatSubEl = document.getElementById("chatSub");

// const btnNeedHuman = document.getElementById("btnNeedHuman");
// const btnBotActive = document.getElementById("btnBotActive");
// const btnResolved = document.getElementById("btnResolved");

// const replyEl = document.getElementById("reply");
// const btnSend = document.getElementById("btnSend");
// const rtStatus = document.getElementById("rtStatus");
// const btnLogout = document.getElementById("btnLogout");

// // -------------------------
// // State
// // -------------------------
// let msgChannel = null;
// let convChannel = null;
// let currentConversationId = null;
// let lastConversations = [];

// // -------------------------
// // Logout
// // -------------------------
// btnLogout.addEventListener("click", async () => {
//   await sb.auth.signOut();
//   location.replace("login.html");
// });

// // -------------------------
// // Helpers
// // -------------------------
// function escapeHtml(str) {
//   return String(str).replace(/[&<>"']/g, (s) => ({
//     "&": "&amp;",
//     "<": "&lt;",
//     ">": "&gt;",
//     "\"": "&quot;",
//     "'": "&#039;"
//   }[s]));
// }

// function setActionsEnabled(enabled) {
//   btnNeedHuman.disabled = !enabled;
//   btnBotActive.disabled = !enabled;
//   btnResolved.disabled = !enabled;
//   btnSend.disabled = !enabled;
//   replyEl.disabled = !enabled;
// }

// function setChatHeader(conv) {
//   if (!conv) {
//     chatTitleEl.textContent = "Select a conversation";
//     statusPillEl.textContent = "—";
//     chatSubEl.textContent = "";
//     return;
//   }
//   chatTitleEl.textContent = `Conversation #${conv.id}`;
//   statusPillEl.textContent = conv.status || "—";
//   chatSubEl.textContent = conv.customer_name
//     ? `Customer: ${conv.customer_name}`
//     : `Customer ID: ${conv.customer_id}`;
// }

// function addMessageBubble(m) {
//   // Matches new dashboard.css classes: .msg, .inbound, .outbound
//   const div = document.createElement("div");
//   const cls = m.direction === "inbound" ? "inbound" : "outbound";
//   div.className = `msg ${cls}`;
//   div.innerHTML = `
//     <div><b>${escapeHtml(m.sender_type)}</b>: ${escapeHtml(m.content)}</div>
//     <div class="meta">${m.created_at || ""}</div>
//   `;
//   chatEl.appendChild(div);
//   chatEl.scrollTop = chatEl.scrollHeight;
// }

// // -------------------------
// // API
// // -------------------------
// async function fetchConversations() {
//   const res = await fetch(`${API_BASE}/api/conversations`);
//   const data = await res.json();
//   return Array.isArray(data) ? data : [];
// }

// async function loadMessages(conversationId) {
//   chatEl.innerHTML = "";
//   const res = await fetch(`${API_BASE}/api/conversations/${conversationId}/messages`);
//   const data = await res.json();
//   (Array.isArray(data) ? data : []).forEach(addMessageBubble);
// }

// // -------------------------
// // Sidebar render + search/filter
// // -------------------------
// function renderConversations(list) {
//   convListEl.innerHTML = "";

//   const f = (filterEl?.value || "ALL").trim();
//   const q = (searchEl?.value || "").trim().toLowerCase();

//   const filtered = list.filter(c => {
//     const statusOk = (f === "ALL") ? true : c.status === f;
//     if (!statusOk) return false;

//     if (!q) return true;

//     const hay = [
//       String(c.id),
//       String(c.customer_id),
//       String(c.customer_name || ""),
//       String(c.status || "")
//     ].join(" ").toLowerCase();

//     return hay.includes(q);
//   });

//   for (const c of filtered) {
//     const item = document.createElement("div");
//     item.className = "conv-item";
//     item.innerHTML = `
//       <div class="conv-top">
//         <div class="conv-id">#${c.id}</div>
//         <div class="status-pill">${escapeHtml(c.status || "")}</div>
//       </div>
//       <div class="conv-meta">${escapeHtml(c.customer_name || ("Customer " + c.customer_id))}</div>
//     `;

//     item.addEventListener("click", () => openConversation(String(c.id), c));
//     convListEl.appendChild(item);
//   }
// }

// async function refreshInbox() {
//   const convs = await fetchConversations();
//   lastConversations = convs;

//   const needsHumanCount = convs.filter(c => c.status === "NEEDS_HUMAN").length;
//   badgeEl.textContent = `Needs Human: ${needsHumanCount}`;

//   renderConversations(convs);

//   // Keep header status synced if current conversation exists
//   if (currentConversationId) {
//     const current = convs.find(x => String(x.id) === String(currentConversationId));
//     if (current) setChatHeader(current);
//   }
// }

// // UI listeners
// btnRefresh.addEventListener("click", refreshInbox);
// filterEl.addEventListener("change", () => renderConversations(lastConversations));
// searchEl.addEventListener("input", () => renderConversations(lastConversations));

// // -------------------------
// // Realtime
// // -------------------------
// function startMessageRealtime(conversationId) {
//   if (msgChannel) sb.removeChannel(msgChannel);

//   msgChannel = sb
//     .channel(`messages:${conversationId}`)
//     .on(
//       "postgres_changes",
//       {
//         event: "INSERT",
//         schema: "public",
//         table: "messages",
//         filter: `conversation_id=eq.${conversationId}`,
//       },
//       (payload) => {
//         const m = payload.new;
//         addMessageBubble({
//           id: m.id,
//           direction: m.direction,
//           sender_type: m.sender_type,
//           content: m.content,
//           created_at: m.created_at,
//         });
//       }
//     )
//     .subscribe((status) => {
//       rtStatus.textContent = `Realtime: ${status}`;
//     });
// }

// function startConversationRealtime() {
//   if (convChannel) sb.removeChannel(convChannel);

//   convChannel = sb
//     .channel("conversations_changes")
//     .on(
//       "postgres_changes",
//       { event: "*", schema: "public", table: "conversations" },
//       () => {
//         // Any status change -> refresh inbox list + badge + header sync
//         refreshInbox();
//       }
//     )
//     .subscribe();
// }

// // -------------------------
// // Open conversation
// // -------------------------
// async function openConversation(conversationId, convObj = null) {
//   currentConversationId = conversationId;

//   // Update header (use convObj if provided)
//   if (convObj) {
//     setChatHeader(convObj);
//   } else {
//     const current = lastConversations.find(x => String(x.id) === String(conversationId));
//     setChatHeader(current || null);
//   }

//   setActionsEnabled(true);
//   await loadMessages(conversationId);
//   startMessageRealtime(conversationId);
// }

// // -------------------------
// // Admin actions (token-protected)
// // -------------------------
// async function getTokenOrRedirect() {
//   const { data } = await sb.auth.getSession();
//   if (!data.session) {
//     location.replace("login.html");
//     return null;
//   }
//   return data.session.access_token;
// }

// async function setStatus(status) {
//   if (!currentConversationId) return;

//   const token = await getTokenOrRedirect();
//   if (!token) return;

//   await fetch(
//     `${API_BASE}/api/admin/conversations/${currentConversationId}/status?status=${encodeURIComponent(status)}`,
//     {
//       method: "POST",
//       headers: { "Authorization": `Bearer ${token}` },
//     }
//   );

//   await refreshInbox();
// }

// btnNeedHuman.addEventListener("click", () => setStatus("NEEDS_HUMAN"));
// btnBotActive.addEventListener("click", () => setStatus("BOT_ACTIVE"));
// btnResolved.addEventListener("click", () => setStatus("RESOLVED"));

// btnSend.addEventListener("click", async () => {
//   if (!currentConversationId) return;

//   const content = replyEl.value.trim();
//   if (!content) return;

//   const token = await getTokenOrRedirect();
//   if (!token) return;

//   await fetch(
//     `${API_BASE}/api/admin/conversations/${currentConversationId}/reply?content=${encodeURIComponent(content)}`,
//     {
//       method: "POST",
//       headers: { "Authorization": `Bearer ${token}` },
//     }
//   );

//   replyEl.value = "";
// });

// // -------------------------
// // Main init
// // -------------------------
// async function main() {
//   const session = await requireAuth();
//   if (!session) return;

//   // Disable actions until a conversation is selected
//   setActionsEnabled(false);
//   setChatHeader(null);

//   startConversationRealtime();
//   await refreshInbox();
// }

// main();


const { API_BASE, SUPABASE_URL, SUPABASE_ANON_KEY } = window.APP_CONFIG;
const sb = supabase.createClient(SUPABASE_URL, SUPABASE_ANON_KEY);

// Authentication guard
async function requireAuth() {
  const { data } = await sb.auth.getSession();
  if (!data.session) {
    location.replace("login.html");
    return null;
  }
  return data.session;
}

// Prevent bfcache/back-forward access
window.addEventListener("pageshow", async () => {
  await requireAuth();
});

// DOM elements
const badgeEl = document.getElementById("badge");
const convListEl = document.getElementById("conversations");
const filterEl = document.getElementById("filter");
const btnRefresh = document.getElementById("btnRefresh");

const chatEl = document.getElementById("chat");

const btnNeedHuman = document.getElementById("btnNeedHuman");
const btnBotActive = document.getElementById("btnBotActive");
const btnResolved = document.getElementById("btnResolved");

const replyEl = document.getElementById("reply");
const btnSend = document.getElementById("btnSend");
const rtStatus = document.getElementById("rtStatus");
const btnLogout = document.getElementById("btnLogout");

let msgChannel = null;
let convChannel = null;
let currentConversationId = null;

// Logout handler with proper cleanup
btnLogout.addEventListener("click", async () => {
  await sb.auth.signOut();
  location.replace("login.html");
});

// Helper functions
function escapeHtml(str) {
  return String(str).replace(/[&<>"']/g, (s) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    "\"": "&quot;",
    "'": "&#039;"
  }[s]));
}

function addBubble(m) {
  const div = document.createElement("div");
  div.className = `bubble ${m.direction === "inbound" ? "left" : "right"}`;
  div.innerHTML = `<div><b>${escapeHtml(m.sender_type)}</b>: ${escapeHtml(m.content)}</div>
                   <div class="meta">${m.created_at || ""}</div>`;
  chatEl.appendChild(div);
  chatEl.scrollTop = chatEl.scrollHeight;
}

async function fetchConversations() {
  const res = await fetch(`${API_BASE}/api/conversations`);
  const data = await res.json();
  return Array.isArray(data) ? data : [];
}

function renderConversations(list) {
  convListEl.innerHTML = "";
  const f = filterEl.value;

  const filtered = list.filter(c => (f === "ALL" ? true : c.status === f));

  for (const c of filtered) {
    const item = document.createElement("div");
    item.className = "list-item";
    item.innerHTML = `
      <div><b>#${c.id}</b> <span class="muted">${escapeHtml(c.status)}</span></div>
      <div class="muted">Customer: ${c.customer_name || ("Customer " + c.customer_id)}</div>
    `;
    item.addEventListener("click", () => {
      openConversation(String(c.id));
    });
    convListEl.appendChild(item);
  }
}

async function refreshInbox() {
  const convs = await fetchConversations();
  const needsHumanCount = convs.filter(c => c.status === "NEEDS_HUMAN").length;
  badgeEl.textContent = `Needs Human: ${needsHumanCount}`;
  renderConversations(convs);
}

btnRefresh.addEventListener("click", refreshInbox);
filterEl.addEventListener("change", refreshInbox);

async function loadMessages(conversationId) {
  chatEl.innerHTML = "";
  const res = await fetch(`${API_BASE}/api/conversations/${conversationId}/messages`);
  const data = await res.json();
  (Array.isArray(data) ? data : []).forEach(addBubble);
}

function startMessageRealtime(conversationId) {
  if (msgChannel) sb.removeChannel(msgChannel);

  msgChannel = sb
    .channel(`messages:${conversationId}`)
    .on(
      "postgres_changes",
      {
        event: "INSERT",
        schema: "public",
        table: "messages",
        filter: `conversation_id=eq.${conversationId}`,
      },
      (payload) => {
        const m = payload.new;
        addBubble({
          id: m.id,
          direction: m.direction,
          sender_type: m.sender_type,
          content: m.content,
          created_at: m.created_at,
        });
      }
    )
    .subscribe((status) => {
      rtStatus.textContent = `Realtime: ${status}`;
    });
}

function startConversationRealtime() {
  if (convChannel) sb.removeChannel(convChannel);

  convChannel = sb
    .channel("conversations_changes")
    .on(
      "postgres_changes",
      { event: "*", schema: "public", table: "conversations" },
      () => {
        // Any status change -> refresh inbox count/list
        refreshInbox();
      }
    )
    .subscribe();
}

async function openConversation(conversationId) {
  currentConversationId = conversationId;
  await loadMessages(conversationId);
  startMessageRealtime(conversationId);
}

async function setStatus(status) {
  if (!currentConversationId) return;
  
  // Get auth token
  const { data } = await sb.auth.getSession();
  if (!data.session) {
    location.replace("login.html");
    return;
  }
  const token = data.session.access_token;

  await fetch(
    `${API_BASE}/api/admin/conversations/${currentConversationId}/status?status=${encodeURIComponent(status)}`,
    {
      method: "POST",
      headers: {
        "Authorization": `Bearer ${token}`
      }
    }
  );
  
  await refreshInbox();
}

btnNeedHuman.addEventListener("click", () => setStatus("NEEDS_HUMAN"));
btnBotActive.addEventListener("click", () => setStatus("BOT_ACTIVE"));
btnResolved.addEventListener("click", () => setStatus("RESOLVED"));

btnSend.addEventListener("click", async () => {
  if (!currentConversationId) return;
  const content = replyEl.value.trim();
  if (!content) return;

  // Get auth token
  const { data } = await sb.auth.getSession();
  if (!data.session) {
    location.replace("login.html");
    return;
  }
  const token = data.session.access_token;

  await fetch(
    `${API_BASE}/api/admin/conversations/${currentConversationId}/reply?content=${encodeURIComponent(content)}`,
    {
      method: "POST",
      headers: {
        "Authorization": `Bearer ${token}`
      }
    }
  );

  replyEl.value = "";
});

// Main initialization
async function main() {
  const session = await requireAuth();
  if (!session) return;

  // Initialize dashboard
  startConversationRealtime();
  refreshInbox();
}

main();