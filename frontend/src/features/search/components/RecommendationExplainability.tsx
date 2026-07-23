import React, { useState } from 'react';
import { 
  Sparkles, 
  CheckCircle2, 
  XCircle, 
  AlertCircle, 
  Info,
  ThumbsUp,
  ThumbsDown,
  Eye,
  EyeOff,
  ChevronDown,
  ChevronUp
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { cn } from '@/lib/utils';

interface RecommendationExplanation {
  recommendationId: string;
  whyRecommended: string;
  matchingSkills: string[];
  matchingExperience: string[];
  missingSkills: string[];
  resumeSimilarity: number;
  jobSimilarity: number;
  confidence: 'high' | 'medium' | 'low';
  factors: Array<{
    name: string;
    value: number;
    description: string;
  }>;
}

interface RecommendationExplainabilityProps {
  explanation: RecommendationExplanation;
  onFeedback?: (recommendationId: string, feedback: 'positive' | 'negative') => void;
  onHide?: (recommendationId: string) => void;
  onSave?: (recommendationId: string) => void;
  className?: string;
}

export const RecommendationExplainability: React.FC<RecommendationExplainabilityProps> = ({
  explanation,
  onFeedback,
  onHide,
  onSave,
  className,
}) => {
  const [showDetails, setShowDetails] = useState(false);
  const [feedback, setFeedback] = useState<'positive' | 'negative' | null>(null);

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

  const handleFeedback = (type: 'positive' | 'negative') => {
    setFeedback(type);
    onFeedback?.(explanation.recommendationId, type);
  };

  const handleHide = () => {
    onHide?.(explanation.recommendationId);
  };

  return (
    <Card className={cn('border-l-4 border-l-purple-500 bg-gradient-to-br from-purple-50/50 to-blue-50/50', className)}>
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <CardTitle className="text-lg flex items-center gap-2">
              <Sparkles className="h-5 w-5 text-purple-500" />
              Why This Was Recommended
            </CardTitle>
            <Badge className={getConfidenceColor(explanation.confidence)} variant="outline">
              {explanation.confidence} confidence
            </Badge>
          </div>
          <div className="flex gap-1">
            <Button
              variant="ghost"
              size="sm"
              className="h-8 w-8 p-0"
              onClick={() => setShowDetails(!showDetails)}
            >
              {showDetails ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
            </Button>
            <Button
              variant="ghost"
              size="sm"
              className="h-8 w-8 p-0"
              onClick={handleHide}
            >
              <EyeOff className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* Main Reason */}
        <div className="bg-white/80 rounded-lg p-3 border">
          <div className="flex items-start gap-2">
            <Info className="h-4 w-4 text-blue-500 mt-0.5 flex-shrink-0" />
            <p className="text-sm">{explanation.whyRecommended}</p>
          </div>
        </div>

        {showDetails && (
          <>
            {/* Similarity Scores */}
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <div className="flex items-center justify-between text-sm">
                  <span className="font-medium">Resume Similarity</span>
                  <span className="text-purple-600 font-semibold">{explanation.resumeSimilarity}%</span>
                </div>
                <div className="relative h-2 bg-secondary rounded-full overflow-hidden">
                  <div
                    className={cn('h-full transition-all', getScoreColor(explanation.resumeSimilarity))}
                    style={{ width: `${explanation.resumeSimilarity}%` }}
                  />
                </div>
              </div>

              <div className="space-y-2">
                <div className="flex items-center justify-between text-sm">
                  <span className="font-medium">Job Similarity</span>
                  <span className="text-blue-600 font-semibold">{explanation.jobSimilarity}%</span>
                </div>
                <div className="relative h-2 bg-secondary rounded-full overflow-hidden">
                  <div
                    className={cn('h-full transition-all', getScoreColor(explanation.jobSimilarity))}
                    style={{ width: `${explanation.jobSimilarity}%` }}
                  />
                </div>
              </div>
            </div>

            {/* Matching Skills */}
            {explanation.matchingSkills.length > 0 && (
              <div className="space-y-2">
                <h4 className="text-sm font-semibold flex items-center gap-2">
                  <CheckCircle2 className="h-4 w-4 text-green-500" />
                  Matching Skills
                </h4>
                <div className="flex flex-wrap gap-1">
                  {explanation.matchingSkills.map((skill, index) => (
                    <Badge key={index} variant="secondary" className="text-xs bg-green-100 text-green-800 border-green-200">
                      {skill}
                    </Badge>
                  ))}
                </div>
              </div>
            )}

            {/* Matching Experience */}
            {explanation.matchingExperience.length > 0 && (
              <div className="space-y-2">
                <h4 className="text-sm font-semibold flex items-center gap-2">
                  <CheckCircle2 className="h-4 w-4 text-blue-500" />
                  Matching Experience
                </h4>
                <ul className="text-sm text-muted-foreground space-y-1">
                  {explanation.matchingExperience.map((exp, index) => (
                    <li key={index} className="flex items-start gap-2">
                      <span className="text-blue-500 mt-1">•</span>
                      <span>{exp}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Missing Skills */}
            {explanation.missingSkills.length > 0 && (
              <div className="space-y-2">
                <h4 className="text-sm font-semibold flex items-center gap-2">
                  <AlertCircle className="h-4 w-4 text-orange-500" />
                  Missing Skills (Opportunity to Improve)
                </h4>
                <div className="flex flex-wrap gap-1">
                  {explanation.missingSkills.map((skill, index) => (
                    <Badge key={index} variant="outline" className="text-xs bg-orange-50 text-orange-800 border-orange-200">
                      {skill}
                    </Badge>
                  ))}
                </div>
              </div>
            )}

            {/* Detailed Factors */}
            {explanation.factors && explanation.factors.length > 0 && (
              <div className="space-y-2 border-t pt-4">
                <h4 className="text-sm font-semibold">Detailed Factors</h4>
                <div className="space-y-2">
                  {explanation.factors.map((factor, index) => (
                    <div key={index} className="flex items-start gap-2 p-2 rounded-lg bg-white/50 border">
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
                  ))}
                </div>
              </div>
            )}
          </>
        )}

        {/* Feedback Actions */}
        <div className="border-t pt-4 space-y-3">
          <div className="flex items-center gap-2">
            <span className="text-sm font-medium">Was this recommendation helpful?</span>
          </div>
          <div className="flex gap-2">
            <Button
              variant={feedback === 'positive' ? 'default' : 'outline'}
              size="sm"
              className="flex-1"
              onClick={() => handleFeedback('positive')}
              disabled={feedback !== null}
            >
              <ThumbsUp className="h-4 w-4 mr-2" />
              Helpful
            </Button>
            <Button
              variant={feedback === 'negative' ? 'destructive' : 'outline'}
              size="sm"
              className="flex-1"
              onClick={() => handleFeedback('negative')}
              disabled={feedback !== null}
            >
              <ThumbsDown className="h-4 w-4 mr-2" />
              Not Relevant
            </Button>
          </div>

          {feedback && (
            <div className={cn(
              'text-sm p-2 rounded-lg flex items-center gap-2',
              feedback === 'positive' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
            )}>
              {feedback === 'positive' ? (
                <CheckCircle2 className="h-4 w-4" />
              ) : (
                <XCircle className="h-4 w-4" />
              )}
              <span>
                {feedback === 'positive' 
                  ? 'Thanks for your feedback! We\'ll show more recommendations like this.' 
                  : 'Thanks for your feedback! We\'ll adjust your recommendations.'}
              </span>
            </div>
          )}

          <div className="flex gap-2">
            <Button
              variant="ghost"
              size="sm"
              className="flex-1"
              onClick={() => onSave?.(explanation.recommendationId)}
            >
              <Eye className="h-4 w-4 mr-2" />
              Save for Later
            </Button>
            <Button
              variant="ghost"
              size="sm"
              className="flex-1 text-destructive hover:text-destructive"
              onClick={handleHide}
            >
              <EyeOff className="h-4 w-4 mr-2" />
              Hide This
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};
