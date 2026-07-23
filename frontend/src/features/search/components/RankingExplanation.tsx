import React from 'react';
import { Info, TrendingUp, Target, Clock, Users, CheckCircle2 } from 'lucide-react';
import type { RankingExplanation } from '../types';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';
import { cn } from '@/lib/utils';

interface RankingExplanationProps {
  explanation: RankingExplanation;
  className?: string;
}

export const RankingExplanationComponent: React.FC<RankingExplanationProps> = ({
  explanation,
  className,
}) => {
  const getConfidenceColor = (confidence: string) => {
    switch (confidence) {
      case 'high':
        return 'bg-green-100 text-green-800 border-green-200';
      case 'medium':
        return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      case 'low':
        return 'bg-orange-100 text-orange-800 border-orange-200';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  const getScoreColor = (score: number) => {
    if (score >= 80) return 'bg-green-500';
    if (score >= 60) return 'bg-yellow-500';
    if (score >= 40) return 'bg-orange-500';
    return 'bg-red-500';
  };

  return (
    <Card className={cn('border-l-4 border-l-blue-500', className)}>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg flex items-center gap-2">
            <Info className="h-5 w-5 text-blue-500" />
            Why This Result?
          </CardTitle>
          <Badge className={getConfidenceColor(explanation.confidence)}>
            {explanation.confidence} confidence
          </Badge>
        </div>
      </CardHeader>
      
      <CardContent className="space-y-4">
        {/* Overall Score */}
        <div className="text-center p-4 bg-gradient-to-br from-blue-50 to-indigo-50 rounded-lg">
          <div className="text-4xl font-bold text-blue-600 mb-1">
            {explanation.overall_score}%
          </div>
          <div className="text-sm text-muted-foreground">Overall Match Score</div>
        </div>

        {/* Score Breakdown */}
        <div className="space-y-3">
          <div className="space-y-1">
            <div className="flex items-center justify-between text-sm">
              <span className="flex items-center gap-2">
                <Target className="h-4 w-4 text-purple-500" />
                Semantic Match
              </span>
              <span className="font-medium">{explanation.semantic_score}%</span>
            </div>
            <div className="relative h-2 bg-secondary rounded-full overflow-hidden">
              <div
                className={cn('h-full transition-all', getScoreColor(explanation.semantic_score))}
                style={{ width: `${explanation.semantic_score}%` }}
              />
            </div>
          </div>

          <div className="space-y-1">
            <div className="flex items-center justify-between text-sm">
              <span className="flex items-center gap-2">
                <TrendingUp className="h-4 w-4 text-green-500" />
                Keyword Match
              </span>
              <span className="font-medium">{explanation.keyword_score}%</span>
            </div>
            <div className="relative h-2 bg-secondary rounded-full overflow-hidden">
              <div
                className={cn('h-full transition-all', getScoreColor(explanation.keyword_score))}
                style={{ width: `${explanation.keyword_score}%` }}
              />
            </div>
          </div>

          <div className="space-y-1">
            <div className="flex items-center justify-between text-sm">
              <span className="flex items-center gap-2">
                <Clock className="h-4 w-4 text-orange-500" />
                Recency
              </span>
              <span className="font-medium">{explanation.recency_score}%</span>
            </div>
            <div className="relative h-2 bg-secondary rounded-full overflow-hidden">
              <div
                className={cn('h-full transition-all', getScoreColor(explanation.recency_score))}
                style={{ width: `${explanation.recency_score}%` }}
              />
            </div>
          </div>

          <div className="space-y-1">
            <div className="flex items-center justify-between text-sm">
              <span className="flex items-center gap-2">
                <Users className="h-4 w-4 text-blue-500" />
                Popularity
              </span>
              <span className="font-medium">{explanation.popularity_score}%</span>
            </div>
            <div className="relative h-2 bg-secondary rounded-full overflow-hidden">
              <div
                className={cn('h-full transition-all', getScoreColor(explanation.popularity_score))}
                style={{ width: `${explanation.popularity_score}%` }}
              />
            </div>
          </div>
        </div>

        {/* Key Factors */}
        {explanation.factors && explanation.factors.length > 0 && (
          <div className="border-t pt-4">
            <h4 className="font-medium mb-3 flex items-center gap-2">
              <CheckCircle2 className="h-4 w-4 text-green-500" />
              Key Factors
            </h4>
            <div className="space-y-2">
              {explanation.factors.map((factor, index) => (
                <TooltipProvider key={index}>
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <div className="flex items-start gap-2 p-2 rounded-lg hover:bg-muted transition-colors cursor-help">
                        <div className="flex-1">
                          <div className="text-sm font-medium">{factor.name}</div>
                          <div className="text-xs text-muted-foreground mt-1">
                            {factor.description}
                          </div>
                        </div>
                        <Badge variant="outline" className="text-xs">
                          {factor.value}%
                        </Badge>
                      </div>
                    </TooltipTrigger>
                    <TooltipContent>
                      <p className="text-sm">This factor contributed {factor.value}% to the overall score</p>
                    </TooltipContent>
                  </Tooltip>
                </TooltipProvider>
              ))}
            </div>
          </div>
        )}

        {/* Score Calculation Explanation */}
        <div className="bg-muted/50 rounded-lg p-3 text-xs text-muted-foreground">
          <p className="font-medium mb-1">How scores are calculated:</p>
          <ul className="space-y-1 ml-4 list-disc">
            <li><strong>Semantic Match:</strong> AI-powered understanding of meaning and context</li>
            <li><strong>Keyword Match:</strong> Direct matching of search terms</li>
            <li><strong>Recency:</strong> How recently the item was updated</li>
            <li><strong>Popularity:</strong> Engagement and activity metrics</li>
          </ul>
        </div>
      </CardContent>
    </Card>
  );
};
