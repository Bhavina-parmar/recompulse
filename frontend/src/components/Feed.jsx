import { useEffect, useState } from "react";
import { getRecommendations, sendEvent } from "../api";

export default function Feed({ userId }) {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(false);

  const loadFeed = async () => {
    setLoading(true);
    try {
      const data = await getRecommendations(userId);

      console.log("API RESPONSE 👉", data);

      setItems(data.items);   // ✅ correct
    } catch (err) {
      console.error("Failed to load feed", err);
      setItems([]);
    }
    setLoading(false);
  };


  useEffect(() => {
    loadFeed();
  }, [userId]);

  const handleClick = async (itemId) => {
    await sendEvent({
      user_id: userId,
      item_id: itemId,
      action: "click",
    });

    loadFeed();
  };

  if (loading) return <p>Loading feed...</p>;

  return (
    <div>
      <h2>Recommendations for User {userId}</h2>

      {Array.isArray(items) &&
        items.map((item) => (
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
            <p>Category: {item.category}</p>
          </div>
        ))}
    </div>
  );
}
