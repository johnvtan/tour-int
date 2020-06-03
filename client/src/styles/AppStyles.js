import styled, { createGlobalStyle } from "styled-components";

export const GlobalStyle = createGlobalStyle`
  body {
    font-family:'Space Mono', monospace;
    background: #111111;
    color: #ffffff;
    margin: 0;
    overflow: hidden;
  }
`;

export const AppContainer = styled.div`
  margin-top: 160px;
  width: 900px;
  display: flex;
  align-items: center;
  justify-content: center;
`;

export const Container = styled.div`
  min-height: 100vh;
  min-width: 100vw;
`;
