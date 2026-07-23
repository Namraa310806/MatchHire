# Search Platform Testing Strategy

## Overview

This document outlines the comprehensive testing strategy for the MatchHire Search & Recommendation Platform. The testing approach covers unit tests, integration tests, and end-to-end tests to ensure reliability and performance.

## Test Infrastructure

### Required Dependencies

```json
{
  "devDependencies": {
    "@testing-library/react": "^14.0.0",
    "@testing-library/jest-dom": "^6.0.0",
    "@testing-library/user-event": "^14.0.0",
    "@types/jest": "^29.0.0",
    "jest": "^29.0.0",
    "jest-environment-jsdom": "^29.0.0",
    "@vitest/ui": "^1.0.0",
    "vitest": "^1.0.0",
    "msw": "^2.0.0"
  }
}
```

### Test Configuration

```typescript
// vitest.config.ts
import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  test: {
    environment: 'jsdom',
    setupFiles: ['./src/test/setup.ts'],
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html'],
      exclude: ['node_modules/', 'src/test/'],
    },
  },
});
```

## Unit Tests

### Hook Tests

#### useDebounce.test.ts

```typescript
import { renderHook, act } from '@testing-library/react';
import { useDebounce, useDebouncedCallback } from './useDebounce';

describe('useDebounce', () => {
  it('should return the initial value immediately', () => {
    const { result } = renderHook(() => useDebounce('test', 300));
    expect(result.current).toBe('test');
  });

  it('should debounce value changes', () => {
    const { result, rerender } = renderHook(
      ({ value, delay }) => useDebounce(value, delay),
      { initialProps: { value: 'initial', delay: 300 } }
    );

    rerender({ value: 'updated', delay: 300 });
    expect(result.current).toBe('initial');

    act(() => {
      jest.advanceTimersByTime(300);
    });

    expect(result.current).toBe('updated');
  });

  it('should reset timer on rapid changes', () => {
    const { result, rerender } = renderHook(
      ({ value, delay }) => useDebounce(value, delay),
      { initialProps: { value: 'initial', delay: 300 } }
    );

    rerender({ value: 'first', delay: 300 });
    act(() => {
      jest.advanceTimersByTime(200);
    });

    rerender({ value: 'second', delay: 300 });
    act(() => {
      jest.advanceTimersByTime(300);
    });

    expect(result.current).toBe('second');
  });
});

describe('useDebouncedCallback', () => {
  it('should debounce callback execution', () => {
    const callback = jest.fn();
    const { result } = renderHook(() => useDebouncedCallback(callback, 300));

    result.current('test');
    expect(callback).not.toHaveBeenCalled();

    act(() => {
      jest.advanceTimersByTime(300);
    });

    expect(callback).toHaveBeenCalledWith('test');
  });

  it('should cancel previous callback on new call', () => {
    const callback = jest.fn();
    const { result } = renderHook(() => useDebouncedCallback(callback, 300));

    result.current('first');
    act(() => {
      jest.advanceTimersByTime(200);
    });

    result.current('second');
    act(() => {
      jest.advanceTimersByTime(300);
    });

    expect(callback).toHaveBeenCalledTimes(1);
    expect(callback).toHaveBeenCalledWith('second');
  });
});
```

#### useVirtualizedList.test.ts

```typescript
import { renderHook } from '@testing-library/react';
import { useVirtualizedList, useVirtualizedListFixed } from './useVirtualizedList';

describe('useVirtualizedList', () => {
  it('should calculate visible items correctly', () => {
    const { result } = renderHook(() =>
      useVirtualizedList({
        itemCount: 100,
        itemHeight: 50,
        containerHeight: 300,
        overscan: 2,
      })
    );

    expect(result.current.visibleItems).toHaveLength(8); // 300/50 + 2*2
  });

  it('should update visible items on scroll', () => {
    const { result } = renderHook(() =>
      useVirtualizedList({
        itemCount: 100,
        itemHeight: 50,
        containerHeight: 300,
        overscan: 2,
      })
    );

    result.current.handleScroll(100);

    expect(result.current.visibleItems[0].index).toBeGreaterThan(0);
  });

  it('should calculate total height correctly', () => {
    const { result } = renderHook(() =>
      useVirtualizedList({
        itemCount: 100,
        itemHeight: 50,
        containerHeight: 300,
      })
    );

    expect(result.current.totalHeight).toBe(5000); // 100 * 50
  });
});
```

### Component Tests

#### GlobalSearchBar.test.tsx

```typescript
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { SearchProvider } from '../context/SearchContext';
import { GlobalSearchBar } from './GlobalSearchBar';

const renderWithProvider = (component: React.ReactElement) => {
  return render(<SearchProvider>{component}</SearchProvider>);
};

describe('GlobalSearchBar', () => {
  it('should render search input', () => {
    renderWithProvider(<GlobalSearchBar />);
    expect(screen.getByPlaceholderText(/search/i)).toBeInTheDocument();
  });

  it('should update query on input change', async () => {
    renderWithProvider(<GlobalSearchBar />);
    const input = screen.getByPlaceholderText(/search/i);

    fireEvent.change(input, { target: { value: 'react developer' } });

    await waitFor(() => {
      expect(input).toHaveValue('react developer');
    });
  });

  it('should show autocomplete suggestions', async () => {
    renderWithProvider(<GlobalSearchBar />);
    const input = screen.getByPlaceholderText(/search/i);

    fireEvent.change(input, { target: { value: 'react' } });

    await waitFor(() => {
      expect(screen.getByText(/react developer/i)).toBeInTheDocument();
    });
  });

  it('should handle keyboard navigation', () => {
    renderWithProvider(<GlobalSearchBar />);
    const input = screen.getByPlaceholderText(/search/i);

    fireEvent.keyDown(input, { key: 'ArrowDown' });

    // Should navigate through suggestions
  });
});
```

#### SearchResultCard.test.tsx

```typescript
import { render, screen, fireEvent } from '@testing-library/react';
import { SearchResultCard } from './SearchResultCard';

const mockResult = {
  id: '1',
  type: 'job' as const,
  score: 85,
  data: {
    title: 'Senior React Developer',
    company_name: 'Tech Corp',
    location: 'San Francisco',
    skills: ['React', 'TypeScript', 'Node.js'],
    salary_min: 120000,
    salary_max: 180000,
    created_at: '2024-01-15T00:00:00Z',
  },
  highlighted_fields: {},
};

describe('SearchResultCard', () => {
  it('should render job result', () => {
    render(<SearchResultCard result={mockResult} />);

    expect(screen.getByText('Senior React Developer')).toBeInTheDocument();
    expect(screen.getByText('Tech Corp')).toBeInTheDocument();
    expect(screen.getByText('85%')).toBeInTheDocument();
  });

  it('should render match score with correct color', () => {
    render(<SearchResultCard result={mockResult} />);

    const scoreElement = screen.getByText('85%');
    expect(scoreElement).toHaveClass('text-green-600');
  });

  it('should call onResultClick when clicked', () => {
    const handleClick = jest.fn();
    render(<SearchResultCard result={mockResult} onResultClick={handleClick} />);

    const card = screen.getByText('Senior React Developer').closest('.cursor-pointer');
    fireEvent.click(card!);

    expect(handleClick).toHaveBeenCalledWith(mockResult);
  });

  it('should toggle save state', () => {
    render(<SearchResultCard result={mockResult} />);

    const saveButton = screen.getByRole('button');
    fireEvent.click(saveButton);

    expect(saveButton.querySelector('svg')).toHaveClass('fill-current');
  });
});
```

#### AdvancedSearchFilters.test.tsx

```typescript
import { render, screen, fireEvent } from '@testing-library/react';
import { SearchProvider } from '../context/SearchContext';
import { AdvancedSearchFilters } from './AdvancedSearchFilters';

describe('AdvancedSearchFilters', () => {
  it('should render all filter sections', () => {
    render(
      <SearchProvider>
        <AdvancedSearchFilters />
      </SearchProvider>
    );

    expect(screen.getByText(/location/i)).toBeInTheDocument();
    expect(screen.getByText(/skills/i)).toBeInTheDocument();
    expect(screen.getByText(/experience/i)).toBeInTheDocument();
  });

  it('should update filters on input change', () => {
    render(
      <SearchProvider>
        <AdvancedSearchFilters />
      </SearchProvider>
    );

    const locationInput = screen.getByLabelText(/location/i);
    fireEvent.change(locationInput, { target: { value: 'San Francisco' } });

    expect(locationInput).toHaveValue('San Francisco');
  });

  it('should clear all filters', () => {
    render(
      <SearchProvider>
        <AdvancedSearchFilters />
      </SearchProvider>
    );

    const clearButton = screen.getByText(/clear all/i);
    fireEvent.click(clearButton);

    // Verify filters are cleared
  });
});
```

### Service Tests

#### searchService.test.ts

```typescript
import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import { searchService } from './searchService';
import { setupServer } from 'msw/node';
import { rest } from 'msw';

const server = setupServer(
  rest.get('/api/search/global/', (req, res, ctx) => {
    return res(
      ctx.json({
        results: [],
        total: 0,
        page: 1,
        page_size: 20,
      })
    );
  })
);

beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

describe('searchService', () => {
  it('should perform global search', async () => {
    const result = await searchService.globalSearch({
      q: 'react developer',
      entity_type: 'job',
      page: 1,
    });

    expect(result).toHaveProperty('results');
    expect(result).toHaveProperty('total');
  });

  it('should get autocomplete suggestions', async () => {
    server.use(
      rest.get('/api/search/autocomplete/', (req, res, ctx) => {
        return res(ctx.json(['React Developer', 'React Native Developer']));
      })
    );

    const suggestions = await searchService.getAutocomplete('react', 'job');

    expect(suggestions).toHaveLength(2);
    expect(suggestions[0]).toBe('React Developer');
  });

  it('should handle errors gracefully', async () => {
    server.use(
      rest.get('/api/search/global/', (req, res, ctx) => {
        return res(ctx.status(500));
      })
    );

    await expect(
      searchService.globalSearch({ q: 'test', entity_type: 'job' })
    ).rejects.toThrow();
  });
});
```

## Integration Tests

### Search Flow Integration Test

```typescript
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { SearchProvider, useSearch } from '../context/SearchContext';
import { GlobalSearchBar } from '../components/GlobalSearchBar';
import { SearchResultCard } from '../components/SearchResultCard';

describe('Search Flow Integration', () => {
  it('should complete full search flow', async () => {
    render(
      <SearchProvider>
        <GlobalSearchBar />
        <SearchResults />
      </SearchProvider>
    );

    // User types search query
    const input = screen.getByPlaceholderText(/search/i);
    fireEvent.change(input, { target: { value: 'react developer' } });

    // Wait for results
    await waitFor(() => {
      expect(screen.getByText(/senior react developer/i)).toBeInTheDocument();
    });

    // User clicks a result
    const resultCard = screen.getByText(/senior react developer/i);
    fireEvent.click(resultCard);

    // Verify navigation or action
  });
});
```

### Context Integration Test

```typescript
import { renderHook, act } from '@testing-library/react';
import { SearchProvider, useSearch } from '../context/SearchContext';

describe('SearchContext Integration', () => {
  it('should update query and sync to URL', () => {
    const wrapper = ({ children }: { children: React.ReactNode }) => (
      <SearchProvider>{children}</SearchProvider>
    );

    const { result } = renderHook(() => useSearch(), { wrapper });

    act(() => {
      result.current.setQuery({ q: 'test', page: 1 });
    });

    expect(result.current.query.q).toBe('test');
    expect(window.location.search).toContain('q=test');
  });

  it('should persist to localStorage', () => {
    const wrapper = ({ children }: { children: React.ReactNode }) => (
      <SearchProvider>{children}</SearchProvider>
    );

    const { result } = renderHook(() => useSearch(), { wrapper });

    act(() => {
      result.current.setPreferences({ default_entity_type: 'job' });
    });

    const saved = localStorage.getItem('search_preferences');
    expect(saved).toContain('job');
  });
});
```

## End-to-End Tests

### E2E Test Scenarios

```typescript
// e2e/search.spec.ts
import { test, expect } from '@playwright/test';

test.describe('Search E2E', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/search');
  });

  test('should perform basic search', async ({ page }) => {
    await page.fill('[data-testid="search-input"]', 'react developer');
    await page.press('[data-testid="search-input"]', 'Enter');

    await expect(page.locator('[data-testid="search-results"]')).toBeVisible();
    await expect(page.locator('.search-result-card')).toHaveCount(10);
  });

  test('should use autocomplete', async ({ page }) => {
    await page.fill('[data-testid="search-input"]', 'react');

    await expect(page.locator('[data-testid="autocomplete"]')).toBeVisible();
    await expect(page.locator('[data-testid="autocomplete-item"]').first()).toContainText('React Developer');
  });

  test('should apply filters', async ({ page }) => {
    await page.fill('[data-testid="search-input"]', 'developer');
    await page.press('[data-testid="search-input"]', 'Enter');

    await page.click('[data-testid="filter-location"]');
    await page.fill('[data-testid="filter-location-input"]', 'San Francisco');

    await expect(page.locator('.search-result-card')).toHaveCount(5);
  });

  test('should save search', async ({ page }) => {
    await page.fill('[data-testid="search-input"]', 'react developer');
    await page.press('[data-testid="search-input"]', 'Enter');

    await page.click('[data-testid="save-search-button"]');
    await page.fill('[data-testid="save-search-name"]', 'My React Search');
    await page.click('[data-testid="save-search-confirm"]');

    await expect(page.locator('[data-testid="saved-searches"]')).toContainText('My React Search');
  });

  test('should view ranking explanation', async ({ page }) => {
    await page.fill('[data-testid="search-input"]', 'react developer');
    await page.press('[data-testid="search-input"]', 'Enter');

    await page.click('[data-testid="ranking-explanation-toggle"]');

    await expect(page.locator('[data-testid="ranking-explanation"]')).toBeVisible();
    await expect(page.locator('[data-testid="semantic-score"]')).toBeVisible();
  });
});
```

## Performance Tests

### Load Testing

```typescript
// performance/load-test.ts
import { performance } from 'perf_hooks';

describe('Search Performance', () => {
  it('should handle 1000 search requests', async () => {
    const start = performance.now();

    const promises = Array.from({ length: 1000 }, () =>
      searchService.globalSearch({ q: 'test', entity_type: 'job' })
    );

    await Promise.all(promises);

    const duration = performance.now() - start;
    expect(duration).toBeLessThan(5000); // 5 seconds for 1000 requests
  });

  it('should render 1000 results in under 1 second', () => {
    const results = Array.from({ length: 1000 }, (_, i) => ({
      id: i.toString(),
      type: 'job',
      score: 80 + Math.random() * 20,
      data: { title: `Job ${i}` },
    }));

    const start = performance.now();
    render(<SearchResultsList results={results} />);
    const duration = performance.now() - start;

    expect(duration).toBeLessThan(1000);
  });
});
```

## Accessibility Tests

### A11y Tests

```typescript
import { axe } from 'jest-axe';

describe('Accessibility', () => {
  it('should have no accessibility violations', async () => {
    const { container } = render(<GlobalSearchBar />);
    const results = await axe(container);

    expect(results).toHaveNoViolations();
  });

  it('should support keyboard navigation', () => {
    render(<GlobalSearchBar />);
    const input = screen.getByPlaceholderText(/search/i);

    input.focus();
    fireEvent.keyDown(input, { key: 'ArrowDown' });

    // Should navigate to first suggestion
  });

  it('should have proper ARIA labels', () => {
    render(<SearchResultCard result={mockResult} />);

    expect(screen.getByRole('button')).toHaveAttribute('aria-label');
  });
});
```

## Test Coverage Goals

- **Unit Tests**: 80% coverage minimum
- **Integration Tests**: 60% coverage minimum
- **E2E Tests**: Critical user paths covered
- **Accessibility**: 100% WCAG 2.1 AA compliance

## Continuous Integration

### GitHub Actions Workflow

```yaml
name: Search Platform Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: '18'
      - run: npm ci
      - run: npm run test:unit
      - run: npm run test:integration
      - run: npm run test:e2e
      - run: npm run test:a11y
      - run: npm run test:coverage
```

## Running Tests

```bash
# Unit tests
npm run test:unit

# Integration tests
npm run test:integration

# E2E tests
npm run test:e2e

# Accessibility tests
npm run test:a11y

# Coverage report
npm run test:coverage

# All tests
npm run test
```

## Test Data Management

### Mock Data

```typescript
// test/mockData.ts
export const mockSearchResults = {
  jobs: [
    {
      id: '1',
      type: 'job',
      score: 85,
      data: {
        title: 'Senior React Developer',
        company_name: 'Tech Corp',
        location: 'San Francisco',
      },
    },
  ],
  candidates: [
    {
      id: '1',
      type: 'candidate',
      score: 90,
      data: {
        first_name: 'John',
        last_name: 'Doe',
        title: 'Senior Developer',
      },
    },
  ],
};
```

### API Mocking

```typescript
// test/mocks/handlers.ts
import { rest } from 'msw';

export const handlers = [
  rest.get('/api/search/global/', (req, res, ctx) => {
    return res(
      ctx.json({
        results: mockSearchResults.jobs,
        total: 100,
        page: 1,
        page_size: 20,
      })
    );
  }),
];
```

## Summary

This testing strategy ensures comprehensive coverage of the search platform's functionality, performance, and accessibility. The combination of unit, integration, and E2E tests provides confidence in the platform's reliability and user experience.
