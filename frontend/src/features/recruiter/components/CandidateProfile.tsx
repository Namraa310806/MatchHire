import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { Skeleton } from '@/components/ui/skeleton';
import { useCandidate } from '../hooks';
import { useParams } from 'react-router-dom';
import { MapPin, Briefcase, GraduationCap, Mail, Phone, Calendar, FileText, Download, Star, Clock, MessageSquare } from 'lucide-react';
import { format } from 'date-fns';

export function CandidateProfile() {
  const { id } = useParams<{ id: string }>();
  const { data: candidate, isLoading } = useCandidate(id || '');

  if (isLoading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-32 w-full" />
        <Skeleton className="h-48 w-full" />
        <Skeleton className="h-48 w-full" />
      </div>
    );
  }

  if (!candidate) {
    return (
      <Card>
        <CardContent className="p-12 text-center">
          <p className="text-muted-foreground">Candidate not found</p>
        </CardContent>
      </Card>
    );
  }

  const profile = candidate.candidate_profile;

  return (
    <div className="space-y-6">
      {/* Header */}
      <Card>
        <CardContent className="p-6">
          <div className="flex gap-6">
            <Avatar className="h-24 w-24">
              <AvatarImage src="/placeholder-avatar.png" />
              <AvatarFallback className="text-2xl">
                {candidate.first_name && candidate.last_name
                  ? `${candidate.first_name[0]}${candidate.last_name[0]}`
                  : 'C'}
              </AvatarFallback>
            </Avatar>

            <div className="flex-1">
              <div className="flex items-start justify-between mb-2">
                <div>
                  <h1 className="text-2xl font-bold">
                    {candidate.first_name} {candidate.last_name}
                  </h1>
                  <p className="text-lg text-muted-foreground">
                    {profile?.title || 'No title specified'}
                  </p>
                </div>
                <div className="flex gap-2">
                  <Button variant="outline" size="sm">
                    <MessageSquare className="h-4 w-4 mr-2" />
                    Message
                  </Button>
                  <Button size="sm">
                    <Star className="h-4 w-4 mr-2" />
                    Save
                  </Button>
                </div>
              </div>

              <div className="flex flex-wrap gap-4 text-sm text-muted-foreground mb-4">
                {profile?.location && (
                  <div className="flex items-center gap-1">
                    <MapPin className="h-4 w-4" />
                    {profile.location}
                  </div>
                )}
                {profile?.experience_years && (
                  <div className="flex items-center gap-1">
                    <Briefcase className="h-4 w-4" />
                    {profile.experience_years} years experience
                  </div>
                )}
                {candidate.email && (
                  <div className="flex items-center gap-1">
                    <Mail className="h-4 w-4" />
                    {candidate.email}
                  </div>
                )}
              </div>

              {profile?.skills && profile.skills.length > 0 && (
                <div className="flex flex-wrap gap-2">
                  {profile.skills.map((skill) => (
                    <Badge key={skill} variant="secondary">
                      {skill}
                    </Badge>
                  ))}
                </div>
              )}
            </div>
          </div>
        </CardContent>
      </Card>

      <div className="grid gap-6 lg:grid-cols-3">
        <div className="lg:col-span-2 space-y-6">
          {/* About */}
          <Card>
            <CardHeader>
              <CardTitle>About</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-muted-foreground">
                {profile?.summary || 'No summary provided.'}
              </p>
            </CardContent>
          </Card>

          {/* Experience */}
          <Card>
            <CardHeader>
              <CardTitle>Experience</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {profile?.experience && profile.experience.length > 0 ? (
                profile.experience.map((exp, index) => (
                  <div key={index} className="border-l-2 border-muted pl-4 pb-4 last:pb-0">
                    <h4 className="font-semibold">{exp.title}</h4>
                    <p className="text-sm text-muted-foreground">{exp.company}</p>
                    <p className="text-xs text-muted-foreground">
                      {exp.start_date && format(new Date(exp.start_date), 'MMM yyyy')}
                      {exp.end_date && ` - ${format(new Date(exp.end_date), 'MMM yyyy')}`}
                    </p>
                    <p className="text-sm mt-2">{exp.description}</p>
                  </div>
                ))
              ) : (
                <p className="text-muted-foreground">No experience listed.</p>
              )}
            </CardContent>
          </Card>

          {/* Education */}
          <Card>
            <CardHeader>
              <CardTitle>Education</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {profile?.education && profile.education.length > 0 ? (
                profile.education.map((edu, index) => (
                  <div key={index} className="flex items-start gap-4">
                    <GraduationCap className="h-5 w-5 text-muted-foreground mt-1" />
                    <div>
                      <h4 className="font-semibold">{edu.degree}</h4>
                      <p className="text-sm text-muted-foreground">{edu.school}</p>
                      <p className="text-xs text-muted-foreground">
                        {edu.start_date && format(new Date(edu.start_date), 'MMM yyyy')}
                        {edu.end_date && ` - ${format(new Date(edu.end_date), 'MMM yyyy')}`}
                      </p>
                    </div>
                  </div>
                ))
              ) : (
                <p className="text-muted-foreground">No education listed.</p>
              )}
            </CardContent>
          </Card>

          {/* Resume */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <FileText className="h-5 w-5" />
                Resume
              </CardTitle>
            </CardHeader>
            <CardContent>
              {candidate.resume_url ? (
                <div className="flex items-center justify-between p-4 border rounded-lg">
                  <div>
                    <p className="font-medium">Resume.pdf</p>
                    <p className="text-sm text-muted-foreground">Latest version</p>
                  </div>
                  <Button variant="outline" size="sm">
                    <Download className="h-4 w-4 mr-2" />
                    Download
                  </Button>
                </div>
              ) : (
                <p className="text-muted-foreground">No resume uploaded.</p>
              )}
            </CardContent>
          </Card>
        </div>

        <div className="space-y-6">
          {/* Contact Information */}
          <Card>
            <CardHeader>
              <CardTitle>Contact Information</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {candidate.email && (
                <div className="flex items-center gap-3">
                  <Mail className="h-4 w-4 text-muted-foreground" />
                  <a href={`mailto:${candidate.email}`} className="text-sm hover:underline">
                    {candidate.email}
                  </a>
                </div>
              )}
              {profile?.phone && (
                <div className="flex items-center gap-3">
                  <Phone className="h-4 w-4 text-muted-foreground" />
                  <a href={`tel:${profile.phone}`} className="text-sm hover:underline">
                    {profile.phone}
                  </a>
                </div>
              )}
              {profile?.linkedin_url && (
                <div className="flex items-center gap-3">
                  <Briefcase className="h-4 w-4 text-muted-foreground" />
                  <a
                    href={profile.linkedin_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-sm hover:underline"
                  >
                    LinkedIn Profile
                  </a>
                </div>
              )}
              {profile?.github_url && (
                <div className="flex items-center gap-3">
                  <FileText className="h-4 w-4 text-muted-foreground" />
                  <a
                    href={profile.github_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-sm hover:underline"
                  >
                    GitHub Profile
                  </a>
                </div>
              )}
              {profile?.portfolio_url && (
                <div className="flex items-center gap-3">
                  <FileText className="h-4 w-4 text-muted-foreground" />
                  <a
                    href={profile.portfolio_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-sm hover:underline"
                  >
                    Portfolio
                  </a>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Availability */}
          <Card>
            <CardHeader>
              <CardTitle>Availability</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="flex items-center gap-3">
                <Calendar className="h-4 w-4 text-muted-foreground" />
                <div>
                  <p className="text-sm font-medium">Available to start</p>
                  <p className="text-sm text-muted-foreground">
                    {profile?.availability || 'Not specified'}
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <Clock className="h-4 w-4 text-muted-foreground" />
                <div>
                  <p className="text-sm font-medium">Last active</p>
                  <p className="text-sm text-muted-foreground">
                    {candidate.last_active
                      ? format(new Date(candidate.last_active), 'MMM d, yyyy')
                      : 'Unknown'}
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Quick Actions */}
          <Card>
            <CardHeader>
              <CardTitle>Quick Actions</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              <Button className="w-full" variant="outline">
                <MessageSquare className="h-4 w-4 mr-2" />
                Send Message
              </Button>
              <Button className="w-full" variant="outline">
                <Briefcase className="h-4 w-4 mr-2" />
                Invite to Apply
              </Button>
              <Button className="w-full" variant="outline">
                <Star className="h-4 w-4 mr-2" />
                Add to Favorites
              </Button>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
