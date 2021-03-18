import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit
from ckanext.matomo import helpers


class MatomoPlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.ITemplateHelpers)
    plugins.implements(plugins.IConfigurable)

    # IConfigurer

    def update_config(self, config_):
        toolkit.add_template_directory(config_, 'templates')
        toolkit.add_public_directory(config_, 'public')
        toolkit.add_resource('fanstatic', 'matomo')

    #IConfigurable

    def configure(self, config):

        self.config = config
        for config_option in (
            u'ckanext.matomo.domain',
            u'ckanext.matomo.site_id',
        ):
            if not config.get(config_option):
                raise Exception(u"Config option `{0}` must be set to use Matomo".format(config_option))


    # ITemplateHelpers

    def get_helpers(self):
        return {
            "matomo_snippet": helpers.matomo_snippet
        }

