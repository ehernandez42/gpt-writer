import { NavLink, Outlet } from 'react-router-dom'

export function Layout() {
  return (
    <div>
      <nav>
        <NavLink to="/styles">Styles</NavLink>
        {' '}
        <NavLink to="/generate">Generate</NavLink>
      </nav>
      <main>
        <Outlet />
      </main>
    </div>
  )
}
