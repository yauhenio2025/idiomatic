import { NavLink, Outlet } from "react-router-dom";

const NAV = [
  { to: "/", label: "Overview", icon: "◉" },
  { to: "/videos", label: "Videos", icon: "▤" },
  { to: "/expressions", label: "Expressions", icon: "❝" },
  { to: "/channels", label: "Channels", icon: "⚲" },
  { to: "/delivery", label: "Delivery", icon: "⇣" },
];

export default function Layout({ onLogout }: { onLogout: () => void }) {
  return (
    <div className="flex min-h-screen">
      <aside className="fixed inset-y-0 flex w-52 flex-col border-r border-edge bg-surface px-3 py-5">
        <div className="mb-6 px-2">
          <div className="text-lg font-bold tracking-tight">idiomatic</div>
          <div className="text-xs text-muted">harvest dashboard</div>
        </div>
        <nav className="flex flex-col gap-1">
          {NAV.map((n) => (
            <NavLink
              key={n.to}
              to={n.to}
              end={n.to === "/"}
              className={({ isActive }) =>
                `flex items-center gap-2.5 rounded-md px-2.5 py-1.5 text-sm transition-colors ${
                  isActive
                    ? "bg-surface-2 font-semibold text-ink"
                    : "text-ink-2 hover:bg-surface-2 hover:text-ink"
                }`
              }
            >
              <span className="w-4 text-center text-muted">{n.icon}</span>
              {n.label}
            </NavLink>
          ))}
        </nav>
        <div className="mt-auto px-2">
          <button
            onClick={onLogout}
            className="text-xs text-muted transition-colors hover:text-ink-2"
          >
            log out
          </button>
        </div>
      </aside>
      <main className="ml-52 min-w-0 flex-1 px-8 py-6">
        <Outlet />
      </main>
    </div>
  );
}
