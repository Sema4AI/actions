/* eslint-disable no-restricted-syntax */
/* eslint-disable @typescript-eslint/no-explicit-any */
import { useMutation } from '@tanstack/react-query';
import {
  ICollectedOauth2Tokens,
  IOAuth2UserProvider,
  IProviderToCollectedOauth2Tokens,
  IRequiredOauth2Data,
  isOAuthTokenExpired,
} from '~/lib/oauth2';

export type ActionRunPayload = {
  actionPackageName: string;
  actionName: string;
  args: object;
  apiKey?: string;
  secretsData?: Map<string, string>;
  oauth2SecretsData?: IProviderToCollectedOauth2Tokens;
  requiredOauth2SecretsData: Map<IOAuth2UserProvider, IRequiredOauth2Data>;
};

export const useActionRunMutation = () => {
  return useMutation({
    mutationFn: async ({
      actionPackageName,
      args,
      actionName,
      apiKey,
      secretsData,
      oauth2SecretsData,
      requiredOauth2SecretsData,
    }: ActionRunPayload) => {
      const headers: Record<string, string> = {
        Authorization: `Bearer ${apiKey}`,
      };

      const secretDataAsObject: any = {};
      let foundSecrets: boolean = false;

      if (secretsData && secretsData.size > 0) {
        foundSecrets = true;
        for (const [key, val] of secretsData.entries()) {
          secretDataAsObject[key] = val;
        }
      }

      if (requiredOauth2SecretsData && requiredOauth2SecretsData.size > 0) {
        if (!oauth2SecretsData) {
          throw new Error('Required OAuth2 data is not available.');
        }

        for (const [requiredProvider, requiredInfo] of requiredOauth2SecretsData.entries()) {
          const tokenInfo = oauth2SecretsData[requiredProvider];
          if (!tokenInfo) {
            throw new Error(`Login must be made for provider: ${requiredProvider}`);
          }

          for (const scope of requiredInfo.scopes) {
            if (!tokenInfo.scopes.includes(scope)) {
              throw new Error(
                `The required scope: ${scope} is not available for ${requiredProvider}. Please logout and login again to access all scopes required.`,
              );
            }
          }

          // Data must be filled as:
          // "my_oauth2_secret": {
          //   "provider": "google",
          //   "scopes": ["scope1", "scope2"],
          //   "access_token": "<this-is-the-access-token>",
          //   "metadata": { "any": "additional info" }
          // }
          for (const paramName of requiredInfo.paramNames) {
            secretDataAsObject[paramName] = {
              access_token: tokenInfo.token.accessToken,
              scopes: tokenInfo.scopes,
            };
          }
        }
      }
      headers['x-action-context'] = btoa(JSON.stringify({ secrets: secretDataAsObject }));

      const request = await fetch(`/api/actions/${actionPackageName}/${actionName}/run`, {
        method: 'POST',
        headers,
        body: JSON.stringify(args),
      });

      const runId = request.headers.get('X-Action-Server-Run-Id') || '';
      let response = '';

      try {
        const json = await request.json();
        response = JSON.stringify(json, null, 2);
      } catch {
        response = await request.text();
      }

      return {
        runId,
        response,
      };
    },
  });
};
