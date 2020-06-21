import React, { useState } from "react";
import { createTorrent } from "../api/torrent";
import { FormContainer, FormInput, SubmitButton } from "../styles/FormStyles";

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
      <FormContainer onSubmit={handleSubmit}>
        <label htmlFor="url">Torrent link: </label>
        <FormInput
          type="text"
          name="url"
          value={values.url}
          required
          onChange={handleInputChange}
          placeholder="enter url..."
        />
        <label htmlFor="name">Name: </label>
        <FormInput
          type="text"
          name="name"
          value={values.name}
          required
          onChange={handleInputChange}
          placeholder="enter name..."
        />
        <SubmitButton>Submit</SubmitButton>
      </FormContainer>
    </>
  );
}

export default TorrentForm;
