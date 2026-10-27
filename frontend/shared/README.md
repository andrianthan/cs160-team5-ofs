# @ofs/shared

Local React package shared by the customer storefront and staff dashboard.

```tsx
import { AuthProvider, RequireAuth, useAuth } from "@ofs/shared/auth";
import { AppHeader, FormField, NavPill } from "@ofs/shared/components";
```

This repository is an npm workspace. Both apps list `"@ofs/shared": "0.0.0"`,
which matches this workspace package and makes npm link it automatically. Run
`npm install` once at the repository root. The workspace provides one React
installation for all three packages, and Vite also deduplicates React as a
safety measure. Both Tailwind entry files scan `frontend/shared/src` so shared
component classes are included in their generated CSS.

Keep code here only when both apps can use it. Customer Cart and Product state
belongs in the storefront; preparation, dispatch, inventory, and report state
belongs in the staff dashboard.
