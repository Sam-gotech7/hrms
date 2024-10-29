import frappe

no_cache = 1


def get_context(context):
	csrf_token = frappe.sessions.get_csrf_token()
	frappe.db.commit()  # nosempgrep
	context = frappe._dict()
	context.csrf_token = csrf_token
	context.boot = get_boot()
	return context


@frappe.whitelist(methods=["POST"], allow_guest=True)
def get_context_for_dev():
	if not frappe.conf.developer_mode:
		frappe.throw(frappe._("This method is only meant for developer mode"))
	return get_boot()


def get_boot():
	return frappe._dict(
		{
			"site_name": frappe.local.site,
			"push_relay_server_url": frappe.conf.get("push_relay_server_url") or "",
			"default_route": get_default_route(),
		}
	)
<<<<<<< HEAD
=======

	bootinfo.lang = frappe.local.lang
	load_translations(bootinfo)

	return bootinfo


def get_default_route():
	return "/hrms"
>>>>>>> 4ba8046db (fix(PWA): post login redirection fails due to `default_route` conflict with other app (#2351))
