import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { Skeleton } from '@/components/ui/skeleton';
import { useCandidateSearch } from '../hooks';
import { Link } from 'react-router-dom';
import { MapPin, Briefcase, GraduationCap, Star, Clock } from 'lucide-react';

interface CandidateSearchResultsProps {
  filters: any;
}

export function CandidateSearchResults({ filters }: CandidateSearchResultsProps) {
  const { data: searchResults, isLoading } = useCandidateSearch(filters);

  if (isLoading) {
    return (
      <div className="space-y-4">
        {[...Array(5)].map((_, i) => (
          <Card key={i}>
            <CardContent className="p-6">
              <div className="flex gap-4">
                <Skeleton className="h-12 w-12 rounded-full" />
                <div className="flex-1 space-y-2">
                  <Skeleton className="h-5 w-48" />
                  <Skeleton className="h-4 w-32" />
                  <Skeleton className="h-4 w-24" />
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    );
  }

  if (!searchResults || searchResults.results.length === 0) {
    return (
      <Card>
        <CardContent className="p-12 text-center">
          <p className="text-muted-foreground">No candidates found matching your criteria</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-4">
      {searchResults.results.map((candidate) => (
        <Card key={candidate.id}>
          <CardContent className="p-6">
            <div className="flex gap-4">
              <Avatar className="h-12 w-12">
                <AvatarImage src="/placeholder-avatar.png" />
                <AvatarFallback>
                  {candidate.candidate_profile?.title
                    ?.split(' ')
                    .map((n) => n[0])
                    .join('') || 'C'}
                </AvatarFallback>
              </Avatar>

              <div className="flex-1">
                <div className="flex items-start justify-between mb-2">
                  <div>
                    <h3 className="font-semibold text-lg">
                      {candidate.first_name && candidate.last_name
                        ? `${candidate.first_name} ${candidate.last_name}`
                        : candidate.email}
                    </h3>
                    <p className="text-sm text-muted-foreground">
                      {candidate.candidate_profile?.title || 'No title'}
                    </p>
                  </div>
                  {candidate.match_score && (
                    <Badge variant="outline" className="flex items-center gap-1">
                      <Star className="h-3 w-3 fill-yellow-500 text-yellow-500" />
                      {Math.round(candidate.match_score * 100)}% match
                    </Badge>
                  )}
                </div>

                <div className="flex flex-wrap gap-4 text-sm text-muted-foreground mb-3">
                  {candidate.candidate_profile?.location && (
                    <div className="flex items-center gap-1">
                      <MapPin className="h-4 w-4" />
                      {candidate.candidate_profile.location}
                    </div>
                  )}
                  {candidate.candidate_profile?.experience_years && (
                    <div className="flex items-center gap-1">
                      <Briefcase className="h-4 w-4" />
                      {candidate.candidate_profile.experience_years} years experience
                    </div>
                  )}
                  {candidate.candidate_profile?.education &&
                    candidate.candidate_profile.education.length > 0 && (
                      <div className="flex items-center gap-1">
                        <GraduationCap className="h-4 w-4" />
                        {candidate.candidate_profile.education[0].degree}
                      </div>
                    )}
                </div>

                {candidate.candidate_profile?.skills &&
                  candidate.candidate_profile.skills.length > 0 && (
                    <div className="flex flex-wrap gap-2 mb-3">
                      {candidate.candidate_profile.skills.slice(0, 5).map((skill) => (
                        <Badge key={skill} variant="secondary">
                          {skill}
                        </Badge>
                      ))}
                      {candidate.candidate_profile.skills.length > 5 && (
                        <Badge variant="secondary">
                          +{candidate.candidate_profile.skills.length - 5} more
                        </Badge>
                      )}
                    </div>
                  )}

                {candidate.match_signals && (
                  <div className="text-xs text-muted-foreground mb-3">
                    <strong>Match signals:</strong>{' '}
                    {Object.entries(candidate.match_signals)
                      .slice(0, 3)
                      .map(([signal, score]) => `${signal} (${Math.round(score * 100)}%)`)
                      .join(', ')}
                  </div>
                )}

                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2 text-xs text-muted-foreground">
                    <Clock className="h-3 w-3" />
                    <span>Recently active</span>
                  </div>
                  <div className="flex gap-2">
                    <Link to={`/recruiter/candidates/${candidate.id}`}>
                      <Button variant="outline" size="sm">
                        View Profile
                      </Button>
                    </Link>
                    <Button size="sm">Contact</Button>
                  </div>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      ))}

      {/* Pagination */}
      {searchResults.count > searchResults.results.length && (
        <div className="flex justify-center gap-2">
          <Button variant="outline" disabled>
            Previous
          </Button>
          <Button variant="outline">
            Next
          </Button>
        </div>
      )}
    </div>
  );
}
