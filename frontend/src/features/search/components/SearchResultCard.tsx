import React, { useState } from 'react';
import { 
  Building2, 
  MapPin, 
  DollarSign, 
  Clock, 
  Briefcase, 
  GraduationCap,
  User,
  Star,
  ExternalLink,
  Bookmark,
  Share2,
  ChevronDown,
  ChevronUp,
  Sparkles
} from 'lucide-react';
import { SearchResult, RankingExplanation } from '../types';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardFooter, CardHeader } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';
import { cn } from '@/lib/utils';
import { formatDistanceToNow } from 'date-fns';

interface SearchResultCardProps {
  result: SearchResult;
  onResultClick?: (result: SearchResult) => void;
  onSave?: (result: SearchResult) => void;
  onShare?: (result: SearchResult) => void;
  showRankingExplanation?: boolean;
  rankingExplanation?: RankingExplanation;
  className?: string;
}

export const SearchResultCard: React.FC<SearchResultCardProps> = ({
  result,
  onResultClick,
  onSave,
  onShare,
  showRankingExplanation = false,
  rankingExplanation,
  className,
}) => {
  const [showExplanation, setShowExplanation] = useState(false);
  const [isSaved, setIsSaved] = useState(false);

  const isJob = result.type === 'job';
  const data = result.data;

  const matchScore = result.score || 0;
  const matchColor = matchScore >= 80 ? 'text-green-600' : matchScore >= 60 ? 'text-yellow-600' : 'text-orange-600';
  const matchBg = matchScore >= 80 ? 'bg-green-100' : matchScore >= 60 ? 'bg-yellow-100' : 'bg-orange-100';

  const handleSave = (e: React.MouseEvent) => {
    e.stopPropagation();
    setIsSaved(!isSaved);
    onSave?.(result);
  };

  const handleShare = (e: React.MouseEvent) => {
    e.stopPropagation();
    onShare?.(result);
  };

  return (
    <Card
      className={cn(
        'hover:shadow-lg transition-all cursor-pointer group',
        className
      )}
      onClick={() => onResultClick?.(result)}
    >
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-2">
              <Badge variant={isJob ? 'default' : 'secondary'} className="text-xs">
                {isJob ? 'Job' : 'Candidate'}
              </Badge>
              {result.highlighted_fields && Object.keys(result.highlighted_fields).length > 0 && (
                <Badge variant="outline" className="text-xs">
                  <Sparkles className="h-3 w-3 mr-1" />
                  AI Matched
                </Badge>
              )}
            </div>
            
            <h3 className="font-semibold text-lg mb-1">
              {isJob ? data.title : `${data.first_name} ${data.last_name}`}
            </h3>
            
            {isJob ? (
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <Building2 className="h-4 w-4" />
                <span>{data.company_name}</span>
              </div>
            ) : (
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <User className="h-4 w-4" />
                <span>{data.candidate_profile?.title || 'No title specified'}</span>
              </div>
            )}
          </div>

          <div className="flex flex-col items-end gap-2">
            <TooltipProvider>
              <Tooltip>
                <TooltipTrigger asChild>
                  <div className={cn('flex items-center gap-1 px-3 py-1 rounded-full text-sm font-semibold', matchBg, matchColor)}>
                    <Star className="h-4 w-4 fill-current" />
                    {matchScore}%
                  </div>
                </TooltipTrigger>
                <TooltipContent>
                  <p>Match Score: {matchScore}%</p>
                </TooltipContent>
              </Tooltip>
            </TooltipProvider>

            <div className="flex gap-1">
              <Button
                variant="ghost"
                size="sm"
                className="h-8 w-8 p-0 opacity-0 group-hover:opacity-100 transition-opacity"
                onClick={handleSave}
              >
                <Bookmark className={cn('h-4 w-4', isSaved && 'fill-current')} />
              </Button>
              <Button
                variant="ghost"
                size="sm"
                className="h-8 w-8 p-0 opacity-0 group-hover:opacity-100 transition-opacity"
                onClick={handleShare}
              >
                <Share2 className="h-4 w-4" />
              </Button>
            </div>
          </div>
        </div>
      </CardHeader>

      <CardContent className="space-y-3">
        {/* Location */}
        <div className="flex items-center gap-2 text-sm text-muted-foreground">
          <MapPin className="h-4 w-4" />
          <span>{data.location || 'Remote'}</span>
          {data.is_remote !== undefined && data.is_remote && (
            <Badge variant="outline" className="text-xs">Remote</Badge>
          )}
        </div>

        {/* Skills */}
        {data.skills && data.skills.length > 0 && (
          <div className="flex flex-wrap gap-1">
            {data.skills.slice(0, 5).map((skill: string, index: number) => (
              <Badge key={index} variant="secondary" className="text-xs">
                {skill}
              </Badge>
            ))}
            {data.skills.length > 5 && (
              <Badge variant="outline" className="text-xs">
                +{data.skills.length - 5} more
              </Badge>
            )}
          </div>
        )}

        {/* Job-specific details */}
        {isJob && (
          <>
            {data.salary_min || data.salary_max ? (
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <DollarSign className="h-4 w-4" />
                <span>
                  {data.salary_min && `$${data.salary_min.toLocaleString()}`}
                  {data.salary_min && data.salary_max && ' - '}
                  {data.salary_max && `$${data.salary_max.toLocaleString()}`}
                  {data.currency && ` ${data.currency}`}
                </span>
              </div>
            ) : null}
            
            {data.employment_type && (
              <Badge variant="outline" className="text-xs w-fit">
                {data.employment_type.replace('_', ' ')}
              </Badge>
            )}

            {data.experience_level && (
              <Badge variant="outline" className="text-xs w-fit">
                <Briefcase className="h-3 w-3 mr-1" />
                {data.experience_level}
              </Badge>
            )}
          </>
        )}

        {/* Candidate-specific details */}
        {!isJob && (
          <>
            {data.candidate_profile?.experience_years !== undefined && (
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <Briefcase className="h-4 w-4" />
                <span>{data.candidate_profile.experience_years} years experience</span>
              </div>
            )}

            {data.candidate_profile?.education && data.candidate_profile.education.length > 0 && (
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <GraduationCap className="h-4 w-4" />
                <span>{data.candidate_profile.education[0].degree}</span>
              </div>
            )}

            {data.candidate_profile?.experience && data.candidate_profile.experience.length > 0 && (
              <div className="text-sm text-muted-foreground">
                <span className="font-medium">Recent:</span> {data.candidate_profile.experience[0].position} at {data.candidate_profile.experience[0].company}
              </div>
            )}
          </>
        )}

        {/* Ranking Explanation */}
        {showRankingExplanation && rankingExplanation && (
          <div className="border-t pt-3 mt-3">
            <Button
              variant="ghost"
              size="sm"
              className="text-xs w-full justify-between"
              onClick={() => setShowExplanation(!showExplanation)}
            >
              <span>Why this result?</span>
              {showExplanation ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
            </Button>
            
            {showExplanation && (
              <div className="mt-3 space-y-2">
                <div className="space-y-1">
                  <div className="flex justify-between text-xs">
                    <span>Semantic Match</span>
                    <span className="font-medium">{rankingExplanation.semantic_score}%</span>
                  </div>
                  <Progress value={rankingExplanation.semantic_score} className="h-1" />
                </div>
                
                <div className="space-y-1">
                  <div className="flex justify-between text-xs">
                    <span>Keyword Match</span>
                    <span className="font-medium">{rankingExplanation.keyword_score}%</span>
                  </div>
                  <Progress value={rankingExplanation.keyword_score} className="h-1" />
                </div>
                
                <div className="space-y-1">
                  <div className="flex justify-between text-xs">
                    <span>Recency</span>
                    <span className="font-medium">{rankingExplanation.recency_score}%</span>
                  </div>
                  <Progress value={rankingExplanation.recency_score} className="h-1" />
                </div>
                
                <div className="space-y-1">
                  <div className="flex justify-between text-xs">
                    <span>Popularity</span>
                    <span className="font-medium">{rankingExplanation.popularity_score}%</span>
                  </div>
                  <Progress value={rankingExplanation.popularity_score} className="h-1" />
                </div>

                {rankingExplanation.factors && rankingExplanation.factors.length > 0 && (
                  <div className="mt-2 pt-2 border-t">
                    <p className="text-xs font-medium mb-1">Key Factors:</p>
                    <ul className="text-xs text-muted-foreground space-y-1">
                      {rankingExplanation.factors.slice(0, 3).map((factor, index) => (
                        <li key={index} className="flex items-start gap-1">
                          <span className="text-green-600">✓</span>
                          <span>{factor.description}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            )}
          </div>
        )}
      </CardContent>

      <CardFooter className="pt-3 border-t flex justify-between items-center">
        <div className="text-xs text-muted-foreground">
          {data.created_at && (
            <span className="flex items-center gap-1">
              <Clock className="h-3 w-3" />
              {formatDistanceToNow(new Date(data.created_at), { addSuffix: true })}
            </span>
          )}
        </div>
        
        <Button variant="ghost" size="sm" className="text-sm">
          View Details
          <ExternalLink className="h-4 w-4 ml-1" />
        </Button>
      </CardFooter>
    </Card>
  );
};
