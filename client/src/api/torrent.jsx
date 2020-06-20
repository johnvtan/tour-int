import axios from "axios";

const apiUrl = "BACKEND URL HERE";

export const createTorrent = (formData) => {
  return axios({
    url: apiUrl,
    method: "POST",
    data: {
      torrent: {
        url: formData.url,
        name: formData.name,
      },
    },
  });
};

export const updateStatus = (file_hash, statusRequest) => {
  return axios({
    url: `${apiUrl}/${file_hash}`,
    method: "PATCH",
    data: {
      torrent: {
        download_status: statusRequest,
      },
    },
  });
};

export const deleteTorrent = (torrent_hash) => {
  return axios({
    url: `${apiUrl}/${torrent_hash}`,
    method: "DELETE",
  });
};
