import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import Header from "./components/Header";
import Chat from "./pages/Chat";
import Topics from "./pages/Topics/Topics";
import Home from "./pages/Home";
import ContentWrapper from "./components/ContentWrapper";

export default function App() {
  return (
    <Router>
      <Header/>
      <div style={{ padding: "20px", background: "#002A3E" }}>
        <ContentWrapper>
          <Routes>
            <Route path="/home" element={<Home />} />
            <Route path="/chat" element={<Chat />} />
            <Route path="/topics" element={<Topics />} />
          </Routes>
        </ContentWrapper>
      </div>
    </Router>
  );
}
