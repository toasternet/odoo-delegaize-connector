# Publishing on the Odoo Apps Store (apps.odoo.com)

Nothing has been submitted yet. This needs the publisher's odoo.com account (that account
owns the listing; the module is free, so no Odoo partnership or payout setup is needed).

## Before you start

* Repository: `https://github.com/toasternet/odoo-delegaize-connector` (public).
* Branches: `17.0`, `18.0`, `19.0` - each contains the four modules at the repo root:
  `delegaize_connector` (main app) and the auto-installing companions
  `delegaize_connector_crm`, `delegaize_connector_sale`, `delegaize_connector_account`.
* Store page: `delegaize_connector/static/description/index.html`, icon `icon.png`,
  banner `banner.png` (manifest key `images`).
* No `price` in the manifests → the apps are listed as free.

## Steps (once per Odoo version)

1. Log in at <https://apps.odoo.com> with the odoo.com account.
2. Top right: **Upload** (or "My Apps" → **Upload a module**) → page *Register a repository*.
3. Repository URL - Odoo expects the branch in the URL, use the SSH form with `#branch`:
   * `ssh://git@github.com/toasternet/odoo-delegaize-connector.git#17.0`
   * `ssh://git@github.com/toasternet/odoo-delegaize-connector.git#18.0`
   * `ssh://git@github.com/toasternet/odoo-delegaize-connector.git#19.0`
   (`https://github.com/toasternet/odoo-delegaize-connector.git#17.0` works as well for a
   public repo.)
4. Click **Submit**. Odoo clones the branch and scans every folder with a `__manifest__.py`.
   The first scan can take a few minutes up to a few hours; the repository then shows up under
   "My Apps" with the four modules.
5. Repeat steps 2-4 for the other two branches.
6. Check each listing (title, icon, banner, description page) and that the version filter
   shows 17.0 / 18.0 / 19.0.

## Updates

Push to the branch and increase the module version in `__manifest__.py`
(e.g. `17.0.1.0.1`). apps.odoo.com rescans registered repositories automatically (roughly
daily); "My Apps" → repository → **Scan** forces it.

## If the scan fails

* "No module found": the branch name in the URL is wrong.
* "Access denied": the repo must be public, or Odoo's deploy key must be added on GitHub
  (Settings → Deploy keys) - not needed while the repo is public.
* Description not rendered: `static/description/index.html` must be valid HTML without scripts.
