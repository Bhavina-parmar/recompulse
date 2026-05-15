const BASE = "http://127.0.0.1:8000";

export const getPersonalFeed = async (userId) => {
  const res = await fetch(`${BASE}/recommend/personal?user_id=${userId}`);
  return res.json();
};

export const getTrendingFeed = async () => {
  const res = await fetch(`${BASE}/recommend/trending`);
  return res.json();
};

export const sendEvent = async (event) => {
  await fetch(`${BASE}/event`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(event),
  });
};

// const BASE = "http://127.0.0.1:8000";

// export const getRecommendations = async (userId) => {
//   const res = await fetch(`${BASE}/recommend?user_id=${userId}`);
//   return res.json();
// };

// export const sendEvent = async (event) => {
//   await fetch(`${BASE}/event`, {
//     method: "POST",
//     headers: { "Content-Type": "application/json" },
//     body: JSON.stringify(event),
//   });
// };
