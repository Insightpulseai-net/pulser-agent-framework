/**
 * Configuration management for IPAI MCP Server
 * Reads from environment variables with sensible defaults
 */

export interface IpaiConfig {
  // Supabase
  supabase: {
    url: string;
    anonKey: string;
    serviceRoleKey: string;
    projectRef: string;
  };

  // Odoo
  odoo: {
    url: string;
    db: string;
    username: string;
    password: string;
  };

  // n8n
  n8n: {
    baseUrl: string;
    apiKey: string;
  };

  // Figma
  figma: {
    accessToken: string;
    webhookSecret?: string;
  };

  // GitHub
  github: {
    token: string;
    defaultOwner?: string;
  };
}

function getEnvOrThrow(key: string): string {
  const value = process.env[key];
  if (!value) {
    throw new Error(`Missing required environment variable: ${key}`);
  }
  return value;
}

function getEnvOrDefault(key: string, defaultValue: string): string {
  return process.env[key] || defaultValue;
}

export function loadConfig(): IpaiConfig {
  return {
    supabase: {
      url: getEnvOrDefault('SUPABASE_URL', 'https://spdtwktxdalcfigzeqrz.supabase.co'),
      anonKey: getEnvOrThrow('SUPABASE_ANON_KEY'),
      serviceRoleKey: getEnvOrThrow('SUPABASE_SERVICE_ROLE_KEY'),
      projectRef: getEnvOrDefault('SUPABASE_PROJECT_REF', 'spdtwktxdalcfigzeqrz'),
    },
    odoo: {
      url: getEnvOrDefault('ODOO_URL', 'https://odoo.insightpulseai.net'),
      db: getEnvOrDefault('ODOO_DB', 'production'),
      username: getEnvOrDefault('ODOO_USERNAME', 'admin'),
      password: process.env.ODOO_PASSWORD || '',
    },
    n8n: {
      baseUrl: getEnvOrDefault('N8N_BASE_URL', 'https://n8n.insightpulseai.net'),
      apiKey: process.env.N8N_API_KEY || '',
    },
    figma: {
      accessToken: process.env.FIGMA_ACCESS_TOKEN || '',
      webhookSecret: process.env.FIGMA_WEBHOOK_SECRET,
    },
    github: {
      token: process.env.GITHUB_TOKEN || '',
      defaultOwner: process.env.GITHUB_DEFAULT_OWNER || 'Insightpulseai-net',
    },
  };
}

// Lazy-loaded singleton config
let _config: IpaiConfig | null = null;

export function getConfig(): IpaiConfig {
  if (!_config) {
    _config = loadConfig();
  }
  return _config;
}
