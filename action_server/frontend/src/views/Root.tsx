import { SideNavigation, Box, Link, Scroll, useSystemTheme } from '@robocorp/components';
import { MouseEvent, StrictMode, useCallback, useEffect, useMemo, useState } from 'react';
import { ThemeOverrides, ThemeProvider, styled } from '@robocorp/theme';
import {
  IconAvatarHexagonal,
  IconBolt,
  IconGlobe,
  IconShare,
  IconUnorderedList,
} from '@robocorp/icons/iconic';
import { IconLogoRobocorp } from '@robocorp/icons/logos';
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
import { LoadedActionsPackages, LoadedRuns, ServerConfig } from '~/lib/types';
import {
  baseUrl,
  startTrackActions,
  startTrackRuns,
  stopTrackActions,
  stopTrackRuns,
} from '~/lib/requestData';
import { useLocalStorage } from '~/lib/useLocalStorage';

import { DEFAULT_OAUTH2_SETTINGS, IOAuth2UserSettings } from '~/lib/oauth2';
import { ActionRuns } from './runs';
import { ActionPackages } from './actions';
import {
  ActionServerContext,
  ActionServerContextType,
  ViewSettings,
  defaultActionServerState,
} from '../lib/actionServerContext';
import { OAuth2Settings } from './oauth2/components/Oauth2Settings';

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

  const [oauth2Settings, setOAuth2Settings] = useLocalStorage<IOAuth2UserSettings>(
    'oauth2/settings',
    DEFAULT_OAUTH2_SETTINGS,
  );

  const [loadedRuns, setLoadedRuns] = useState<LoadedRuns>(defaultActionServerState.loadedRuns);

  const [loadedActions, setLoadedActions] = useState<LoadedActionsPackages>(
    defaultActionServerState.loadedActions,
  );

  const [serverConfig, setServerConfig] = useState<ServerConfig | undefined>(undefined);

  const queryClient = new QueryClient();

  useEffect(() => {
    const fetchConfig = async () => {
      const response = await fetch(`${baseUrl}/config`);
      const payload = await response.json();
      setServerConfig(payload);
    };

    fetchConfig();
  }, []);

  const actionServerContextValue = useMemo<ActionServerContextType>(
    () => ({
      viewSettings,
      setViewSettings,
      loadedRuns,
      setLoadedRuns,
      loadedActions,
      setLoadedActions,
      serverConfig,
      oauth2Settings,
      setOAuth2Settings,
    }),
    [
      viewSettings,
      setViewSettings,
      loadedRuns,
      setLoadedRuns,
      loadedActions,
      setLoadedActions,
      serverConfig,
      oauth2Settings,
      setOAuth2Settings,
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

    return () => {
      stopTrackActions(setLoadedActions);
      stopTrackRuns(setLoadedRuns);
    };
  }, []);

  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider name={viewSettings.theme} overrides={overrides}>
        <ActionServerContext.Provider value={actionServerContextValue}>
          <Main isCollapsed={false}>
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
                {serverConfig?.expose_url && (
                  <SideNavigation.Link
                    href={serverConfig?.expose_url}
                    target="_blank"
                    icon={<IconGlobe />}
                  >
                    Public URL
                  </SideNavigation.Link>
                )}
                <SideNavigation.Link
                  aria-current={location.pathname.startsWith('/oauth2/settings')}
                  href="/oauth2/settings"
                  onClick={onNavigate('/oauth2/settings')}
                  icon={<IconAvatarHexagonal />}
                >
                  OAuth2 Settings
                </SideNavigation.Link>
                <SideNavigation.Link href="/openapi.json" target="_blank" icon={<IconShare />}>
                  OpenAPI spec
                </SideNavigation.Link>
              </ContentScroll>

              <Box display="flex" alignItems="center" ml={24} mt={8} color="content.subtle.light">
                <IconLogoRobocorp size={24} />
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
          path: 'oauth2/settings',
          element: <OAuth2Settings />,
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
