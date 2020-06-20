import styled, { createGlobalStyle } from "styled-components";

export const GlobalStyle = createGlobalStyle`
  body {
    font-family:'Space Mono', monospace;
    // background: #111111;
    // color: #ffffff;
    overflow: hidden;
  }

  .hoverable {
    cursor: pointer;
  }

  .push-left {
    margin-left: auto;
  }
`;

export const Container = styled.div`
  min-height: 100vh;
  min-width: 100vw;
  display: flex;
  flex-direction: column;
  align-items: center;
`;

export const AppContainer = styled.div`
  margin-top: 64px;
  width: 864px;
`;
