import React from "react";

import { GlobalStyle, Container, AppContainer } from "../styles/AppStyles";
import Title from "../components/Title";

function App() {
  return (
    <>
      <GlobalStyle />
      <Container>
        <AppContainer>
          <Title />
        </AppContainer>
      </Container>
    </>
  );
}

export default App;
