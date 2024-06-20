import { Dispatch, SetStateAction, createContext, useContext } from 'react';
import { LoadedActionsPackages, LoadedRuns, ServerConfig } from './types';
import { DEFAULT_OAUTH2_SETTINGS, IOAuth2UserSettings } from './oauth2';

export type ViewSettings = {
  theme: 'dark' | 'light';
};

export type ActionServerContextType = {
  viewSettings: ViewSettings;
  setViewSettings: Dispatch<SetStateAction<ViewSettings>>;
  loadedRuns: LoadedRuns;
  setLoadedRuns: Dispatch<SetStateAction<LoadedRuns>>;
  loadedActions: LoadedActionsPackages;
  setLoadedActions: Dispatch<SetStateAction<LoadedActionsPackages>>;
  serverConfig?: ServerConfig;
  oauth2Settings: IOAuth2UserSettings;
  setOAuth2Settings: Dispatch<SetStateAction<IOAuth2UserSettings>>;
};

export const defaultActionServerState: ActionServerContextType = {
  viewSettings: {
    theme: 'dark',
  },
  setViewSettings: () => null,

  // Runs
  loadedRuns: {
    isPending: true,
    data: [],
    errorMessage: undefined,
  },
  setLoadedRuns: () => null,

  // Actions
  loadedActions: {
    isPending: true,
    data: [],
    errorMessage: undefined,
  },
  setLoadedActions: () => null,

  // OAuth2
  oauth2Settings: DEFAULT_OAUTH2_SETTINGS,
  setOAuth2Settings: () => null,
};

export const ActionServerContext = createContext<ActionServerContextType>(defaultActionServerState);

export const useActionServerContext = () => {
  return useContext(ActionServerContext);
};
