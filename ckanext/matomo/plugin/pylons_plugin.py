import ckan.plugins as plugins
from routes.mapper import SubMapper
from ckanext.matomo import tracking
from flask import Blueprint
from ckan.controllers.package import PackageController
from ckan.plugins import plugin_loaded


class MixinPlugin:
    plugins.implements(plugins.IRoutes, inherit=True)
    plugins.implements(plugins.IBlueprint)

    # IRoutes

    def before_map(self, map):
        with SubMapper(map, controller='ckanext.matomo.plugin.pylons_plugin:TrackedResourceController') as m:
            m.connect('/dataset/{id}/resource/{resource_id}/download', action='resource_download')
            m.connect('/dataset/{id}/resource/{resource_id}/download/{filename}', action='resource_download')
        return map

    # IBlueprint

    def get_blueprint(self):
        blueprint = Blueprint('matomo', self.__module__)
        rules = [
            ('/api/action/<logic_function>', 'tracked_action', tracking.tracked_action),
            ('/api/<ver>/action/<logic_function>', 'tracked_action', tracking.tracked_action),
        ]
        for rule in rules:
            blueprint.add_url_rule(*rule)

        return blueprint


# Ugly hack since ckanext-cloudstorage replaces resource_download action
# and we can't inherit from the correct controller,
# googleanalytics needs to before cloudstorage in plugin list
OptionalController = PackageController
if plugin_loaded('cloudstorage'):
    from ckanext.cloudstorage.controller import StorageController
    OptionalController = StorageController


class TrackedResourceController(OptionalController):
    def resource_download(self, id, resource_id, filename=None):
        tracking.post_analytics('Resource / Download', download=True)
        return OptionalController.resource_download(self, id, resource_id, filename)
