import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { useFeatureFlags, useUpdateFeatureFlag } from '../hooks/useFeatureFlags';
import { Flag, RefreshCw, ToggleLeft, ToggleRight } from 'lucide-react';

export default function FeatureFlags() {
  const { data: flags, isLoading, refetch } = useFeatureFlags();
  const updateFeatureFlag = useUpdateFeatureFlag();

  const handleToggle = async (id: string, currentEnabled: boolean) => {
    try {
      await updateFeatureFlag.mutateAsync({ id, enabled: !currentEnabled });
    } catch (error) {
      console.error('Failed to update feature flag:', error);
    }
  };

  const getEnvironmentBadge = (env: string) => {
    const colors = {
      development: 'bg-slate-500/10 text-slate-400 border-slate-500/20',
      staging: 'bg-amber-500/10 text-amber-400 border-amber-500/20',
      production: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
    };
    return (
      <Badge className={colors[env as keyof typeof colors] || colors.development} variant="outline">
        {env}
      </Badge>
    );
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Feature Flags</h1>
          <p className="text-slate-400 mt-2">Manage feature flags across environments</p>
        </div>
        <Button variant="outline" onClick={() => refetch()} disabled={isLoading}>
          <RefreshCw className={`h-4 w-4 mr-2 ${isLoading ? 'animate-spin' : ''}`} />
          Refresh
        </Button>
      </div>

      <Card className="border-slate-800 bg-slate-900/50">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Flag className="h-5 w-5" />
            Feature Flags
          </CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="space-y-4">
              {[...Array(5)].map((_, i) => (
                <Skeleton key={i} className="h-20" />
              ))}
            </div>
          ) : flags && flags.length > 0 ? (
            <div className="space-y-4">
              {flags.map((flag) => (
                <div
                  key={flag.id}
                  className="flex items-center justify-between p-4 rounded-lg border border-slate-800 bg-slate-800/50"
                >
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2">
                      <h3 className="font-semibold">{flag.name}</h3>
                      {getEnvironmentBadge(flag.environment)}
                      <Badge className={flag.enabled ? 'bg-emerald-500/10 text-emerald-400' : 'bg-red-500/10 text-red-400'} variant="outline">
                        {flag.enabled ? 'Enabled' : 'Disabled'}
                      </Badge>
                    </div>
                    <p className="text-sm text-slate-400 mb-1">{flag.description}</p>
                    <p className="text-xs text-slate-500 font-mono">{flag.key}</p>
                  </div>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => handleToggle(flag.id, flag.enabled)}
                    disabled={updateFeatureFlag.isPending}
                    className={flag.enabled ? 'text-emerald-400 hover:text-emerald-300 hover:bg-emerald-500/10' : 'text-slate-400 hover:text-slate-300 hover:bg-slate-500/10'}
                  >
                    {flag.enabled ? (
                      <ToggleRight className="h-5 w-5" />
                    ) : (
                      <ToggleLeft className="h-5 w-5" />
                    )}
                  </Button>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-12">
              <Flag className="h-12 w-12 text-slate-600 mx-auto mb-4" />
              <p className="text-slate-400">No feature flags configured</p>
              <p className="text-sm text-slate-500 mt-2">
                Feature flag management requires backend support
              </p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
