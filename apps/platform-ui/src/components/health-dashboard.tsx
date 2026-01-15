"use client";

import * as React from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { mcpTools } from "@/lib/pulser-client";

interface HealthCheck {
  name: string;
  passed: boolean;
  message?: string;
  duration_ms?: number;
}

interface ServiceHealth {
  status: "healthy" | "degraded" | "broken";
  checks: HealthCheck[];
  timestamp: string;
}

interface StackHealthResult {
  overall_status: "healthy" | "degraded" | "broken";
  services: Record<string, ServiceHealth>;
  timestamp: string;
}

export function HealthDashboard() {
  const [loading, setLoading] = React.useState(false);
  const [health, setHealth] = React.useState<StackHealthResult | null>(null);
  const [error, setError] = React.useState<string | null>(null);

  const checkHealth = async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await mcpTools.ops.stackHealth();
      if (response.success && response.result) {
        setHealth(response.result as StackHealthResult);
      } else {
        setError(response.error || "Health check failed");
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "Unknown error");
    } finally {
      setLoading(false);
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "healthy":
        return <Badge variant="success">Healthy</Badge>;
      case "degraded":
        return <Badge variant="warning">Degraded</Badge>;
      case "broken":
        return <Badge variant="destructive">Broken</Badge>;
      default:
        return <Badge variant="outline">Unknown</Badge>;
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold">Stack Health Overview</h2>
          <p className="text-sm text-muted-foreground">
            Monitor the health of all platform services
          </p>
        </div>
        <Button onClick={checkHealth} disabled={loading}>
          {loading ? "Checking..." : "Run Health Check"}
        </Button>
      </div>

      {error && (
        <Card className="border-destructive">
          <CardContent className="pt-6">
            <p className="text-destructive">{error}</p>
          </CardContent>
        </Card>
      )}

      {health && (
        <>
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center justify-between">
                <span>Overall Status</span>
                {getStatusBadge(health.overall_status)}
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground">
                Last checked: {new Date(health.timestamp).toLocaleString()}
              </p>
            </CardContent>
          </Card>

          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            {Object.entries(health.services).map(([service, data]) => (
              <Card key={service}>
                <CardHeader className="pb-2">
                  <CardTitle className="flex items-center justify-between text-base">
                    <span className="capitalize">{service}</span>
                    {getStatusBadge(data.status)}
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <ul className="space-y-1 text-sm">
                    {data.checks.slice(0, 4).map((check, idx) => (
                      <li key={idx} className="flex items-center gap-2">
                        <span>{check.passed ? "✅" : "❌"}</span>
                        <span className="truncate">{check.name}</span>
                      </li>
                    ))}
                    {data.checks.length > 4 && (
                      <li className="text-muted-foreground">
                        +{data.checks.length - 4} more checks
                      </li>
                    )}
                  </ul>
                </CardContent>
              </Card>
            ))}
          </div>
        </>
      )}

      {!health && !error && (
        <Card>
          <CardContent className="py-8 text-center">
            <p className="text-muted-foreground">
              Click "Run Health Check" to check the status of all services
            </p>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
