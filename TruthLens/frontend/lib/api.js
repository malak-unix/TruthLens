const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

async function readJson(response, fallbackMessage) {
  let data = null;

  try {
    data = await response.json();
  } catch {
    data = null;
  }

  if (!response.ok) {
    throw new Error(data?.detail || fallbackMessage);
  }

  return data;
}

export async function fetchNews(country = "", category = "") {
  const params = new URLSearchParams();

  if (country) params.append("country", country);
  if (category && category !== "All") params.append("category", category);

  const response = await fetch(`${API_URL}/news?${params.toString()}`, {
    method: "GET",
    cache: "no-store",
  });

  return readJson(response, "Failed to fetch news");
}

export async function fetchHistoricalNews({
  country = "",
  category = "",
  search = "",
  limit = 60,
} = {}) {
  const params = new URLSearchParams();

  if (country) params.append("country", country);
  if (category && category !== "All") params.append("category", category);
  if (search) params.append("search", search);
  if (limit) params.append("limit", String(limit));

  const response = await fetch(`${API_URL}/news/history?${params.toString()}`, {
    method: "GET",
    cache: "no-store",
  });

  return readJson(response, "Failed to fetch historical news");
}

export async function fetchCategories() {
  const response = await fetch(`${API_URL}/categories`, {
    method: "GET",
    cache: "no-store",
  });

  return readJson(response, "Failed to fetch categories");
}

export async function fetchTrending(region = "") {
  const params = new URLSearchParams();

  if (region) {
    params.append("region", region);
  }

  const response = await fetch(`${API_URL}/trending?${params.toString()}`, {
    method: "GET",
    cache: "no-store",
  });

  return readJson(response, "Failed to fetch trending topics");
}

export async function fetchOverviewStats() {
  const response = await fetch(`${API_URL}/stats/overview`, {
    method: "GET",
    cache: "no-store",
  });

  return readJson(response, "Failed to fetch overview stats");
}

export async function fetchRefreshLogs() {
  const response = await fetch(`${API_URL}/refresh/logs`, {
    method: "GET",
    cache: "no-store",
  });

  return readJson(response, "Failed to fetch refresh logs");
}

export async function analyzeContent(payload) {
  const response = await fetch(`${API_URL}/analyze`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });

  return readJson(response, "Failed to analyze content");
}

export async function chatWithAssistant(payload) {
  const response = await fetch(`${API_URL}/chat`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });

  return readJson(response, "Failed to chat with assistant");
}

export async function registerUser(payload) {
  const response = await fetch(`${API_URL}/auth/register`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });

  return readJson(response, "Failed to register");
}

export async function loginUser(payload) {
  const response = await fetch(`${API_URL}/auth/login`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });

  return readJson(response, "Failed to login");
}

export async function fetchCurrentUser(token) {
  const response = await fetch(`${API_URL}/auth/me`, {
    method: "GET",
    headers: {
      Authorization: `Bearer ${token}`,
    },
    cache: "no-store",
  });

  return readJson(response, "Failed to fetch current user");
}
