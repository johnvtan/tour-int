import React from "react";

import { GlobalStyle, Container, AppContainer } from "../styles/AppStyles";
import Title from "../components/Title";
import TorrentForm from "../components/TorrentForm";

function App() {
  return (
    <>
      <GlobalStyle />
      <Container>
        <AppContainer>
          <Title />
          <TorrentForm />
          <h3>---------------------------</h3>
          <h3>Stub: torrent table here</h3>
          <h3>
            exampleTorrent123 cool progress bar ||||||||||||||||||||||||||||
          </h3>
          <h3>
            exampleTorrent123 cool progress bar ||||||||||||||||||||||||||||
          </h3>
          <h3>
            exampleTorrent123 cool progress bar ||||||||||||||||||||||||||||
          </h3>
        </AppContainer>
      </Container>
    </>
  );
}

export default App;
