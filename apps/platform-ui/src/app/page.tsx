import { Header } from "@/components/shell";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import Link from "next/link";

export default function DashboardPage() {
  const quickLinks = [
    {
      title: "Stack Health",
      description: "Monitor all platform services",
      href: "/health",
      icon: "🏥",
      status: "Live",
    },
    {
      title: "Supabase",
      description: "Database, Auth, Storage",
      href: "/supabase",
      icon: "⚡",
      status: "Connected",
    },
    {
      title: "Scout Analytics",
      description: "Retail transaction insights",
      href: "/scout",
      icon: "🔍",
      status: "Active",
    },
    {
      title: "CES Campaigns",
      description: "Creative effectiveness scores",
      href: "/ces",
      icon: "🎨",
      status: "Active",
    },
    {
      title: "Figma Integration",
      description: "Design system sync",
      href: "/figma",
      icon: "🎯",
      status: "Synced",
    },
    {
      title: "Odoo Mirror",
      description: "ERP data synchronization",
      href: "/odoo",
      icon: "🏢",
      status: "Synced",
    },
  ];

  return (
    <div>
      <Header
        title="Dashboard"
        description="Welcome to the IPAI Platform Control Room"
      />

      <div className="p-6 space-y-6">
        {/* Quick Stats */}
        <div className="grid gap-4 md:grid-cols-4">
          <Card>
            <CardHeader className="pb-2">
              <CardDescription>Active Agents</CardDescription>
              <CardTitle className="text-3xl">5</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-xs text-muted-foreground">
                Bolt, FeedMe, Ask Ces, Scout, Figma
              </p>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardDescription>MCP Tools</CardDescription>
              <CardTitle className="text-3xl">24</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-xs text-muted-foreground">
                Across 8 namespaces
              </p>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardDescription>Services</CardDescription>
              <CardTitle className="text-3xl">4</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-xs text-muted-foreground">
                Supabase, n8n, Figma, Odoo
              </p>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardDescription>Status</CardDescription>
              <CardTitle className="text-3xl text-green-500">Healthy</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-xs text-muted-foreground">
                All systems operational
              </p>
            </CardContent>
          </Card>
        </div>

        {/* Quick Links */}
        <div>
          <h2 className="text-lg font-semibold mb-4">Quick Access</h2>
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {quickLinks.map((link) => (
              <Link key={link.href} href={link.href}>
                <Card className="hover:border-primary transition-colors cursor-pointer">
                  <CardHeader>
                    <div className="flex items-center justify-between">
                      <span className="text-2xl">{link.icon}</span>
                      <span className="text-xs text-muted-foreground bg-muted px-2 py-1 rounded">
                        {link.status}
                      </span>
                    </div>
                    <CardTitle className="text-base">{link.title}</CardTitle>
                    <CardDescription>{link.description}</CardDescription>
                  </CardHeader>
                </Card>
              </Link>
            ))}
          </div>
        </div>

        {/* Agent Overview */}
        <div>
          <h2 className="text-lg font-semibold mb-4">Available Agents</h2>
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-5">
            {[
              { name: "Bolt", focus: "Backend/Infra", tools: "supabase.*, n8n.*, odoo.*, ops.*" },
              { name: "FeedMe", focus: "Data Pipelines", tools: "supabase.*, n8n.*" },
              { name: "Ask Ces", focus: "Creative Analysis", tools: "ces.*, scout.*, supabase.*" },
              { name: "Scout", focus: "Retail Analytics", tools: "scout.*, supabase.*" },
              { name: "Figma Agent", focus: "Design System", tools: "figma.*, ces.*, github.*" },
            ].map((agent) => (
              <Card key={agent.name}>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm">{agent.name}</CardTitle>
                  <CardDescription className="text-xs">{agent.focus}</CardDescription>
                </CardHeader>
                <CardContent>
                  <p className="text-xs text-muted-foreground font-mono">
                    {agent.tools}
                  </p>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
