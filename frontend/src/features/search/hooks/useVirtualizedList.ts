import { useState, useRef, useCallback } from 'react';

interface UseVirtualizedListProps {
  itemCount: number;
  itemHeight: number | ((index: number) => number);
  containerHeight: number;
  overscan?: number;
}

interface VirtualizedListResult {
  visibleItems: Array<{ index: number; offsetTop: number }>;
  totalHeight: number;
  scrollTop: number;
  handleScroll: (scrollTop: number) => void;
  containerRef: React.RefObject<HTMLDivElement | null>;
}

export function useVirtualizedList({
  itemCount,
  itemHeight,
  containerHeight,
  overscan = 5,
}: UseVirtualizedListProps): VirtualizedListResult {
  const [scrollTop, setScrollTop] = useState(0);
  const containerRef = useRef<HTMLDivElement | null>(null);

  const getItemHeight = useCallback(
    (index: number) => {
      return typeof itemHeight === 'function' ? itemHeight(index) : itemHeight;
    },
    [itemHeight]
  );

  const totalHeight = useCallback(() => {
    let height = 0;
    for (let i = 0; i < itemCount; i++) {
      height += getItemHeight(i);
    }
    return height;
  }, [itemCount, getItemHeight]);

  const getVisibleRange = useCallback(() => {
    let startIndex = 0;
    let endIndex = itemCount - 1;
    let accumulatedHeight = 0;

    // Find start index
    for (let i = 0; i < itemCount; i++) {
      const height = getItemHeight(i);
      if (accumulatedHeight + height > scrollTop) {
        startIndex = Math.max(0, i - overscan);
        break;
      }
      accumulatedHeight += height;
    }

    // Find end index
    accumulatedHeight = 0;
    for (let i = startIndex; i < itemCount; i++) {
      accumulatedHeight += getItemHeight(i);
      if (accumulatedHeight > scrollTop + containerHeight) {
        endIndex = Math.min(itemCount - 1, i + overscan);
        break;
      }
    }

    return { startIndex, endIndex };
  }, [scrollTop, containerHeight, itemCount, getItemHeight, overscan]);

  const visibleItems = useCallback(() => {
    const { startIndex, endIndex } = getVisibleRange();
    const items: Array<{ index: number; offsetTop: number }> = [];
    let offsetTop = 0;

    for (let i = 0; i < startIndex; i++) {
      offsetTop += getItemHeight(i);
    }

    for (let i = startIndex; i <= endIndex; i++) {
      items.push({ index: i, offsetTop });
      offsetTop += getItemHeight(i);
    }

    return items;
  }, [getVisibleRange, getItemHeight]);

  const handleScroll = useCallback((newScrollTop: number) => {
    setScrollTop(newScrollTop);
  }, []);

  return {
    visibleItems: visibleItems(),
    totalHeight: totalHeight(),
    scrollTop,
    handleScroll,
    containerRef,
  };
}

// Simplified version for fixed-height items
export function useVirtualizedListFixed({
  itemCount,
  itemHeight,
  containerHeight,
  overscan = 5,
}: Omit<UseVirtualizedListProps, 'itemHeight'> & { itemHeight: number }): VirtualizedListResult {
  const [scrollTop, setScrollTop] = useState(0);
  const containerRef = useRef<HTMLDivElement | null>(null);

  const totalHeight = itemCount * itemHeight;

  const visibleItems = useCallback(() => {
    const startIndex = Math.max(0, Math.floor(scrollTop / itemHeight) - overscan);
    const endIndex = Math.min(
      itemCount - 1,
      Math.floor((scrollTop + containerHeight) / itemHeight) + overscan
    );

    const items: Array<{ index: number; offsetTop: number }> = [];
    for (let i = startIndex; i <= endIndex; i++) {
      items.push({ index: i, offsetTop: i * itemHeight });
    }

    return items;
  }, [scrollTop, itemHeight, containerHeight, itemCount, overscan]);

  const handleScroll = useCallback((newScrollTop: number) => {
    setScrollTop(newScrollTop);
  }, []);

  return {
    visibleItems: visibleItems(),
    totalHeight,
    scrollTop,
    handleScroll,
    containerRef,
  };
}
