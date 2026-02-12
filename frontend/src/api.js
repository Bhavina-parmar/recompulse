const API_BASE = "http://localhost:8000";

export async function getRecommendations(userId) {
  const res = await fetch(`${API_BASE}/recommend?user_id=${userId}`);
  return res.json();
}

export async function sendEvent(event) {
  await fetch(`${API_BASE}/event`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(event),
  });
}
