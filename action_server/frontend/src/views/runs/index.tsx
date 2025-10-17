import { FC, MouseEvent, useCallback, useEffect, useMemo, useState } from 'react';
import { useNavigate, useParams, useSearchParams } from 'react-router-dom';
import {
  Box,
  Button,
  Column,
  EmptyState,
  Filter,
  FilterGroup,
  Header,
  Input,
  Link,
  SortDirection,
  Table,
  TableRowProps,
  Tooltip,
} from '@sema4ai/components';
import {
  IconArrowUpRight,
  IconExpandSmall,
  IconFileText,
  IconInformation,
  IconSearch,
} from '@sema4ai/icons';

import { RunStatus, RunTableEntry } from '@/shared/types';
import { useActionServerContext } from '@/shared/context/actionServerContext';
import { Duration, Timestamp, StatusBadge, ViewLoader, ViewError } from '~/components';
import { baseUrl } from '@/shared/api-client';

import { ActionRunsContext, useActionRunsContext } from './components/context';
import { ActionRunDetails } from './components/ActionRunDetails';

const RunRow: FC<TableRowProps<RunTableEntry>> = ({ rowData: run }) => {
  const { setShowRun, showRun } = useActionRunsContext();
  const navigate = useNavigate();

  // Issue: if we have a run and click it, we'll set the showRun to the run,
  // but afterwards, if the run is changed (so, we have a new run instance
  // representing the same run), we have to use an effect to update the clicked
  // run.

  useEffect(() => {
    if (run && showRun && run.id === showRun.id) {
      setShowRun(run);
    }
  }, [run, showRun, setShowRun]);

  const onClickRun = useCallback(
    (event: MouseEvent) => {
      setShowRun(run);
      navigate(`/runs/${run.id}`);
      event.stopPropagation();
    },
    [run, setShowRun, navigate],
  );

  const onClickAction = useCallback(
    (event: MouseEvent) => {
      navigate(`/actions/${run.action_id}`);
      event.stopPropagation();
    },
    [run, navigate],
  );

  return (
    <Table.Row onClick={onClickRun}>
      <Table.Cell>#{run.numbered_id}</Table.Cell>
      <Table.Cell>
        <Button onClick={onClickAction} variant="ghost" size="small" iconAfter={IconExpandSmall}>
          {run.action?.name}
        </Button>
      </Table.Cell>
      <Table.Cell>
        <StatusBadge status={run.status} />
      </Table.Cell>
      <Table.Cell>
        <Timestamp timestamp={run.start_time} />
      </Table.Cell>
      <Table.Cell>
        <Duration seconds={run.run_time} />
      </Table.Cell>
      <Table.Cell controls>
        <Tooltip text="View log">
          <Button
            icon={IconFileText}
            aria-label="Log"
            variant="ghost"
            forwardedAs="a"
            href={`${baseUrl}/api/runs/${run.id}/log.html`}
            target="_blank"
          />
        </Tooltip>
      </Table.Cell>
    </Table.Row>
  );
};

const columns: Column[] = [
  {
    title: 'Run',
    id: 'id',
    width: 50,
    sortable: true,
  },
  {
    title: 'Action',
    id: 'action',
    sortable: true,
  },
  {
    title: 'Status',
    id: 'status',
    width: 150,
    sortable: true,
  },
  {
    title: 'Start Time',
    id: 'start_time',
    sortable: true,
    width: 200,
  },
  {
    title: 'Run Time',
    id: 'run_time',
    sortable: true,
    width: 200,
  },
  {
    title: '',
    id: 'actions',
    width: 50,
  },
];

export const ActionRuns: FC = () => {
  const navigate = useNavigate();
  const { runId } = useParams<{ runId: string }>();
  const [searchParams] = useSearchParams();
  const [sort, onSort] = useState<[string, SortDirection] | null>(['start_time', 'desc']);
  const [search, setSearch] = useState<string>(searchParams.get('search') || '');
  const { loadedRuns, loadedActions } = useActionServerContext();
  const [showRun, setShowRun] = useState<RunTableEntry | undefined>(undefined);
  const [selectedStates, setSelectedStates] = useState({ Status: [] as string[] });

  const contextMemoized = useMemo(
    () => ({
      showRun,
      setShowRun,
    }),
    [showRun, setShowRun, loadedRuns],
  );

  const stateOptions = useMemo(
    () => ({
      Status: {
        label: 'Status',
        permanent: true,
        options: [
          { label: 'Failed', value: `${RunStatus.FAILED}`, itemType: 'checkbox' },
          { label: 'Not Run', value: `${RunStatus.NOT_RUN}`, itemType: 'checkbox' },
          { label: 'Successful', value: `${RunStatus.PASSED}`, itemType: 'checkbox' },
          { label: 'Running', value: `${RunStatus.RUNNING}`, itemType: 'checkbox' },
          { label: 'Cancelled', value: `${RunStatus.CANCELLED}`, itemType: 'checkbox' },
        ],
      } satisfies FilterGroup,
    }),
    [],
  );

  const runs = useMemo(() => {
    const actions = loadedActions.data?.flatMap((item) => item.actions) || [];

    const filteredRuns =
      loadedRuns.data
        ?.map(
          (run) =>
            ({
              ...run,
              action: actions.find((action) => action.id === run.action_id),
            }) satisfies RunTableEntry,
        )
        .filter(
          (row) =>
            (selectedStates.Status.length === 0 ||
              selectedStates.Status.includes(row.status.toString())) &&
            row.action?.name.toLowerCase().includes(search.toLocaleLowerCase()),
        ) || [];

    const [id, direction] = sort ?? [];

    filteredRuns.sort((a, b) => {
      const aItem = a[id as keyof typeof a];
      const bItem = b[id as keyof typeof b];

      if (!aItem || !bItem) {
        return 0;
      }
      if (aItem < bItem) {
        return direction === 'asc' ? -1 : 1;
      }
      if (aItem > bItem) {
        return direction === 'asc' ? 1 : -1;
      }
      return 0;
    });

    return filteredRuns;
  }, [loadedRuns.data, loadedActions.data, sort, selectedStates, search]);

  const onNavigateActions = useCallback(() => {
    navigate('/actions');
  }, []);

  // Effect to handle direct URL access with runId
  useEffect(() => {
    if (runId && loadedRuns.data && loadedActions.data) {
      const actions = loadedActions.data?.flatMap((item) => item.actions) || [];
      const runData = loadedRuns.data.find((run) => run.id === runId);

      if (runData) {
        const runWithAction = {
          ...runData,
          action: actions.find((action) => action.id === runData.action_id),
        } as RunTableEntry;

        setShowRun(runWithAction);
      }
    }
  }, [runId, loadedRuns.data, loadedActions.data]);

  if (loadedRuns.isPending) {
    return <ViewLoader />;
  }

  if (
    loadedRuns.errorMessage ||
    loadedActions.errorMessage ||
    loadedActions.isPending ||
    !loadedRuns.data
  ) {
    return (
      <ViewError>
        It was not possible to load the data.
        <br />
        {`Error: ${loadedActions.errorMessage}`}
      </ViewError>
    );
  }

  if (!loadedRuns.data.length) {
    return (
      <Box
        display="flex"
        flex="1"
        justifyContent="center"
        flexDirection="column"
        minHeight="100%"
        pb="$64"
      >
        <EmptyState
          title="No action runs"
          description="Once actions are run, the output will appear here."
          action={<Button onClick={onNavigateActions}>Go to actions</Button>}
          secondaryAction={
            <Link
              icon={IconInformation}
              iconAfter={IconArrowUpRight}
              href="https://github.com/Sema4ai/actions"
              target="_blank"
              rel="noopener"
              variant="subtle"
              fontWeight="medium"
            >
              Learn more
            </Link>
          }
        />
      </Box>
    );
  }

  return (
    <ActionRunsContext.Provider value={contextMemoized}>
      <Header>
        <Header.Title title="Action Runs" />
      </Header>
      <Filter
        contentBefore={
          <Input
            iconLeft={IconSearch}
            placeholder="Search..."
            value={search}
            onChange={(event) => setSearch(event.target.value)}
            aria-label="Search"
          />
        }
        options={stateOptions}
        values={selectedStates}
        onChange={setSelectedStates}
      />
      <Table sort={sort} onSort={onSort} columns={columns} data={runs} row={RunRow} rowCount={20} />
      <ActionRunDetails />
    </ActionRunsContext.Provider>
  );
};
