import { Link } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';

export default function HomePage() {
  return (
    <div className="flex flex-col items-center justify-center space-y-12 py-16">
      <div className="max-w-3xl text-center space-y-6">
        <p className="text-sm uppercase tracking-[0.35em] text-emerald-400">MatchHire</p>
        <h1 className="text-5xl font-semibold leading-tight md:text-7xl">
          Verified job aggregation and intelligent matching.
        </h1>
        <p className="max-w-2xl text-lg leading-8 text-slate-300">
          Jobs are sourced only from official company career portals, normalized through automation, 
          and matched with candidate profiles using ranking and semantic scoring.
        </p>
        <div className="flex gap-4 justify-center">
          <Link to="/register">
            <Button size="lg">Get Started</Button>
          </Link>
          <Link to="/login">
            <Button size="lg" variant="outline">Sign In</Button>
          </Link>
        </div>
      </div>

      <div className="grid gap-6 md:grid-cols-3 max-w-5xl w-full">
        <Card className="border-slate-800 bg-slate-900/50">
          <CardHeader>
            <CardTitle>For Candidates</CardTitle>
            <CardDescription>Find your perfect job match</CardDescription>
          </CardHeader>
          <CardContent className="text-slate-300">
            <ul className="space-y-2 text-sm">
              <li>• AI-powered job recommendations</li>
              <li>• Resume parsing and matching</li>
              <li>• Application tracking</li>
              <li>• Interview scheduling</li>
            </ul>
          </CardContent>
        </Card>

        <Card className="border-slate-800 bg-slate-900/50">
          <CardHeader>
            <CardTitle>For Recruiters</CardTitle>
            <CardDescription>Hire the best talent faster</CardDescription>
          </CardHeader>
          <CardContent className="text-slate-300">
            <ul className="space-y-2 text-sm">
              <li>• Intelligent candidate matching</li>
              <li>• Advanced search and filters</li>
              <li>• Application management</li>
              <li>• Analytics and insights</li>
            </ul>
          </CardContent>
        </Card>

        <Card className="border-slate-800 bg-slate-900/50">
          <CardHeader>
            <CardTitle>Verified Jobs</CardTitle>
            <CardDescription>Only from official sources</CardDescription>
          </CardHeader>
          <CardContent className="text-slate-300">
            <ul className="space-y-2 text-sm">
              <li>• Direct from company portals</li>
              <li>• Real-time job updates</li>
              <li>• No expired listings</li>
              <li>• Trusted employers</li>
            </ul>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
