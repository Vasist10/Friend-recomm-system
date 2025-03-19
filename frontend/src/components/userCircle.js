import React, { useState } from "react";
import axios from "axios";
import "./index.css";


const UserCircle = ({ user, refreshUsers }) => {
  const [newFriend, setNewFriend] = useState("");

  const addFriend = async () => {
    await axios.post("http://127.0.0.1:8000/add_friend", {
      user1: user.name,
      user2: newFriend,
    });
    refreshUsers();
  };

  return (
    <div className="user-circle">
      <p>{user.name}</p>
      <button onClick={() => setNewFriend(prompt("Enter new friend name:"))}>
        +
      </button>
      {newFriend && <button onClick={addFriend}>Confirm</button>}
    </div>
  );
};

export default UserCircle;
