import { useQuery } from '@tanstack/react-query';
import { baseUrl } from '@/shared/api-client';

export interface AnalyticsSummary {
  total_runs: number;
  success_rate: number;
  avg_duration_ms: number;
  runs_today: number;
}

export interface RunsByDay {
  date: string;
  total: number;
  passed: number;
  failed: number;
}

export interface RunsByAction {
  action_name: string;
  package_name: string;
  total: number;
  passed: number;
  failed: number;
  avg_duration_ms: number;
}

// Fetch analytics data from the specified endpoint
async function fetchAnalytics<T>(endpoint: string): Promise<T> {
  const response = await fetch(`${baseUrl}/api/analytics/${endpoint}`);
  if (!response.ok) {
    throw new Error(`Failed to fetch ${endpoint}: ${response.statusText}`);
  }
  return response.json() as Promise<T>;
}

// Analytics query configuration
const ANALYTICS_CONFIG = {
  refetchInterval: 30000, // Refetch every 30 seconds
  staleTime: 10000, // Consider data stale after 10 seconds
} as const;

export function useAnalyticsSummary() {
  return useQuery({
    queryKey: ['analytics', 'summary'],
    queryFn: () => fetchAnalytics<AnalyticsSummary>('summary'),
    ...ANALYTICS_CONFIG,
  });
}

export function useRunsByDay(days: number = 30) {
  return useQuery({
    queryKey: ['analytics', 'runs-by-day', days],
    queryFn: () => fetchAnalytics<RunsByDay[]>(`runs-by-day?days=${days}`),
    ...ANALYTICS_CONFIG,
  });
}

export function useRunsByAction() {
  return useQuery({
    queryKey: ['analytics', 'runs-by-action'],
    queryFn: () => fetchAnalytics<RunsByAction[]>('runs-by-action'),
    ...ANALYTICS_CONFIG,
  });
}
