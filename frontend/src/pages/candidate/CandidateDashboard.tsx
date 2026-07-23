import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';

export default function CandidateDashboard() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Candidate Dashboard</h1>
        <p className="text-slate-400 mt-2">Manage your job search and applications</p>
      </div>

      <div className="grid gap-6 md:grid-cols-3">
        <Card className="border-slate-800 bg-slate-900/50">
          <CardHeader>
            <CardTitle>My Applications</CardTitle>
            <CardDescription>Track your job applications</CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-4xl font-bold text-emerald-400">0</p>
          </CardContent>
        </Card>

        <Card className="border-slate-800 bg-slate-900/50">
          <CardHeader>
            <CardTitle>Recommended Jobs</CardTitle>
            <CardDescription>AI-powered job matches</CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-4xl font-bold text-emerald-400">0</p>
          </CardContent>
        </Card>

        <Card className="border-slate-800 bg-slate-900/50">
          <CardHeader>
            <CardTitle>Interviews</CardTitle>
            <CardDescription>Scheduled interviews</CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-4xl font-bold text-emerald-400">0</p>
          </CardContent>
        </Card>
      </div>

      <Card className="border-slate-800 bg-slate-900/50">
        <CardHeader>
          <CardTitle>Dashboard Features</CardTitle>
          <CardDescription>Coming soon</CardDescription>
        </CardHeader>
        <CardContent className="text-slate-300">
          <ul className="space-y-2">
            <li>• Profile management</li>
            <li>• Resume upload and parsing</li>
            <li>• Job search with advanced filters</li>
            <li>• Application tracking</li>
            <li>• Interview scheduling</li>
            <li>• Analytics and insights</li>
          </ul>
        </CardContent>
      </Card>
    </div>
  );
}
