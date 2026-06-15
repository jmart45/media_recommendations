import { Outlet } from 'react-router-dom'

import TopNav from './TopNav'

export default function Layout() {
  return (
    <div className="flex h-full flex-col">
      <TopNav />
      <div className="min-h-0 flex-1">
        <Outlet />
      </div>
    </div>
  )
}
