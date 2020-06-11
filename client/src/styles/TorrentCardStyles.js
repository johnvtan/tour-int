import styled from "styled-components";

export const TableRow = styled.div`
  display: flex;
  // border: dashed white;
`;

export const TableCell = styled.div`
  padding: 16px 16px 16px 0;
  width: ${(props) => props.cellWidth};
  // border: dashed blue;
`;
