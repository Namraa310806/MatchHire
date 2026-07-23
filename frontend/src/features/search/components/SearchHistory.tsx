import React, { useState } from 'react';
import { Clock, Star, Trash2, Pin, PinOff, Search, Calendar, BarChart3 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { cn } from '@/lib/utils';
import { RecentSearch, SavedSearch } from '../types';
import { formatDistanceToNow } from 'date-fns';

interface SearchHistoryProps {
  recentSearches: RecentSearch[];
  savedSearches: SavedSearch[];
  onRunSearch: (query: string, entityType: string) => void;
  onSaveSearch: (name: string, query: any) => void;
  onDeleteSavedSearch: (id: string) => void;
  onPinSearch: (id: string) => void;
  onUnpinSearch: (id: string) => void;
  onClearRecentSearches: () => void;
  onDeleteRecentSearch: (query: string) => void;
  className?: string;
}

export const SearchHistory: React.FC<SearchHistoryProps> = ({
  recentSearches,
  savedSearches,
  onRunSearch,
  onSaveSearch,
  onDeleteSavedSearch,
  onPinSearch,
  onUnpinSearch,
  onClearRecentSearches,
  onDeleteRecentSearch,
  className,
}) => {
  const [saveDialogOpen, setSaveDialogOpen] = useState(false);
  const [saveSearchName, setSaveSearchName] = useState('');
  const [saveSearchQuery, setSaveSearchQuery] = useState<any>(null);
  const [activeTab, setActiveTab] = useState<'recent' | 'saved'>('recent');

  const pinnedSearches = savedSearches.filter(s => s.is_pinned);
  const unpinnedSearches = savedSearches.filter(s => !s.is_pinned);

  const handleSaveSearch = () => {
    if (saveSearchName.trim() && saveSearchQuery) {
      onSaveSearch(saveSearchName, saveSearchQuery);
      setSaveSearchName('');
      setSaveSearchQuery(null);
      setSaveDialogOpen(false);
    }
  };

  const openSaveDialog = (query: any) => {
    setSaveSearchQuery(query);
    setSaveSearchName('');
    setSaveDialogOpen(true);
  };

  const entityTypeLabels = {
    all: 'All',
    job: 'Jobs',
    candidate: 'Candidates',
  };

  return (
    <div className={cn('space-y-6', className)}>
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold">Search History</h2>
        <div className="flex gap-2">
          <Button
            variant={activeTab === 'recent' ? 'default' : 'outline'}
            size="sm"
            onClick={() => setActiveTab('recent')}
          >
            <Clock className="h-4 w-4 mr-2" />
            Recent ({recentSearches.length})
          </Button>
          <Button
            variant={activeTab === 'saved' ? 'default' : 'outline'}
            size="sm"
            onClick={() => setActiveTab('saved')}
          >
            <Star className="h-4 w-4 mr-2" />
            Saved ({savedSearches.length})
          </Button>
        </div>
      </div>

      {/* Recent Searches */}
      {activeTab === 'recent' && (
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="text-lg">Recent Searches</CardTitle>
              {recentSearches.length > 0 && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={onClearRecentSearches}
                  className="text-destructive hover:text-destructive"
                >
                  <Trash2 className="h-4 w-4 mr-1" />
                  Clear All
                </Button>
              )}
            </div>
          </CardHeader>
          <CardContent>
            {recentSearches.length === 0 ? (
              <div className="text-center py-8 text-muted-foreground">
                <Clock className="h-12 w-12 mx-auto mb-4 opacity-50" />
                <p>No recent searches</p>
              </div>
            ) : (
              <div className="space-y-2">
                {recentSearches.map((search, index) => (
                  <div
                    key={`${search.query}-${index}`}
                    className="flex items-center justify-between p-3 rounded-lg hover:bg-muted transition-colors group"
                  >
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <Search className="h-4 w-4 text-muted-foreground" />
                        <span className="font-medium">{search.query}</span>
                        <Badge variant="outline" className="text-xs">
                          {entityTypeLabels[search.entity_type]}
                        </Badge>
                      </div>
                      <div className="flex items-center gap-4 mt-1 text-xs text-muted-foreground">
                        <span className="flex items-center gap-1">
                          <Calendar className="h-3 w-3" />
                          {formatDistanceToNow(new Date(search.timestamp), { addSuffix: true })}
                        </span>
                        {search.result_count !== undefined && (
                          <span className="flex items-center gap-1">
                            <BarChart3 className="h-3 w-3" />
                            {search.result_count} results
                          </span>
                        )}
                      </div>
                    </div>
                    <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                      <Button
                        variant="ghost"
                        size="sm"
                        className="h-8 w-8 p-0"
                        onClick={() => onRunSearch(search.query, search.entity_type)}
                      >
                        <Search className="h-4 w-4" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        className="h-8 w-8 p-0"
                        onClick={() => openSaveDialog({ q: search.query, entity_type: search.entity_type })}
                      >
                        <Star className="h-4 w-4" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        className="h-8 w-8 p-0 text-destructive hover:text-destructive"
                        onClick={() => onDeleteRecentSearch(search.query)}
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Saved Searches */}
      {activeTab === 'saved' && (
        <div className="space-y-6">
          {/* Pinned Searches */}
          {pinnedSearches.length > 0 && (
            <Card className="border-amber-200 bg-amber-50/50">
              <CardHeader>
                <CardTitle className="text-lg flex items-center gap-2">
                  <Pin className="h-5 w-5 text-amber-500" />
                  Pinned Searches
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  {pinnedSearches.map((search) => (
                    <SavedSearchItem
                      key={search.id}
                      search={search}
                      onRun={onRunSearch}
                      onPin={onUnpinSearch}
                      onDelete={onDeleteSavedSearch}
                      isPinned
                    />
                  ))}
                </div>
              </CardContent>
            </Card>
          )}

          {/* Regular Saved Searches */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">
                {pinnedSearches.length > 0 ? 'Other Saved Searches' : 'Saved Searches'}
              </CardTitle>
            </CardHeader>
            <CardContent>
              {unpinnedSearches.length === 0 && pinnedSearches.length === 0 ? (
                <div className="text-center py-8 text-muted-foreground">
                  <Star className="h-12 w-12 mx-auto mb-4 opacity-50" />
                  <p>No saved searches yet</p>
                  <p className="text-sm mt-2">Save your frequent searches for quick access</p>
                </div>
              ) : (
                <div className="space-y-2">
                  {unpinnedSearches.map((search) => (
                    <SavedSearchItem
                      key={search.id}
                      search={search}
                      onRun={onRunSearch}
                      onPin={onPinSearch}
                      onDelete={onDeleteSavedSearch}
                      isPinned={false}
                    />
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      )}

      {/* Save Search Dialog */}
      <Dialog open={saveDialogOpen} onOpenChange={setSaveDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Save Search</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <Label htmlFor="search-name">Search Name</Label>
              <Input
                id="search-name"
                placeholder="e.g., Senior React Developers"
                value={saveSearchName}
                onChange={(e) => setSaveSearchName(e.target.value)}
                className="mt-1"
              />
            </div>
            <div className="flex justify-end gap-2">
              <Button variant="outline" onClick={() => setSaveDialogOpen(false)}>
                Cancel
              </Button>
              <Button onClick={handleSaveSearch} disabled={!saveSearchName.trim()}>
                Save Search
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
};

interface SavedSearchItemProps {
  search: SavedSearch;
  onRun: (query: string, entityType: string) => void;
  onPin: (id: string) => void;
  onDelete: (id: string) => void;
  isPinned: boolean;
}

const SavedSearchItem: React.FC<SavedSearchItemProps> = ({
  search,
  onRun,
  onPin,
  onDelete,
  isPinned,
}) => {
  const query = search.query_params || search.query;
  const queryText = query?.q || 'Untitled Search';

  return (
    <div className="flex items-center justify-between p-3 rounded-lg hover:bg-muted transition-colors group">
      <div className="flex-1">
        <div className="flex items-center gap-2">
          <span className="font-medium">{search.name}</span>
          {isPinned && <Pin className="h-4 w-4 text-amber-500" />}
        </div>
        <div className="text-sm text-muted-foreground mt-1">
          {queryText}
        </div>
        <div className="flex items-center gap-4 mt-1 text-xs text-muted-foreground">
          <span className="flex items-center gap-1">
            <Calendar className="h-3 w-3" />
            {formatDistanceToNow(new Date(search.created_at), { addSuffix: true })}
          </span>
          {search.last_used && (
            <span className="flex items-center gap-1">
              Last used {formatDistanceToNow(new Date(search.last_used), { addSuffix: true })}
            </span>
          )}
        </div>
      </div>
      <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
        <Button
          variant="ghost"
          size="sm"
          className="h-8 w-8 p-0"
          onClick={() => onRun(query?.q || '', query?.entity_type || 'all')}
        >
          <Search className="h-4 w-4" />
        </Button>
        <Button
          variant="ghost"
          size="sm"
          className="h-8 w-8 p-0"
          onClick={() => onPin(search.id)}
          title={isPinned ? 'Unpin' : 'Pin'}
        >
          {isPinned ? <PinOff className="h-4 w-4" /> : <Pin className="h-4 w-4" />}
        </Button>
        <Button
          variant="ghost"
          size="sm"
          className="h-8 w-8 p-0 text-destructive hover:text-destructive"
          onClick={() => onDelete(search.id)}
        >
          <Trash2 className="h-4 w-4" />
        </Button>
      </div>
    </div>
  );
};
