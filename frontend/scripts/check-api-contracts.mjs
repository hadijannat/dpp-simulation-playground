#!/usr/bin/env node
import { readdir, readFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import ts from "typescript";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const frontendRoot = path.resolve(__dirname, "..");
const srcRoot = path.join(frontendRoot, "src");
const generatedTypesPath = path.join(srcRoot, "types", "generated", "platform-api.ts");

const SOURCE_EXTENSIONS = new Set([".ts", ".tsx"]);
const GENERATED_PATH_PATTERN = /^\s+"(\/api\/v2\/[^"]+)":\s*\{/gm;
const API_FUNCTIONS = new Set(["apiGet", "apiPost", "apiRequest", "apiPatch", "apiDelete"]);

function normalizePath(raw) {
  const withoutQuery = raw.split("?")[0].replaceAll("${}", "{expr}");
  const normalizedSegments = withoutQuery
    .split("/")
    .filter(Boolean)
    .map((segment) => {
      if (segment === "{expr}") return "{}";
      if (/^\{[^}]+\}$/.test(segment)) return "{}";
      if (segment.includes("{expr}")) return segment.replaceAll("{expr}", "");
      return segment;
    })
    .filter(Boolean);
  return `/${normalizedSegments.join("/")}`;
}

async function* walkFiles(dir) {
  const entries = await readdir(dir, { withFileTypes: true });
  for (const entry of entries) {
    const fullPath = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      if (entry.name === "generated") continue;
      yield* walkFiles(fullPath);
      continue;
    }
    if (SOURCE_EXTENSIONS.has(path.extname(entry.name))) {
      yield fullPath;
    }
  }
}

function extractRouteLiteral(argumentNode) {
  if (ts.isStringLiteral(argumentNode) || ts.isNoSubstitutionTemplateLiteral(argumentNode)) {
    return argumentNode.text;
  }

  if (ts.isTemplateExpression(argumentNode)) {
    let route = argumentNode.head.text;
    for (const span of argumentNode.templateSpans) {
      route += "${}";
      route += span.literal.text;
    }
    return route;
  }

  return null;
}

function findApiRoutes(filePath, content) {
  const scriptKind = filePath.endsWith(".tsx") ? ts.ScriptKind.TSX : ts.ScriptKind.TS;
  const source = ts.createSourceFile(filePath, content, ts.ScriptTarget.Latest, true, scriptKind);
  const routes = [];

  function visit(node) {
    if (ts.isCallExpression(node) && node.arguments.length > 0 && ts.isIdentifier(node.expression)) {
      const functionName = node.expression.text;
      if (API_FUNCTIONS.has(functionName)) {
        const route = extractRouteLiteral(node.arguments[0]);
        if (route) {
          const position = source.getLineAndCharacterOfPosition(node.arguments[0].getStart(source));
          routes.push({ line: position.line + 1, route });
        }
      }
    }
    ts.forEachChild(node, visit);
  }

  visit(source);
  return routes;
}

async function getSupportedPaths() {
  const generated = await readFile(generatedTypesPath, "utf8");
  const paths = [...generated.matchAll(GENERATED_PATH_PATTERN)].map((match) => match[1]);
  const normalized = new Set(paths.map(normalizePath));
  return { generated, normalized };
}

async function main() {
  const { generated, normalized: supportedPaths } = await getSupportedPaths();
  const legacyRoutes = [];
  const unknownV2Routes = [];

  for await (const filePath of walkFiles(srcRoot)) {
    const content = await readFile(filePath, "utf8");
    const relative = path.relative(frontendRoot, filePath);
    const routes = findApiRoutes(filePath, content);

    for (const { route, line } of routes) {
      if (!route.startsWith("/api/v")) continue;

      if (route.startsWith("/api/v1/")) {
        legacyRoutes.push(`${relative}:${line} -> ${route}`);
        continue;
      }

      if (route.startsWith("/api/v2/")) {
        const normalizedRoute = normalizePath(route);
        if (!supportedPaths.has(normalizedRoute)) {
          unknownV2Routes.push(`${relative}:${line} -> ${route}`);
        }
      }
    }
  }

  if (generated.includes('"application/json": unknown')) {
    console.error("OpenAPI contract check failed: generated response schemas still contain unknown JSON payloads.");
    process.exit(1);
  }

  if (legacyRoutes.length > 0) {
    console.error("Legacy /api/v1 routes are not allowed in frontend source:");
    for (const entry of legacyRoutes) {
      console.error(`  - ${entry}`);
    }
    process.exit(1);
  }

  if (unknownV2Routes.length > 0) {
    console.error("Unrecognized /api/v2 routes found (not present in generated OpenAPI paths):");
    for (const entry of unknownV2Routes) {
      console.error(`  - ${entry}`);
    }
    process.exit(1);
  }

  console.log("API contract checks passed.");
}

main().catch((error) => {
  console.error("API contract check failed with an unexpected error:");
  console.error(error);
  process.exit(1);
});
