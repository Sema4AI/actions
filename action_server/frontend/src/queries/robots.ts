import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import type { RobotCatalogResponseAPI, RobotRunRequestAPI, RobotRunResponseAPI } from '~/lib/types';

export const useRobotCatalog = () => {
  return useQuery<RobotCatalogResponseAPI, Error>({
    queryKey: ['robotCatalog'],
    queryFn: async () => {
      const response = await fetch('/api/robots/catalog');
      if (!response.ok) {
        throw new Error(`Failed to fetch robot catalog: ${response.statusText}`);
      }
      return response.json();
    },
  });
};

export const useRunRobotTask = () => {
  const queryClient = useQueryClient();
  const navigate = useNavigate();

  return useMutation<RobotRunResponseAPI, Error, RobotRunRequestAPI>({
    mutationFn: async (payload) => {
      const response = await fetch('/api/robots/run', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      if (!response.ok) {
        const error = await response.json().catch(() => ({}));
        throw new Error(error.message || 'Failed to run robot task');
      }
      return response.json();
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['runHistory'] });
      navigate(`/runs/${data.run_id}`);
    },
  });
};
