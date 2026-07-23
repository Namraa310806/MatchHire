import React from 'react';
import { Search, Filter, Sparkles, AlertCircle, RefreshCw } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';

interface EmptySearchStateProps {
  onClearFilters?: () => void;
  onResetSearch?: () => void;
}

export const EmptySearchState: React.FC<EmptySearchStateProps> = ({
  onClearFilters,
  onResetSearch,
}) => {
  return (
    <Card>
      <CardContent className="flex flex-col items-center justify-center py-12">
        <Search className="h-16 w-16 text-muted-foreground mb-4" />
        <h3 className="text-lg font-semibold mb-2">No results found</h3>
        <p className="text-muted-foreground text-center max-w-sm mb-6">
          Try adjusting your search terms or filters to find what you're looking for.
        </p>
        <div className="flex gap-2">
          {onResetSearch && (
            <Button variant="outline" onClick={onResetSearch}>
              <RefreshCw className="h-4 w-4 mr-2" />
              Reset Search
            </Button>
          )}
          {onClearFilters && (
            <Button variant="outline" onClick={onClearFilters}>
              <Filter className="h-4 w-4 mr-2" />
              Clear Filters
            </Button>
          )}
        </div>
      </CardContent>
    </Card>
  );
};

export const EmptyRecommendationState: React.FC = () => {
  return (
    <Card>
      <CardContent className="flex flex-col items-center justify-center py-12">
        <Sparkles className="h-16 w-16 text-muted-foreground mb-4" />
        <h3 className="text-lg font-semibold mb-2">No recommendations yet</h3>
        <p className="text-muted-foreground text-center max-w-sm">
          Complete your profile and add more details to get personalized recommendations.
        </p>
      </CardContent>
    </Card>
  );
};

export const EmptyHistoryState: React.FC = () => {
  return (
    <Card>
      <CardContent className="flex flex-col items-center justify-center py-12">
        <Search className="h-16 w-16 text-muted-foreground mb-4" />
        <h3 className="text-lg font-semibold mb-2">No search history</h3>
        <p className="text-muted-foreground text-center max-w-sm">
          Your recent searches will appear here as you use the search feature.
        </p>
      </CardContent>
    </Card>
  );
};

export const EmptySavedSearchesState: React.FC = () => {
  return (
    <Card>
      <CardContent className="flex flex-col items-center justify-center py-12">
        <Filter className="h-16 w-16 text-muted-foreground mb-4" />
        <h3 className="text-lg font-semibold mb-2">No saved searches</h3>
        <p className="text-muted-foreground text-center max-w-sm">
          Save your frequent searches for quick access later.
        </p>
      </CardContent>
    </Card>
  );
};

interface ErrorStateProps {
  message?: string;
  onRetry?: () => void;
}

export const SearchErrorState: React.FC<ErrorStateProps> = ({
  message = 'Something went wrong while searching',
  onRetry,
}) => {
  return (
    <Card className="border-destructive">
      <CardContent className="flex flex-col items-center justify-center py-12">
        <AlertCircle className="h-16 w-16 text-destructive mb-4" />
        <h3 className="text-lg font-semibold mb-2 text-destructive">Search Error</h3>
        <p className="text-muted-foreground text-center max-w-sm mb-6">
          {message}
        </p>
        {onRetry && (
          <Button variant="outline" onClick={onRetry}>
            <RefreshCw className="h-4 w-4 mr-2" />
            Try Again
          </Button>
        )}
      </CardContent>
    </Card>
  );
};

export const NetworkErrorState: React.FC<ErrorStateProps> = ({
  onRetry,
}) => {
  return (
    <Card className="border-orange-200">
      <CardContent className="flex flex-col items-center justify-center py-12">
        <AlertCircle className="h-16 w-16 text-orange-500 mb-4" />
        <h3 className="text-lg font-semibold mb-2">Connection Error</h3>
        <p className="text-muted-foreground text-center max-w-sm mb-6">
          Unable to connect to the search service. Please check your internet connection.
        </p>
        {onRetry && (
          <Button variant="outline" onClick={onRetry}>
            <RefreshCw className="h-4 w-4 mr-2" />
            Retry
          </Button>
        )}
      </CardContent>
    </Card>
  );
};
