import React from "react";
import {
  ProgressBarContainer,
  Edge,
  Bar,
  Percent,
} from "../styles/ProgressBarStyles";

function ProgressBar(props) {
  const { amountDownloaded, totalSize } = props;
  const progress = (amountDownloaded / totalSize) * 100;

  const bars = [];
  // hardcoding 1 bar every 5%, up to 20 max.
  // changing this requires making styling dynamic for the entire component
  const numberOfBars = Math.floor(progress / 5);
  for (let i = 0; i < numberOfBars; i++) {
    bars.push("|");
  }

  return (
    <ProgressBarContainer>
      <Edge>[</Edge>
      {bars.map((bar, idx) => (
        <Bar key={idx}>{bar}</Bar>
      ))}
      <div style={{ marginLeft: "auto", display: "flex" }}>
        <Percent>{progress}%</Percent>
        <Edge>]</Edge>
      </div>
    </ProgressBarContainer>
  );
}

export default ProgressBar;
