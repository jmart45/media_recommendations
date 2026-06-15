import Sidebar from '../components/Sidebar'
import Chat from '../components/chat/Chat'

export default function ChatPage() {
  return (
    <div className="flex h-full">
      <Sidebar />
      <Chat />
    </div>
  )
}
