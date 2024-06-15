import {
  OAuth2Token,
  OAuthClient,
  OAuthProvider,
  OAuthProviderSettings,
} from '@sema4ai/oauth-client';
import { baseUrl } from '~/lib/requestData';

/**
 * Used to collect the scopes needed by some action.
 */
export interface IRequiredOauth2Data {
  scopes: string[];
  description: string;
}

/**
 * Used to define oauth tokens which were actually collected from the user.
 */
export interface ICollectedOauth2Data {
  scopes: string[];
  token: OAuth2Token;
}

/**
 * The user should configure a map of provider->IOAuth2UserSetting
 * with the server information.
 */
export interface IOAuth2UserSetting {
  clientId: string;
  clientSecret: string;

  server?: string;
  tokenEndpoint?: string;
  authorizationEndpoint?: string;

  // The redirectUri is based on the current location of the host
  // and should not be specified.
  // redirectUri?: string;
}

// We define an IOauth2UserProvider instead of using the OAuthProvider because in the app we consider
// any name valid (and if a name -- say "yahoo", isn't in the pre-defined providers,
// we need to map it as OAuthProvider.generic to the library when needed).
export type IOauth2UserProvider = string;

export interface IOAuth2UserSettings {
  [key: IOauth2UserProvider]: IOAuth2UserSetting;
}

const useAsBase = baseUrl ? baseUrl : `${window.location.protocol}//${window.location.host}`;
export const OAUTH2_REDIRECT_URL = `${useAsBase}/oauth2/redirect/`;

const oauthProviderMap: { [key: string]: OAuthProvider } = {
  github: OAuthProvider.github,
  zendesk: OAuthProvider.zendesk,
  google: OAuthProvider.google,
  hubspot: OAuthProvider.hubspot,
  microsoft: OAuthProvider.microsoft,
  slack: OAuthProvider.slack,
};

export const getOauthProviderEnumFromStr = (provider: IOauth2UserProvider): OAuthProvider => {
  const found = oauthProviderMap[provider];
  if (found) {
    return found;
  }

  return OAuthProvider.generic;
};

export const DEFAULT = '<default>';

export const DEFAULT_OAUTH2_SETTINGS: IOAuth2UserSettings = {
  google: {
    clientId: '',
    clientSecret: '',
    server: DEFAULT,
    tokenEndpoint: DEFAULT,
    authorizationEndpoint: DEFAULT,
  },
  slack: {
    clientId: '',
    clientSecret: '',
    server: DEFAULT,
    tokenEndpoint: DEFAULT,
    authorizationEndpoint: DEFAULT,
  },
  zendesk: {
    clientId: '',
    clientSecret: '',
    server: DEFAULT,
    tokenEndpoint: DEFAULT,
    authorizationEndpoint: DEFAULT,
  },
  hubspot: {
    clientId: '',
    clientSecret: '',
    server: DEFAULT,
    tokenEndpoint: DEFAULT,
    authorizationEndpoint: DEFAULT,
  },
  github: {
    clientId: '',
    clientSecret: '',
    server: DEFAULT,
    tokenEndpoint: DEFAULT,
    authorizationEndpoint: DEFAULT,
  },
  microsoft: {
    clientId: '',
    clientSecret: '',
    server: DEFAULT,
    tokenEndpoint: DEFAULT,
    authorizationEndpoint: DEFAULT,
  },
};

export function asOAuth2Settings(settings: any): IOAuth2UserSettings {
  for (const provider of Object.keys(settings)) {
    if (typeof provider === 'string') {
      const setting = settings[provider];
      const settingKeys = Object.keys(setting);
      if (!settingKeys.includes('clientId')) {
        throw new Error(`Did not find "clientId" in settings for ${provider}`);
      }
      if (!settingKeys.includes('clientSecret')) {
        throw new Error(`Did not find "clientSecret" in settings for ${provider}`);
      }
      if (settingKeys.includes('server') && typeof setting.server !== 'string') {
        throw new Error(`Expected "server" to be a string in settings for ${provider}`);
      }
      if (settingKeys.includes('tokenEndpoint') && typeof setting.tokenEndpoint !== 'string') {
        throw new Error(`Expected "tokenEndpoint" to be a string in settings for ${provider}`);
      }
      if (
        settingKeys.includes('authorizationEndpoint') &&
        typeof setting.authorizationEndpoint !== 'string'
      ) {
        throw new Error(
          `Expected "authorizationEndpoint" to be a string in settings for ${provider}`,
        );
      }
      if (settingKeys.includes('redirectUri') && typeof setting.redirectUri !== 'string') {
        throw new Error(`Expected "redirectUri" to be a string in settings for ${provider}`);
      }
    } else {
      throw new Error(`Expected ${provider} to be a string.`);
    }
  }
  return settings as IOAuth2UserSettings;
}

export const createOAuthProviderSettingsFromUserSettings = (
  provider: IOauth2UserProvider,
  settings: IOAuth2UserSetting,
): Partial<OAuthProviderSettings> => {
  if (!settings.clientId) {
    throw new Error(`Unable to make login because the ${provider} "clientId" is not configured.`);
  }
  if (!settings.clientSecret) {
    throw new Error(
      `Unable to make login because the ${provider} "clientSecret" is not configured.`,
    );
  }

  const ret: Partial<OAuthProviderSettings> = {
    clientId: settings.clientId,
    clientSecret: settings.clientSecret,
    redirectUri: OAUTH2_REDIRECT_URL,
  };
  if (settings.server && settings.server !== DEFAULT) {
    ret.server = settings.server;
  }
  if (settings.tokenEndpoint && settings.tokenEndpoint !== DEFAULT) {
    ret.tokenEndpoint = settings.tokenEndpoint;
  }
  if (settings.authorizationEndpoint && settings.authorizationEndpoint !== DEFAULT) {
    ret.authorizationEndpoint = settings.authorizationEndpoint;
  }
  return ret;
};

export const createClientFromSettings = (
  provider: IOauth2UserProvider,
  settings: IOAuth2UserSetting,
): OAuthClient => {
  const client = new OAuthClient(
    getOauthProviderEnumFromStr(provider),
    createOAuthProviderSettingsFromUserSettings(provider, settings),
  );
  return client;
};

export const mergeScopes = (a: string[], b: string[]): string[] => {
  return Array.from(new Set(a.concat(b)));
};

export const areScopesEqual = (a: string[], b: string[]): boolean =>
  a.length === b.length && a.every((val, index) => val === b[index]);

export const isOAuthTokenExpired = (expiryDate: number | null): boolean => {
  if (!expiryDate) {
    return false;
  }

  const expiryWindow = 10 * 60 * 1000; // Ten minutes
  const currentTime = Date.now();

  return expiryDate - currentTime < expiryWindow;
};
