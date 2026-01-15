import { Header } from "@/components/shell";
import { HealthDashboard } from "@/components/health-dashboard";

export default function HealthPage() {
  return (
    <div>
      <Header
        title="Stack Health"
        description="Monitor the health of all platform services"
      />

      <div className="p-6">
        <HealthDashboard />
      </div>
    </div>
  );
}
