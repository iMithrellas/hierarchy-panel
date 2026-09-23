import { describe, expect, it } from 'vitest';
import { resetScrollTop } from './panelState';

describe('resetScrollTop', () => {
  it('returns the same state when scroll is already at the top', () => {
    const state = { top: 0, left: 24, height: 400 };
    expect(resetScrollTop(state)).toBe(state);
  });

  it('resets vertical scroll while preserving the rest of the viewport state', () => {
    expect(resetScrollTop({ top: 120, left: 24, height: 400 })).toEqual({ top: 0, left: 24, height: 400 });
  });
});
