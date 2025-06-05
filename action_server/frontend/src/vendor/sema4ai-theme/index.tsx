import React from 'react';
import styledComponents, { ThemeProvider as StyledProvider } from 'styled-components';

export const styled = styledComponents;

export type Color = string;

export interface ThemeOverrides {
  fonts?: {
    title?: string;
    default?: string;
  };
}

const baseTheme = {
  name: 'light',
  space: {
    $8: '8px',
    $16: '16px',
    $24: '24px',
    $32: '32px',
  },
  sizes: {
    $24: '24px',
    $32: '32px',
    $48: '48px',
  },
  radii: {
    $8: '8px',
    $16: '16px',
    $24: '24px',
  },
  colors: {
    background: {
      primary: { color: '#ffffff' },
      subtle: { color: '#f5f5f5' },
    },
    content: {
      primary: { color: '#000000' },
      disabled: { color: '#888888' },
      subtle: {
        light: { color: '#666666' },
      },
      accent: { color: '#007bff' },
      error: { color: '#ff0000' },
    },
  },
  screen: {
    s: '@media (max-width: 600px)',
    m: '@media (max-width: 900px)',
  },
  color: (c: string) => {
    const mapping: Record<string, string> = {
      grey100: '#ffffff',
      grey10: '#f0f0f0',
    };
    return mapping[c] || '#000000';
  },
};

export const ThemeProvider: React.FC<{ name?: string; overrides?: ThemeOverrides }> = ({
  children,
  name,
  overrides,
}) => {
  const theme = { ...baseTheme, ...overrides, name: name || baseTheme.name };
  return <StyledProvider theme={theme}>{children}</StyledProvider>;
};
