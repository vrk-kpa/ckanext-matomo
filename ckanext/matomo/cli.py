import click

from ckanext.matomo import commands


def get_commands():
    return [matomo]


@click.group()
def matomo():
    """Matomo related commands
    """
    pass


@matomo.command(
    u'fetch',
    help='Fetches data from Matomo to local database'
)
@click.option(u'--dryrun', is_flag=True, help="Prints what would be updated without making any changes.")
@click.option(u'--since', help="First date to fetch in YYYY-MM-DD format. Default: latest PackageStats entry date.")
@click.option(u'--until', help="Last date to fetch in YYYY-MM-DD format. Default: current date.")
@click.option(u'--dataset', required=False, help="Fetch analytics data for a single dataset")
def fetch(dryrun, since, until, dataset):
    commands.fetch(dryrun, since, until, dataset)


@matomo.command(
    u'init_db',
    help='Initializes analytics database tables'
)
def init_db():
    commands.init_db()
