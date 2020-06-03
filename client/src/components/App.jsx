import React from "react";

import { GlobalStyle, Container, AppContainer } from "../styles/AppStyles";

function App() {
  return (
    <>
      <GlobalStyle />
      <Container>
        <AppContainer>
          <h1>Hello, world!</h1>
        </AppContainer>
      </Container>
    </>
  );
}

export default App;
