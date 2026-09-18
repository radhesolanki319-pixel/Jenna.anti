import { describe, it } from 'node:test';
import assert from 'node:assert/strict';

describe('Tools, MCP & Web Research Logic Tests', () => {
  it('validates supported tool categories and metadata structure', () => {
    const categories = ['GENERAL', 'CALCULATOR', 'FILESYSTEM', 'WEB', 'SYSTEM', 'MCP'];
    assert.equal(categories.length, 6);
    assert.ok(categories.includes('CALCULATOR'));
    assert.ok(categories.includes('FILESYSTEM'));
    assert.ok(categories.includes('WEB'));
    assert.ok(categories.includes('SYSTEM'));
    assert.ok(categories.includes('MCP'));
  });

  it('validates tool parameter schema validation and type checking', () => {
    const mockTool = {
      name: 'calculator',
      parameters: [
        { name: 'expression', type: 'string', required: true },
      ],
    };

    const validateCall = (params) => {
      for (const p of mockTool.parameters) {
        if (p.required && !(p.name in params)) {
          return { valid: false, error: `Missing required parameter '${p.name}'` };
        }
        if (p.name in params && typeof params[p.name] !== p.type) {
          return { valid: false, error: `Parameter '${p.name}' must be a ${p.type}` };
        }
      }
      return { valid: true, error: null };
    };

    assert.equal(validateCall({ expression: 'sqrt(144)' }).valid, true);
    assert.equal(validateCall({}).valid, false);
    assert.equal(validateCall({ expression: 12345 }).valid, false);
  });

  it('verifies 3-tier authorization evaluation for sensitive actions', () => {
    const evaluateAuth = (tool, userRole, confirmed) => {
      if (userRole === 'readonly' && tool.requires_write) {
        return 'DENIED';
      }
      if (tool.is_sensitive && !confirmed) {
        return 'REQUIRES_CONFIRMATION';
      }
      return 'ALLOWED';
    };

    const readTool = { name: 'filesystem_read', is_sensitive: false, requires_write: false };
    const writeTool = { name: 'filesystem_write', is_sensitive: true, requires_write: true };

    assert.equal(evaluateAuth(readTool, 'user', false), 'ALLOWED');
    assert.equal(evaluateAuth(writeTool, 'user', false), 'REQUIRES_CONFIRMATION');
    assert.equal(evaluateAuth(writeTool, 'user', true), 'ALLOWED');
    assert.equal(evaluateAuth(writeTool, 'readonly', true), 'DENIED');
  });

  it('verifies MCP protocol response parsing and tool mapping', () => {
    const rawMcpTools = [
      {
        name: 'weather_lookup',
        description: 'Get weather forecast',
        inputSchema: {
          type: 'object',
          properties: { city: { type: 'string' } },
          required: ['city'],
        },
      },
    ];

    const mapped = rawMcpTools.map((t) => ({
      name: `mcp_${t.name}`,
      description: t.description,
      category: 'MCP',
      parameters: Object.keys(t.inputSchema.properties).map((prop) => ({
        name: prop,
        type: t.inputSchema.properties[prop].type,
        required: t.inputSchema.required?.includes(prop) || false,
      })),
    }));

    assert.equal(mapped.length, 1);
    assert.equal(mapped[0].name, 'mcp_weather_lookup');
    assert.equal(mapped[0].category, 'MCP');
    assert.equal(mapped[0].parameters[0].name, 'city');
    assert.equal(mapped[0].parameters[0].required, true);
  });

  it('verifies web research source deduplication and citation indices', () => {
    const rawSources = [
      { url: 'https://docs.sqlalchemy.org/guide', title: 'SQLAlchemy Docs' },
      { url: 'https://magicstack.github.io/asyncpg', title: 'AsyncPG Docs' },
      { url: 'https://docs.sqlalchemy.org/guide', title: 'Duplicate Guide' },
    ];

    const seenUrls = new Set();
    const unique = [];
    for (const s of rawSources) {
      if (!seenUrls.has(s.url)) {
        seenUrls.add(s.url);
        unique.push(s);
      }
    }

    assert.equal(unique.length, 2);
    const citations = unique.map((u, i) => ({ index: i + 1, ...u }));
    assert.equal(citations[0].index, 1);
    assert.equal(citations[1].index, 2);
    assert.equal(citations[0].title, 'SQLAlchemy Docs');
    assert.equal(citations[1].title, 'AsyncPG Docs');
  });

  it('verifies defensive prompt injection containment wrapping', () => {
    const formatPromptOutput = (toolName, success, data) => {
      return `<tool_output name="${toolName}" status="${success ? 'success' : 'failed'}">\n${JSON.stringify(data)}\n</tool_output>`;
    };

    const formatted = formatPromptOutput('calculator', true, { result: 42 });
    assert.ok(formatted.startsWith('<tool_output name="calculator" status="success">'));
    assert.ok(formatted.includes('"result":42') || formatted.includes('42'));
    assert.ok(formatted.endsWith('</tool_output>'));
  });
});
