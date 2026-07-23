import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';

export default function AdminDashboard() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Admin Dashboard</h1>
        <p className="text-slate-400 mt-2">Platform administration and monitoring</p>
      </div>

      <div className="grid gap-6 md:grid-cols-4">
        <Card className="border-slate-800 bg-slate-900/50">
          <CardHeader>
            <CardTitle>Total Users</CardTitle>
            <CardDescription>Registered users</CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-4xl font-bold text-emerald-400">0</p>
          </CardContent>
        </Card>

        <Card className="border-slate-800 bg-slate-900/50">
          <CardHeader>
            <CardTitle>Total Jobs</CardTitle>
            <CardDescription>Active job listings</CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-4xl font-bold text-emerald-400">0</p>
          </CardContent>
        </Card>

        <Card className="border-slate-800 bg-slate-900/50">
          <CardHeader>
            <CardTitle>Applications</CardTitle>
            <CardDescription>Total applications</CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-4xl font-bold text-emerald-400">0</p>
          </CardContent>
        </Card>

        <Card className="border-slate-800 bg-slate-900/50">
          <CardHeader>
            <CardTitle>Companies</CardTitle>
            <CardDescription>Registered companies</CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-4xl font-bold text-emerald-400">0</p>
          </CardContent>
        </Card>
      </div>

      <Card className="border-slate-800 bg-slate-900/50">
        <CardHeader>
          <CardTitle>Admin Features</CardTitle>
          <CardDescription>Coming soon</CardDescription>
        </CardHeader>
        <CardContent className="text-slate-300">
          <ul className="space-y-2">
            <li>• User management</li>
            <li>• Job moderation</li>
            <li>• Platform analytics</li>
            <li>• System health monitoring</li>
            <li>• Feature flags</li>
            <li>• Provider configuration</li>
          </ul>
        </CardContent>
      </Card>
    </div>
  );
}
