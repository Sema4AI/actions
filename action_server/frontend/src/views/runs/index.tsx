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
  Badge,
  Select,
} from '@sema4ai/components';
import {
  IconArrowUpRight,
  IconExpandSmall,
  IconFileText,
  IconInformation,
  IconSearch,
} from '@sema4ai/icons';

import { Run, RunStatus, RunTableEntry, Action, ActionPackage, AsyncLoaded } from '~/lib/types';
import { useActionServerContext } from '~/lib/actionServerContext';
import { Duration, Timestamp, StatusBadge, ViewLoader, ViewError } from '~/components';
import { baseUrl, fetchRuns } from '~/lib/requestData';

import { RunsContext, useRunsContext } from './components/context';
import { RunDetails } from './components/RunDetails';

const RunRow: FC<TableRowProps<RunTableEntry>> = ({ rowData: run }) => {
  const { setShowRun, showRun } = useActionRunsContext();
  const navigate = useNavigate();

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
      if (run.run_type === 'action') {
        navigate(`/actions/${run.action_id}`);
      }
      event.stopPropagation();
    },
    [run, navigate],
  );

  return (
    <Table.Row onClick={onClickRun}>
      <Table.Cell>#{run.numbered_id}</Table.Cell>
      <Table.Cell>
        {run.run_type === 'robot' ? (
          <Box>
            <div>{run.robot_task_name}</div>
            <Box fontSize="$small" color="neutral-400">
              {run.robot_package_path}
            </Box>
          </Box>
        ) : (
          <Button onClick={onClickAction} variant="ghost" size="small" iconAfter={IconExpandSmall}>
            {run.action_name}
          </Button>
        )}
      </Table.Cell>
      <Table.Cell>
        <Badge variant={run.run_type === 'robot' ? 'secondary' : 'primary'}>
          {run.run_type === 'robot' ? 'Robot' : 'Action'}
        </Badge>
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
    id: 'numbered_id',
    width: 50,
    sortable: true,
  },
  {
    title: 'Name',
    id: 'name',
    sortable: true,
  },
  {
    title: 'Type',
    id: 'run_type',
    width: 100,
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
  const { loadedActions } = useActionServerContext();
  const [loadedRuns, setLoadedRuns] = useState<AsyncLoaded<Run[]>>({ isPending: true });
  const [showRun, setShowRun] = useState<RunTableEntry | undefined>(undefined);
  const [selectedStates, setSelectedStates] = useState({ 
    Status: [] as string[], 
    Type: [] as string[] 
  });
  const [runTypeFilter, setRunTypeFilter] = useState<string>('all');

  const contextMemoized = useMemo(
    () => ({
      showRun,
      setShowRun,
    }),
    [showRun, setShowRun, loadedRuns],
  );

  const filterOptions = useMemo(
    () => ({
      Type: {
        label: 'Type',
        permanent: true,
        options: [
          { label: 'Action', value: 'action', itemType: 'checkbox' },
          { label: 'Robot', value: 'robot', itemType: 'checkbox' },
        ],
      },
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

  const filterRuns = useMemo(() => {
    const actions = loadedActions.data?.flatMap((item: ActionPackage) => item.actions) || [];

    const filteredRuns =
      loadedRuns.data
        ?.map((run: Run) => ({
          ...run,
          action: actions.find((action: Action) => action.id === run.action_id),
        }))
        .filter((row: RunTableEntry) => (
          // Type filter
          (selectedStates.Type.length === 0 || selectedStates.Type.includes(row.run_type)) &&
          // Status filter
          (selectedStates.Status.length === 0 || selectedStates.Status.includes(row.status.toString())) &&
          // Search filter
          (row.run_type === 'robot'
            ? row.robot_task_name?.toLowerCase().includes(search.toLowerCase())
            : row.action_name?.toLowerCase().includes(search.toLowerCase()))
        )) || [];

    const [id, direction] = sort ?? [];

    filteredRuns.sort((a: RunTableEntry, b: RunTableEntry) => {
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

  const runTypeOptions = [
    { label: 'All Runs', value: 'all' },
    { label: 'Actions Only', value: 'action' },
    { label: 'Robots Only', value: 'robot' },
  ];

  useEffect(() => {
    setLoadedRuns({ isPending: true });
    fetchRuns(runTypeFilter).then((data) => {
      setLoadedRuns({ isPending: false, data });
    }).catch((err) => {
      setLoadedRuns({ isPending: false, errorMessage: err.message });
    });
  }, [runTypeFilter]);

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
        <Header.Title title="Runs History" />
      </Header>
      <Box display="flex" alignItems="center" gap="$16" mb="$16">
        <Input
          iconLeft={IconSearch}
          placeholder="Search..."
          value={search}
          onChange={(event) => setSearch(event.target.value)}
          aria-label="Search"
        />
        <Select
          aria-label="Run Type Filter"
          value={runTypeFilter}
          options={runTypeOptions}
          onChange={(val) => setRunTypeFilter(val as string)}
          style={{ width: 180 }}
        />
      </Box>
      <Filter
        options={filterOptions}
        values={selectedStates}
        onChange={setSelectedStates}
      />
      <Table sort={sort} onSort={onSort} columns={columns} data={filterRuns} row={RunRow} rowCount={20} />
      <RunDetails />
    </ActionRunsContext.Provider>
  );
};
