import styled from "styled-components";

export const TableRow = styled.div`
  display: flex;
  // border: dashed white;
`;

export const TableRowAlternate = styled.div`
  display: flex;
  margin-bottom: 32px;
  // border: dashed white;
`;

export const TableCell = styled.div`
  padding-right: 16px;
  width: ${(props) => props.cellWidth};
  // border: dashed blue;
`;
