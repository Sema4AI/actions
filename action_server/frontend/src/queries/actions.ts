/* eslint-disable no-restricted-syntax */
/* eslint-disable @typescript-eslint/no-explicit-any */
import { useMutation } from '@tanstack/react-query';

export type ActionRunPayload = {
  actionPackageName: string;
  actionName: string;
  args: object;
  apiKey?: string;
  secretsData?: Map<string, string>;
  requestId?: string;
};

export const useActionRunMutation = () => {
  return useMutation({
    mutationFn: async ({
      actionPackageName,
      args,
      actionName,
      apiKey,
      secretsData,
      requestId,
    }: ActionRunPayload) => {
      const headers: Record<string, string> = {
        Authorization: `Bearer ${apiKey}`,
      };

      const secretDataAsObject: any = {};

      if (secretsData && secretsData.size > 0) {
        // Convert from map to object for json serialization.
        for (const [key, val] of secretsData.entries()) {
          secretDataAsObject[key] = val;
        }
      }

      headers['x-action-context'] = btoa(JSON.stringify({ secrets: secretDataAsObject }));

      if (requestId) {
        headers['x-actions-request-id'] = requestId;
      }

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
