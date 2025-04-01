import React, { useState, useEffect, useCallback, useRef } from "react";
import CytoscapeComponent from "react-cytoscapejs";

// Add debounce function at the top level
const debounce = (func, delay) => {
  let timeout;
  return (...args) => {
    clearTimeout(timeout);
    timeout = setTimeout(() => func(...args), delay);
  };
};

const FriendGraph = () => {
  const [elements, setElements] = useState([]);
  const [selectedNodes, setSelectedNodes] = useState([]);
  const [cyInstance, setCyInstance] = useState(null);
  const [userData, setUserData] = useState({});
  const [friendRecommendations, setFriendRecommendations] = useState([]);
  const [newUser, setNewUser] = useState({ name: "", age: "", gender: "", hobbies: "" });
  const [isLoading, setIsLoading] = useState(false);
  const [showRecommendations, setShowRecommendations] = useState(false);
  const lastRequestRef = useRef(null);
  const [lastFetchedNode, setLastFetchedNode] = useState(null);

  useEffect(() => {
    setElements([{ data: { id: "You", label: "You", color: getRandomColor() } }]);
    setUserData({ You: { name: "You", age: "", gender: "", hobbies: "" } });
  }, []);

  const getRandomColor = () => {
    const colors = ["#e74c3c", "#8e44ad", "#3498db", "#2ecc71", "#f39c12", "#1abc9c"];
    return colors[Math.floor(Math.random() * colors.length)];
  };

  const addNode = async () => {
    if (!newUser.name.trim()) {
      alert("Please enter a name for the new user.");
      return;
    }
  
    try {
      const response = await fetch("http://127.0.0.1:8000/add_user/", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          name: newUser.name,
          age: parseInt(newUser.age),
          gender: newUser.gender,
          hobbies: newUser.hobbies.split(",").map(h => h.trim()), // Assuming hobbies are comma-separated
        }),
      });
  
      if (response.ok) {
        const newId = newUser.name; // Using name as ID to match backend
        setElements((prevElements) => [
          ...prevElements,
          { data: { id: newId, label: newUser.name, color: getRandomColor() } },
        ]);
        setUserData((prevData) => ({
          ...prevData,
          [newId]: { 
            name: newUser.name, 
            age: newUser.age, 
            gender: newUser.gender, 
            hobbies: newUser.hobbies 
          },
        }));
        setNewUser({ name: "", age: "", gender: "", hobbies: "" });
      } else {
        alert("Failed to add user to database");
      }
    } catch (error) {
      console.error("Error adding user:", error);
      alert("Error adding user");
    }
  };
  
  const addConnection = async () => {
    if (selectedNodes.length === 2) {
      try {
        const response = await fetch("http://127.0.0.1:8000/add_friend/", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            user1: selectedNodes[0],
            user2: selectedNodes[1],
          }),
        });
  
        const data = await response.json();
        console.log("API Response:", data);
  
        if (response.ok) {
          setElements((prevElements) => [
            ...prevElements,
            { data: { source: selectedNodes[0], target: selectedNodes[1] } },
          ]);
          setSelectedNodes([]);
        } else {
          console.error("Error:", data);
          alert(`Failed: ${data.message || "Unknown error"}`);
        }
      } catch (error) {
        console.error("Connection error:", error);
        alert("Network error - check console");
      }
    }
  };

  const deleteNode = () => {
    if (selectedNodes.length === 1) {
      const nodeId = selectedNodes[0];
      setElements((prevElements) => prevElements.filter((el) => el.data.id !== nodeId && el.data.source !== nodeId && el.data.target !== nodeId));
      setUserData((prevData) => {
        const newData = { ...prevData };
        delete newData[nodeId];
        return newData;
      });
      setFriendRecommendations([]);
      setSelectedNodes([]);
    } else {
      alert("Select exactly one node to delete!");
    }
  };

  const deleteConnection = () => {
    if (selectedNodes.length === 2) {
      setElements((prevElements) => prevElements.filter((el) => !(el.data.source === selectedNodes[0] && el.data.target === selectedNodes[1]) && !(el.data.source === selectedNodes[1] && el.data.target === selectedNodes[0])));
      setSelectedNodes([]);
    } else {
      alert("Select exactly two connected nodes to delete their connection!");
    }
  };

  const fetchRecommendations = useCallback(async (nodeId) => {
    if (isLoading || lastFetchedNode === nodeId) return;
    
    try {
      setIsLoading(true);
      setLastFetchedNode(nodeId);
      const userName = userData[nodeId]?.name || nodeId;
      
      const response = await fetch(
        `http://127.0.0.1:8000/recommendations/${encodeURIComponent(userName)}`
      );
      
      if (!response.ok) throw new Error(await response.text());
      
      const { recommendations } = await response.json();
      setFriendRecommendations(recommendations);
      setShowRecommendations(true);
    } catch (error) {
      console.error("Fetch error:", error);
    } finally {
      setIsLoading(false);
    }
  }, [isLoading, userData, lastFetchedNode]);

  // Create debounced version of fetchRecommendations
  const debouncedUpdate = useCallback(
    debounce((nodeId) => {
      fetchRecommendations(nodeId);
    }, 500),
    [fetchRecommendations]
  );

  return (
    <div style={{ display: "flex", flexDirection: "row", alignItems: "center", background: "#000", height: "100vh", padding: "20px" }}>
      <CytoscapeComponent
        elements={elements}
        style={{
          width: "800px",
          height: "600px",
          border: "2px solid #333",
          backgroundColor: "#000",
          borderRadius: "10px",
        }}
        layout={{ name: "cose" }}
        stylesheet={[
          { selector: "node", style: { "background-color": "data(color)", label: "data(label)", "font-size": "16px", color: "#fff", width: "50px", height: "50px", "border-width": "2px", "border-color": "#fff" } },
          { selector: "edge", style: { width: 3, "line-color": "#fff", "target-arrow-color": "#fff", "target-arrow-shape": "triangle" } },
          { selector: ".selected", style: { "border-width": "5px", "border-color": "#FFD700" } },
        ]}
        cy={(cy) => {
          if (!cy) return;
          setCyInstance(cy);
          cy.on("tap", "node", (event) => {
            const nodeId = event.target.id();
            setSelectedNodes((prev) => {
              const newSelection = prev.includes(nodeId) 
                ? prev.filter((id) => id !== nodeId) 
                : [...prev, nodeId].slice(-2);
              
              // Only fetch if exactly one node is selected
              if (newSelection.length === 1) {
                debouncedUpdate(newSelection[0]);
              }
              
              return newSelection;
            });
          });
        }}
      />

      <div style={{ marginLeft: "20px", padding: "20px", borderRadius: "10px", background: "#222", color: "#fff", boxShadow: "0 4px 6px rgba(255,255,255,0.1)" }}>
        <h3>Add New User</h3>
        <label>Name:</label>
        <input type="text" value={newUser.name} onChange={(e) => setNewUser({ ...newUser, name: e.target.value })} />
        <label>Age:</label>
        <input type="number" value={newUser.age} onChange={(e) => setNewUser({ ...newUser, age: e.target.value })} />
        <label>Gender:</label>
        <input type="text" value={newUser.gender} onChange={(e) => setNewUser({ ...newUser, gender: e.target.value })} />
        <label>Hobbies:</label>
        <input type="text" value={newUser.hobbies} onChange={(e) => setNewUser({ ...newUser, hobbies: e.target.value })} />
        <button onClick={addNode} style={buttonStyle}>Add User</button>


        <h3>Selected Nodes:</h3>
        <p>{selectedNodes.join(", ") || "None"}</p>

        {selectedNodes.length === 1 && (
          <div>
            <h3>Selected Node Details</h3>
            <p><strong>Name:</strong> {userData[selectedNodes[0]]?.name || "Unknown"}</p>
            <p><strong>Age:</strong> {userData[selectedNodes[0]]?.age || "N/A"}</p>
            <p><strong>Gender:</strong> {userData[selectedNodes[0]]?.gender || "N/A"}</p>
            <p><strong>Hobbies:</strong> {userData[selectedNodes[0]]?.hobbies || "N/A"}</p>
          </div>
        )}

        <button onClick={addConnection} style={buttonStyle} disabled={selectedNodes.length !== 2}>
          Create Connection
        </button>
        <button onClick={deleteNode} style={buttonStyle} disabled={selectedNodes.length !== 1}>
          Delete Node
        </button>
        <button onClick={deleteConnection} style={buttonStyle} disabled={selectedNodes.length !== 2}>
          Delete Connection
        </button>

        <button 
          onClick={() => selectedNodes.length === 1 && debouncedUpdate(selectedNodes[0])} 
          style={{
            ...buttonStyle,
            opacity: isLoading ? 0.7 : 1,
            cursor: isLoading ? 'not-allowed' : 'pointer'
          }}
          disabled={isLoading || selectedNodes.length !== 1}
        >
          {isLoading ? 'Loading...' : 'Test Recommendations'}
        </button>

        <div style={{backgroundColor: "#222", color: "#fff", padding: "20px", borderRadius: "10px", marginTop: "20px"}}>
          {selectedNodes.length === 1 && showRecommendations && friendRecommendations.length > 0 && (
            <div style={{
              backgroundColor: "#222",
              color: "#fff",
              padding: "20px",
              borderRadius: "10px",
              marginTop: "20px",
              maxHeight: "300px",  // Fixed height
              overflowY: "auto",    // Scrollable
              overflowX: "hidden"   // Prevent horizontal scroll
            }}>
              <h3>Friend Recommendations</h3>
              <ul style={{ listStyle: "none", padding: 0 }}>
                {friendRecommendations.map((friend, index) => (
                  <li key={index} style={{ 
                    margin: "8px 0",
                    padding: "10px",
                    backgroundColor: "#333",
                    borderRadius: "5px",
                    display: "flex",
                    justifyContent: "space-between"
                  }}>
                    <span>{friend.name}</span>
                    <span style={{ color: "#FFD700" }}>Score: {friend.score}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

const buttonStyle = { padding: "10px", margin: "5px", background: "#FFD700", color: "#000", cursor: "pointer" };

export default FriendGraph;
