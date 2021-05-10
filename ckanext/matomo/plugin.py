import queue
import logging

import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit
from ckanext.report.interfaces import IReport
from ckanext.matomo import helpers, tracking, reports
from flask import Blueprint

from routes.mapper import SubMapper

log = logging.getLogger(__name__)


class MatomoPlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.ITemplateHelpers)
    plugins.implements(plugins.IConfigurable)
    plugins.implements(plugins.IBlueprint)
    plugins.implements(plugins.IRoutes, inherit=True)
    plugins.implements(IReport)

    tracking_event_queue = queue.Queue()
    tracking_event_threads = []

    # IConfigurer

    def update_config(self, config_):
        toolkit.add_template_directory(config_, 'templates')
        toolkit.add_public_directory(config_, 'public')
        toolkit.add_resource('fanstatic', 'matomo')
        toolkit.add_resource('public/javascript/', 'ckanext-matomo_js')

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
            "matomo_snippet": helpers.matomo_snippet
        }

    # IRoutes
    # TODO: Port to flask like action tracking when resource_download is ported

    def before_map(self, map):
        with SubMapper(map, controller='ckanext.matomo.tracking:TrackedResourceController') as m:
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

    # IReport
    def register_reports(self):
        """Register details of an extension's reports"""
        return [reports.matomo_dataset_report_info,
                reports.matomo_resource_report_info,
                reports.matomo_location_report_info,
                reports.matomo_dataset_least_popular_report_info,
                reports.matomo_organizations_with_most_popular_datasets_info,
                reports.matomo_most_popular_search_terms_info]
