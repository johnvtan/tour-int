import React from "react";
import TorrentCard from "./TorrentCard";
import { TableContainer } from "../styles/TorrentTableStyles";

const fakeData = [
  {
    name: "exampleTorrent1",
    torrent_id: 1,
    amountDownloaded: 50,
    totalSize: 200,
    speed: "120/kbps",
    status: "in progress",
    seeds: "10",
    peers: "22",
    eta: "5 mins",
  },
  {
    name: "exampleTorrent2",
    torrent_id: 2,
    amountDownloaded: 500,
    totalSize: 500,
    status: "completed",
  },
  {
    name: "exampleTorrent3",
    torrent_id: 3,
    amountDownloaded: 960,
    totalSize: 1000,
    speed: "120/kbps",
    status: "in progress",
    seeds: "10",
    peers: "22",
    eta: "5 mins",
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
