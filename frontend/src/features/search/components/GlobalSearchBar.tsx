import React, { useState, useCallback, useEffect, useRef } from 'react';
import { Search, X, Clock, TrendingUp } from 'lucide-react';
import { useSearch } from '../context/SearchContext';
import { useAutocomplete, usePopularSearches } from '../hooks/useSearch';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Command, CommandEmpty, CommandGroup, CommandItem, CommandList } from '@/components/ui/command';
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover';
import { cn } from '@/lib/utils';

interface GlobalSearchBarProps {
  className?: string;
  placeholder?: string;
  autoFocus?: boolean;
}

export const GlobalSearchBar: React.FC<GlobalSearchBarProps> = ({
  className,
  placeholder = 'Search jobs, candidates, skills...',
  autoFocus = false,
}) => {
  const { query, setQuery, recentSearches, addToRecentSearches, clearRecentSearches } = useSearch();
  const [open, setOpen] = useState(false);
  const [inputValue, setInputValue] = useState(query.q);
  const inputRef = useRef<HTMLInputElement>(null);

  const { data: suggestions, isLoading: suggestionsLoading } = useAutocomplete(inputValue, query.entity_type);
  const { data: popularSearches } = usePopularSearches(5);

  useEffect(() => {
    setInputValue(query.q);
  }, [query.q]);

  const handleSearch = useCallback((searchQuery: string) => {
    setQuery({ q: searchQuery, page: 1 });
    setOpen(false);
    
    if (searchQuery.trim()) {
      addToRecentSearches({
        query: searchQuery,
        entity_type: query.entity_type,
        timestamp: new Date().toISOString(),
      });
    }
  }, [setQuery, query.entity_type, addToRecentSearches]);

  const handleInputChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    setInputValue(e.target.value);
    if (e.target.value.length >= 2) {
      setOpen(true);
    }
  }, []);

  const handleKeyDown = useCallback((e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && inputValue.trim()) {
      handleSearch(inputValue);
    }
    if (e.key === 'Escape') {
      setOpen(false);
    }
    if (e.key === 'k' && (e.metaKey || e.ctrlKey)) {
      e.preventDefault();
      inputRef.current?.focus();
    }
  }, [inputValue, handleSearch]);

  const clearInput = useCallback(() => {
    setInputValue('');
    setQuery({ q: '' });
    inputRef.current?.focus();
  }, [setQuery]);

  const entityTypeLabels = {
    all: 'All',
    job: 'Jobs',
    candidate: 'Candidates',
  };

  return (
    <div className={cn('relative w-full max-w-2xl', className)}>
      <Popover open={open} onOpenChange={setOpen}>
        <PopoverTrigger asChild>
          <div className="relative">
            <div className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground">
              <Search className="h-4 w-4" />
            </div>
            <Input
              ref={inputRef}
              value={inputValue}
              onChange={handleInputChange}
              onKeyDown={handleKeyDown}
              placeholder={placeholder}
              className="pl-10 pr-20 h-12 text-base"
              autoFocus={autoFocus}
            />
            <div className="absolute right-2 top-1/2 -translate-y-1/2 flex items-center gap-1">
              {inputValue && (
                <Button
                  variant="ghost"
                  size="sm"
                  className="h-8 w-8 p-0"
                  onClick={clearInput}
                >
                  <X className="h-4 w-4" />
                </Button>
              )}
              <kbd className="pointer-events-none inline-flex h-8 select-none items-center gap-1 rounded border bg-muted px-2 font-mono text-xs font-medium text-muted-foreground opacity-50">
                <span className="text-xs">⌘</span>K
              </kbd>
            </div>
          </div>
        </PopoverTrigger>
        <PopoverContent
          className="w-[--radix-popover-trigger-width] p-0"
          align="start"
          sideOffset={4}
        >
          <Command>
            <CommandList className="max-h-[400px]">
              {!inputValue && recentSearches.length > 0 && (
                <CommandGroup heading="Recent Searches">
                  {recentSearches.slice(0, 5).map((search, index) => (
                    <CommandItem
                      key={`${search.query}-${index}`}
                      onSelect={() => handleSearch(search.query)}
                      className="cursor-pointer"
                    >
                      <Clock className="mr-2 h-4 w-4 text-muted-foreground" />
                      <span className="flex-1">{search.query}</span>
                      <Badge variant="outline" className="ml-2">
                        {entityTypeLabels[search.entity_type]}
                      </Badge>
                    </CommandItem>
                  ))}
                  <CommandItem
                    onSelect={() => clearRecentSearches()}
                    className="cursor-pointer text-destructive"
                  >
                    <X className="mr-2 h-4 w-4" />
                    Clear recent searches
                  </CommandItem>
                </CommandGroup>
              )}

              {!inputValue && popularSearches && popularSearches.length > 0 && (
                <CommandGroup heading="Popular Searches">
                  {popularSearches.map((search, index) => (
                    <CommandItem
                      key={`popular-${index}`}
                      onSelect={() => handleSearch(search)}
                      className="cursor-pointer"
                    >
                      <TrendingUp className="mr-2 h-4 w-4 text-muted-foreground" />
                      <span className="flex-1">{search}</span>
                    </CommandItem>
                  ))}
                </CommandGroup>
              )}

              {inputValue && suggestions && suggestions.length > 0 && (
                <CommandGroup heading="Suggestions">
                  {suggestions.map((suggestion, index) => (
                    <CommandItem
                      key={`${suggestion.type}-${suggestion.value}-${index}`}
                      onSelect={() => handleSearch(suggestion.value)}
                      className="cursor-pointer"
                    >
                      <Search className="mr-2 h-4 w-4 text-muted-foreground" />
                      <span className="flex-1">{suggestion.value}</span>
                      <Badge variant="secondary" className="ml-2">
                        {suggestion.type}
                      </Badge>
                      {suggestion.count && (
                        <span className="ml-2 text-xs text-muted-foreground">
                          {suggestion.count}
                        </span>
                      )}
                    </CommandItem>
                  ))}
                </CommandGroup>
              )}

              {inputValue && suggestions && suggestions.length === 0 && !suggestionsLoading && (
                <CommandEmpty>No suggestions found</CommandEmpty>
              )}
            </CommandList>
          </Command>
        </PopoverContent>
      </Popover>
    </div>
  );
};
