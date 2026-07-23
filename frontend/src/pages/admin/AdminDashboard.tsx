import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import SystemDashboard from '@/features/admin/pages/SystemDashboard';
import UserManagement from '@/features/admin/pages/UserManagement';
import JobAdministration from '@/features/admin/pages/JobAdministration';
import ApplicationAdministration from '@/features/admin/pages/ApplicationAdministration';
import ResumeAdministration from '@/features/admin/pages/ResumeAdministration';
import SearchMonitoring from '@/features/admin/pages/SearchMonitoring';
import RecommendationMonitoring from '@/features/admin/pages/RecommendationMonitoring';
import SystemConfiguration from '@/features/admin/pages/SystemConfiguration';
import {
  LayoutDashboard,
  Users,
  Briefcase,
  FileText,
  Database,
  Search,
  Brain,
  Settings,
  RefreshCw,
} from 'lucide-react';

export default function AdminDashboard() {
  const [activeTab, setActiveTab] = useState('dashboard');

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Admin Console</h1>
          <p className="text-slate-400 mt-2">Platform administration and operations</p>
        </div>
        <Button variant="outline" size="sm">
          <RefreshCw className="h-4 w-4 mr-2" />
          Refresh All
        </Button>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
        <TabsList className="bg-slate-900/50 border border-slate-800">
          <TabsTrigger value="dashboard" className="data-[state=active]:bg-slate-800">
            <LayoutDashboard className="h-4 w-4 mr-2" />
            Dashboard
          </TabsTrigger>
          <TabsTrigger value="users" className="data-[state=active]:bg-slate-800">
            <Users className="h-4 w-4 mr-2" />
            Users
          </TabsTrigger>
          <TabsTrigger value="jobs" className="data-[state=active]:bg-slate-800">
            <Briefcase className="h-4 w-4 mr-2" />
            Jobs
          </TabsTrigger>
          <TabsTrigger value="applications" className="data-[state=active]:bg-slate-800">
            <FileText className="h-4 w-4 mr-2" />
            Applications
          </TabsTrigger>
          <TabsTrigger value="resumes" className="data-[state=active]:bg-slate-800">
            <Database className="h-4 w-4 mr-2" />
            Resumes
          </TabsTrigger>
          <TabsTrigger value="search" className="data-[state=active]:bg-slate-800">
            <Search className="h-4 w-4 mr-2" />
            Search
          </TabsTrigger>
          <TabsTrigger value="recommendations" className="data-[state=active]:bg-slate-800">
            <Brain className="h-4 w-4 mr-2" />
            Recommendations
          </TabsTrigger>
          <TabsTrigger value="config" className="data-[state=active]:bg-slate-800">
            <Settings className="h-4 w-4 mr-2" />
            Config
          </TabsTrigger>
        </TabsList>

        <TabsContent value="dashboard">
          <SystemDashboard />
        </TabsContent>

        <TabsContent value="users">
          <UserManagement />
        </TabsContent>

        <TabsContent value="jobs">
          <JobAdministration />
        </TabsContent>

        <TabsContent value="applications">
          <ApplicationAdministration />
        </TabsContent>

        <TabsContent value="resumes">
          <ResumeAdministration />
        </TabsContent>

        <TabsContent value="search">
          <SearchMonitoring />
        </TabsContent>

        <TabsContent value="recommendations">
          <RecommendationMonitoring />
        </TabsContent>

        <TabsContent value="config">
          <SystemConfiguration />
        </TabsContent>
      </Tabs>
    </div>
  );
}
