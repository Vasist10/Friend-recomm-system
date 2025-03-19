import React, { useState } from "react";
import axios from "axios";

const UserForm = ({ refreshUsers }) => {
  const [name, setName] = useState("");
  const [age, setAge] = useState("");
  const [hobbies, setHobbies] = useState("");

  const handleSubmit = async (e) => {
    e.preventDefault();
    await axios.post("http://127.0.0.1:8000/add_user", {
      name,
      age: parseInt(age),
      hobbies: hobbies.split(","),
    });
    refreshUsers();
  };

  return (
    <form onSubmit={handleSubmit}>
      <input type="text" placeholder="Name" onChange={(e) => setName(e.target.value)} />
      <input type="number" placeholder="Age" onChange={(e) => setAge(e.target.value)} />
      <input type="text" placeholder="Hobbies (comma-separated)" onChange={(e) => setHobbies(e.target.value)} />
      <button type="submit">Add User</button>
    </form>
  );
};

export default UserForm;
