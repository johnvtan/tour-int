import React, { useState } from "react";
import { createTorrent } from "../api/torrent";

function TorrentForm() {
  const [values, setValues] = useState({ url: "", name: "" });

  const handleInputChange = (e) => {
    e.persist();

    setValues((values) => ({ ...values, [e.target.name]: e.target.value }));
  };

  const handleSubmit = (e) => {
    e.preventDefault();

    createTorrent(values)
      .then((data) => console.log("POST SUCCESS", data))
      .catch((err) => console.warn("POST failed with message:", err));
    setValues({ url: "", name: "" });
  };

  return (
    <>
      <form onSubmit={handleSubmit}>
        <label htmlFor="url">Torrent link: </label>
        <input
          type="text"
          name="url"
          value={values.url}
          required
          onChange={handleInputChange}
        />
        <label htmlFor="name">Name: </label>
        <input
          type="text"
          name="name"
          value={values.name}
          required
          onChange={handleInputChange}
        />
        <button>Submit</button>
      </form>
    </>
  );
}

export default TorrentForm;
