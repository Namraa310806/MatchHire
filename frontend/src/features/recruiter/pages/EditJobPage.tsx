import { JobForm } from '../components/JobForm';

export function EditJobPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Edit Job</h1>
        <p className="text-muted-foreground">
          Update job details and settings
        </p>
      </div>

      <JobForm mode="edit" />
    </div>
  );
}
