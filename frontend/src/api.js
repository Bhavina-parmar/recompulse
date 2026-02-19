const BASE = "http://127.0.0.1:8000";

export const getRecommendations = async (userId) => {
  const res = await fetch(`${BASE}/recommend?user_id=${userId}`);
  return res.json();
};

export const sendEvent = async (event) => {
  await fetch(`${BASE}/event`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(event),
  });
};
