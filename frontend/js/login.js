const { SUPABASE_URL, SUPABASE_ANON_KEY } = window.APP_CONFIG;

const sb = supabase.createClient(SUPABASE_URL, SUPABASE_ANON_KEY);

const emailEl = document.getElementById("email");
const passEl = document.getElementById("password");
const msgEl = document.getElementById("msg");
const btn = document.getElementById("btnLogin");

async function redirectIfLoggedIn() {
  const { data } = await sb.auth.getSession();
  if (data.session) {
    location.replace("dashboard.html");
  }
}

btn.addEventListener("click", async () => {
  msgEl.textContent = "Logging in...";

  const email = emailEl.value.trim();
  const password = passEl.value.trim();

  const { data, error } = await sb.auth.signInWithPassword({ email, password });

  if (error) {
    msgEl.textContent = error.message;
    return;
  }

  if (data.session) {
    location.replace("dashboard.html");
  }
});

window.addEventListener("pageshow", redirectIfLoggedIn);
redirectIfLoggedIn();