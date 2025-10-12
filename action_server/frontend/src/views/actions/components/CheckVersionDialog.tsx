/* eslint-disable no-restricted-globals */
/* eslint-disable @typescript-eslint/no-empty-function */
/* eslint-disable no-underscore-dangle */
/* eslint-disable no-console */

import { Button, Dialog, Tooltip } from '@sema4ai/components';
import { FC, useCallback, useState } from 'react';
import { ServerConfig } from '@/shared/types';

export interface CheckVersionDialogInfo {
  serverConfig: ServerConfig | undefined;
}

declare global {
  interface Window {
    // Not available with `npm run dev`, but should be available when
    // loaded from the action server backend.
    __ACTION_SERVER_VERSION__: string | undefined;
  }
}

if (!window.__ACTION_SERVER_VERSION__) {
  console.log(
    'Note: __ACTION_SERVER_VERSION__ not available (first version loaded from the backend will be considered the current one).',
  );
}

export const CheckVersionDialog: FC<{ config: CheckVersionDialogInfo }> = ({ config }) => {
  let versionChanged = false;

  const [lastVersion, setLastVersion] = useState<string | undefined>(
    window.__ACTION_SERVER_VERSION__,
  );

  if (config.serverConfig) {
    if (lastVersion === undefined) {
      setLastVersion(config.serverConfig.version);
    } else if (lastVersion !== config.serverConfig.version) {
      versionChanged = true;
    }
  }

  const ignore = useCallback(() => {
    if (config.serverConfig) {
      setLastVersion(config.serverConfig.version);
    }
  }, [config, lastVersion]);

  return (
    versionChanged && (
      <Dialog open onClose={() => {}} size="medium">
        <Dialog.Header>
          <Dialog.Header.Description>
            Action Server Backend version changed!
          </Dialog.Header.Description>
        </Dialog.Header>
        <Dialog.Content>How would you like to proceed?</Dialog.Content>
        <Dialog.Actions>
          <Button
            onClick={() => {
              location.reload();
            }}
            variant="primary"
          >
            Reload Page
          </Button>
          <Tooltip
            text={`Ignore to copy content being edited; 
              interacting with page may cause errors.`}
          >
            <Button onClick={ignore} variant="primary">
              Ignore
            </Button>
          </Tooltip>
        </Dialog.Actions>
      </Dialog>
    )
  );
};
