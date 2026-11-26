"""UI check + screenshots against a running Odoo (used in Docker with the Playwright image).

python screenshots.py <base_url> <major_version> <out_dir>
Login of the throwaway test database comes from ODOO_LOGIN / ODOO_PASSWORD.
"""
import json
import os
import sys

from playwright.sync_api import sync_playwright

BASE, V, OUT = sys.argv[1].rstrip("/"), int(sys.argv[2]), sys.argv[3]
report = {"version": V}


def rpc(page, model, method, args, kwargs=None):
    return page.evaluate(
        """async ([model, method, args, kwargs]) => {
            const r = await fetch('/web/dataset/call_kw', {method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({jsonrpc: '2.0', method: 'call', params: {
                    model, method, args, kwargs}})});
            return (await r.json());
        }""",
        [model, method, args, kwargs or {}],
    )


def form_url(model, rec_id):
    if V >= 18:
        return f"{BASE}/odoo/{model}/{rec_id}"
    return f"{BASE}/web#model={model}&id={rec_id}&view_type=form"


with sync_playwright() as p:
    browser = p.chromium.launch()
    ctx = browser.new_context(viewport={"width": 1400, "height": 900}, locale="en-US")
    page = ctx.new_page()
    page.goto(f"{BASE}/web/login")
    page.fill("input[name=login]", os.environ.get("ODOO_LOGIN", "admin"))
    page.fill("input[name=password]", os.environ["ODOO_PASSWORD"])
    page.click("button[type=submit]")
    page.wait_for_selector(".o_main_navbar", timeout=60000)
    print("lang reset:", rpc(page, "res.users", "write", [[2], {"lang": "en_US"}]), flush=True)

    # --- settings --------------------------------------------------------------
    if V >= 18:
        page.goto(f"{BASE}/odoo/action-delegaize_connector.action_delegaize_settings")
    else:
        page.goto(f"{BASE}/web#action=delegaize_connector.action_delegaize_settings")
    page.wait_for_selector("button[name=action_delegaize_test_connection]", timeout=60000)
    page.wait_for_timeout(1500)
    key = page.locator("div[name=delegaize_api_key] input")
    key.fill("cpa_invalid_demo_key")
    page.click("button[name=action_delegaize_test_connection]")
    # Odoo asks to save unsaved settings before running a button.
    save = page.locator(".modal-footer .btn-primary")
    try:
        save.wait_for(timeout=5000)
        save.click()
        # Saving settings reloads the page; then run the test on the saved values.
        page.wait_for_timeout(3000)
        page.wait_for_selector("button[name=action_delegaize_test_connection]", timeout=60000)
        page.wait_for_timeout(1500)
        page.click("button[name=action_delegaize_test_connection]")
    except Exception:
        pass
    try:
        page.wait_for_selector(".o_notification", timeout=30000)
    except Exception:
        page.screenshot(path=f"{OUT}/odoo{V}-debug-settings.png")
        raise
    report["connection_test_notification"] = page.locator(".o_notification").first.inner_text()
    page.screenshot(path=f"{OUT}/odoo{V}-settings.png", full_page=False)
    report["settings_url_field"] = page.locator("div[name=delegaize_url] input").input_value()

    # --- menu -------------------------------------------------------------------
    page.goto(f"{BASE}/web" if V < 18 else f"{BASE}/odoo")
    page.wait_for_selector(".o_main_navbar", timeout=60000)
    page.wait_for_timeout(1500)
    page.locator(".o_navbar_apps_menu button, .o_navbar_apps_menu a").first.click()
    page.wait_for_timeout(1500)
    app = page.locator(".o_app:has-text('DelegAIze'), .dropdown-item:has-text('DelegAIze')").first
    report["menu_DelegAIze_visible"] = app.count() > 0
    page.screenshot(path=f"{OUT}/odoo{V}-apps-menu.png")
    try:
        with page.expect_popup(timeout=20000) as pop:
            app.click()
            page.wait_for_timeout(1500)
            sub = page.locator("a:has-text('Open DelegAIze'), .dropdown-item:has-text('Open DelegAIze')")
            if sub.count():
                sub.first.click()
        report["menu_opened_url"] = pop.value.url
        pop.value.close()
    except Exception as exc:  # noqa: BLE001
        report["menu_opened_url"] = "no popup: %s" % exc.__class__.__name__
        page.screenshot(path=f"{OUT}/odoo{V}-debug-menu.png")

    # --- records ---------------------------------------------------------------
    created = rpc(page, "res.partner", "create", [{"name": "Muster GmbH", "is_company": True}])
    print("partner create:", created, flush=True)
    partner = created["result"]
    if isinstance(partner, list):
        partner = partner[0]
    lead = rpc(page, "crm.lead", "create", [{"name": "Website-Relaunch", "partner_id": partner}])["result"]
    order = rpc(page, "sale.order", "create", [{"partner_id": partner}])["result"]
    move = rpc(page, "account.move", "create", [{"move_type": "out_invoice", "partner_id": partner}])["result"]
    targets = [("res.partner", partner), ("crm.lead", lead), ("sale.order", order), ("account.move", move)]
    report["records"] = {}
    for model, rid in targets:
        if isinstance(rid, list):
            rid = rid[0]
        page.goto(form_url(model, rid))
        if V < 18:
            page.reload()
        btn = page.locator("button[name=action_delegaize_open]")
        page.wait_for_selector(".o_form_view", timeout=60000)
        page.wait_for_timeout(1500)
        report.setdefault("in_more_dropdown", {})[model] = btn.count() == 0
        if btn.count() == 0:
            page.locator(".o_button_more, button:has-text('More')").first.click()
        try:
            btn.first.wait_for(state="attached", timeout=60000)
        except Exception:
            page.screenshot(path=f"{OUT}/odoo{V}-debug-{model}.png")
            raise
        page.wait_for_timeout(1000)
        entry = {"open_buttons": btn.count(),
                 "ask_buttons": page.locator("button[name=action_delegaize_ask]").count()}
        with page.expect_popup(timeout=30000) as pop:
            page.locator("button[name=action_delegaize_open]").first.click()
        entry["opened_url"] = pop.value.url
        pop.value.close()
        page.screenshot(path=f"{OUT}/odoo{V}-{model.replace('.', '_')}.png")
        report["records"][model] = entry

    # --- German UI ---------------------------------------------------------------
    uid = 2  # admin
    rpc(page, "res.users", "write", [[uid], {"lang": "de_DE"}])
    page.goto(form_url("crm.lead", lead))
    if V < 18:
        page.reload()
    page.wait_for_selector("button[name=action_delegaize_open]", timeout=60000)
    page.wait_for_timeout(1500)
    report["german_open_button"] = page.locator("button[name=action_delegaize_open]").first.inner_text()
    report["german_ask_button"] = page.locator("button[name=action_delegaize_ask]").first.inner_text()
    page.screenshot(path=f"{OUT}/odoo{V}-crm_lead-de.png")
    if V >= 18:
        page.goto(f"{BASE}/odoo/action-delegaize_connector.action_delegaize_settings")
    else:
        page.goto(f"{BASE}/web#action=delegaize_connector.action_delegaize_settings")
        page.reload()
    page.wait_for_selector("button[name=action_delegaize_test_connection]", timeout=60000)
    page.wait_for_timeout(1500)
    report["german_test_button"] = page.locator("button[name=action_delegaize_test_connection]").inner_text()
    page.screenshot(path=f"{OUT}/odoo{V}-settings-de.png")
    rpc(page, "res.users", "write", [[uid], {"lang": "en_US"}])

    with open(f"{OUT}/report-odoo{V}.json", "w") as fh:
        json.dump(report, fh, indent=1, ensure_ascii=False)
    print(json.dumps(report, indent=1, ensure_ascii=False))
    browser.close()
