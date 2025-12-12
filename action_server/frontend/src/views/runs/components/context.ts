import { Dispatch, SetStateAction, createContext, useContext } from 'react';

import { Run, RunTableEntry } from '@/shared/types';

export type RunsContextType = {
  showRun: RunTableEntry | undefined;
  setShowRun: Dispatch<SetStateAction<Run | undefined>>;
};

export const RunsContext = createContext<RunsContextType>({
  showRun: undefined,
  setShowRun: () => {
    return null;
  },
});

export const useRunsContext = () => {
  return useContext(RunsContext);
};
