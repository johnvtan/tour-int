import axios from "axios";

export const createTorrent = (formData) => {
  return axios({
    url: "BACKEND URL HERE",
    method: "POST",
    data: {
      torrent: {
        url: formData.url,
        name: formData.name,
      },
    },
  });
};
