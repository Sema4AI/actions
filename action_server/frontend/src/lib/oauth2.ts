/* eslint-disable no-restricted-syntax */
/* eslint-disable @typescript-eslint/no-explicit-any */
/* eslint-disable @typescript-eslint/no-use-before-define */

/**
 * Used to collect the scopes needed by some action.
 */
export interface IRequiredOauth2Data {
  scopes: string[];
  description: string;
  paramNames: string[];
}

/**
 * Used to define oauth tokens which were actually collected from the user.
 */
export interface ICollectedOauth2Tokens {
  scopes: string[];
}

export interface IProviderToCollectedOauth2Tokens {
  [key: IOAuth2UserProvider]: ICollectedOauth2Tokens;
}

// We define an IOAuth2UserProvider instead of using the OAuthProvider because in the app we consider
// any name valid (and if a name -- say "yahoo", isn't in the pre-defined providers,
// we need to map it as OAuthProvider.generic to the library when needed).
export type IOAuth2UserProvider = string;
