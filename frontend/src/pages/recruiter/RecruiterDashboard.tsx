import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';

export default function RecruiterDashboard() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Recruiter Dashboard</h1>
        <p className="text-slate-400 mt-2">Manage your jobs and find the best candidates</p>
      </div>

      <div className="grid gap-6 md:grid-cols-3">
        <Card className="border-slate-800 bg-slate-900/50">
          <CardHeader>
            <CardTitle>Active Jobs</CardTitle>
            <CardDescription>Your posted job listings</CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-4xl font-bold text-emerald-400">0</p>
          </CardContent>
        </Card>

        <Card className="border-slate-800 bg-slate-900/50">
          <CardHeader>
            <CardTitle>Total Applications</CardTitle>
            <CardDescription>Applications to your jobs</CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-4xl font-bold text-emerald-400">0</p>
          </CardContent>
        </Card>

        <Card className="border-slate-800 bg-slate-900/50">
          <CardHeader>
            <CardTitle>Recommended Candidates</CardTitle>
            <CardDescription>AI-powered candidate matches</CardDescription>
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
            <li>• Job posting and management</li>
            <li>• Candidate search and filtering</li>
            <li>• Application management</li>
            <li>• Interview scheduling</li>
            <li>• Analytics and insights</li>
            <li>• Company profile management</li>
          </ul>
        </CardContent>
      </Card>
    </div>
  );
}
