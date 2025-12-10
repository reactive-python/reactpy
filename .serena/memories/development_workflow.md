# Development Workflow

1. **Bootstrap**: Install Python 3.9+, Hatch, Bun.
2. **Changes**: Modify code.
3. **Format**: `hatch fmt`.
4. **Type Check**: `hatch run python:type_check`.
5. **JS Check**: `hatch run javascript:check` (if JS changed).
6. **Test**: `hatch test`.
7. **Validate**: Manual component/server tests.
8. **Build JS**: `hatch run javascript:build` (if JS changed).
9. **Docs**: Update if Python source changed.
10. **Changelog**: Add entry in `docs/source/about/changelog.rst`.
