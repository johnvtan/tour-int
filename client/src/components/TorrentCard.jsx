import React from "react";
import ProgressBar from "./ProgressBar";
import {
  TableRow,
  TableRowAlternate,
  TableCell,
} from "../styles/TorrentCardStyles";

const TorrentCard = (props) => {
  const {
    name,
    amountDownloaded,
    totalSize,
    speed,
    status,
    seeds,
    peers,
    eta,
  } = props.data;

  return (
    <>
      <TableRow>
        <TableCell cellWidth="148px">{name}</TableCell>
        <TableCell cellWidth="32px">{amountDownloaded}</TableCell>
        <TableCell cellWidth="40px">{totalSize}</TableCell>
        <TableCell cellWidth="80px">{speed}</TableCell>
        <TableCell cellWidth="128px">{status}</TableCell>
        <TableCell cellWidth="255px">
          <ProgressBar
            amountDownloaded={amountDownloaded}
            totalSize={totalSize}
          />
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
