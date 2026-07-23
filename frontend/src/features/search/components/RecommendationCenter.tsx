import React, { useState } from 'react';
import { Sparkles, TrendingUp, Clock, Heart, ThumbsUp, ThumbsDown } from 'lucide-react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { cn } from '@/lib/utils';
import { SearchResult } from '../types';

interface RecommendationCenterProps {
  userType: 'candidate' | 'recruiter';
  recommendedItems: SearchResult[];
  trendingItems: SearchResult[];
  recentlyViewed: SearchResult[];
  similarItems?: SearchResult[];
  onItemClick?: (item: SearchResult) => void;
  onFeedback?: (itemId: string, feedback: 'positive' | 'negative') => void;
  onSave?: (item: SearchResult) => void;
  className?: string;
}

export const RecommendationCenter: React.FC<RecommendationCenterProps> = ({
  userType,
  recommendedItems,
  trendingItems,
  recentlyViewed,
  similarItems = [],
  onItemClick,
  onFeedback,
  onSave,
  className,
}) => {
  const [activeTab, setActiveTab] = useState('recommended');
  const [savedItems, setSavedItems] = useState<Set<string>>(new Set());
  const [feedbackGiven, setFeedbackGiven] = useState<Record<string, 'positive' | 'negative'>>({});

  const handleSave = (item: SearchResult) => {
    const newSaved = new Set(savedItems);
    if (newSaved.has(item.id)) {
      newSaved.delete(item.id);
    } else {
      newSaved.add(item.id);
    }
    setSavedItems(newSaved);
    onSave?.(item);
  };

  const handleFeedback = (itemId: string, feedback: 'positive' | 'negative') => {
    setFeedbackGiven(prev => ({ ...prev, [itemId]: feedback }));
    onFeedback?.(itemId, feedback);
  };

  const renderRecommendationCard = (item: SearchResult, showFeedback = true) => {
    const isJob = item.type === 'job';
    const data = item.data;
    const isSaved = savedItems.has(item.id);
    const feedback = feedbackGiven[item.id];

    return (
      <Card
        key={item.id}
        className="hover:shadow-lg transition-all cursor-pointer group"
        onClick={() => onItemClick?.(item)}
      >
        <CardHeader className="pb-3">
          <div className="flex items-start justify-between">
            <div className="flex-1">
              <div className="flex items-center gap-2 mb-2">
                <Badge variant="secondary" className="text-xs">
                  <Sparkles className="h-3 w-3 mr-1" />
                  AI Recommended
                </Badge>
                <Badge className={cn('text-xs', item.score >= 80 ? 'bg-green-100 text-green-800' : 'bg-yellow-100 text-yellow-800')}>
                  {item.score}% Match
                </Badge>
              </div>
              
              <h4 className="font-semibold mb-1">
                {isJob ? data.title : `${data.first_name} ${data.last_name}`}
              </h4>
              
              <div className="text-sm text-muted-foreground">
                {isJob ? data.company_name : data.candidate_profile?.title}
              </div>
            </div>

            <Button
              variant="ghost"
              size="sm"
              className="h-8 w-8 p-0"
              onClick={(e) => {
                e.stopPropagation();
                handleSave(item);
              }}
            >
              <Heart className={cn('h-4 w-4', isSaved && 'fill-current text-red-500')} />
            </Button>
          </div>
        </CardHeader>

        <CardContent className="space-y-2">
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            {data.location && <span>{data.location}</span>}
            {data.is_remote && <Badge variant="outline" className="text-xs">Remote</Badge>}
          </div>

          {data.skills && data.skills.length > 0 && (
            <div className="flex flex-wrap gap-1">
              {data.skills.slice(0, 3).map((skill: string, index: number) => (
                <Badge key={index} variant="outline" className="text-xs">
                  {skill}
                </Badge>
              ))}
              {data.skills.length > 3 && (
                <Badge variant="outline" className="text-xs">
                  +{data.skills.length - 3}
                </Badge>
              )}
            </div>
          )}

          {showFeedback && (
            <div className="flex items-center gap-2 pt-2 border-t">
              <Button
                variant={feedback === 'positive' ? 'default' : 'outline'}
                size="sm"
                className="flex-1"
                onClick={(e) => {
                  e.stopPropagation();
                  handleFeedback(item.id, 'positive');
                }}
              >
                <ThumbsUp className="h-4 w-4 mr-1" />
                Helpful
              </Button>
              <Button
                variant={feedback === 'negative' ? 'destructive' : 'outline'}
                size="sm"
                className="flex-1"
                onClick={(e) => {
                  e.stopPropagation();
                  handleFeedback(item.id, 'negative');
                }}
              >
                <ThumbsDown className="h-4 w-4 mr-1" />
                Not Relevant
              </Button>
            </div>
          )}
        </CardContent>
      </Card>
    );
  };

  const candidateTabs = [
    { id: 'recommended', label: 'Recommended Jobs', icon: Sparkles, items: recommendedItems },
    { id: 'trending', label: 'Trending Jobs', icon: TrendingUp, items: trendingItems },
    { id: 'recent', label: 'Recently Viewed', icon: Clock, items: recentlyViewed },
  ];

  const recruiterTabs = [
    { id: 'recommended', label: 'Recommended Candidates', icon: Sparkles, items: recommendedItems },
    { id: 'trending', label: 'Trending Candidates', icon: TrendingUp, items: trendingItems },
    { id: 'recent', label: 'Recently Active', icon: Clock, items: recentlyViewed },
  ];

  const tabs = userType === 'candidate' ? candidateTabs : recruiterTabs;

  return (
    <div className={cn('space-y-6', className)}>
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold flex items-center gap-2">
            <Sparkles className="h-6 w-6 text-purple-500" />
            AI Recommendations
          </h2>
          <p className="text-muted-foreground mt-1">
            Personalized {userType === 'candidate' ? 'job' : 'candidate'} recommendations powered by AI
          </p>
        </div>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
        <TabsList className="grid w-full grid-cols-3">
          {tabs.map((tab) => (
            <TabsTrigger key={tab.id} value={tab.id} className="flex items-center gap-2">
              <tab.icon className="h-4 w-4" />
              {tab.label}
              {tab.items.length > 0 && (
                <Badge variant="secondary" className="ml-1">
                  {tab.items.length}
                </Badge>
              )}
            </TabsTrigger>
          ))}
        </TabsList>

        {tabs.map((tab) => (
          <TabsContent key={tab.id} value={tab.id} className="mt-6">
            {tab.items.length === 0 ? (
              <Card>
                <CardContent className="flex flex-col items-center justify-center py-12">
                  <Sparkles className="h-12 w-12 text-muted-foreground mb-4" />
                  <h3 className="text-lg font-semibold mb-2">No recommendations yet</h3>
                  <p className="text-muted-foreground text-center max-w-sm">
                    {userType === 'candidate'
                      ? 'Complete your profile and add more skills to get personalized job recommendations.'
                      : 'Post more jobs and review candidates to get better recommendations.'}
                  </p>
                </CardContent>
              </Card>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {tab.items.map((item) => renderRecommendationCard(item))}
              </div>
            )}
          </TabsContent>
        ))}

        {similarItems.length > 0 && (
          <TabsContent value="similar" className="mt-6">
            <div className="mb-4">
              <h3 className="text-lg font-semibold">Similar {userType === 'candidate' ? 'Jobs' : 'Candidates'}</h3>
              <p className="text-sm text-muted-foreground">
                Based on your recent activity
              </p>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {similarItems.map((item) => renderRecommendationCard(item, false))}
            </div>
          </TabsContent>
        )}
      </Tabs>

      {/* Recommendation Insights */}
      <Card className="bg-gradient-to-br from-purple-50 to-blue-50 border-purple-200">
        <CardHeader>
          <CardTitle className="text-lg flex items-center gap-2">
            <Sparkles className="h-5 w-5 text-purple-500" />
            How Recommendations Work
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-2 text-sm">
          <p className="flex items-start gap-2">
            <span className="text-purple-500 mt-0.5">•</span>
            <span><strong>Profile Analysis:</strong> We analyze your profile, skills, and preferences</span>
          </p>
          <p className="flex items-start gap-2">
            <span className="text-purple-500 mt-0.5">•</span>
            <span><strong>Semantic Matching:</strong> AI understands context and meaning beyond keywords</span>
          </p>
          <p className="flex items-start gap-2">
            <span className="text-purple-500 mt-0.5">•</span>
            <span><strong>Behavioral Learning:</strong> Recommendations improve based on your feedback</span>
          </p>
          <p className="flex items-start gap-2">
            <span className="text-purple-500 mt-0.5">•</span>
            <span><strong>Real-time Updates:</strong> Recommendations refresh as you interact</span>
          </p>
        </CardContent>
      </Card>
    </div>
  );
};
