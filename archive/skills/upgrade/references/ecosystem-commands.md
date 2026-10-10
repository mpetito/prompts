# Ecosystem Command Reference

Per-ecosystem commands for each phase of the upgrade protocol. Commands are shown for
PowerShell but work in any shell unless noted.

## Quick Reference

| Task                     | npm                     | dotnet                                   |
| ------------------------ | ----------------------- | ---------------------------------------- |
| List outdated            | `npm outdated`          | `dotnet list package --outdated`         |
| Install specific version | `npm install pkg@1.2.3` | `dotnet add package pkg --version 1.2.3` |
| Security audit           | `npm audit`             | `dotnet list package --vulnerable`       |
| Run tests                | `npm test`              | `dotnet test`                            |
| Type check               | `npx tsc --noEmit`      | `dotnet build`                           |
| Lint                     | `npm run lint`          | `dotnet format --verify-no-changes`      |
| View dependency tree     | `npm ls pkg`            | `dotnet list package`                    |
| Clean install            | `npm ci`                | `dotnet restore`                         |

---

## Phase 1 — Inventory

### npm

```powershell
# List outdated packages
npm outdated

# Detailed package info
npm info <package> version
npm info <package> peerDependencies

# Check for vulnerabilities
npm audit

# View dependency tree
npm ls <package>

# Check what would be installed
npm install <package>@<version> --dry-run
```

### dotnet

```powershell
# List outdated packages
dotnet list package --outdated

# Include transitive dependencies
dotnet list package --outdated --include-transitive

# Check for vulnerable packages
dotnet list package --vulnerable

# View all packages
dotnet list package
```

---

## Phase 2 — Codebase Impact Analysis

Find usages of affected APIs before changing versions:

```powershell
# Search for package imports/usage
grep -r "from 'package-name'" --include="*.ts" --include="*.tsx"
grep -r "require('package-name')" --include="*.js"

# For a specific API
grep -r "specificFunction\|specificMethod" --include="*.ts"
```

---

## Phase 3 — Implement

### npm

```powershell
# Install specific version
npm install <package>@<version>

# Install multiple packages
npm install <pkg1>@<ver1> <pkg2>@<ver2>

# Update within semver range
npm update <package>

# Install and save as dev dependency
npm install -D <package>@<version>

# Clean install from lockfile
npm ci

# Dedupe dependencies
npm dedupe
```

### dotnet

```powershell
# Add/update package
dotnet add package <package> --version <version>

# Update to latest
dotnet add package <package>

# Restore packages
dotnet restore

# Clean and rebuild
dotnet clean
dotnet build
```

### Peer Dependency Conflicts

```powershell
# View peer dependency requirements
npm info <package> peerDependencies

# Install with legacy peer deps (npm 7+)
npm install <package>@<version> --legacy-peer-deps

# Force resolution (use carefully)
npm install <package>@<version> --force
```

---

## Phase 4 — Validation

### npm

```powershell
# Run tests
npm test
npm run test:unit
npm run test:integration

# Type checking (TypeScript)
npx tsc --noEmit

# Linting
npm run lint
npx eslint . --ext .ts,.tsx

# Build
npm run build

# Security audit
npm audit
npm audit fix  # Auto-fix if safe

# Start application
npm start
npm run dev
```

### dotnet

```powershell
# Run tests
dotnet test
dotnet test --verbosity normal

# Build
dotnet build
dotnet build --no-restore

# Format check
dotnet format --verify-no-changes

# Vulnerability scan
dotnet list package --vulnerable

# Run application
dotnet run
```

---

## Security Audit

```powershell
# npm
npm audit
npm audit --json        # Machine-readable output
npm audit fix           # Auto-fix compatible updates
npm audit fix --force   # Force fix (may have breaking changes)

# dotnet
dotnet list package --vulnerable
dotnet list package --vulnerable --include-transitive
```

---

## Migration Automation

```powershell
# Use codemods if available
npx @package/codemod migrate-v2

# Search and replace with ripgrep + sed
rg "oldFunction" --files-with-matches | xargs sed -i 's/oldFunction/newFunction/g'
```
