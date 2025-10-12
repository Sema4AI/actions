import * as axeCore from 'axe-core';

// Lightweight Vitest matcher that mirrors jest-axe's toHaveNoViolations
expect.extend({
  async toHaveNoViolations(received: any) {
    const violations = received?.violations ?? [];
    const pass = violations.length === 0;
    if (pass) {
      return {
        pass: true,
        message: () => 'Expected no accessibility violations',
      };
    }

    const summary = violations
      .map((v: any) => {
        const nodes = v.nodes?.map((n: any) => n.target.join(', ')).join('\n') || '';
        return `${v.id} — ${v.help}\n${v.description}\nNodes:\n${nodes}`;
      })
      .join('\n\n');

    return {
      pass: false,
      message: () => `Accessibility violations found:\n\n${summary}`,
    };
  },
});

// Optional helper to run axe on a container
export async function runAxe(container: HTMLElement) {
  // axe-core exposes a run method which returns a results object { violations, passes, ... }
  // In jsdom certain APIs used by axe for color-contrast (getComputedStyle for pseudo elements)
  // are not implemented. Configure axe to skip the color-contrast check when running under jsdom
  // to avoid spurious Not implemented errors. This keeps other accessibility checks active.
  const options = {
    rules: {
      'color-contrast': { enabled: false },
    },
  };
  const results = await (axeCore as any).run(container, options);
  return results;
}
