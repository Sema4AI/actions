/* eslint-disable react/no-array-index-key */
/* eslint-disable no-restricted-syntax */
/* eslint-disable no-continue */
/* eslint-disable @typescript-eslint/no-explicit-any */
/* eslint-disable react/jsx-no-useless-fragment */
/* eslint-disable jsx-a11y/anchor-is-valid */
/* eslint-disable @typescript-eslint/no-use-before-define */
/* eslint-disable @typescript-eslint/no-unused-vars */
import { ChangeEvent, FC, FormEvent, ReactNode, useCallback, useEffect, useState } from 'react';
import {
  Box,
  Button,
  Checkbox,
  Divider,
  Form,
  Input,
  Link,
  Select,
  Switch,
  Typography,
} from '@sema4ai/components';
import { IconBolt, IconLoading, IconLogIn, IconLogOut } from '@sema4ai/icons';

import { Action, ActionPackage, AsyncLoaded, RunStatus, ServerConfig } from '@/shared/types';
import { toKebabCase } from '@/shared/utils/helpers';
import { useActionServerContext } from '@/shared/context/actionServerContext';
import { useLocalStorage } from '@/shared/hooks/useLocalStorage';
import {
  formDataToPayload,
  Payload,
  payloadToFormData,
  propertiesToFormData,
  PropertyFormData,
  PropertyFormDataType,
  setArrayItemTitle,
} from '@/shared/utils/formData';
import { useActionRunMutation } from '~/queries/actions';
import { Code } from '~/components/Code';
import {
  ICollectedOauth2Tokens,
  IOAuth2UserProvider,
  IProviderToCollectedOauth2Tokens,
  IRequiredOauth2Data,
} from '@/shared/utils/oauth2';
import { collectOAuth2Status } from '@/shared/api-client';
import { CancelButton } from '~/components/CancelButton';
import { ActionRunResult } from './ActionRunResult';
import { ErrorDialog, ErrorDialogInfo } from './ErrorDialog';

let lastRequestId: string | undefined;
type Props = {
  action: Action;
  actionPackage: ActionPackage;
};

const Item: FC<{ children?: ReactNode; title?: string; name: string }> = ({
  children,
  title,
  name,
}) => {
  const indent = name.split('.').length - 1;
  return (
    <Box pl={indent * 8}>
      {title && (
        <Typography mb="$8" variant="display.small">
          {title}
        </Typography>
      )}
      {children}
    </Box>
  );
};

const ItemArray: FC<{ children?: ReactNode; title?: string; name: string }> = ({
  children,
  title,
  name,
}) => {
  const indent = name.split('.').length - 2;
  return (
    <Box display="flex" justifyContent="space-between" pl={indent * 16}>
      <Typography mb="$8" variant="display.small">
        {title}
      </Typography>
      {children}
    </Box>
  );
};

const asFloat = (v: string) => {
  // note: the current approach of always converting to the actual
  // data has a big drawback: the user can't have invalid data
  // temporarily (so, he can't enter 10e-10 as the 'e' can never
  // be entered and even if the user copies/pastes it the value
  // will be converted from the internal float value -- maybe
  // this should be revisited later on so that internal values
  // for basic types are always strings).
  // For the time being this is a limitation of the current approach
  // (so, it's possible that a Nan is generated here and then
  // the handleInputChange needs to guard against it).
  return parseFloat(v);
};

const asInt = (v: string) => {
  return parseInt(v, 10);
};

type ManagedParams = Record<string, any>;

export const ActionRun: FC<Props> = ({ action, actionPackage }) => {
  // The API key is currently saved in the local storage.
  const [apiKey, setApiKey] = useLocalStorage<string>('api-key', '');

  const { loadedServerConfig } = useActionServerContext();
  const { mutate: runAction, isPending, isSuccess, data, reset } = useActionRunMutation();
  const [formData, setFormData] = useState<PropertyFormData[]>([]);
  const [secretsData, setSecretsData] = useState<Map<string, string>>(new Map());

  // This is the information on the data required for oauth2 (not the actually obtained
  // tokens which must be collected based on it).
  const [requiredOauth2SecretsData, setRequiredOauth2SecretsData] = useState<
    Map<IOAuth2UserProvider, IRequiredOauth2Data>
  >(new Map());

  // Information on the secrets collected (by the backend).
  const [oauth2SecretsData, setOauth2SecretsData] = useState<
    AsyncLoaded<IProviderToCollectedOauth2Tokens>
  >({ data: {}, isPending: false, errorMessage: undefined });

  const [useRawJSON, setUseRawJSON] = useState<boolean>(false);
  const [formRawJSON, setFormRawJSON] = useState<string>('');
  const [errorJSON, setErrorJSON] = useState<string>();
  const [errorDialogMessage, setErrorDialogMessage] = useState<ErrorDialogInfo>();
  const [collectOAuth2Mtime, setCollectOAuth2Mtime] = useState<number>(0);

  useEffect(() => {
    if (action.managed_params_schema) {
      const managedParams: ManagedParams = JSON.parse(action.managed_params_schema);

      const secretsMap: Map<string, string> = new Map();
      const requiredOauth2: Map<string, IRequiredOauth2Data> = new Map();

      for (const [key, val] of Object.entries(managedParams)) {
        if (val?.type === 'Secret') {
          secretsMap.set(key, '');
        } else if (val?.type === 'OAuth2Secret') {
          const { provider } = val;
          const { scopes } = val;
          const { description } = val;
          const existing = requiredOauth2.get(provider);
          if (!existing) {
            requiredOauth2.set(provider, { scopes, description, paramNames: [key] });
          } else {
            for (const s of scopes) {
              // Just update the existing scopes (in practice I guess this shouldn't even
              // happen, as it'd be kind of silly to add more than one provider of the same type
              // in a single action but no harm in supporting it either).
              if (!existing.scopes.includes(s)) {
                existing.scopes.push(s);
              }
            }
          }
        }
      }
      setSecretsData(secretsMap);
      setRequiredOauth2SecretsData(requiredOauth2);
    } else {
      setSecretsData(new Map());
    }
  }, [action, actionPackage]);

  useEffect(() => {
    if (requiredOauth2SecretsData.size > 0) {
      collectOAuth2Status(setOauth2SecretsData, {});
    }
  }, [requiredOauth2SecretsData, collectOAuth2Mtime]);

  useEffect(() => {
    setFormData(propertiesToFormData(JSON.parse(action.input_schema)));
  }, [action, actionPackage]);

  const handleInputChange = useCallback((value: PropertyFormDataType, index: number) => {
    if (typeof value === 'number') {
      if (Number.isNaN(value)) {
        // i.e.: this means the user entered a bad value. Don't enter it as the roundtrip
        // would make the user loose the current value up to this point.
        return;
      }
    }
    setFormData((curr) => curr.map((item, idx) => (idx === index ? { ...item, value } : item)));
    reset();
  }, []);

  const onAddRow = (index: number) => {
    setFormData((curr) => {
      let row: PropertyFormData[] = JSON.parse(JSON.stringify(curr[index].value));

      const depth = curr[index].name.split('.').length + 1;

      const lastIndex =
        curr
          .findLast((item) => item.name.startsWith(curr[index].name))
          ?.name.split('.')
          .slice(depth - 1)[0] || '0';

      const newIndex = parseInt(lastIndex, 10) + 1;

      row = row.map((item) => {
        const suffix = item.name.split('.').slice(depth).join('.');
        const newName = `${curr[index].name}.${newIndex}${suffix ? `.${suffix}` : suffix}`;

        const ret = {
          ...item,
          name: newName,
        };
        setArrayItemTitle(item);
        return ret;
      });

      let indexAt = index + 1;

      for (let i = index; i <= curr.length - 1; i += 1) {
        if (curr[i].name.startsWith(curr[index].name)) {
          indexAt = i + 1;
        } else {
          break;
        }
      }

      if (Array.isArray(row)) {
        return [...curr.slice(0, indexAt), ...row, ...curr.slice(indexAt)];
      }

      return curr;
    });
  };

  const onSubmit = useCallback(
    async (e: FormEvent) => {
      e.preventDefault();
      let args;
      try {
        args = useRawJSON ? JSON.parse(formRawJSON) : formDataToPayload(formData);
      } catch (err) {
        setErrorDialogMessage({
          errorMessage: 'Invalid input (the input cannot be converted to JSON).',
          errorTitle: 'Unable to run',
        });
        return;
      }
      const serverConfig: ServerConfig | undefined = loadedServerConfig.data;
      try {
        lastRequestId = crypto.randomUUID();
        runAction({
          actionPackageName: toKebabCase(actionPackage.name),
          actionName: toKebabCase(action.name),
          args,
          apiKey: serverConfig?.auth_enabled ? apiKey : undefined,
          secretsData,
          requestId: lastRequestId,
        });
      } catch (error) {
        setErrorDialogMessage({
          errorMessage: (error as Error).message,
          errorTitle: 'Unable to run',
        });
      }
    },
    [
      action,
      actionPackage,
      formData,
      apiKey,
      loadedServerConfig,
      useRawJSON,
      formRawJSON,
      secretsData,
      oauth2SecretsData,
    ],
  );

  const onCodeChange = useCallback(
    (value: string) => {
      setFormRawJSON(value);
      try {
        JSON.parse(value) as Payload;
        setErrorJSON(undefined);
      } catch (_) {
        setErrorJSON('Error while parsing JSON. Please review value and try again');
      }
    },
    [setFormRawJSON, setErrorJSON],
  );

  useEffect(() => {
    setFormData(propertiesToFormData(JSON.parse(action.input_schema)));
  }, [action, actionPackage]);

  useEffect(() => {
    if (!useRawJSON) {
      try {
        setFormData(payloadToFormData(JSON.parse(formRawJSON), formData));
      } catch (err) {
        // eslint-disable-line no-empty
      }
    } else {
      try {
        if (formData.length === 0) {
          setFormRawJSON('');
        } else {
          const payload = formDataToPayload(formData);
          setFormRawJSON(JSON.stringify(payload, null, 4));
        }
      } catch (err) {
        // eslint-disable-line no-empty
      }
    }
  }, [useRawJSON]);

  let secretsFields;
  if (secretsData || requiredOauth2SecretsData) {
    const secretsFieldsChildren = [];
    let i = 0;
    if (secretsData) {
      for (const [key, value] of secretsData.entries()) {
        i += 1;
        const onChangeSecret = (e: ChangeEvent<HTMLInputElement>) => {
          setSecretsData((old) => {
            const newSecrets: Map<string, string> = new Map(old);
            newSecrets.set(key, e.target.value);
            return newSecrets;
          });
        };
        secretsFieldsChildren.push(
          <Input
            key={`secret-${i}`}
            label={`Secret: ${key} *`}
            type="password"
            value={value}
            onChange={onChangeSecret}
          />,
        );
      }
    }

    if (requiredOauth2SecretsData) {
      i = 0;
      for (const [key, value] of requiredOauth2SecretsData.entries()) {
        i += 1;
        if (oauth2SecretsData.isPending) {
          secretsFieldsChildren.push(
            <Link
              key={`oauthSecret-${i}`}
              icon={IconLoading}
              href="#"
              target="_blank"
              rel="noopener"
              variant="subtle"
              fontWeight="medium"
            >
              Loading {`${key}`}
            </Link>,
          );
          continue;
        }
        const useData = oauth2SecretsData.data;

        const currentCollectedTokens: ICollectedOauth2Tokens | undefined = !useData
          ? undefined
          : useData[key];

        let loginRequired = !currentCollectedTokens;
        if (currentCollectedTokens && currentCollectedTokens.scopes) {
          for (const scope of value.scopes) {
            if (!currentCollectedTokens.scopes.includes(scope)) {
              loginRequired = true;
              break;
            }
          }
        }

        if (loginRequired) {
          secretsFieldsChildren.push(
            <Link
              key={`oauthSecret-${i}`}
              icon={IconLogIn}
              href="#"
              target="_blank"
              rel="noopener"
              variant="subtle"
              fontWeight="medium"
              onClick={(ev) => {
                ev.preventDefault();
                const { scopes } = value;
                onLogin(key, scopes, setCollectOAuth2Mtime, setErrorDialogMessage);
              }}
            >
              Login {`${key}`}
            </Link>,
          );
        } else {
          secretsFieldsChildren.push(
            <Link
              key={`oauthSecret-${i}`}
              icon={IconLogOut}
              href="#"
              target="_blank"
              rel="noopener"
              variant="subtle"
              fontWeight="medium"
              onClick={(ev) => {
                ev.preventDefault();
                onLogout(key, setCollectOAuth2Mtime, setErrorDialogMessage);
              }}
            >
              Logout {`${key}`}
            </Link>,
          );
        }
      }
    }

    secretsFields = <Form.Fieldset>{secretsFieldsChildren}</Form.Fieldset>;
  }

  const serverConfig: ServerConfig | undefined = loadedServerConfig.data;

  return (
    <Form busy={isPending} onSubmit={onSubmit}>
      {errorDialogMessage ? (
        <ErrorDialog
          info={errorDialogMessage}
          clearError={() => {
            setErrorDialogMessage(undefined);
          }}
        />
      ) : (
        <></>
      )}
      {serverConfig?.auth_enabled && (
        <Form.Fieldset>
          <Input
            label="API Key *"
            description="Bearer key printed out when '--expose' is used"
            type="password"
            value={apiKey}
            onChange={(e) => setApiKey(e.target.value)}
          />
        </Form.Fieldset>
      )}
      {secretsFields}
      {useRawJSON ? (
        <Code
          key="form-raw-json-input"
          lang="json"
          aria-label="Run JSON input"
          value={formRawJSON}
          onChange={onCodeChange}
          error={errorJSON}
          readOnly={false}
          lineNumbers
          autoFocus
        />
      ) : (
        <Form.Fieldset key="form-field-sets">
          {formData.map((item, index) => {
            const title = `${item.property.title}${item.required ? ' *' : ''}`;

            switch (item.property.type) {
              case 'boolean':
                return (
                  <Item title={item.title} name={item.name} key={item.name}>
                    <Checkbox
                      key={`${title}-${item.name}-${index}`}
                      label={title}
                      description={item.property.description}
                      checked={typeof item.value === 'boolean' && item.value}
                      required={item.required}
                      onChange={(e) => handleInputChange(e.target.checked, index)}
                    />
                  </Item>
                );
              case 'number':
                return (
                  <Item title={item.title} name={item.name} key={item.name}>
                    <Input
                      key={`${title}-${item.name}-${index}`}
                      label={title}
                      description={item.property.description}
                      required={item.required}
                      value={typeof item.value === 'number' ? item.value.toString() : '0'}
                      type="number"
                      onChange={(e) => handleInputChange(asFloat(e.target.value), index)}
                    />
                  </Item>
                );
              case 'integer':
                return (
                  <Item title={item.title} name={item.name} key={item.name}>
                    <Input
                      key={`${title}-${item.name}-${index}`}
                      label={title}
                      description={item.property.description}
                      required={item.required}
                      value={typeof item.value === 'number' ? item.value.toString() : '0'}
                      type="number"
                      onChange={(e) => handleInputChange(asInt(e.target.value), index)}
                    />
                  </Item>
                );
              case 'object':
                return (
                  <Item title={item.title} name={item.name} key={item.name}>
                    <Input
                      key={`${title}-${item.name}-${index}`}
                      label={title}
                      description={item.property.description}
                      required={item.required}
                      value={
                        typeof item.value === 'string'
                          ? item.value.toString()
                          : JSON.stringify(item.value)
                      }
                      rows={4}
                      onChange={(e) => handleInputChange(e.target.value, index)}
                    />
                  </Item>
                );
              case 'enum':
                return (
                  <Item title={item.title} name={item.name} key={item.name}>
                    <Select
                      key={`${title}-${item.name}-${index}`}
                      label={title}
                      description={item.property.description}
                      required={item.required}
                      value={
                        typeof item.value === 'string' ? item.value : JSON.stringify(item.value)
                      }
                      items={item.options?.map((value) => ({ label: value, value })) || []}
                      onChange={(e) => handleInputChange(e, index)}
                    />
                  </Item>
                );
              case 'array':
                return (
                  <ItemArray title={title} name={item.name} key={item.name}>
                    <Button type="button" onClick={() => onAddRow(index)} size="small">
                      Add row
                    </Button>
                  </ItemArray>
                );
              case 'string':
              default:
                return (
                  <Item title={item.title} name={item.name} key={item.name}>
                    <Input
                      key={`${title}-${item.name}-${index}`}
                      label={title}
                      description={item.property.description}
                      rows={1}
                      required={item.required}
                      value={
                        typeof item.value === 'string' ? item.value : JSON.stringify(item.value)
                      }
                      onChange={(e) => handleInputChange(e.target.value, index)}
                    />
                  </Item>
                );
            }
          })}
        </Form.Fieldset>
      )}
      <Button.Group align="right" marginBottom={isSuccess ? 16 : 32} justifyContent="space-between">
        <Button
          loading={isPending}
          type="submit"
          variant="primary"
          icon={IconBolt}
          style={{ width: '160px' }}
          disabled={errorJSON !== undefined}
        >
          {isPending ? 'Executing...' : 'Execute Action'}
        </Button>
        {isPending && lastRequestId && (
          <CancelButton requestId={lastRequestId} status={RunStatus.RUNNING} />
        )}
        <Switch
          label=""
          value="Use JSON"
          checked={useRawJSON}
          onChange={(e) => setUseRawJSON(e.target.checked)}
        />
      </Button.Group>
      <Divider />
      {isSuccess && (
        <ActionRunResult
          result={data.response}
          runId={data.runId}
          outputSchemaType={JSON.parse(action.output_schema) as { type: string }}
        />
      )}
    </Form>
  );
};

const onLogin = async (
  provider: IOAuth2UserProvider,
  scopes: string[],
  setCollectOAuth2Mtime: React.Dispatch<React.SetStateAction<number>>,
  setErrorDialogMessage: React.Dispatch<React.SetStateAction<ErrorDialogInfo | undefined>>,
) => {
  try {
    const uri = `/oauth2/login?provider=${provider}&scopes=${scopes.join(' ')}`;

    const authWindow = window.open(uri, undefined, 'width=800,height=800,popup=true');
    if (authWindow) {
      // The authWindow will call this function when it's finished.
      window.finishOAuth2 = async () => {
        authWindow.close();
        setCollectOAuth2Mtime((curr) => {
          return curr + 1;
        });
      };
    }
  } catch (error: any) {
    setErrorDialogMessage({ errorMessage: error.message, errorTitle: 'Unable to Login' });
  }
};

declare global {
  interface Window {
    finishOAuth2: (url: any) => void;
  }
}

const onLogout = async (
  provider: IOAuth2UserProvider,
  setCollectOAuth2Mtime: React.Dispatch<React.SetStateAction<number>>,
  setErrorDialogMessage: React.Dispatch<React.SetStateAction<ErrorDialogInfo | undefined>>,
) => {
  async function doLogOut() {
    let requestURL = '/oauth2/logout';
    const params = { provider };
    if (params) {
      requestURL += `?${new URLSearchParams(params)}`;
    }
    const method = 'GET';

    const fetchArgs: RequestInit = {
      method,
      headers: {
        Accept: 'application/json',
        'Content-Type': 'application/json',
      },
    };
    await fetch(requestURL, fetchArgs);

    setCollectOAuth2Mtime((curr) => {
      return curr + 1;
    });
  }
  doLogOut();
};
