import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { Button } from '@/components/ui/button';
import { Link } from 'react-router-dom';
import { AlertCircle } from 'lucide-react';

interface ProfileCompletionCardProps {
  completion: number;
  missingFields?: string[];
}

export function ProfileCompletionCard({ completion, missingFields = [] }: ProfileCompletionCardProps) {
  const isComplete = completion === 100;

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          Profile Completion
          {!isComplete && <AlertCircle className="h-4 w-4 text-yellow-500" />}
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="space-y-2">
          <div className="flex items-center justify-between text-sm">
            <span className="font-medium">{completion}% Complete</span>
            {!isComplete && (
              <Link to="/candidate/profile">
                <Button variant="link" className="p-0 h-auto text-sm">
                  Complete Now
                </Button>
              </Link>
            )}
          </div>
          <Progress value={completion} className="h-2" />
        </div>

        {!isComplete && missingFields.length > 0 && (
          <div className="space-y-2">
            <p className="text-sm font-medium">Missing information:</p>
            <ul className="space-y-1">
              {missingFields.map((field) => (
                <li key={field} className="text-sm text-muted-foreground flex items-center gap-2">
                  <span className="h-1.5 w-1.5 rounded-full bg-yellow-500" />
                  {field}
                </li>
              ))}
            </ul>
          </div>
        )}

        {isComplete && (
          <p className="text-sm text-green-600 dark:text-green-400">
            Your profile is complete! You're ready to apply for jobs.
          </p>
        )}
      </CardContent>
    </Card>
  );
}
