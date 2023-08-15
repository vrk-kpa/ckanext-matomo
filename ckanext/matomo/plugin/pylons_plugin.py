import ckan.plugins as plugins
from routes.mapper import SubMapper
from ckanext.matomo import tracking
from ckan.controllers.package import PackageController
from ckan.plugins import plugin_loaded


class MixinPlugin:
    plugins.implements(plugins.IRoutes, inherit=True)

    # IRoutes

    def before_map(self, map):
        if plugins.toolkit.asbool(plugins.toolkit.config.get('ckanext.matomo.track_downloads', False)):
            with SubMapper(map, controller='ckanext.matomo.plugin.pylons_plugin:TrackedResourceController') as m:
                m.connect('/dataset/{id}/resource/{resource_id}/download', action='resource_download')
                m.connect('/dataset/{id}/resource/{resource_id}/download/{filename}', action='resource_download')
        return map


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
