import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { Skeleton } from '@/components/ui/skeleton';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import React from 'react';
import { useMatchingCandidates, useMyJobs } from '../hooks';
import { Link } from 'react-router-dom';
import { Star, MapPin, Briefcase, Sparkles, TrendingUp, Clock, ArrowRight } from 'lucide-react';

export function RecommendedCandidates() {
  const [selectedJob, setSelectedJob] = React.useState<string>('');
  const { data: myJobs, isLoading: isLoadingJobs } = useMyJobs();
  const { data: recommendations, isLoading: isLoadingRecs } = useMatchingCandidates(selectedJob);

  if (isLoadingJobs) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-12 w-64" />
        <Skeleton className="h-48 w-full" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header with Job Selection */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold flex items-center gap-2">
            <Sparkles className="h-6 w-6 text-purple-500" />
            Recommended Candidates
          </h2>
          <p className="text-muted-foreground">
            AI-powered recommendations based on your job requirements
          </p>
        </div>
        <div className="flex items-center gap-4">
          <Select value={selectedJob} onValueChange={setSelectedJob}>
            <SelectTrigger className="w-[300px]">
              <SelectValue placeholder="Select a job to see recommendations" />
            </SelectTrigger>
            <SelectContent>
              {myJobs?.map((job) => (
                <SelectItem key={job.id} value={job.id}>
                  {job.title}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          {selectedJob && (
            <Button variant="outline">
              <TrendingUp className="h-4 w-4 mr-2" />
              Refresh Matches
            </Button>
          )}
        </div>
      </div>

      {!selectedJob ? (
        <Card>
          <CardContent className="p-12 text-center">
            <Sparkles className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
            <h3 className="text-lg font-semibold mb-2">Select a Job</h3>
            <p className="text-muted-foreground">
              Choose a job posting to see AI-powered candidate recommendations
            </p>
          </CardContent>
        </Card>
      ) : isLoadingRecs ? (
        <div className="space-y-4">
          {[...Array(3)].map((_, i) => (
            <Card key={i}>
              <CardContent className="p-6">
                <Skeleton className="h-12 w-12 rounded-full mb-4" />
                <Skeleton className="h-6 w-48 mb-2" />
                <Skeleton className="h-4 w-32" />
              </CardContent>
            </Card>
          ))}
        </div>
      ) : !recommendations || recommendations.length === 0 ? (
        <Card>
          <CardContent className="p-12 text-center">
            <p className="text-muted-foreground">No recommendations available for this job yet</p>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-4">
          {recommendations.map((rec) => (
            <Card key={rec.id} className="hover:shadow-md transition-shadow">
              <CardContent className="p-6">
                <div className="flex gap-4">
                  <Avatar className="h-16 w-16">
                    <AvatarImage src="/placeholder-avatar.png" />
                    <AvatarFallback className="text-xl">
                      {rec.candidate_name
                        ? rec.candidate_name.split(' ').map((n) => n[0]).join('')
                        : 'C'}
                    </AvatarFallback>
                  </Avatar>

                  <div className="flex-1">
                    <div className="flex items-start justify-between mb-3">
                      <div>
                        <h3 className="font-semibold text-lg">
                          {rec.candidate_name || rec.candidate_email || 'Unknown'}
                        </h3>
                        <p className="text-sm text-muted-foreground">
                          {rec.candidate_profile?.title || 'No title'}
                        </p>
                      </div>
                      <div className="flex items-center gap-2">
                        <Badge className="bg-purple-500/10 text-purple-500 hover:bg-purple-500/20 flex items-center gap-1">
                          <Star className="h-3 w-3 fill-purple-500 text-purple-500" />
                          {Math.round(rec.match_score * 100)}% Match
                        </Badge>
                      </div>
                    </div>

                    {/* AI Explanation */}
                    {rec.explanation && (
                      <div className="bg-purple-50 dark:bg-purple-950/20 rounded-lg p-4 mb-4">
                        <div className="flex items-start gap-2">
                          <Sparkles className="h-4 w-4 text-purple-500 mt-0.5 flex-shrink-0" />
                          <div>
                            <p className="text-sm font-medium text-purple-900 dark:text-purple-100 mb-1">
                              AI Recommendation
                            </p>
                            <p className="text-sm text-purple-800 dark:text-purple-200">
                              {rec.explanation}
                            </p>
                          </div>
                        </div>
                      </div>
                    )}

                    {/* Match Signals */}
                    {rec.signals && Object.keys(rec.signals).length > 0 && (
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-4">
                        {Object.entries(rec.signals)
                          .slice(0, 4)
                          .map(([signal, score]) => (
                            <div key={signal} className="text-center p-2 bg-muted rounded">
                              <p className="text-xs text-muted-foreground capitalize">
                                {signal.replace('_', ' ')}
                              </p>
                              <p className="text-sm font-semibold">
                                {Math.round((score as number) * 100)}%
                              </p>
                            </div>
                          ))}
                      </div>
                    )}

                    <div className="flex flex-wrap gap-4 text-sm text-muted-foreground mb-3">
                      {rec.candidate_profile?.location && (
                        <div className="flex items-center gap-1">
                          <MapPin className="h-4 w-4" />
                          {rec.candidate_profile.location}
                        </div>
                      )}
                      {rec.candidate_profile?.experience_years && (
                        <div className="flex items-center gap-1">
                          <Briefcase className="h-4 w-4" />
                          {rec.candidate_profile.experience_years} years
                        </div>
                      )}
                      <div className="flex items-center gap-1">
                        <Clock className="h-4 w-4" />
                        Recently active
                      </div>
                    </div>

                    {rec.candidate_profile?.skills && rec.candidate_profile.skills.length > 0 && (
                      <div className="flex flex-wrap gap-2 mb-4">
                        {rec.candidate_profile.skills.slice(0, 6).map((skill) => (
                          <Badge key={skill} variant="secondary">
                            {skill}
                          </Badge>
                        ))}
                        {rec.candidate_profile.skills.length > 6 && (
                          <Badge variant="secondary">
                            +{rec.candidate_profile.skills.length - 6} more
                          </Badge>
                        )}
                      </div>
                    )}

                    <div className="flex items-center justify-between">
                      <Link to={`/recruiter/candidates/${rec.id}`}>
                        <Button variant="outline" size="sm">
                          View Full Profile
                          <ArrowRight className="h-4 w-4 ml-2" />
                        </Button>
                      </Link>
                      <div className="flex gap-2">
                        <Button variant="outline" size="sm">
                          Save
                        </Button>
                        <Button size="sm">Contact</Button>
                      </div>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
