import { FC } from 'react';
import { Header, Link } from '@sema4ai/components';
import { baseUrl } from '@/shared/api-client';
import { ActionRunConsole, Code } from '~/components';
import { IconFileText } from '@sema4ai/icons';

type Props = {
  result: string;
  runId: string;
  outputSchemaType?: { type: string };
};

const getFormattedString = (value: string): string => {
  const fmt = value.replaceAll('\\n', '\n').trim();
  if (fmt.charAt(0) === '"' && fmt.charAt(fmt.length - 1) === '"') {
    return fmt.substring(1, fmt.length - 1);
  }
  return fmt;
};

export const ActionRunResult: FC<Props> = ({ result, runId, outputSchemaType }) => {
  return (
    <>
      <Header size="small">
        <Header.Title title={outputSchemaType ? `Result (${outputSchemaType.type})` : 'Result'} />
      </Header>
      <Code lineNumbers={false} lineWrapping value={getFormattedString(result)} />

      <Header size="small">
        <Header.Title title="Console output" />
      </Header>
      <ActionRunConsole runId={runId} />
      <Link href={`${baseUrl}/api/runs/${runId}/log.html`} icon={IconFileText}>
        Open Log
      </Link>
    </>
  );
};
