import React from "react";
import { TableRow, TableCell } from "../styles/TorrentCardStyles";

const TorrentCard = (props) => {
  const { name, amountDownloaded, totalSize, status } = props.data;
  const progress = (amountDownloaded / totalSize) * 100;

  return (
    <TableRow>
      <TableCell>{name}</TableCell>
      <TableCell cellWidth="32px">{amountDownloaded}</TableCell>
      <TableCell cellWidth="40px">{totalSize}</TableCell>
      <TableCell cellWidth="128px">{status}</TableCell>
      <TableCell>[|||||||||||||||||||||{progress}%]</TableCell>
    </TableRow>
  );
};

export default TorrentCard;
