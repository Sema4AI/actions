/* eslint-disable @typescript-eslint/no-explicit-any */
/* eslint-disable no-alert */

import { Box, Button, Header, Link } from '@robocorp/components';
import { FC, useCallback, useState } from 'react';
import { Code } from '~/components/Code';
import { useActionServerContext } from '~/lib/actionServerContext';
import { IOAuth2UserSettings, OAUTH2_REDIRECT_URL, asOAuth2Settings } from '~/lib/oauth2';

const getProviderName = (oauth2Settings: IOAuth2UserSettings): string => {
  const baseName = 'fill-with-provider-name';
  for (let index = 0; index < 1000; index += 1) {
    const name = index === 0 ? baseName : `${baseName}-${index}`;
    if (!oauth2Settings[name]) {
      return name;
    }
  }
  return 'provider';
};

const addProvider = (jsonBuffer: string, setJsonBuffer: any, newContents: any) => {
  let loadedSettings;
  try {
    loadedSettings = JSON.parse(jsonBuffer);
  } catch (error) {
    alert(
      'Unable to add provider because the current contents are not valid as JSON. Please fix the syntax error(s) and retry.',
    );
  }
  if (loadedSettings !== undefined) {
    const newName = getProviderName(loadedSettings);
    loadedSettings[newName] = newContents;
    setJsonBuffer(JSON.stringify(loadedSettings, undefined, 4));
  }
};

export const OAuth2Settings: FC = () => {
  const [errorJSON, setErrorJSON] = useState<string>();
  const [jsonBuffer, setJsonBuffer] = useState<string>('');
  const { oauth2Settings, setOAuth2Settings } = useActionServerContext();

  const onCodeChange = useCallback(
    (value: string) => {
      setJsonBuffer(value);
      try {
        const loadedSettings = JSON.parse(value); // may throw
        setOAuth2Settings(asOAuth2Settings(loadedSettings)); // may throw

        setErrorJSON(undefined);
      } catch (err) {
        setErrorJSON(`Invalid output: ${(err as Error).message}`);
      }
    },
    [setOAuth2Settings, setErrorJSON, setJsonBuffer],
  );

  let useAsBuffer = '';
  if (!jsonBuffer || jsonBuffer.length === 0) {
    useAsBuffer = JSON.stringify(oauth2Settings, undefined, 4);
    if (useAsBuffer !== jsonBuffer) {
      setJsonBuffer(useAsBuffer);
    }
  } else {
    useAsBuffer = jsonBuffer;
  }

  const onAddSupported = useCallback(() => {
    addProvider(jsonBuffer, setJsonBuffer, { clientId: '', clientSecret: '' });
  }, [jsonBuffer, setJsonBuffer]);

  const onAddGeneric = useCallback(() => {
    addProvider(jsonBuffer, setJsonBuffer, {
      clientId: '',
      clientSecret: '',
      server: '',
      tokenEndpoint: '',
      authorizationEndpoint: '',
    });
  }, [jsonBuffer, setJsonBuffer]);

  return (
    <>
      <Header>
        <Header.Title title="OAuth2 Settings" />
      </Header>
      <p>
        Configure the OAuth2 Settings (as JSON) so that authentication using OAuth2 is possible.
      </p>
      <br />
      <p>
        <strong>See:</strong>
        <br />
        <Link
          href="https://github.com/Sema4AI/actions/blob/master/action_server/docs/guides/07-secrets.md#oauth2-secrets"
          fontWeight="medium"
        >
          OAuth2 Secrets Guide
        </Link>{' '}
        on how to create an <strong>@action</strong> that accepts OAuth2 Secrets.
      </p>
      <br />
      <p>
        <strong>Important:</strong>
      </p>
      <p>
        The <strong>redirectUri</strong> callback registered in the related provider must be:{' '}
        <strong>{OAUTH2_REDIRECT_URL}</strong>
      </p>
      <br />
      <p>
        <strong>Note:</strong>
      </p>
      <p>
        The providers supported out of the box (<strong>google</strong>, <strong>github</strong>,{' '}
        <strong>microsoft</strong>, <strong>slack</strong>, <strong>zendesk</strong> and{' '}
        <strong>hubspot</strong>) require <strong>clientId</strong> and{' '}
        <strong>clientSecret</strong> to be specified).
      </p>
      <br />
      <p>
        Any other provider besides those also needs to specify <strong>server</strong>,{' '}
        <strong>tokenEndpoint</strong> and <strong>authorizationEndpoint</strong>.
      </p>
      <br />
      <Button onClick={onAddSupported} variant="secondary">
        Add known provider
      </Button>
      <Button onClick={onAddGeneric} variant="secondary">
        Add generic provider
      </Button>
      <Box
        borderColor={errorJSON ? 'border.error' : 'background.primary'}
        p="$8"
        borderRadius="$16"
        borderWidth="3px"
      >
        <Code
          key="oauth2"
          lang="json"
          aria-label="OAuth2 Settings"
          value={useAsBuffer}
          onChange={onCodeChange}
          error={errorJSON}
          readOnly={false}
          lineNumbers
          autoFocus
          rows={30}
        />
      </Box>
    </>
  );
};
