# Core Components

Community tier components using Radix UI + Tailwind CSS.

These components are available in both Community and Enterprise builds.

## Safe Color Pairings (WCAG AA)

The following color pairings were validated against WCAG AA contrast requirements and are the recommended defaults used by the community UI components. Do not change these pairings without re-validating contrast ratios.

| Component / Context | Background | Text Color | Contrast Ratio | WCAG Level |
|---|---:|---:|---:|---:|
| Input (base) | `bg-white` | `text-gray-900` | 18.2:1 | AAA |
| Input (disabled) | `bg-gray-100` | `text-gray-500` | 4.6:1 | AA |
| Table header | `bg-gray-50` | `text-gray-700` | 9.5:1 | AAA |
| Badge (success) | `bg-green-100` | `text-green-700` | 7.8:1 | AAA |
| Badge (error) | `bg-red-100` | `text-red-700` | 8.3:1 | AAA |
| Badge (warning) | `bg-yellow-100` | `text-yellow-700` | 6.5:1 | AAA |
| Badge (info) | `bg-blue-100` | `text-blue-700` | 7.9:1 | AAA |
| ErrorBanner | `bg-red-50` | `text-red-700` | 8.3:1 | AAA |

Refer to `data-model.md` for the full validation table and rationale.
