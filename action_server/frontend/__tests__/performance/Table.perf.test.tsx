import React from 'react';
import { render, cleanup } from '../utils/test-utils';
import { describe, it, expect, afterEach } from 'vitest';

import {
  Table,
  TableHeader,
  TableBody,
  TableRow,
  TableHead,
  TableCell,
} from '@/core/components/ui/Table';

// Performance thresholds (in milliseconds)
// Note: These are very conservative thresholds for jsdom test environment
// Real browser performance is typically faster. Test environment has high variability.
// These thresholds are meant to catch severe regressions, not measure exact performance.
const PERF_THRESHOLDS = {
  SMALL_RENDER: 1000, // 100 rows should render in < 1000ms (very conservative for CI)
  MEDIUM_RENDER: 1500, // 500 rows should render in < 1500ms
  LARGE_RENDER: 2000, // 1000 rows should render in < 2000ms
  FRAME_TIME: 16, // 60fps target (16.67ms per frame)
  SCROLL_THRESHOLD: 32, // Allow up to 2 frames for scroll operations
};

// Test data generators
function generateRowData(count: number) {
  return Array.from({ length: count }, (_, index) => ({
    id: `row-${index}`,
    name: `Item ${index}`,
    value: Math.random() * 1000,
    status: index % 2 === 0 ? 'active' : 'inactive',
    timestamp: new Date(Date.now() - index * 1000).toISOString(),
  }));
}

// Helper to measure render performance
function measureRender(rowCount: number) {
  const data = generateRowData(rowCount);
  const startTime = performance.now();

  const result = render(
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>ID</TableHead>
          <TableHead>Name</TableHead>
          <TableHead>Value</TableHead>
          <TableHead>Status</TableHead>
          <TableHead>Timestamp</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {data.map((row) => (
          <TableRow key={row.id}>
            <TableCell>{row.id}</TableCell>
            <TableCell>{row.name}</TableCell>
            <TableCell>{row.value.toFixed(2)}</TableCell>
            <TableCell>{row.status}</TableCell>
            <TableCell>{row.timestamp}</TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );

  const endTime = performance.now();
  const renderTime = endTime - startTime;

  return {
    result,
    renderTime,
    rowCount,
  };
}

// Helper to measure memory usage (if available)
function getMemoryUsage() {
  if ('memory' in performance && (performance as any).memory) {
    const memory = (performance as any).memory;
    return {
      usedJSHeapSize: memory.usedJSHeapSize,
      totalJSHeapSize: memory.totalJSHeapSize,
      jsHeapSizeLimit: memory.jsHeapSizeLimit,
    };
  }
  return null;
}

describe('Table component - Performance benchmarks', () => {
  afterEach(() => {
    cleanup();
  });

  describe('Render performance', () => {
    it('renders 100 rows within acceptable time', () => {
      const { renderTime, rowCount } = measureRender(100);

      console.log(`✓ Rendered ${rowCount} rows in ${renderTime.toFixed(2)}ms`);
      expect(renderTime).toBeLessThan(PERF_THRESHOLDS.SMALL_RENDER);
    });

    it('renders 500 rows within acceptable time', () => {
      const { renderTime, rowCount } = measureRender(500);

      console.log(`✓ Rendered ${rowCount} rows in ${renderTime.toFixed(2)}ms`);
      expect(renderTime).toBeLessThan(PERF_THRESHOLDS.MEDIUM_RENDER);
    });

    it('renders 1000 rows within acceptable time', () => {
      const { renderTime, rowCount } = measureRender(1000);

      console.log(`✓ Rendered ${rowCount} rows in ${renderTime.toFixed(2)}ms`);
      expect(renderTime).toBeLessThan(PERF_THRESHOLDS.LARGE_RENDER);
    });

    it('maintains consistent render time across multiple renders', () => {
      const iterations = 5;
      const renderTimes: number[] = [];

      for (let i = 0; i < iterations; i++) {
        const { renderTime } = measureRender(100);
        renderTimes.push(renderTime);
        cleanup();
      }

      const avgRenderTime = renderTimes.reduce((a, b) => a + b, 0) / iterations;
      const maxRenderTime = Math.max(...renderTimes);
      const minRenderTime = Math.min(...renderTimes);
      const variance = maxRenderTime - minRenderTime;

      console.log(`✓ Average render time: ${avgRenderTime.toFixed(2)}ms`);
      console.log(`  Min: ${minRenderTime.toFixed(2)}ms, Max: ${maxRenderTime.toFixed(2)}ms`);
      console.log(`  Variance: ${variance.toFixed(2)}ms`);

      // Variance should be reasonable (not more than 2x the average)
      expect(variance).toBeLessThan(avgRenderTime * 2);
    });
  });

  describe('DOM structure efficiency', () => {
    it('generates minimal DOM nodes for 100 rows', () => {
      const { result } = measureRender(100);
      const container = result.container;

      const allElements = container.querySelectorAll('*');
      const tableRows = container.querySelectorAll('tbody tr');
      const tableCells = container.querySelectorAll('td');

      console.log(`✓ DOM nodes: ${allElements.length}`);
      console.log(`  Rows: ${tableRows.length}, Cells: ${tableCells.length}`);

      // Should have exactly 100 rows and 500 cells (5 columns * 100 rows)
      expect(tableRows.length).toBe(100);
      expect(tableCells.length).toBe(500);

      // Total DOM nodes should be reasonable (not excessive wrapper divs)
      // Approximate: 1 wrapper div + 1 table + 1 thead + 1 header row + 5 th + 1 tbody + 100 tr + 500 td = ~609 nodes
      expect(allElements.length).toBeLessThan(700);
    });

    it('maintains efficient DOM structure for large tables', () => {
      const { result } = measureRender(1000);
      const container = result.container;

      const tableRows = container.querySelectorAll('tbody tr');
      const tableCells = container.querySelectorAll('td');

      // Should have exactly 1000 rows and 5000 cells
      expect(tableRows.length).toBe(1000);
      expect(tableCells.length).toBe(5000);
    });
  });

  describe('Re-render performance', () => {
    it('efficiently updates table content on re-render', () => {
      const data = generateRowData(100);

      const TestWrapper = ({ data }: { data: ReturnType<typeof generateRowData> }) => (
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>ID</TableHead>
              <TableHead>Name</TableHead>
              <TableHead>Value</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {data.map((row) => (
              <TableRow key={row.id}>
                <TableCell>{row.id}</TableCell>
                <TableCell>{row.name}</TableCell>
                <TableCell>{row.value.toFixed(2)}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      );

      const { rerender } = render(<TestWrapper data={data} />);

      // Measure re-render with updated data
      const updatedData = data.map((row) => ({
        ...row,
        value: row.value * 2,
      }));

      const startTime = performance.now();
      rerender(<TestWrapper data={updatedData} />);
      const rerenderTime = performance.now() - startTime;

      console.log(`✓ Re-render time: ${rerenderTime.toFixed(2)}ms`);

      // Re-render should be fast (within frame budget)
      expect(rerenderTime).toBeLessThan(PERF_THRESHOLDS.FRAME_TIME * 2);
    });
  });

  describe('Scroll performance simulation', () => {
    it('verifies table container supports overflow scrolling', () => {
      const { result } = measureRender(1000);
      const container = result.container;

      // Find the wrapper div that should have overflow-auto
      const wrapperDiv = container.querySelector('div');
      expect(wrapperDiv).toBeTruthy();

      if (wrapperDiv) {
        const styles = window.getComputedStyle(wrapperDiv);
        const classList = wrapperDiv.className;

        // Check that overflow-auto is applied
        expect(classList).toContain('overflow-auto');
        console.log(`✓ Table wrapper has overflow-auto for scroll support`);
      }
    });

    it('measures scroll container rendering without layout thrashing', () => {
      const { result } = measureRender(1000);
      const container = result.container;
      const wrapperDiv = container.querySelector('div');

      if (!wrapperDiv) {
        throw new Error('Wrapper div not found');
      }

      // Simulate scroll measurements (reading layout properties)
      const startTime = performance.now();

      // These operations should not cause layout thrashing
      const scrollHeight = wrapperDiv.scrollHeight;
      const clientHeight = wrapperDiv.clientHeight;
      const offsetHeight = wrapperDiv.offsetHeight;

      // Batch read operations
      const measurements = [scrollHeight, clientHeight, offsetHeight];

      const measurementTime = performance.now() - startTime;

      console.log(`✓ Scroll measurements completed in ${measurementTime.toFixed(2)}ms`);
      console.log(`  ScrollHeight: ${scrollHeight}, ClientHeight: ${clientHeight}`);

      // Reading layout properties should be very fast (sub-millisecond)
      expect(measurementTime).toBeLessThan(5);

      // In jsdom test environment, dimensions may be 0, but we should be able to read them
      // In a real browser with layout, these would be > 0
      expect(measurements.every((m) => typeof m === 'number')).toBe(true);
    });
  });

  describe('Memory usage validation', () => {
    it('reports memory usage for different table sizes (if available)', () => {
      const memoryBefore = getMemoryUsage();

      if (!memoryBefore) {
        console.log('⚠ Memory API not available in this environment');
        return;
      }

      console.log(`Memory before: ${(memoryBefore.usedJSHeapSize / 1024 / 1024).toFixed(2)}MB`);

      // Render large table
      const { result } = measureRender(1000);
      const memoryAfter = getMemoryUsage();

      if (memoryAfter) {
        const memoryIncrease = memoryAfter.usedJSHeapSize - memoryBefore.usedJSHeapSize;
        console.log(`Memory after: ${(memoryAfter.usedJSHeapSize / 1024 / 1024).toFixed(2)}MB`);
        console.log(`Memory increase: ${(memoryIncrease / 1024 / 1024).toFixed(2)}MB`);

        // 1000 rows should not consume excessive memory (< 10MB increase is reasonable)
        expect(memoryIncrease).toBeLessThan(10 * 1024 * 1024);
      }

      // Cleanup
      cleanup();

      // Force garbage collection if available
      if (global.gc) {
        global.gc();
        const memoryAfterCleanup = getMemoryUsage();
        if (memoryAfterCleanup) {
          console.log(
            `Memory after cleanup: ${(memoryAfterCleanup.usedJSHeapSize / 1024 / 1024).toFixed(2)}MB`
          );
        }
      }
    });

    it('cleans up efficiently after unmounting large tables', () => {
      const iterations = 3;
      const memoryReadings: number[] = [];

      for (let i = 0; i < iterations; i++) {
        const { result } = measureRender(500);
        const memoryDuring = getMemoryUsage();

        if (memoryDuring) {
          memoryReadings.push(memoryDuring.usedJSHeapSize);
        }

        cleanup();

        // Force GC if available
        if (global.gc) {
          global.gc();
        }
      }

      if (memoryReadings.length > 0) {
        console.log('✓ Memory readings across iterations:');
        memoryReadings.forEach((reading, idx) => {
          console.log(`  Iteration ${idx + 1}: ${(reading / 1024 / 1024).toFixed(2)}MB`);
        });

        // Memory should not continuously grow (leak detection)
        if (memoryReadings.length >= 3) {
          const firstReading = memoryReadings[0];
          const lastReading = memoryReadings[memoryReadings.length - 1];
          const growth = lastReading - firstReading;

          // Allow some growth but not excessive (< 5MB total growth)
          expect(growth).toBeLessThan(5 * 1024 * 1024);
        }
      }
    });
  });

  describe('Interactive element performance', () => {
    it('renders clickable rows without significant performance impact', () => {
      const data = generateRowData(100);

      const startTime = performance.now();
      const result = render(
        <Table>
          <TableBody>
            {data.map((row) => (
              <TableRow key={row.id} clickable onClick={() => {}}>
                <TableCell>{row.name}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      );
      const renderTime = performance.now() - startTime;

      console.log(`✓ Rendered 100 clickable rows in ${renderTime.toFixed(2)}ms`);

      // Clickable rows should not significantly impact render time
      expect(renderTime).toBeLessThan(PERF_THRESHOLDS.SMALL_RENDER);

      // Verify clickable styling is applied
      const rows = result.container.querySelectorAll('tbody tr');
      expect(rows[0].className).toContain('cursor-pointer');
    });

    it('renders selected rows efficiently', () => {
      const data = generateRowData(100);
      const selectedIds = new Set(['row-10', 'row-25', 'row-50', 'row-75']);

      const startTime = performance.now();
      render(
        <Table>
          <TableBody>
            {data.map((row) => (
              <TableRow key={row.id} selected={selectedIds.has(row.id)}>
                <TableCell>{row.name}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      );
      const renderTime = performance.now() - startTime;

      console.log(`✓ Rendered 100 rows with 4 selected in ${renderTime.toFixed(2)}ms`);

      // Selected state should not significantly impact performance
      expect(renderTime).toBeLessThan(PERF_THRESHOLDS.SMALL_RENDER);
    });
  });

  describe('Performance regression suite', () => {
    it('provides baseline performance metrics for all table sizes', () => {
      const testSizes = [100, 500, 1000];
      const results: Record<number, number> = {};

      console.log('\n=== Table Performance Baseline ===');

      for (const size of testSizes) {
        const { renderTime } = measureRender(size);
        results[size] = renderTime;
        cleanup();

        console.log(`${size} rows: ${renderTime.toFixed(2)}ms`);
      }

      console.log('===================================\n');

      // All sizes should meet their respective thresholds
      expect(results[100]).toBeLessThan(PERF_THRESHOLDS.SMALL_RENDER);
      expect(results[500]).toBeLessThan(PERF_THRESHOLDS.MEDIUM_RENDER);
      expect(results[1000]).toBeLessThan(PERF_THRESHOLDS.LARGE_RENDER);

      // Performance should scale reasonably (1000 rows shouldn't be more than 20x slower than 100)
      // In practice, we expect closer to linear or sub-linear scaling
      const scaleFactor = results[1000] / results[100];
      console.log(`Performance scale factor (1000/100): ${scaleFactor.toFixed(2)}x`);
      expect(scaleFactor).toBeLessThan(20);
    });
  });
});
