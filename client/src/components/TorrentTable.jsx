import React from "react";
import TorrentCard from "./TorrentCard";
import { TableContainer } from "../styles/TorrentTableStyles";

const fakeData = [
  {
    name: "exampleTorrent1",
    torrent_id: 1,
    downloaded_bytes: 50,
    total_size_bytes: 200,
    speed: "120/kbps",
    download_status: "in progress",
    seeds: "10",
    peers: "22",
    eta: "5 mins",
    file_hash: "deadbeef",
  },
  {
    name: "exampleTorrent2",
    torrent_id: 2,
    downloaded_bytes: 500,
    total_size_bytes: 500,
    download_status: "completed",
    file_hash: "abcdabcd",
  },
  {
    name: "exampleTorrent3",
    torrent_id: 3,
    downloaded_bytes: 960,
    total_size_bytes: 1000,
    speed: "120/kbps",
    download_status: "paused",
    seeds: "10",
    peers: "22",
    eta: "5 mins",
    file_hash: "fffeee",
  },
];

function TorrentTable() {
  return (
    <TableContainer>
      {fakeData.map((data) => (
        <TorrentCard data={data} key={data.torrent_id} />
      ))}
    </TableContainer>
  );
}

export default TorrentTable;
