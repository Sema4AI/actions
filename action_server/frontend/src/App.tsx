import { lazy, Suspense, useEffect, useMemo, useState } from 'react';
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
import { ArtifactsPage } from '@/core/pages/Artifacts';
import { LogsPage } from '@/core/pages/Logs';
import { RunHistoryPage } from '@/core/pages/RunHistory';
import {
  ActionServerContext,
  ActionServerContextType,
  defaultActionServerState,
} from '@/shared/context/actionServerContext';
import { useLocalStorage } from '@/shared/hooks/useLocalStorage';
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
let EnterpriseAnalyticsPage: React.LazyExoticComponent<() => JSX.Element> | null = null;
let EnterpriseOrgManagementPage: React.LazyExoticComponent<() => JSX.Element> | null = null;
let EnterpriseSsoPage: React.LazyExoticComponent<() => JSX.Element> | null = null;

if (isEnterpriseTier) {
  EnterpriseKnowledgeBasePage = lazy(() => import('@/enterprise/pages/KnowledgeBase'));
  EnterpriseAnalyticsPage = lazy(() => import('@/enterprise/pages/Analytics'));
  EnterpriseOrgManagementPage = lazy(() => import('@/enterprise/pages/OrgManagement'));
  EnterpriseSsoPage = lazy(() => import('@/enterprise/pages/SSO'));
}

type NavItem = {
  label: string;
  path: string;
  tier: 'core' | 'enterprise';
  exact?: boolean;
};

const NAV_ITEMS: NavItem[] = [
  { label: 'Actions', path: '/actions', tier: 'core' },
  { label: 'Run History', path: '/runs', tier: 'core' },
  { label: 'Knowledge Base', path: '/knowledge-base', tier: 'enterprise' },
  { label: 'Analytics', path: '/analytics', tier: 'enterprise' },
  { label: 'Org Management', path: '/org-management', tier: 'enterprise' },
  { label: 'SSO', path: '/sso', tier: 'enterprise' },
];

const Navigation = () => {
  const location = useLocation();

  return (
    <aside className="flex w-64 flex-col border-r border-gray-200 bg-white">
      <div className="border-b border-gray-200 p-6">
        <h1 className="text-xl font-semibold text-gray-900">Action Server</h1>
        <p className="mt-2 text-sm text-gray-500 capitalize">{__TIER__} tier</p>
      </div>
      <nav className="flex-1 space-y-1 p-4">
        {NAV_ITEMS.map((item) => {
          const isActive = item.exact
            ? location.pathname === item.path
            : location.pathname.startsWith(item.path);
          const available = item.tier === 'core' || isEnterpriseTier;

          if (!available) {
            return (
              <div
                key={item.path}
                className="group flex items-center justify-between rounded-md px-3 py-2 text-sm text-gray-400"
              >
                <span>{item.label}</span>
                <span className="text-xs uppercase tracking-wide text-gray-300">Locked</span>
              </div>
            );
          }

          return (
            <Link
              key={item.path}
              to={item.path}
              className={cn(
                'flex items-center rounded-md px-3 py-2 text-sm font-medium transition-colors',
                isActive
                  ? 'bg-blue-50 text-blue-700'
                  : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900',
              )}
            >
              {item.label}
            </Link>
          );
        })}
      </nav>
      <div className="border-t border-gray-200 p-4 text-xs text-gray-400">
        Build {new Date().getFullYear()}
      </div>
    </aside>
  );
};

const FeatureUnavailable = ({ feature }: { feature: string }) => (
  <div className="flex h-full items-center justify-center">
    <div className="max-w-md rounded-md border border-gray-200 bg-white p-8 text-center shadow-sm">
      <h2 className="text-lg font-semibold text-gray-900">{feature}</h2>
      <p className="mt-3 text-sm text-gray-600">
        This feature is available in the Enterprise edition of Action Server. Upgrade or contact the
        Sema4.ai team to explore enterprise capabilities.
      </p>
      <Button
        asChild
        className="mt-6"
        variant="secondary"
      >
        <a href="https://sema4.ai" target="_blank" rel="noreferrer">
          Explore pricing
        </a>
      </Button>
    </div>
  </div>
);

const Layout = ({ children }: { children: React.ReactNode }) => (
  <div className="flex min-h-screen bg-gray-100">
    <Navigation />
    <main className="flex-1 overflow-auto p-6">{children}</main>
  </div>
);

const ActionServerProvider = ({ children }: { children: React.ReactNode }) => {
  const [viewSettings, setViewSettings] = useLocalStorage('view-settings', { theme: 'light' });
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

const AppRoutes = () => (
  <Routes>
    <Route path="/" element={<Navigate to="/actions" replace />} />
    <Route path="/actions" element={<ActionsPage />} />
    <Route path="/runs" element={<RunHistoryPage />} />
    <Route path="/logs/:runId" element={<LogsPage />} />
    <Route path="/artifacts/:runId" element={<ArtifactsPage />} />

    <Route
      path="/knowledge-base"
      element={
        isEnterpriseTier && EnterpriseKnowledgeBasePage ? (
          <Suspense fallback={<div>Loading enterprise module…</div>}>
            <EnterpriseKnowledgeBasePage />
          </Suspense>
        ) : (
          <FeatureUnavailable feature="Knowledge Base" />
        )
      }
    />
    <Route
      path="/analytics"
      element={
        isEnterpriseTier && EnterpriseAnalyticsPage ? (
          <Suspense fallback={<div>Loading enterprise module…</div>}>
            <EnterpriseAnalyticsPage />
          </Suspense>
        ) : (
          <FeatureUnavailable feature="Analytics" />
        )
      }
    />
    <Route
      path="/org-management"
      element={
        isEnterpriseTier && EnterpriseOrgManagementPage ? (
          <Suspense fallback={<div>Loading enterprise module…</div>}>
            <EnterpriseOrgManagementPage />
          </Suspense>
        ) : (
          <FeatureUnavailable feature="Organization Management" />
        )
      }
    />
    <Route
      path="/sso"
      element={
        isEnterpriseTier && EnterpriseSsoPage ? (
          <Suspense fallback={<div>Loading enterprise module…</div>}>
            <EnterpriseSsoPage />
          </Suspense>
        ) : (
          <FeatureUnavailable feature="SSO" />
        )
      }
    />
    <Route path="*" element={<Navigate to="/actions" replace />} />
  </Routes>
);

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
