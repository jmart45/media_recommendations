import { Routes, Route } from 'react-router-dom'

import Layout from './components/Layout'
import ChatPage from './pages/ChatPage'
import BrowsePage from './pages/BrowsePage'

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route path="/" element={<ChatPage />} />
        <Route path="/browse" element={<BrowsePage />} />
      </Route>
    </Routes>
  )
}
