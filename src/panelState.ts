export interface ScrollState {
  top: number;
  left: number;
  height: number;
}

export function resetScrollTop(previous: ScrollState): ScrollState {
  return previous.top === 0 ? previous : { ...previous, top: 0 };
}
