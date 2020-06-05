import axios from "axios";

export const createTorrent = (data) => {
  return axios({
    url: "BACKEND URL HERE",
    method: "POST",
    data: {
      torrent: {
        url: data,
      },
    },
  });
};
