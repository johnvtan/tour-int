import React from "react";
import ProgressBar from "./ProgressBar";
import { updateStatus, deleteTorrent } from "../api/torrent";
import {
  TableRow,
  TableRowAlternate,
  TableCell,
} from "../styles/TorrentCardStyles";
import { AiOutlinePauseCircle, AiOutlinePlayCircle } from "react-icons/ai";
import { FiDelete } from "react-icons/fi";

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
      <div className="hoverable" onClick={() => handleUpdateClick(file_hash)}>
        {download_status === "in progress" ? (
          <AiOutlinePlayCircle fontSize="22" />
        ) : (
          <AiOutlinePauseCircle fontSize="22" />
        )}
      </div>
    );
  };

  const handleUpdateClick = (file_hash) => {
    download_status === "in progress"
      ? onUpdateTorrent(file_hash, "pause")
      : onUpdateTorrent(file_hash, "resume");
  };

  const onUpdateTorrent = (file_hash, statusRequest) => {
    alert("You requested " + statusRequest + " on file_hash: " + file_hash);
    updateStatus(file_hash, statusRequest)
      .then((data) => console.log("PATCH SUCCESS", data))
      // TODO: .then GET specific torrent again here for updated status, or use websocket
      .catch((err) => console.warn("PATCH failed with message:", err));
  };

  const onDeleteTorrent = (file_hash) => {
    alert("You requested cancel on file_hash: " + file_hash);
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
        <TableCell
          className="hoverable"
          onClick={() => onDeleteTorrent(file_hash)}
        >
          <FiDelete fontSize="22" color="#d12626" />
        </TableCell>
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
