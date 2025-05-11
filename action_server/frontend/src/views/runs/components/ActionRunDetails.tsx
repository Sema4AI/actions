import { Drawer, Header, Link } from '@sema4ai/components';
import { FC, useCallback, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { logError } from '~/lib/helpers';
import {
  ActionRunConsole,
  DefinitionList,
  Duration,
  StatusBadge,
  Timestamp,
  Code,
} from '~/components';
import { baseUrl } from '~/lib/requestData';
import { IconFileText } from '@sema4ai/icons';
import { CancelButton } from '~/components/CancelButton';
import { useActionRunsContext } from './context';

export const ActionRunDetails: FC = () => {
  const { showRun: run, setShowRun } = useActionRunsContext();
  const navigate = useNavigate();

  const onClose = useCallback(() => {
    setShowRun(undefined);
    navigate('/runs');
  }, [navigate]);

  const inputs = useMemo(() => {
    try {
      if (!run) {
        return '';
      }
      const output = Object.entries(JSON.parse(run.inputs));
      if (output.length === 0) {
        return 'No inputs sent';
      }
      return JSON.stringify(JSON.parse(run.inputs), null, 4);
    } catch (err) {
      logError(err);
      return `Error collecting inputs: ${JSON.stringify(err)}`;
    }
  }, [run?.inputs]);

  if (!run) {
    return '';
  }

  const isRobot = run.run_type === 'robot';
  const title = isRobot
    ? `Robot Task Run: ${run.robot_task_name} (${run.robot_package_path})`
    : `Action Run: ${run.action_name}`;

  return (
    <Drawer onClose={onClose} width={760} open>
      <Drawer.Header>
        <Drawer.Header.Title title={title} />
        <Drawer.Header.Description>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <StatusBadge status={run.status} size="medium" />
            <CancelButton runId={run.id} status={run.status} />
          </div>
        </Drawer.Header.Description>
      </Drawer.Header>
      <Drawer.Content>
        <Header size="small">
          <Header.Title title="Run information" />
        </Header>
        <DefinitionList>
          {isRobot && (
            <>
              <DefinitionList.Key>Robot Package:</DefinitionList.Key>
              <DefinitionList.Value>{run.robot_package_path}</DefinitionList.Value>
              <DefinitionList.Key>Task Name:</DefinitionList.Key>
              <DefinitionList.Value>{run.robot_task_name}</DefinitionList.Value>
              <DefinitionList.Key>Environment Hash:</DefinitionList.Key>
              <DefinitionList.Value>{run.robot_env_hash}</DefinitionList.Value>
            </>
          )}
          {!isRobot && (
            <>
              <DefinitionList.Key>Action Name:</DefinitionList.Key>
              <DefinitionList.Value>{run.action_name}</DefinitionList.Value>
            </>
          )}
          <DefinitionList.Key>Started at:</DefinitionList.Key>
          <DefinitionList.Value>
            <Timestamp timestamp={run.start_time} />
          </DefinitionList.Value>
          <DefinitionList.Key>Run time:</DefinitionList.Key>
          <DefinitionList.Value>
            <Duration seconds={run.run_time} />
          </DefinitionList.Value>
        </DefinitionList>

        <Header size="small">
          <Header.Title title="Run input" />
        </Header>
        <Code lang="json" aria-label="Run input" value={inputs} />

        {!isRobot && run.result && (
          <>
            <Header size="small">
              <Header.Title title="Run result" />
            </Header>
            <Code aria-label="Run result" value={run.result || ''} />
          </>
        )}

        {isRobot && (
          <>
            {run.stdout && (
              <>
                <Header size="small">
                  <Header.Title title="Robot Stdout" />
                </Header>
                <Code aria-label="Robot stdout" value={run.stdout} />
              </>
            )}
            {run.stderr && (
              <>
                <Header size="small">
                  <Header.Title title="Robot Stderr" />
                </Header>
                <Code aria-label="Robot stderr" value={run.stderr} />
              </>
            )}
          </>
        )}

        {run.error_message && (
          <>
            <Header size="small">
              <Header.Title title="Run error message" />
            </Header>
            <Code aria-label="Run error message" value={run.error_message || ''} />
          </>
        )}

        <Header size="small">
          <Header.Title title="Console output" />
        </Header>
        <ActionRunConsole runId={run.id} />
        <Link href={`${baseUrl}/api/runs/${run.id}/log.html`} icon={IconFileText}>
          Open Log
        </Link>
      </Drawer.Content>
    </Drawer>
  );
};

// Rename component for unified run details
export const ActionRunDetails = RunDetails;
// For compatibility, keep the old export for now
export { ActionRunDetails as RunDetails };
