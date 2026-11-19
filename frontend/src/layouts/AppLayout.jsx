import { useState } from 'react';
import { NavLink, Outlet, useLocation, useNavigate } from 'react-router-dom';
import {
  Activity,
  Bell,
  CheckSquare,
  FolderKanban,
  Kanban,
  LayoutDashboard,
  LogOut,
  Menu,
  Search,
  Settings,
  X,
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { BrandLogo } from '../components/common/BrandLogo';
import { getInitials } from '../utils/formatters';

const NAV_ITEMS = [
  { to: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { to: '/projects', label: 'Projects', icon: FolderKanban },
  { to: '/my-tasks', label: 'My Tasks', icon: CheckSquare },
  { to: '/kanban', label: 'Kanban Board', icon: Kanban },
  { to: '/notifications', label: 'Notifications', icon: Bell, showBadge: true },
  { to: '/activity', label: 'Activity Log', icon: Activity },
  { to: '/settings', label: 'Settings', icon: Settings },
];

function getPageTitle(pathname) {
  if (pathname.startsWith('/projects/')) return 'Project Details';
  const match = NAV_ITEMS.find((item) => pathname.startsWith(item.to));
  return match ? match.label : 'SprintFlow';
}

export function AppLayout() {
  const { user, unreadCount, logout } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();
  const [mobileOpen, setMobileOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');

  const pageTitle = getPageTitle(location.pathname);

  const handleGlobalSearch = (e) => {
    e.preventDefault();
    const q = searchQuery.trim();
    if (!q) return;
    navigate(`/projects?search=${encodeURIComponent(q)}`);
  };

  const handleLogout = () => {
    logout();
    navigate('/login', { replace: true });
  };

  const sidebarContent = (
    <div className="flex flex-col h-full bg-[#101010] text-white">
      <div className="h-16 px-5 flex items-center justify-between border-b border-neutral-800">
        <BrandLogo dark />
        <button
          type="button"
          onClick={() => setMobileOpen(false)}
          className="lg:hidden p-1.5 rounded-lg text-neutral-400 hover:text-white hover:bg-[#171717]"
          aria-label="Close sidebar"
        >
          <X className="w-5 h-5" />
        </button>
      </div>

      <nav className="flex-1 px-3 py-5 space-y-1 overflow-y-auto">
        {NAV_ITEMS.map(({ to, label, icon: Icon, showBadge }) => (
          <NavLink
            key={to}
            to={to}
            onClick={() => setMobileOpen(false)}
            className={({ isActive }) =>
              `relative flex items-center justify-between px-3.5 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                isActive
                  ? 'bg-[#171717] text-white'
                  : 'text-neutral-300 hover:bg-[#171717]/80 hover:text-white'
              }`
            }
          >
            {({ isActive }) => (
              <>
                {isActive && (
                  <span className="absolute left-0 top-1.5 bottom-1.5 w-1 rounded-r bg-[#75C900]" />
                )}
                <span className="flex items-center gap-3">
                  <Icon
                    className={`w-4 h-4 ${isActive ? 'text-[#75C900]' : 'text-white'}`}
                  />
                  <span>{label}</span>
                </span>
                {showBadge && unreadCount > 0 && (
                  <span className="px-2 py-0.5 text-[11px] font-bold rounded-full bg-[#75C900] text-[#101010]">
                    {unreadCount > 99 ? '99+' : unreadCount}
                  </span>
                )}
              </>
            )}
          </NavLink>
        ))}
      </nav>

      <div className="p-4 border-t border-neutral-800">
        <div className="flex items-center gap-3 px-2 py-2 rounded-lg bg-[#171717]">
          <div className="w-8 h-8 rounded-full bg-[#75C900] text-[#101010] font-bold text-xs flex items-center justify-center shrink-0">
            {getInitials(user?.full_name)}
          </div>
          <div className="min-w-0 flex-1">
            <p className="text-xs font-semibold text-white truncate">
              {user?.full_name}
            </p>
            <p className="text-[11px] text-neutral-400 truncate">{user?.email}</p>
          </div>
        </div>
      </div>
    </div>
  );

  return (
    <div className="min-h-screen bg-white flex">
      {/* Desktop sidebar */}
      <aside className="hidden lg:block w-64 shrink-0 fixed inset-y-0 left-0 z-30">
        {sidebarContent}
      </aside>

      {/* Mobile drawer */}
      {mobileOpen && (
        <div className="fixed inset-0 z-40 lg:hidden flex">
          <div className="w-64 shrink-0 h-full">{sidebarContent}</div>
          <div
            className="flex-1 bg-[#101010]/60"
            onClick={() => setMobileOpen(false)}
          />
        </div>
      )}

      {/* Main area */}
      <div className="flex-1 flex flex-col min-w-0 lg:pl-64">
        <header className="sticky top-0 z-20 h-16 bg-white border-b border-[#E5E5E5] px-4 sm:px-6 flex items-center justify-between gap-4">
          <div className="flex items-center gap-3 min-w-0">
            <button
              type="button"
              onClick={() => setMobileOpen(true)}
              className="lg:hidden p-2 rounded-lg text-[#101010] hover:bg-[#F5F5F5]"
              aria-label="Open navigation menu"
            >
              <Menu className="w-5 h-5" />
            </button>
            <h1 className="text-lg font-bold text-[#101010] truncate">{pageTitle}</h1>
          </div>

          <div className="flex items-center gap-3 sm:gap-4">
            <form onSubmit={handleGlobalSearch} className="hidden md:block relative">
              <Search className="w-4 h-4 text-[#737373] absolute left-3 top-1/2 -translate-y-1/2" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search projects..."
                className="w-60 lg:w-72 rounded-lg border border-[#E5E5E5] bg-[#F5F5F5] pl-9 pr-3 py-1.5 text-sm text-[#101010] placeholder:text-[#737373] focus:bg-white focus:outline-none focus:ring-2 focus:ring-[#75C900] focus:border-[#101010]"
              />
            </form>

            <button
              type="button"
              onClick={() => navigate('/notifications')}
              className="relative p-2 rounded-lg text-[#101010] hover:bg-[#F5F5F5] transition-colors"
              title="Notifications"
              aria-label="View notifications"
            >
              <Bell className="w-5 h-5" />
              {unreadCount > 0 && (
                <span className="absolute -top-0.5 -right-0.5 min-w-[18px] h-[18px] px-1 rounded-full bg-[#75C900] text-[#101010] text-[10px] font-bold flex items-center justify-center">
                  {unreadCount > 9 ? '9+' : unreadCount}
                </span>
              )}
            </button>

            <button
              type="button"
              onClick={() => navigate('/settings')}
              className="hidden sm:inline-flex items-center gap-2 px-2.5 py-1.5 rounded-lg border border-[#E5E5E5] hover:bg-[#F5F5F5] transition-colors"
              title="Account settings"
            >
              <span className="w-6 h-6 rounded-full bg-[#101010] text-[#75C900] text-[11px] font-bold flex items-center justify-center">
                {getInitials(user?.full_name)}
              </span>
              <span className="text-xs font-semibold text-[#101010] max-w-[120px] truncate">
                {user?.full_name}
              </span>
            </button>

            <button
              type="button"
              onClick={handleLogout}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-[#101010] text-xs font-semibold text-[#101010] hover:bg-[#101010] hover:text-white transition-colors"
              title="Log out"
            >
              <LogOut className="w-3.5 h-3.5" />
              <span className="hidden sm:inline">Logout</span>
            </button>
          </div>
        </header>

        <main className="flex-1 p-4 sm:p-6 lg:p-8 max-w-[1440px] w-full mx-auto">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
