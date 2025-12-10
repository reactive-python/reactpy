# Suggested Commands (Hatch)

## Python
- **Test**: `hatch test` (All must pass)
- **Coverage**: `hatch test --cover`
- **Format**: `hatch fmt`
- **Check Format**: `hatch fmt --check`
- **Type Check**: `hatch run python:type_check`
- **Build**: `hatch build --clean`

## JavaScript
- **Build**: `hatch run javascript:build` (Rebuild after JS changes)
- **Check**: `hatch run javascript:check`
- **Fix**: `hatch run javascript:fix`

## Shell
- **Dev Shell**: `hatch shell`
