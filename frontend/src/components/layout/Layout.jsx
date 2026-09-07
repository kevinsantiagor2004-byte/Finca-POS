import Sidebar from './Sidebar'
import TopBar  from './TopBar'

export default function Layout({ children }) {
  return (
    <div className="app-shell">
      <Sidebar />
      <div className="main-content">
        <TopBar />
        <main className="page-body fade-in">
          {children}
        </main>
      </div>
    </div>
  )
}
