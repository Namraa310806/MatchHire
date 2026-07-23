import { CompanyProfileForm } from '../components/CompanyProfileForm';

export function CompanyProfilePage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Company Profile</h1>
        <p className="text-muted-foreground">
          Manage your company information and hiring preferences
        </p>
      </div>

      <CompanyProfileForm />
    </div>
  );
}
