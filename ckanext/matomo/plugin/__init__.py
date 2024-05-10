import os
import logging
import ckanext.matomo

import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit
from ckan.lib.plugins import DefaultTranslation

from ckanext.matomo.cli import get_commands
from ckanext.matomo import helpers
import ckanext.matomo.logic as logic

try:
    from ckanext.report.interfaces import IReport
except ImportError:
    IReport = None

try:
    toolkit.requires_ckan_version("2.9")
except toolkit.CkanVersionException:
    from ckanext.matomo.plugin.pylons_plugin import MixinPlugin
else:
    from ckanext.matomo.plugin.flask_plugin import MixinPlugin


log = logging.getLogger(__name__)


class MatomoPlugin(MixinPlugin, plugins.SingletonPlugin, DefaultTranslation):
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.ITemplateHelpers)
    plugins.implements(plugins.IConfigurable)
    plugins.implements(plugins.IActions)
    plugins.implements(plugins.ITranslation)

    if toolkit.check_ckan_version(min_version="2.9"):
        plugins.implements(plugins.IClick)

    # IConfigurer

    def update_config(self, config_):
        toolkit.add_template_directory(config_, '../templates')
        toolkit.add_public_directory(config_, '../public')
        toolkit.add_resource('../fanstatic', 'matomo')
        toolkit.add_resource('../public/javascript/', 'ckanext-matomo_js')

    # IConfigurable

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
            'matomo_snippet': helpers.matomo_snippet,
            'get_visits_for_resource': helpers.get_visits_for_resource,
            'get_visits_for_dataset': helpers.get_visits_for_dataset,
            'get_visit_count_for_dataset': helpers.get_visit_count_for_dataset,
            'get_download_count_for_dataset': helpers.get_download_count_for_dataset,
            'get_visit_count_for_resource': helpers.get_visit_count_for_resource,
            'get_download_count_for_resource': helpers.get_download_count_for_resource,
            'get_organization_url': helpers.get_organization_url,
            'format_date': helpers.format_date,
            'get_date_range': helpers.get_date_range,
            'get_years': helpers.get_years,
            'matomo_show_download_graph': helpers.show_download_graph,
            'get_current_date': helpers.get_current_date,
            'get_downloads_in_date_range_for_resource': helpers.get_downloads_in_date_range_for_resource
        }

    # IClick

    def get_commands(self):
        return get_commands()

    # IActions

    def get_actions(self):
        return {'most_visited_packages': logic.most_visited_packages}

    # ITranslation
    def i18n_directory(self):
        u'''Change the directory of the .mo translation files'''
        return os.path.join(
            os.path.dirname(ckanext.matomo.__file__),
            'i18n'
        )

class MatomoDatasetReport(plugins.SingletonPlugin):
    plugins.implements(IReport)

    # IReport
    def register_reports(self):
        from ckanext.matomo import reports
        return [reports.matomo_dataset_report_info()]

class MatomoResourceReport(plugins.SingletonPlugin):
    plugins.implements(IReport)

    # IReport
    def register_reports(self):
        from ckanext.matomo import reports
        return [reports.matomo_resource_report_info()]

class MatomoLocationReport(plugins.SingletonPlugin):
    plugins.implements(IReport)

    # IReport
    def register_reports(self):
        from ckanext.matomo import reports
        return [reports.matomo_location_report_info()]


class MatomoSearchTermsReport(plugins.SingletonPlugin):
    plugins.implements(IReport)

    # IReport
    def register_reports(self):
        from ckanext.matomo import reports
        return [reports.matomo_most_popular_search_terms_info()]
