import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import Header from "./components/Header";
import Chat from "./pages/Chat";
import Topics from "./pages/Topics/Topics";
import ContentWrapper from "./components/ContentWrapper";

export default function App() {
  return (
    <Router>
      <Header/>
      <div style={{ margin: "20px" }}>
        <ContentWrapper>
          <Routes>
            <Route path="/chat" element={<Chat />} />
            <Route path="/topics" element={<Topics />} />
          </Routes>
        </ContentWrapper>
      </div>
    </Router>
  );
}
