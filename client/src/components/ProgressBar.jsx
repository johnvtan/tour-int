import React from "react";
import {
  ProgressBarContainer,
  Edge,
  Bar,
  Percent,
} from "../styles/ProgressBarStyles";

function ProgressBar(props) {
  const { downloaded_bytes, total_size_bytes } = props;
  const progress = (downloaded_bytes / total_size_bytes) * 100;

  // hardcoding 1 bar every 5%, up to 20 max.
  // changing this requires making styling dynamic for the entire component
  const numberOfBars = Math.floor(progress / 5);

  return (
    <ProgressBarContainer>
      <Edge>[</Edge>
      {[...Array(numberOfBars)].map((num, idx) => (
        <Bar key={idx}>|</Bar>
      ))}
      <div style={{ marginLeft: "auto", display: "flex" }}>
        <Percent>{progress}%</Percent>
        <Edge>]</Edge>
      </div>
    </ProgressBarContainer>
  );
}

export default ProgressBar;
