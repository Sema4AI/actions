import { SideNavigation, Box, Link, Scroll, useSystemTheme } from '@sema4ai/components';
import { MouseEvent, StrictMode, useCallback, useEffect, useMemo, useState } from 'react';
import { ThemeOverrides, ThemeProvider, styled } from '@sema4ai/theme';
import { IconBolt, IconGlobe, IconShare, IconUnorderedList } from '@sema4ai/icons';
import { IconSema4 } from '@sema4ai/icons/logos';
import {
  Outlet,
  RouterProvider,
  createBrowserRouter,
  useLocation,
  useNavigate,
} from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

import { HeaderAndMenu } from '~/components/Header';
import { Redirect, SideHeader } from '~/components';
import { LoadedActionsPackages, LoadedServerConfig, LoadedRuns } from '~/lib/types';
import {
  startTrackActions,
  startTrackRuns,
  startTrackServerConfig,
  stopTrackActions,
  stopTrackRuns,
  stopTrackServerConfig,
} from '~/lib/requestData';
import { useLocalStorage } from '~/lib/useLocalStorage';

import { ActionRuns } from './runs';
import { ActionPackages } from './actions';
import {
  ActionServerContext,
  ActionServerContextType,
  ViewSettings,
  defaultActionServerState,
} from '../lib/actionServerContext';
import { CheckVersionDialog } from './actions/components/CheckVersionDialog';

const Main = styled.main<{ isCollapsed: boolean }>`
  background: ${({ theme }) => theme.colors.background.primary.color};
  height: 100%;
  display: grid;
  grid-template-columns: ${({ isCollapsed }) => (isCollapsed ? 0 : 240)}px 1fr;
  grid-template-rows: auto 1fr;
  grid-template-areas: 'aside header' 'aside section';
  ${({ theme }) => theme.screen.m} {
    grid-template-columns: 1fr;
    grid-template-areas: 'header' 'section';
  }

  > header {
    grid-area: header;
  }

  > aside {
    grid-area: aside;
  }

  > section {
    grid-area: section;
    padding: 0 calc(5rem - var(--scrollbar-width)) 3rem 5rem;

    ${({ theme }) => theme.screen.m} {
      padding: 0 ${({ theme }) => theme.space.$32};
    }

    ${({ theme }) => theme.screen.s} {
      padding: 0 ${({ theme }) => theme.space.$16};
    }
  }
`;

const overrides: ThemeOverrides = {
  fonts: {
    title:
      '-apple-system,BlinkMacSystemFont,Segoe UI,Helvetica,Arial,sans-serif,Apple Color Emoji,Segoe UI Emoji,Segoe UI Symbol',
    default:
      '-apple-system,BlinkMacSystemFont,Segoe UI,Helvetica,Arial,sans-serif,Apple Color Emoji,Segoe UI Emoji,Segoe UI Symbol',
  },
};

const ContentScroll = styled(Scroll)`
  min-height: 0px;

  > div {
    padding: 0 ${({ theme }) => theme.space.$8};
    border-radius: ${({ theme }) => theme.radii.$8};
  }
`;

const ErrorPage = () => {
  return (
    <div>
      <h4>Error: no content found at this url...</h4>
      <p>
        <br />
        <Link href="/">Navigate back to the Sema4.ai Action Server root url.</Link>
      </p>
    </div>
  );
};

const Root = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const systemTheme = useSystemTheme();

  const [viewSettings, setViewSettings] = useLocalStorage<ViewSettings>('view-settings', {
    theme: systemTheme,
  });

  const [loadedRuns, setLoadedRuns] = useState<LoadedRuns>(defaultActionServerState.loadedRuns);

  const [loadedActions, setLoadedActions] = useState<LoadedActionsPackages>(
    defaultActionServerState.loadedActions,
  );

  const [loadedServerConfig, setLoadedServerConfig] = useState<LoadedServerConfig>(
    defaultActionServerState.loadedServerConfig,
  );

  const queryClient = new QueryClient();

  const actionServerContextValue = useMemo<ActionServerContextType>(
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
      setLoadedRuns,
      loadedActions,
      setLoadedActions,
      loadedServerConfig,
    ],
  );
  const [showNavInSmallMode, setNavInSmallMode] = useState<boolean>(false);
  const onClose = useCallback(() => setNavInSmallMode(false), []);
  const onClickMenuButton = useCallback(() => setNavInSmallMode(true), []);

  const onNavigate = useCallback(
    (path: string) => (e: MouseEvent) => {
      e.preventDefault();
      navigate(path);
    },
    [],
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

  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider name={viewSettings.theme} overrides={overrides}>
        <ActionServerContext.Provider value={actionServerContextValue}>
          <Main isCollapsed={false}>
            <CheckVersionDialog config={{ serverConfig: loadedServerConfig.data }} />
            <HeaderAndMenu onClickMenuButton={onClickMenuButton} />
            <SideNavigation aria-label="Navigation" open={showNavInSmallMode} onClose={onClose}>
              <SideHeader />
              <ContentScroll>
                <SideNavigation.Link
                  aria-current={location.pathname.startsWith('/actions')}
                  href="/actions"
                  onClick={onNavigate('/actions')}
                  icon={<IconBolt />}
                >
                  Actions
                </SideNavigation.Link>
                <SideNavigation.Link
                  aria-current={location.pathname.startsWith('/runs')}
                  href="/runs"
                  onClick={onNavigate('/runs')}
                  icon={<IconUnorderedList />}
                >
                  Runs
                </SideNavigation.Link>
                {loadedServerConfig.data?.expose_url && (
                  <SideNavigation.Link
                    href={loadedServerConfig.data?.expose_url}
                    target="_blank"
                    icon={<IconGlobe />}
                  >
                    Public URL
                  </SideNavigation.Link>
                )}
                <SideNavigation.Link href="/openapi.json" target="_blank" icon={<IconShare />}>
                  OpenAPI spec
                </SideNavigation.Link>
              </ContentScroll>

              <Box display="flex" alignItems="center" ml={24} mt={8} color="content.subtle.light">
                <IconSema4 size={24} />
                <Box ml={8} fontSize={12}>
                  Powered by Sema4.ai
                </Box>
              </Box>
            </SideNavigation>
            <section>
              <Outlet />
            </section>
          </Main>
        </ActionServerContext.Provider>
      </ThemeProvider>
    </QueryClientProvider>
  );
};

export const ActionServerRoot = () => {
  const router = createBrowserRouter([
    {
      path: '/',
      element: <Root />,
      errorElement: <ErrorPage />,
      children: [
        {
          path: '',
          element: <Redirect path="/actions" />,
        },
        {
          path: '/actions/:actionId?',
          element: <ActionPackages />,
        },
        {
          path: 'runs',
          element: <ActionRuns />,
        },
        {
          path: 'runs/:runId',
          element: <ActionRuns />,
        },
        {
          path: '*',
          element: <ErrorPage />,
        },
      ],
    },
  ]);

  // Note: strict mode makes rendering twice, so, beware of duplicate network requests
  // due to the additional mount/unmount.
  return (
    <StrictMode>
      <RouterProvider router={router} />
    </StrictMode>
  );
};
