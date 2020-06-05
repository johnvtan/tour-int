import React, { useState } from "react";
import { createTorrent } from "../api/torrent";

function TorrentForm() {
  const [value, setValue] = useState("");

  const handleInputChange = (e) => {
    setValue(e.target.value);
  };

  const handleSubmit = (e) => {
    e.preventDefault();

    createTorrent(value)
      .then((data) => console.log("POST SUCCESS", data))
      .catch((err) => console.warn("POST failed with message:", err));

    setValue("");
  };

  return (
    <>
      <form onSubmit={handleSubmit}>
        <label htmlFor="add-torrent">Torrent link: </label>
        <input
          type="text"
          name="add-torrent"
          value={value}
          required
          onChange={handleInputChange}
        />
        <button>Submit</button>
      </form>
    </>
  );
}

export default TorrentForm;
