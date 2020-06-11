import React from "react";

import { GlobalStyle, Container, AppContainer } from "../styles/AppStyles";
import Title from "../components/Title";
import TorrentForm from "../components/TorrentForm";
import TorrentTable from "../components/TorrentTable";

function App() {
  return (
    <>
      <GlobalStyle />
      <Container>
        <AppContainer>
          <Title />
          <TorrentForm />
          <TorrentTable />
        </AppContainer>
      </Container>
    </>
  );
}

export default App;
