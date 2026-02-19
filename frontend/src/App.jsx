import { useState } from "react";
import Feed from "./components/Feed";

function App() {
  const [userId, setUserId] = useState(1);

  return (
    <div>
      <h1>AI Feed</h1>

      <button onClick={() => setUserId(1)}>User 1</button>
      <button onClick={() => setUserId(2)}>User 2</button>
      <button onClick={() => setUserId(3)}>User 3</button>

      <Feed userId={userId} />
    </div>
  );
}

export default App;
