# CHECKS.md

Extended check implementations for vibe-doctor.
Read during Step 1 for framework-specific checks.

---

## Node.js / React / Vite projects

### shadcn/ui version check

```bash
if [ -f "components.json" ]; then
  # Get shadcn version from components.json
  shadcn_version=$(cat components.json | node -e "
    const c = JSON.parse(require('fs').readFileSync('/dev/stdin','utf8'));
    console.log(c.version || 'unknown');
  " 2>/dev/null)
  
  # Get installed radix-ui version (v3 uses different packages than v2)
  radix_version=$(node -e "
    try {
      console.log(require('./node_modules/@radix-ui/react-primitive/package.json').version);
    } catch { console.log('not installed'); }
  " 2>/dev/null)
  
  echo "INFO:shadcn components.json present, radix-ui: $radix_version"
fi
```

### CommonJS vs ESM consistency

```bash
if [ -f "package.json" ]; then
  module_type=$(node -e "
    const p = JSON.parse(require('fs').readFileSync('package.json','utf8'));
    console.log(p.type || 'commonjs');
  " 2>/dev/null)
  
  if [ "$module_type" = "commonjs" ]; then
    # Check for .js extensions in require statements (needed in CJS)
    # Check for import syntax in .js files without type:module
    esm_in_cjs=$(grep -r "^import " src/ --include="*.js" 2>/dev/null | head -3)
    if [ -n "$esm_in_cjs" ]; then
      echo "FAIL:ESM import syntax in .js files but package.json type is commonjs"
    else
      echo "PASS:module type consistent"
    fi
  fi
  
  if [ "$module_type" = "module" ]; then
    # Check for require() in ESM files
    cjs_in_esm=$(grep -r "require(" src/ --include="*.js" 2>/dev/null | grep -v "//.*require" | head -3)
    if [ -n "$cjs_in_esm" ]; then
      echo "FAIL:require() in ESM project (type:module) — use import instead"
    else
      echo "PASS:module type consistent"
    fi
  fi
fi
```

### Express + Supabase env vars

```bash
# Check that common required env vars are in .env.example
if [ -f ".env.example" ]; then
  required_vars=""
  
  # Supabase vars
  grep -r "SUPABASE_URL\|SUPABASE_KEY\|SUPABASE_ANON" src/ 2>/dev/null | grep -q "process.env" && \
    required_vars="$required_vars SUPABASE_URL SUPABASE_ANON_KEY"
  
  # Auth vars
  grep -r "JWT_SECRET\|SESSION_SECRET" src/ 2>/dev/null | grep -q "process.env" && \
    required_vars="$required_vars JWT_SECRET"
  
  for var in $required_vars; do
    if ! grep -q "$var" .env.example 2>/dev/null; then
      echo "WARN:$var used in code but missing from .env.example"
    fi
  done
  
  echo "PASS:env vars checked"
fi
```

---

## Python projects

### Virtual environment check

```bash
if [ -f "pyproject.toml" ] || [ -f "requirements.txt" ]; then
  if [ ! -d "venv" ] && [ ! -d ".venv" ] && [ -z "$VIRTUAL_ENV" ]; then
    echo "WARN:no virtual environment detected — create with: python -m venv venv"
  else
    echo "PASS:virtual environment present"
  fi
  
  # Check installed packages vs requirements
  if [ -f "requirements.txt" ] && command -v pip >/dev/null 2>&1; then
    missing=$(pip check 2>&1 | grep "is not installed" | head -3)
    if [ -n "$missing" ]; then
      echo "FAIL:missing Python packages: $missing"
    else
      echo "PASS:Python packages installed"
    fi
  fi
fi
```

---

## Flutter/Dart projects

```bash
if [ -f "pubspec.yaml" ]; then
  # Check pub dependencies
  if ! flutter pub get --dry-run 2>/dev/null | grep -q "No changes"; then
    echo "WARN:flutter pub get may be needed — run: flutter pub get"
  else
    echo "PASS:flutter dependencies up to date"
  fi
fi
```

---

## Common remediations reference

| Failure | Auto-fix | Command |
|---------|---------|---------|
| node_modules missing | Yes | `npm install` |
| husky not executable | Yes | `chmod +x .husky/*` |
| node_modules stale | Ask first (may be large) | `npm install` |
| nested .git | Never auto — show command | `git rm --cached [path]` |
| Tailwind version mismatch | Never auto — show diff | Show files to change |
| dotenv order | Never auto — show lines | Show swap needed |
| TypeScript path missing | Never auto — show path | `mkdir -p [path]` |
| ESLint config error | Never auto | Show error detail |
| venv missing (Python) | Never auto | `python -m venv venv` |
