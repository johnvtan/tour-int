import React from "react";
import TorrentCard from "./TorrentCard";
import { TableContainer } from "../styles/TorrentTableStyles";

const fakeData = [
  {
    name: "exampleTorrent1",
    torrent_id: 1,
    amountDownloaded: 50,
    totalSize: 200,
    status: "in progress",
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
    status: "in progress",
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
