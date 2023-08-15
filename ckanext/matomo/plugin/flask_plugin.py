import ckan.plugins as plugins
from ckanext.matomo.tracking import post_analytics, tracked_action
from flask import Blueprint
from ckan.views.resource import download as resource_download

class MixinPlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IBlueprint)

    # IBlueprint

    def get_blueprint(self):
        blueprint = Blueprint('matomo', self.__module__)
        rules = [
            ('/api/action/<logic_function>', 'tracked_action', tracked_action),
            ('/api/<ver>/action/<logic_function>', 'tracked_action', tracked_action),
            # ('/dataset/<package_id>/resource/<resource_id>/download', 'tracked_download', tracked_download),
            # ('/dataset/<package_id>/resource/<resource_id>/download/<filename>', 'tracked_download', tracked_download)
        ]

        if plugins.toolkit.asbool(plugins.toolkit.config.get('ckanext.matomo.track_api', False)):
            for rule in rules:
                blueprint.add_url_rule(*rule)

        return blueprint


def tracked_download(package_id, resource_id, filename=None):
    post_analytics('Resource', 'Download', 'Resource download', download=True)
    return resource_download(None, package_id, resource_id, filename)
