import React, { lazy, Suspense, useEffect, useMemo, useState, useContext } from 'react';
import {
  BrowserRouter,
  Link,
  Navigate,
  Route,
  Routes,
  useLocation,
} from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

import { ActionsPage } from '@/core/pages/Actions';
import { AnalyticsPage } from '@/core/pages/Analytics';
import { ArtifactsPage } from '@/core/pages/Artifacts';
import { LogsPage } from '@/core/pages/Logs';
import { RobotsPage } from '@/core/pages/Robots';
import { RunHistoryPage } from '@/core/pages/RunHistory';
import { WorkItemsPage } from '@/core/pages/WorkItems';
import {
  ActionServerContext,
  ActionServerContextType,
  defaultActionServerState,
} from '@/shared/context/actionServerContext';
import { useLocalStorage } from '@/shared/hooks/useLocalStorage';
import { useTheme } from '@/shared/hooks/useTheme';
import {
  startTrackActions,
  startTrackRuns,
  startTrackServerConfig,
  stopTrackActions,
  stopTrackRuns,
  stopTrackServerConfig,
} from '@/shared/api-client';
import { Button } from '@/core/components/ui/Button';
import { cn } from '@/shared/utils/cn';
import { LoadedActionsPackages, LoadedRuns, LoadedServerConfig } from '@/shared/types';

declare const __TIER__: 'community' | 'enterprise';

const queryClient = new QueryClient();
const isEnterpriseTier = __TIER__ === 'enterprise';

let EnterpriseKnowledgeBasePage: React.LazyExoticComponent<() => JSX.Element> | null = null;
let EnterpriseOrgManagementPage: React.LazyExoticComponent<() => JSX.Element> | null = null;
let EnterpriseSsoPage: React.LazyExoticComponent<() => JSX.Element> | null = null;

if (isEnterpriseTier) {
  EnterpriseKnowledgeBasePage = lazy(() => import('@/enterprise/pages/KnowledgeBase'));
  EnterpriseOrgManagementPage = lazy(() => import('@/enterprise/pages/OrgManagement'));
  EnterpriseSsoPage = lazy(() => import('@/enterprise/pages/SSO'));
}

// ============================================================================
// Icons
// ============================================================================

const LogoIcon = () => (
  <svg width="28" height="28" viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg">
    <circle cx="16" cy="16" r="14" stroke="currentColor" strokeWidth="2.5" className="text-primary" />
    <circle cx="16" cy="16" r="6" fill="currentColor" className="text-primary" />
    <path d="M16 2C16 2 20 8 20 16C20 24 16 30 16 30" stroke="currentColor" strokeWidth="2" className="text-primary/60" />
    <path d="M16 2C16 2 12 8 12 16C12 24 16 30 16 30" stroke="currentColor" strokeWidth="2" className="text-primary/60" />
  </svg>
);

const Sema4Logo = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
    <path d="M12 2L2 7L12 12L22 7L12 2Z" fill="currentColor" className="text-primary/80" />
    <path d="M2 17L12 22L22 17" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-primary/60" />
    <path d="M2 12L12 17L22 12" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-primary/40" />
  </svg>
);

const ActionsIcon = ({ className }: { className?: string }) => (
  <svg className={className} width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="m12 3-1.912 5.813a2 2 0 0 1-1.275 1.275L3 12l5.813 1.912a2 2 0 0 1 1.275 1.275L12 21l1.912-5.813a2 2 0 0 1 1.275-1.275L21 12l-5.813-1.912a2 2 0 0 1-1.275-1.275L12 3Z" />
  </svg>
);

const RunsIcon = ({ className }: { className?: string }) => (
  <svg className={className} width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <line x1="8" x2="21" y1="6" y2="6" />
    <line x1="8" x2="21" y1="12" y2="12" />
    <line x1="8" x2="21" y1="18" y2="18" />
    <line x1="3" x2="3.01" y1="6" y2="6" />
    <line x1="3" x2="3.01" y1="12" y2="12" />
    <line x1="3" x2="3.01" y1="18" y2="18" />
  </svg>
);

const AnalyticsIcon = ({ className }: { className?: string }) => (
  <svg className={className} width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <line x1="12" y1="20" x2="12" y2="10" />
    <line x1="18" y1="20" x2="18" y2="4" />
    <line x1="6" y1="20" x2="6" y2="16" />
  </svg>
);

const OpenApiIcon = ({ className }: { className?: string }) => (
  <svg className={className} width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
    <polyline points="14 2 14 8 20 8" />
    <path d="M10 12h4" />
    <path d="M10 16h4" />
  </svg>
);

const RobotsIcon = ({ className }: { className?: string }) => (
  <svg className={className} width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <rect x="3" y="11" width="18" height="10" rx="2" />
    <circle cx="12" cy="5" r="2" />
    <path d="M12 7v4" />
    <circle cx="8" cy="16" r="1" fill="currentColor" />
    <circle cx="16" cy="16" r="1" fill="currentColor" />
  </svg>
);

const WorkItemsIcon = ({ className }: { className?: string }) => (
  <svg className={className} width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <line x1="8" x2="21" y1="6" y2="6" />
    <line x1="8" x2="21" y1="12" y2="12" />
    <line x1="8" x2="21" y1="18" y2="18" />
    <line x1="3" x2="3.01" y1="6" y2="6" />
    <line x1="3" x2="3.01" y1="12" y2="12" />
    <line x1="3" x2="3.01" y1="18" y2="18" />
  </svg>
);

const LockIcon = ({ className }: { className?: string }) => (
  <svg className={className} width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <rect width="18" height="11" x="3" y="11" rx="2" ry="2" />
    <path d="M7 11V7a5 5 0 0 1 10 0v4" />
  </svg>
);

const SunIcon = ({ className }: { className?: string }) => (
  <svg className={className} width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <circle cx="12" cy="12" r="4" />
    <path d="M12 2v2" />
    <path d="M12 20v2" />
    <path d="m4.93 4.93 1.41 1.41" />
    <path d="m17.66 17.66 1.41 1.41" />
    <path d="M2 12h2" />
    <path d="M20 12h2" />
    <path d="m6.34 17.66-1.41 1.41" />
    <path d="m19.07 4.93-1.41 1.41" />
  </svg>
);

const MoonIcon = ({ className }: { className?: string }) => (
  <svg className={className} width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M12 3a6 6 0 0 0 9 9 9 9 0 1 1-9-9Z" />
  </svg>
);

const MonitorIcon = ({ className }: { className?: string }) => (
  <svg className={className} width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <rect width="20" height="14" x="2" y="3" rx="2" />
    <line x1="8" x2="16" y1="21" y2="21" />
    <line x1="12" x2="12" y1="17" y2="21" />
  </svg>
);

const SettingsIcon = ({ className }: { className?: string }) => (
  <svg className={className} width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <circle cx="12" cy="12" r="3" />
    <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z" />
  </svg>
);

// ============================================================================
// Navigation Items Configuration
// ============================================================================

type NavItem = {
  label: string;
  path: string;
  tier: 'core' | 'enterprise';
  icon: React.ComponentType<{ className?: string }>;
  exact?: boolean;
};

const NAV_ITEMS: NavItem[] = [
  { label: 'Actions', path: '/actions', tier: 'core', icon: ActionsIcon },
  { label: 'Runs', path: '/runs', tier: 'core', icon: RunsIcon },
  { label: 'Robots', path: '/robots', tier: 'core', icon: RobotsIcon },
  { label: 'Work Items', path: '/work-items', tier: 'core', icon: WorkItemsIcon },
  { label: 'Analytics', path: '/analytics', tier: 'core', icon: AnalyticsIcon },
  { label: 'OpenAPI spec', path: '/openapi', tier: 'core', icon: OpenApiIcon },
];

const ENTERPRISE_NAV_ITEMS: NavItem[] = [
  { label: 'Knowledge Base', path: '/knowledge-base', tier: 'enterprise', icon: ActionsIcon },
  { label: 'Org Management', path: '/org-management', tier: 'enterprise', icon: SettingsIcon },
  { label: 'SSO', path: '/sso', tier: 'enterprise', icon: LockIcon },
];

// ============================================================================
// Theme Toggle Component
// ============================================================================

const ThemeToggle = () => {
  const { theme, cycleTheme } = useTheme();

  const getThemeIcon = () => {
    switch (theme) {
      case 'dark':
        return <MoonIcon />;
      case 'system':
        return <MonitorIcon />;
      default:
        return <SunIcon />;
    }
  };

  return (
    <button
      onClick={cycleTheme}
      className={cn(
        // Layout
        'flex h-9 w-9 items-center justify-center',
        // Style
        'rounded-lg',
        // Colors
        'text-sidebar-foreground/70 hover:bg-sidebar-accent/20 hover:text-sidebar-foreground',
        // Focus states
        'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring',
        'focus-visible:ring-offset-2 focus-visible:ring-offset-sidebar',
        // Animations
        'transition-all duration-200 active:scale-95',
        'motion-reduce:transition-none motion-reduce:active:scale-100',
      )}
      aria-label={`Toggle theme (current: ${theme})`}
      title={`Theme: ${theme}`}
    >
      <span className="transition-transform duration-200 hover:rotate-12 motion-reduce:hover:rotate-0">
        {getThemeIcon()}
      </span>
    </button>
  );
};

// ============================================================================
// Sidebar Navigation
// ============================================================================

const Navigation = () => {
  const location = useLocation();
  const { loadedServerConfig } = useActionServerContext();

  const handleOpenApiClick = () => {
    window.open('/openapi.json', '_blank');
  };

  return (
    <aside className="sidebar flex w-56 flex-col">
      {/* Header with Logo */}
      <div className="flex h-14 items-center justify-between px-4">
        <div className="flex items-center gap-3">
          <LogoIcon />
          <span className="text-sm font-semibold text-sidebar-foreground">Action Server</span>
        </div>
        <ThemeToggle />
      </div>

      {/* Navigation Links */}
      <nav className="flex-1 space-y-1 px-3 py-2">
        {NAV_ITEMS.map((item) => {
          const isActive = item.exact
            ? location.pathname === item.path
            : location.pathname.startsWith(item.path);
          const Icon = item.icon;

          // Special handling for OpenAPI spec link
          if (item.path === '/openapi') {
            return (
              <button
                key={item.path}
                onClick={handleOpenApiClick}
                className="sidebar-nav-item animate-slide-in w-full"
              >
                <Icon className="h-4 w-4 flex-shrink-0" />
                <span>{item.label}</span>
              </button>
            );
          }

          return (
            <Link
              key={item.path}
              to={item.path}
              className={cn(
                'sidebar-nav-item animate-slide-in',
                isActive && 'active',
              )}
            >
              <Icon className="h-4 w-4 flex-shrink-0" />
              <span>{item.label}</span>
            </Link>
          );
        })}

        {/* Enterprise Features Section - Only show in enterprise tier */}
        {isEnterpriseTier && ENTERPRISE_NAV_ITEMS.length > 0 && (
          <div className="pt-4">
            <div className="px-3 py-2">
              <span className="text-xs font-medium uppercase tracking-wider text-sidebar-foreground/40">
                Enterprise
              </span>
            </div>
            {ENTERPRISE_NAV_ITEMS.map((item) => {
              const isActive = item.exact
                ? location.pathname === item.path
                : location.pathname.startsWith(item.path);
              const Icon = item.icon;

              return (
                <Link
                  key={item.path}
                  to={item.path}
                  className={cn(
                    'sidebar-nav-item animate-slide-in',
                    isActive && 'active',
                  )}
                >
                  <Icon className="h-4 w-4 flex-shrink-0" />
                  <span>{item.label}</span>
                </Link>
              );
            })}
          </div>
        )}
      </nav>

      {/* Footer */}
      <div className="border-t border-sidebar-accent/20 px-4 py-3">
        {loadedServerConfig.data?.version && (
          <div className="text-xs text-sidebar-foreground/40">
            v{loadedServerConfig.data.version}
          </div>
        )}
      </div>
    </aside>
  );
};

// ============================================================================
// Context Hook (needed by Navigation)
// ============================================================================

const useActionServerContext = () => {
  const context = useContext(ActionServerContext);
  if (!context) {
    throw new Error('useActionServerContext must be used within ActionServerProvider');
  }
  return context;
};

// ============================================================================
// Feature Unavailable Placeholder
// ============================================================================

const FeatureUnavailable = ({ feature }: { feature: string }) => (
  <div className="flex h-full items-center justify-center">
    <div className="max-w-md rounded-xl border border-border bg-card p-8 text-center shadow-lg">
      <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-primary/10">
        <LockIcon className="h-6 w-6 text-primary" />
      </div>
      <h2 className="text-lg font-semibold text-card-foreground">{feature}</h2>
      <p className="mt-3 text-sm text-muted-foreground">
        This feature is available in the Enterprise edition of Action Server.
      </p>
      <Button asChild className="mt-6" variant="default">
        <a href="https://sema4.ai" target="_blank" rel="noreferrer">
          Learn more
        </a>
      </Button>
    </div>
  </div>
);

// ============================================================================
// Enterprise Route Component
// ============================================================================

const EnterpriseRoute = ({
  component: Component,
  featureName
}: {
  component: React.LazyExoticComponent<() => JSX.Element> | null;
  featureName: string;
}) => {
  if (!isEnterpriseTier || !Component) {
    return <FeatureUnavailable feature={featureName} />;
  }

  return (
    <Suspense fallback={
      <div className="flex h-full items-center justify-center text-muted-foreground">
        Loading...
      </div>
    }>
      <Component />
    </Suspense>
  );
};

// ============================================================================
// Layout Component
// ============================================================================

const Layout = ({ children }: { children: React.ReactNode }) => {
  // Initialize theme on mount
  useTheme();

  return (
    <div className="flex min-h-screen bg-background">
      <Navigation />
      <main className="flex-1 overflow-auto">{children}</main>
    </div>
  );
};

// ============================================================================
// Context Provider
// ============================================================================

const ActionServerProvider = ({ children }: { children: React.ReactNode }) => {
  const [viewSettings, setViewSettings] = useLocalStorage('view-settings', { theme: 'dark' });
  const [loadedRuns, setLoadedRuns] = useState<LoadedRuns>(defaultActionServerState.loadedRuns);
  const [loadedActions, setLoadedActions] = useState<LoadedActionsPackages>(
    defaultActionServerState.loadedActions,
  );
  const [loadedServerConfig, setLoadedServerConfig] = useState<LoadedServerConfig>(
    defaultActionServerState.loadedServerConfig,
  );

  useEffect(() => {
    startTrackActions(setLoadedActions);
    startTrackRuns(setLoadedRuns);
    startTrackServerConfig(setLoadedServerConfig);

    return () => {
      stopTrackActions(setLoadedActions);
      stopTrackRuns(setLoadedRuns);
      stopTrackServerConfig(setLoadedServerConfig);
    };
  }, []);

  const value = useMemo<ActionServerContextType>(
    () => ({
      viewSettings,
      setViewSettings,
      loadedRuns,
      setLoadedRuns,
      loadedActions,
      setLoadedActions,
      loadedServerConfig,
      setLoadedServerConfig,
    }),
    [
      viewSettings,
      setViewSettings,
      loadedRuns,
      loadedActions,
      loadedServerConfig,
      setLoadedRuns,
      setLoadedActions,
      setLoadedServerConfig,
    ],
  );

  return <ActionServerContext.Provider value={value}>{children}</ActionServerContext.Provider>;
};

// ============================================================================
// Routes
// ============================================================================

const AppRoutes = () => {
  const location = useLocation();

  return (
    <div key={location.pathname} className="page-transition-wrapper h-full">
      <Routes location={location}>
        <Route path="/" element={<Navigate to="/actions" replace />} />
        <Route path="/actions" element={<ActionsPage />} />
        <Route path="/runs" element={<RunHistoryPage />} />
        <Route path="/robots" element={<RobotsPage />} />
        <Route path="/work-items" element={<WorkItemsPage />} />
        <Route path="/logs/:runId" element={<LogsPage />} />
        <Route path="/artifacts/:runId" element={<ArtifactsPage />} />

        <Route
          path="/knowledge-base"
          element={
            <EnterpriseRoute component={EnterpriseKnowledgeBasePage} featureName="Knowledge Base" />
          }
        />
        <Route path="/analytics" element={<AnalyticsPage />} />
        <Route
          path="/org-management"
          element={
            <EnterpriseRoute component={EnterpriseOrgManagementPage} featureName="Organization Management" />
          }
        />
        <Route
          path="/sso"
          element={
            <EnterpriseRoute component={EnterpriseSsoPage} featureName="SSO" />
          }
        />
        <Route path="*" element={<Navigate to="/actions" replace />} />
      </Routes>
    </div>
  );
};

// ============================================================================
// App Entry Point
// ============================================================================

export const App = () => {
  return (
    <QueryClientProvider client={queryClient}>
      <ActionServerProvider>
        <BrowserRouter>
          <Layout>
            <AppRoutes />
          </Layout>
        </BrowserRouter>
      </ActionServerProvider>
    </QueryClientProvider>
  );
};
