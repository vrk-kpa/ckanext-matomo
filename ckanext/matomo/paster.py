import click

from ckan.lib.cli import (
    load_config,
    paster_click_group,
    click_config_option,
)

from ckanext.matomo import commands

matomo = paster_click_group(
        summary=u'Matomo related commands')


@matomo.command(
    u'fetch',
    help='Fetches data from Matomo to local database'
)
@click_config_option
@click.pass_context
@click.option(u'--dryrun', is_flag=True, help="Prints what would be updated without making any changes.")
@click.option(u'--since', help="First date to fetch in YYYY-MM-DD format. Default: latest PackageStats entry date.")
@click.option(u'--until', help="Last date to fetch in YYYY-MM-DD format. Default: current date.")
def fetch(ctx, config, dryrun, since, until):
    load_config(config or ctx.obj['config'])
    commands.fetch(dryrun, since, until)


@matomo.command(
    u'init_db',
    help='Initializes analytics database tables'
)
@click_config_option
@click.pass_context
def init_db(ctx, config):
    load_config((config or ctx.obj['config']))
    commands.init_db()
