from ckan.plugins.toolkit import render_snippet, config

def matomo_snippet():
    data = {
        "matomo_domain": config.get('ckanext.matomo.domain'),
        "matomo_script_domain": config.get('ckanext.matomo.script_domain', config.get('ckanext.matomo.domain')),
        "matomo_site_id": config.get('ckanext.matomo.site_id')
    }

    return render_snippet("matomo/snippets/matomo.html", data)
