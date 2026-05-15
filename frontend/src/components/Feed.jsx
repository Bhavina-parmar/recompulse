import { useEffect, useState } from "react";
import { getPersonalFeed, getTrendingFeed, sendEvent } from "../api";

export default function Feed({ userId }) {
  const [personal, setPersonal] = useState([]);
  const [trending, setTrending] = useState([]);
  const [loading, setLoading] = useState(false);
  const [updating, setUpdating] = useState(false);

  const loadFeed = async (sendImpressions = false) => {
    setLoading(true);
    try {
      const personalData = await getPersonalFeed(userId);
      const trendingData = await getTrendingFeed();

      setPersonal(personalData.items || []);
      setTrending(trendingData.items || []);

      if (sendImpressions) {
        personalData.items.forEach((item) =>
          sendEvent({ user_id: userId, item_id: item.id, action: "impression" })
        );
        trendingData.items.forEach((item) =>
          sendEvent({ user_id: userId, item_id: item.id, action: "impression" })
        );
      }
    } catch (err) {
      console.error("Feed load failed", err);
    }
    setLoading(false);
  };

  useEffect(() => {
    loadFeed(true);
  }, [userId]);

  const handleClick = async (itemId) => {
    setUpdating(true);
    await sendEvent({ user_id: userId, item_id: itemId, action: "click" });
    await loadFeed(false);
    setUpdating(false);
  };

  if (loading) return <p>Loading...</p>;

  return (
    <div>
      <h2>🧠 Personal for User {userId}</h2>

      {updating && <p>⚡ Updating your feed...</p>}

      {personal.map((item) => (
        <div
          key={item.id}
          onClick={() => handleClick(item.id)}
          style={{
            border: "1px solid #ccc",
            padding: "12px",
            marginBottom: "12px",
            borderRadius: "8px",
            cursor: "pointer",
          }}
        >
          <h3>{item.title}</h3>

          <p>📂 Category: {item.category}</p>
          <p>🤖 Score: {item.score ? item.score.toFixed(3) : "0.000"}</p>
          <p>🧠 Your interest: {item.user_affinity ?? 0}</p>

          <p style={{ color: "#22c55e", fontSize: "14px" }}>
            👉 Click to improve your feed
          </p>
        </div>
      ))}

      <h2>🔥 Trending</h2>

      {trending.map((item) => (
        <div
          key={item.id}
          onClick={() => handleClick(item.id)}
          style={{ cursor: "pointer" }}
        >
          <h3>{item.title}</h3>
        </div>
      ))}
    </div>
  );
}