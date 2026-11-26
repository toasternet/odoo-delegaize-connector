# DelegAIze Connector for Odoo

Free Odoo module (LGPL-3) that connects Odoo with [DelegAIze](https://delegaize.innov-ai-tive.de/?utm_source=github&utm_medium=readme&utm_campaign=odoo_connector_202611&ref=th).

One branch per Odoo version: `17.0`, `18.0`, `19.0`. The code is the same on all three; the
differences are the module versions in the manifests (`17.0.1.0.0`, `18.0.1.0.0`, `19.0.1.0.0`)
and, on `19.0`, the settings action has no `target="inline"` (Odoo 19 removed that value).

| Module | What it adds | Installs |
| --- | --- | --- |
| `delegaize_connector` | Settings (address, API key, connection test), menu "DelegAIze", buttons on contacts | manually (Apps) |
| `delegaize_connector_crm` | Buttons on leads/opportunities (`crm.lead`) | automatically when CRM is installed |
| `delegaize_connector_sale` | Buttons on quotations/sales orders (`sale.order`) | automatically when Sales is installed |
| `delegaize_connector_account` | Buttons on invoices/bills (`account.move`) | automatically when Invoicing is installed |

## Behaviour

* **No background traffic.** The module never sends Odoo data to DelegAIze on its own.
* **Buttons "Open in DelegAIze" / "Ask agent"** return an `ir.actions.act_url` that opens a new
  browser tab:

  ```
  <DelegAIze address><deep link path>?source=odoo&intent=open|ask
      &instance=<web.base.url>&db=<database>&model=<model>&id=<id>[&name=<display name>]
  ```

  Defaults: address `https://delegaize.innov-ai-tive.de`, path `/app/open/odoo`. `name` can be
  switched off in the settings.
* **Menu DelegAIze → Open DelegAIze** opens `<address>/app`.
* **Test connection** (Settings → DelegAIze) sends one MCP JSON-RPC request with the API key:

  ```
  POST <address>/api/sb/functions/v1/mcp-server
  Authorization: Bearer cpa_...
  {"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"whoami","arguments":{}}}
  ```

  `whoami` is read-only. HTTP 401 / JSON-RPC error `-32001` → "API key rejected"; HTTP 200 with
  `result` → "Connection works". Nothing from Odoo is part of the request.
* Settings are stored as `ir.config_parameter` (`delegaize_connector.*`); only administrators
  (`base.group_system`) can see them.

## How DelegAIze gets Odoo data

DelegAIze reads Odoo data only through its own Odoo connection, which the customer sets up in
DelegAIze (Odoo address, database, user and an Odoo API key; XML-RPC `execute_kw`). This module
does not change that and does not transport record data; it only opens DelegAIze with a reference.

## What the DelegAIze side has to provide

* `GET /app/open/odoo` with the query parameters listed above (after login):
  find the DelegAIze record linked to `model` + `id` (checked against the customer's Odoo
  connection for `instance`/`db`) and open it; if there is no link yet, offer to link it,
  using `name` as search text; with `intent=ask`, open the agent chat with the record reference
  as context.
* The connection test uses the existing MCP endpoint and its read-only `whoami` tool. A
  dedicated ping endpoint (e.g. `GET /api/odoo/v1/ping` → `{ok, tenant_name}`) can replace it
  later via the "API path" setting.

## Testing

`tools/test-in-docker.sh <17|18|19>` installs the modules (plus CRM, Sales, Invoicing) into a fresh
database in Docker and runs the module tests. Containers are prefixed `test-odoo-`.
`tools/screenshots.py` (run in the official Playwright Python image against a running test
instance) clicks through settings, connection test, menu and the buttons on all four models,
in English and German, and writes screenshots plus a JSON report.

## License

LGPL-3.0. © Innov-AI-tive.
