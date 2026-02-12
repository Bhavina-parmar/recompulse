import { useEffect, useState } from "react";
import { getRecommendations, sendEvent } from "../api";

export default function Feed() {
  const [items, setItems] = useState([]);
  const USER_ID = 1;

  useEffect(() => {
    getRecommendations(USER_ID).then(data => {
      setItems(data.items);
    });
  }, []);

  const handleClick = (item) => {
    sendEvent({
      user_id: USER_ID,
      item_id: item.id,
      action: "click"
    });

    alert(`Clicked: ${item.title}`);

    // refresh feed after click
    getRecommendations(USER_ID).then(data => {
      setItems(data.items);
    });
  };

  return (
    <div style={{ padding: "20px" }}>
      <h2>Recommended Feed</h2>
      {items.map(item => (
        <div
          key={item.id}
          onClick={() => handleClick(item)}
          style={{
            border: "1px solid #ccc",
            margin: "8px 0",
            padding: "10px",
            cursor: "pointer"
          }}
        >
          <strong>{item.title}</strong>
          <div>{item.category}</div>
        </div>
      ))}
    </div>
  );
}
