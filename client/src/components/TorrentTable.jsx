import React, { useEffect, useState } from "react";
import TorrentCard from "./TorrentCard";
import { TableContainer } from "../styles/TorrentTableStyles";
import { getTorrents } from "../api/torrent";

function TorrentTable() {
  useEffect(() => {
    const interval = setInterval(() => {
      getTorrents().then((data) => setTorrentData(data));
    }, 2000);
    return () => clearInterval(interval);
  }, []);

  const [torrentData, setTorrentData] = useState([]);

  return (
    <TableContainer>
      {torrentData && torrentData.data
        ? torrentData.data.map((data) => (
            <TorrentCard data={data} key={data.torrent_id} />
          ))
        : ""}
    </TableContainer>
  );
}

export default TorrentTable;
