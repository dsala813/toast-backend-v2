# Toast Data Middleware API v3

This version adds the three requested upgrades:

1. Better `profileExport` workflow with richer schema profiling
2. Smoother file-based analysis using upload-first endpoints
3. A test kit and guide for validating against 3 real Toast export types

## New and improved endpoints
- `POST /toast/profile-export`
- `POST /toast/upload-and-profile`
- `POST /toast/upload-and-analyze`
- `POST /toast/upload-and-normalize/item-sales`
- `POST /toast/upload-and-package/knowledge`
