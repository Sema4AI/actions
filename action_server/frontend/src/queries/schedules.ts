/* eslint-disable @typescript-eslint/no-explicit-any */
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import type {
  Schedule,
  ScheduleGroup,
  ScheduleExecution,
  ScheduleStatsResponse,
  CreateScheduleRequest,
  UpdateScheduleRequest,
  CronValidationResponse,
  PreviewRunsResponse,
} from '@/shared/types';

const API_BASE = '/api';

// ============================================================================
// Schedule Queries
// ============================================================================

export const useSchedules = (params?: {
  enabled?: boolean;
  group_id?: string;
  search?: string;
}) => {
  const queryParams = new URLSearchParams();
  if (params?.enabled !== undefined) {
    queryParams.set('enabled', String(params.enabled));
  }
  if (params?.group_id) {
    queryParams.set('group_id', params.group_id);
  }
  if (params?.search) {
    queryParams.set('search', params.search);
  }

  return useQuery({
    queryKey: ['schedules', params],
    queryFn: async (): Promise<Schedule[]> => {
      const url = `${API_BASE}/schedules${queryParams.toString() ? `?${queryParams}` : ''}`;
      const response = await fetch(url);
      if (!response.ok) {
        throw new Error('Failed to fetch schedules');
      }
      const data = await response.json();
      // API returns {schedules: [...], total: N}
      return data.schedules ?? [];
    },
  });
};

export const useSchedule = (scheduleId: string | undefined) => {
  return useQuery({
    queryKey: ['schedule', scheduleId],
    queryFn: async (): Promise<Schedule> => {
      const response = await fetch(`${API_BASE}/schedules/${scheduleId}`);
      if (!response.ok) {
        throw new Error('Failed to fetch schedule');
      }
      return response.json();
    },
    enabled: !!scheduleId,
  });
};

export const useScheduleStats = () => {
  return useQuery({
    queryKey: ['schedule-stats'],
    queryFn: async (): Promise<ScheduleStatsResponse> => {
      const response = await fetch(`${API_BASE}/schedules/stats`);
      if (!response.ok) {
        throw new Error('Failed to fetch schedule stats');
      }
      const data = await response.json();
      // Map backend field names to frontend field names
      return {
        total: data.total ?? 0,
        enabled: data.active ?? 0,
        disabled: data.paused ?? 0,
        running: data.running ?? 0,
        failed_24h: data.failed_24h ?? 0,
        success_rate_7d: data.success_rate_7d ?? 100,
        total_executions_7d: data.executions_24h ?? 0,
      };
    },
    refetchInterval: 30000, // Refresh every 30 seconds
  });
};

export const useScheduleExecutions = (
  scheduleId: string | undefined,
  params?: { limit?: number; offset?: number }
) => {
  return useQuery({
    queryKey: ['schedule-executions', scheduleId, params],
    queryFn: async (): Promise<ScheduleExecution[]> => {
      const queryParams = new URLSearchParams();
      if (params?.limit) queryParams.set('limit', String(params.limit));
      if (params?.offset) queryParams.set('offset', String(params.offset));

      const url = `${API_BASE}/schedules/${scheduleId}/executions${queryParams.toString() ? `?${queryParams}` : ''}`;
      const response = await fetch(url);
      if (!response.ok) {
        throw new Error('Failed to fetch executions');
      }
      return response.json();
    },
    enabled: !!scheduleId,
  });
};

// ============================================================================
// Schedule Mutations
// ============================================================================

export const useCreateSchedule = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (data: CreateScheduleRequest): Promise<Schedule> => {
      const response = await fetch(`${API_BASE}/schedules`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      });
      if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: 'Failed to create schedule' }));
        throw new Error(error.detail || 'Failed to create schedule');
      }
      return response.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['schedules'] });
      queryClient.invalidateQueries({ queryKey: ['schedule-stats'] });
    },
  });
};

export const useUpdateSchedule = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      id,
      data,
    }: {
      id: string;
      data: UpdateScheduleRequest;
    }): Promise<Schedule> => {
      const response = await fetch(`${API_BASE}/schedules/${id}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      });
      if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: 'Failed to update schedule' }));
        throw new Error(error.detail || 'Failed to update schedule');
      }
      return response.json();
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['schedules'] });
      queryClient.invalidateQueries({ queryKey: ['schedule', variables.id] });
      queryClient.invalidateQueries({ queryKey: ['schedule-stats'] });
    },
  });
};

export const useDeleteSchedule = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (scheduleId: string): Promise<void> => {
      const response = await fetch(`${API_BASE}/schedules/${scheduleId}`, {
        method: 'DELETE',
      });
      if (!response.ok) {
        throw new Error('Failed to delete schedule');
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['schedules'] });
      queryClient.invalidateQueries({ queryKey: ['schedule-stats'] });
    },
  });
};

export const useTriggerSchedule = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (scheduleId: string): Promise<{ execution_id: string; run_id?: string }> => {
      const response = await fetch(`${API_BASE}/schedules/${scheduleId}/trigger`, {
        method: 'POST',
      });
      if (!response.ok) {
        throw new Error('Failed to trigger schedule');
      }
      return response.json();
    },
    onSuccess: (_, scheduleId) => {
      queryClient.invalidateQueries({ queryKey: ['schedule', scheduleId] });
      queryClient.invalidateQueries({ queryKey: ['schedule-executions', scheduleId] });
      queryClient.invalidateQueries({ queryKey: ['schedule-stats'] });
    },
  });
};

export const useToggleSchedule = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      scheduleId,
      enabled,
    }: {
      scheduleId: string;
      enabled: boolean;
    }): Promise<Schedule> => {
      const endpoint = enabled ? 'enable' : 'disable';
      const response = await fetch(`${API_BASE}/schedules/${scheduleId}/${endpoint}`, {
        method: 'POST',
      });
      if (!response.ok) {
        throw new Error(`Failed to ${endpoint} schedule`);
      }
      return response.json();
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['schedules'] });
      queryClient.invalidateQueries({ queryKey: ['schedule', variables.scheduleId] });
      queryClient.invalidateQueries({ queryKey: ['schedule-stats'] });
    },
  });
};

export const useDuplicateSchedule = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (scheduleId: string): Promise<Schedule> => {
      const response = await fetch(`${API_BASE}/schedules/${scheduleId}/duplicate`, {
        method: 'POST',
      });
      if (!response.ok) {
        throw new Error('Failed to duplicate schedule');
      }
      return response.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['schedules'] });
      queryClient.invalidateQueries({ queryKey: ['schedule-stats'] });
    },
  });
};

// ============================================================================
// Schedule Groups
// ============================================================================

export const useScheduleGroups = () => {
  return useQuery({
    queryKey: ['schedule-groups'],
    queryFn: async (): Promise<ScheduleGroup[]> => {
      const response = await fetch(`${API_BASE}/schedule-groups`);
      if (!response.ok) {
        throw new Error('Failed to fetch schedule groups');
      }
      const data = await response.json();
      // API returns {groups: [...], total: N}
      return data.groups ?? [];
    },
  });
};

export const useCreateScheduleGroup = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (data: {
      name: string;
      description?: string;
      parent_id?: string;
      color?: string;
    }): Promise<ScheduleGroup> => {
      const response = await fetch(`${API_BASE}/schedule-groups`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      });
      if (!response.ok) {
        throw new Error('Failed to create schedule group');
      }
      return response.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['schedule-groups'] });
    },
  });
};

export const useDeleteScheduleGroup = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (groupId: string): Promise<void> => {
      const response = await fetch(`${API_BASE}/schedule-groups/${groupId}`, {
        method: 'DELETE',
      });
      if (!response.ok) {
        throw new Error('Failed to delete schedule group');
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['schedule-groups'] });
      queryClient.invalidateQueries({ queryKey: ['schedules'] });
    },
  });
};

// ============================================================================
// Utilities
// ============================================================================

export const useValidateCron = () => {
  return useMutation({
    mutationFn: async (cronExpression: string): Promise<CronValidationResponse> => {
      const response = await fetch(`${API_BASE}/schedules/validate-cron`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ cron_expression: cronExpression }),
      });
      if (!response.ok) {
        throw new Error('Failed to validate cron expression');
      }
      const data = await response.json();
      // Map backend field names to frontend field names
      return {
        valid: data.valid,
        error: data.error,
        description: data.human_readable,
      };
    },
  });
};

export const usePreviewRuns = () => {
  return useMutation({
    mutationFn: async (params: {
      schedule_type: string;
      cron_expression?: string;
      interval_seconds?: number;
      weekday_config?: { days: number[]; time: string };
      once_at?: string;
      timezone?: string;
      count?: number;
    }): Promise<PreviewRunsResponse> => {
      const response = await fetch(`${API_BASE}/schedules/preview-runs`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(params),
      });
      if (!response.ok) {
        throw new Error('Failed to preview runs');
      }
      return response.json();
    },
  });
};

export const useTimezones = () => {
  return useQuery({
    queryKey: ['timezones'],
    queryFn: async (): Promise<string[]> => {
      const response = await fetch(`${API_BASE}/schedules/timezones`);
      if (!response.ok) {
        throw new Error('Failed to fetch timezones');
      }
      const data = await response.json();
      // API returns {timezones: [...]}
      return data.timezones ?? ['UTC'];
    },
    staleTime: Infinity, // Timezones don't change
  });
};
