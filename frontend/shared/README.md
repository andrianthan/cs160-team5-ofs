# @ofs/shared

Local React package shared by the customer storefront and staff dashboard.

```tsx
import { AuthProvider, RequireAuth, useAuth } from "@ofs/shared/auth";
import { AppHeader, FormField, NavPill } from "@ofs/shared/components";
```

Each app lists `"@ofs/shared": "file:../shared"` in its dependencies. Run
`npm install` inside each app after changing that dependency. Both Vite configs
preserve the package symlink so the apps and shared package use the same React
installation. Both Tailwind entry files scan `frontend/shared/src` so shared
component classes are included in their generated CSS.

Keep code here only when both apps can use it. Customer Cart and Product state
belongs in the storefront; preparation, dispatch, inventory, and report state
belongs in the staff dashboard.
