import { FC, useCallback, useState } from 'react';
import { Code } from '~/components/Code';
import { useActionServerContext } from '~/lib/actionServerContext';
import { asOAuth2Settings } from '~/lib/oauth2';

export const OAuth2Settings: FC<{}> = ({}) => {
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
        setErrorJSON('Invalid output: ' + (err as Error).message);
      }
    },
    [setOAuth2Settings, setErrorJSON, setJsonBuffer],
  );

  let useAsBuffer: string = '';
  if (!jsonBuffer || jsonBuffer.length === 0) {
    useAsBuffer = JSON.stringify(oauth2Settings);
  } else {
    useAsBuffer = jsonBuffer;
  }

  return (
    <Code
      lang="json"
      aria-label="OAuth2 Settings"
      value={useAsBuffer}
      onChange={onCodeChange}
      error={errorJSON}
      readOnly={false}
      lineNumbers
      autoFocus
    />
  );
};
