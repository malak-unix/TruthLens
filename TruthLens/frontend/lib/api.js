const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

export async function fetchNews(country = "", category = "") {
  const params = new URLSearchParams();

  if (country) params.append("country", country);
  if (category && category !== "All") params.append("category", category);

  const response = await fetch(`${API_URL}/news?${params.toString()}`, {
    method: "GET",
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error("Failed to fetch news");
  }

  return response.json();
}

export async function fetchCategories() {
  const response = await fetch(`${API_URL}/categories`, {
    method: "GET",
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error("Failed to fetch categories");
  }

  return response.json();
}

export async function analyzeContent(payload) {
  const response = await fetch(`${API_URL}/analyze`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    throw new Error("Failed to analyze content");
  }

  return response.json();
}