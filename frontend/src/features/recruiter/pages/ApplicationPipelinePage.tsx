import { ApplicationPipeline } from '../components/ApplicationPipeline';

export function ApplicationPipelinePage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Application Pipeline</h1>
        <p className="text-muted-foreground">
          Manage and track candidate applications through the hiring process
        </p>
      </div>

      <ApplicationPipeline />
    </div>
  );
}
