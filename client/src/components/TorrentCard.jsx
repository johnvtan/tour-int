import React from "react";
import ProgressBar from "./ProgressBar";
import { updateStatus, deleteTorrent } from "../api/torrent";
import {
  TableRow,
  TableRowAlternate,
  TableCell,
} from "../styles/TorrentCardStyles";

const TorrentCard = (props) => {
  const {
    name,
    downloaded_bytes,
    total_size_bytes,
    speed,
    download_status,
    seeds,
    peers,
    eta,
    file_hash,
  } = props.data;

  const mediaControl = () => {
    if (download_status === "completed") return "";

    return (
      <div onClick={() => handleUpdateClick(file_hash)}>
        {download_status === "in progress" ? "->" : "||"}
      </div>
    );
  };

  const handleUpdateClick = (file_hash) => {
    download_status === "in progress"
      ? onUpdateTorrent(file_hash, "pause")
      : onUpdateTorrent(file_hash, "resume");
  };

  const onUpdateTorrent = (file_hash, statusRequest) => {
    updateStatus(file_hash, statusRequest)
      .then((data) => console.log("PATCH SUCCESS", data))
      // TODO: .then GET specific torrent again here for updated status, or use websocket
      .catch((err) => console.warn("PATCH failed with message:", err));
  };

  const onDeleteTorrent = (file_hash) => {
    deleteTorrent(file_hash)
      .then((data) => console.log("DELETE SUCCESS", data))
      // TODO: .then GET all /torrents to see new list, or use websocket
      .catch((err) => console.warn("DELETE failed with message:", err));
  };

  return (
    <>
      <TableRow>
        <TableCell cellWidth="148px">{name}</TableCell>
        <TableCell cellWidth="32px">{downloaded_bytes}</TableCell>
        <TableCell cellWidth="40px">{total_size_bytes}</TableCell>
        <TableCell cellWidth="80px">{speed}</TableCell>
        <TableCell cellWidth="128px">{download_status}</TableCell>
        <TableCell cellWidth="255px">
          <ProgressBar
            downloaded_bytes={downloaded_bytes}
            total_size_bytes={total_size_bytes}
          />
        </TableCell>
        <TableCell>{mediaControl()}</TableCell>
        <TableCell onClick={() => onDeleteTorrent(file_hash)}>X</TableCell>
      </TableRow>
      <TableRowAlternate>
        <TableCell cellWidth="148px"></TableCell>
        <TableCell cellWidth="96px">{seeds ? `seeds: ${seeds}` : ""}</TableCell>
        <TableCell cellWidth="96px">{peers ? `peers: ${peers}` : ""}</TableCell>
        <TableCell cellWidth="120px">{eta ? `${eta} left` : ""}</TableCell>
      </TableRowAlternate>
    </>
  );
};

export default TorrentCard;
