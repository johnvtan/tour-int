import React, { useState } from "react";

function TorrentForm() {
  const [value, setValue] = useState("");

  const handleInputChange = (e) => {
    e.persist();
    setValue(e.target.value);
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    console.log(value);
    setValue("");
  };

  return (
    <>
      <form onSubmit={handleSubmit}>
        <label htmlFor="add-torrent">Torrent link</label>
        <input
          type="text"
          name="add-torrent"
          value={value}
          required
          onChange={handleInputChange}
        />
      </form>
    </>
  );
}

export default TorrentForm;
