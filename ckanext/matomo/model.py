from datetime import date, datetime, timedelta
import json

from sqlalchemy import types, func, Column, ForeignKey, not_, desc
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

import ckan.model as model
from ckan.plugins.toolkit import config, aslist, get_action, ObjectNotFound


log = __import__('logging').getLogger(__name__)

Base = declarative_base()


# TODO: The package stats methods are a bit messed up, they could be organized better
# For example:
# visits, downloads, entrances on dataset (dates separated)
# - by time frame
# - in total
#
# Total visits, downloads, entrances by single dataset (dates combined)
# - On time frame
# - All time total
#
# And top / worst downloaded/visited/entered datasets
# - by timespan
# - in total
#
# and then the others: name by id, updating individual fields, get latest update
class PackageStats(Base):
    """
    Contains stats for package (datasets)
    Stores number of visits per all dates for each package.
    """
    __tablename__ = 'package_stats'

    package_id = Column(types.UnicodeText, nullable=False, index=True, primary_key=True)
    visit_date = Column(types.DateTime, default=datetime.now, primary_key=True)
    visits = Column(types.Integer, default=0)
    entrances = Column(types.Integer, default=0)
    downloads = Column(types.Integer, default=0)

    @classmethod
    def get(cls, id):
        return model.Session.query(cls).filter(cls.package_id == id).first()

    @classmethod
    def create_or_update(cls, package_id, visit_date, visits, entrances, downloads):
        '''
        Creates a new PackageStats or updates an existing one for the same package_id/visit_date
        :param package_id: package id
        :param visit_date: visit date to be updated
        :param visits: number of visits during date
        :param entrances: number of entrances during date
        :param downloads: number of downloads during date
        :return: True for a successful update, otherwise False
        '''
        package = (model.Session.query(cls)
                   .filter(cls.package_id == package_id)
                   .filter(cls.visit_date == visit_date)
                   .first())

        if package is None:
            package = PackageStats(package_id=package_id, visit_date=visit_date,
                                   visits=visits, entrances=entrances, downloads=downloads)
            model.Session.add(package)
        else:
            package.visits = visits
            package.entrances = entrances
            package.downloads = downloads

        model.Session.commit()
        log.debug("Number of visits and downloads for date: %s updated for package id: %s",
                  visit_date, package_id)
        model.Session.flush()
        return True

    @classmethod
    def update_visits(cls, item_id, visit_date, visits=0, entrances=0, downloads=0):
        '''
        Updates the number of visits for a certain package_id
        or creates a new one if it is the first visit for a certain date

        :param item_id: package_id
        :param visit_date: visit date to be updated
        :param visits: number of visits during date
        :param entrances: number of entrances during date
        :return: True for a successful update, otherwise False
        '''
        package = model.Session.query(cls).filter(cls.package_id == item_id).filter(cls.visit_date == visit_date).first()
        if package is None:
            package = PackageStats(package_id=item_id, visit_date=visit_date,
                                   visits=visits, entrances=entrances, downloads=downloads)
            model.Session.add(package)
        else:
            package.visits = visits
            package.entrances = entrances

        log.debug("Number of visits for date: %s updated for package id: %s", visit_date, item_id)
        model.Session.flush()
        return True

    @classmethod
    def update_downloads(cls, package_id, visit_date, downloads):
        '''
        Add's downloads amount to package, by adding downloads together.
        If package doesn't have any stats, adds stats object with empty visits and entrances
        '''
        package = model.Session.query(cls).filter(cls.package_id == package_id).filter(cls.visit_date == visit_date).first()
        if package is None:
            cls.update_visits(item_id=package_id, visit_date=visit_date, visits=0, entrances=0, downloads=downloads)
        else:
            package.downloads = downloads

        log.debug("Downloads updated for date: %s and packag: %s", visit_date, package_id)
        model.Session.flush()
        return True

    @classmethod
    def get_package_name_by_id(cls, package_id):
        package = model.Session.query(model.Package).filter(model.Package.id == package_id).first()
        pack_name = ""
        if package is not None:
            pack_name = package.title or package.name
        return pack_name

    @classmethod
    def get_visits(cls, start_date, end_date):
        '''
        Returns datasets and their visitors amount during time span, grouped by dates.

        :param start_date: Date
        :param end_date: Date
        :return: [{ visits, package_id, package_name, visit_date }, ...]
        '''
        package_visits = (model.Session.query(cls)
                          .join(model.Package, cls.package_id == model.Package.id)
                          .filter(model.Package.state == 'active')
                          .filter(model.Package.private == False)  # noqa: E712
                          .filter(cls.visit_date >= start_date)
                          .filter(cls.visit_date <= end_date)
                          .all())

        return cls.convert_to_dict(package_visits, None)

    @classmethod
    def get_total_visits(
        cls,
        start_date=date(2000, 1, 1),
        end_date=datetime.today(),
        limit=50,
        descending=True,
        package_id=None
    ):
        '''
        Returns datasets and their visitors amount summed during time span, grouped by dataset.

        :param start_date: Date
        :param end_date: Date
        :return: [{ visits, entrances, package_id, package_name }, ...]
        '''
        def sorting_direction(value, descending):
            if descending:
                return desc(value)
            else:
                return value

        query = model.Session.query(
            cls.package_id,
            func.sum(cls.visits).label('total_visits'),
            func.sum(cls.downloads).label('total_downloads'),
            func.sum(cls.entrances).label('total_entrances')
        )

        if package_id:
            query = query.filter(cls.package_id == package_id)

        visits_by_dataset = (query.join(model.Package, cls.package_id == model.Package.id)
                             .filter(model.Package.state == 'active')
                             .filter(model.Package.private == False)  # noqa: E712
                             .filter(cls.visit_date >= start_date)
                             .filter(cls.visit_date <= end_date)
                             .group_by(cls.package_id)
                             .order_by(sorting_direction(func.sum(cls.visits), descending))
                             .limit(limit)
                             .all())

        datasets = []
        for dataset in visits_by_dataset:
            datasets.append({
                "package_name": PackageStats.get_package_name_by_id(dataset.package_id),
                "package_id": dataset.package_id,
                "visits": dataset.total_visits,
                "entrances": dataset.total_entrances,
                "downloads": dataset.total_downloads,
            })

        return datasets

    # Same as above, but uses organization to filter datasets belonging to only that organization
    @classmethod
    def get_total_visits_for_organization(
        cls,
        organization,
        start_date=date(2000, 1, 1),
        end_date=datetime.today(),
        limit=50,
        descending=True,
        package_id=None
    ):

        '''
        Returns datasets and their visitors amount summed during time span, grouped by dataset.

        :param start_date: Date
        :param end_date: Date
        :return: [{ visits, entrances, package_id, package_name }, ...]
        '''
        def sorting_direction(value, descending):
            if descending:
                return desc(value)
            else:
                return value

        query = model.Session.query(
            cls.package_id,
            func.sum(cls.visits).label('total_visits'),
            func.sum(cls.downloads).label('total_downloads'),
            func.sum(cls.entrances).label('total_entrances')
        )

        if package_id:
            query = query.filter(cls.package_id == package_id)

        visits_by_dataset = (query.join(model.Package, cls.package_id == model.Package.id)
                             .filter(model.Package.state == 'active')
                             .filter(model.Package.private == False)  # noqa: E712
                             .filter(model.Package.owner_org == organization)
                             .filter(cls.visit_date >= start_date)
                             .filter(cls.visit_date <= end_date)
                             .group_by(cls.package_id)
                             .order_by(sorting_direction(func.sum(cls.visits), descending))
                             .limit(limit)
                             .all())

        datasets = []
        for dataset in visits_by_dataset:
            datasets.append({
                "package_name": PackageStats.get_package_name_by_id(dataset.package_id),
                "package_id": dataset.package_id,
                "visits": dataset.total_visits,
                "entrances": dataset.total_entrances,
                "downloads": dataset.total_downloads,
            })

        return datasets

    @classmethod
    def get_visits_during_year(cls, resource_id, year):
        '''
        Returns number of visitors during one calendar yearself.
        For example, calling this with parameter year=2017 would returned
        the number of visitors during the year 2017.

        :param resource_id: ID of the resource
        :param year: Year as an integer
        :return: Number of visitors during the year
        '''
        start_date = datetime(year, 1, 1)
        end_date = datetime(year, 12, 31)
        package_visits = model.Session.query(cls).filter(cls.package_id == resource_id) \
            .filter(cls.visit_date >= start_date) \
            .filter(cls.visit_date <= end_date) \
            .all()

        return package_visits

    @classmethod
    def get_last_visits_by_id(cls, package_id, num_days=365):
        end_of_period = datetime.now()
        beginning_of_period = get_beginning_of_next_week(end_of_period - timedelta(days=num_days))

        package_visits = model.Session.query(cls).filter(cls.package_id == package_id).filter(
            cls.visit_date >= beginning_of_period).filter(cls.visit_date <= end_of_period).all()
        # Returns the total number of visits since the beginning of all times
        total_visits = model.Session.query(func.sum(cls.visits)).filter(cls.package_id == package_id).scalar()
        visits = {}

        if total_visits is not None:
            visits = PackageStats.convert_to_dict(package_visits, total_visits)

        total_downloads = model.Session.query(func.sum(cls.downloads)).filter(cls.package_id == package_id).scalar()
        visits['total_downloads'] = total_downloads if total_downloads else 0

        return visits

    @classmethod
    def get_visit_count_for_dataset_during_last_12_months(cls, package_id):
        from dateutil.relativedelta import relativedelta

        # Returns a list of visits during the last 12 months.
        first_day = datetime.now() - relativedelta(months=12)
        last_day = datetime.now()

        visits = cls.get_visits_by_dataset_id_between_two_dates(package_id, first_day, last_day)

        return sum(filter(None, [visit.__dict__.get('visits', 0) for visit in visits]))

    @classmethod
    def get_visit_count_for_dataset_during_last_30_days(cls, package_id):
        from dateutil.relativedelta import relativedelta

        # Returns a list of visits during the last 30 days.
        first_day = datetime.now() - relativedelta(days=30)
        last_day = datetime.now()

        visits = cls.get_visits_by_dataset_id_between_two_dates(package_id, first_day, last_day)

        return sum(filter(None, [visit.__dict__.get('visits', 0) for visit in visits]))

    @classmethod
    def get_visits_by_dataset_id_between_two_dates(cls, package_id, start_date, end_date):
        # Returns a list of visits between the dates
        visits = model.Session.query(cls).filter(cls.package_id == package_id).filter(cls.visit_date >= start_date).filter(
            cls.visit_date <= end_date).all()
        return visits

    @classmethod
    def get_top(cls, limit=20, start_date=None, end_date=None, dataset_type='dataset'):
        package_stats = []
        # TODO: Reimplement in more efficient manner if needed (using RANK OVER and PARTITION in raw sql)
        unique_packages = (model.Session.query(cls.package_id,
                                               func.count(cls.visits),
                                               func.count(cls.entrances),
                                               func.count(cls.downloads))
                           .filter(cls.package_id == model.Package.id)
                           .filter(model.Package.state == 'active')
                           .filter(model.Package.private == False)  # noqa: E712
                           .filter(model.Package.type == dataset_type)
                           .group_by(cls.package_id))

        if start_date:
            unique_packages = unique_packages.filter(cls.visit_date >= start_date)
        if end_date:
            unique_packages = unique_packages.filter(cls.visit_date <= end_date)

        unique_packages = unique_packages.order_by(func.count(cls.visits).desc()).limit(limit).all()

        # Adding last date associated to this package stat and filtering out private and deleted packages
        if unique_packages is not None:
            for package in unique_packages:
                package_id = package[0]
                visits = package[1]

                tot_package = model.Session.query(model.Package).filter(model.Package.id == package_id).filter_by(
                    state='active').filter_by(private=False).first()
                if tot_package is None:
                    continue

                last_date = model.Session.query(func.max(cls.visit_date)).filter(cls.package_id == package_id).first()

                ps = PackageStats(package_id=package_id,
                                  visit_date=last_date[0], visits=visits, entrances=package[2], downloads=package[3])
                package_stats.append(ps)
        dictat = PackageStats.convert_to_dict(package_stats, None)
        return dictat

    @classmethod
    def get_all_visits(cls, dataset_id):

        visits_dict = PackageStats.get_last_visits_by_id(dataset_id)

        visit_list = []
        visits = visits_dict.get('packages', [])
        count = visits_dict.get('tot_visits', 0)

        # Creates a weekly grouped list for last year
        current_end_of_week = get_end_of_last_week(datetime.now())
        start_date = get_beginning_of_next_week(current_end_of_week.replace(hour=0, minute=0, second=0, microsecond=0)
                                                - timedelta(days=365))

        while current_end_of_week > start_date:
            current_start_of_week = get_beginning_of_week(current_end_of_week)
            weekly_download_count = 0
            weekly_visit_count = 0
            for visit in visits:
                visit_date = datetime.strptime(visit.get('visit_date'), '%d-%m-%Y')
                # Do nothing if date of visit isn't in period of current week
                if visit_date < current_start_of_week or visit_date > current_end_of_week:
                    continue
                weekly_download_count += visit.get('downloads', 0)
                weekly_visit_count += visit.get('visits', 0)

            visit_list.append({'year': current_end_of_week.year, 'week': current_end_of_week.isocalendar()[1],
                               'visits': weekly_visit_count, 'downloads': weekly_download_count})
            current_end_of_week = current_end_of_week - timedelta(weeks=1)

        # Revert visit list to make it end on previous week
        visit_list = visit_list[::-1]

        results = {
            "visits": visit_list,
            "count": count,
            "download_count": visits_dict['total_downloads']
        }
        return results

    @classmethod
    def as_dict(cls, pkg):
        result = {}
        package_name = PackageStats.get_package_name_by_id(pkg.package_id)
        result['package_name'] = package_name
        result['package_id'] = pkg.package_id
        result['visits'] = pkg.visits
        result['entrances'] = pkg.entrances
        result['downloads'] = pkg.downloads
        result['visit_date'] = pkg.visit_date.strftime("%d-%m-%Y")
        return result

    @classmethod
    def convert_to_dict(cls, package_stats, tot_visits):
        visits = []
        for pkg in package_stats:
            visits.append(PackageStats.as_dict(pkg))

        results = {
            "packages": visits,
        }
        if tot_visits is not None:
            results["tot_visits"] = tot_visits
        return results

    @classmethod
    def get_latest_update_date(cls):
        result = model.Session.query(cls).order_by(cls.visit_date.desc()).first()
        if result is None:
            return None
        else:
            return result.visit_date

    @classmethod
    def get_organization(cls, dataset_name):
        try:
            package = get_action('package_show')({}, {'id': dataset_name})
            if package.get('organization'):
                return package.get('organization').get('name')
            else:
                return None
        except ObjectNotFound:
            return None

    @classmethod
    def get_organizations_with_most_popular_datasets(cls, start_date, end_date, limit=20):
        all_packages_result = cls.get_total_visits(start_date, end_date, limit=None)
        organization_stats = {}
        for package in all_packages_result:
            package_id = package["package_id"]
            visits = package["visits"]
            downloads = package["downloads"]
            entrances = package["entrances"]

            organization_name = cls.get_organization(package_id)
            if organization_name:
                if (organization_name in organization_stats):
                    organization_stats[organization_name]["visits"] += visits
                    organization_stats[organization_name]["downloads"] += downloads
                    organization_stats[organization_name]["entrances"] += entrances
                else:
                    organization_stats[organization_name] = {
                        "visits": visits,
                        "downloads": downloads,
                        "entrances": entrances
                    }

        organization_list = []
        for organization_name, stats in organization_stats.items():
            organization_list.append(
                {"organization_name": organization_name,
                 "total_visits": stats["visits"],
                 "total_downloads": stats["downloads"],
                 "total_entrances": stats["entrances"]
                 }
            )

        return sorted(organization_list, key=lambda organization: organization["total_visits"], reverse=True)[:limit]


class ResourceStats(Base):
    """
    Contains stats for resources associated to a certain dataset/package
    Stores number of visits i.e. downloads per all dates for each package.
    """
    __tablename__ = 'resource_stats'

    resource_id = Column(types.UnicodeText, nullable=False, index=True, primary_key=True)
    visit_date = Column(types.DateTime, default=datetime.now, primary_key=True)
    visits = Column(types.Integer, default=0)
    downloads = Column(types.Integer, default=0)

    @classmethod
    def get(cls, id):
        return model.Session.query(cls).filter(cls.resource_id == id).first()

    @classmethod
    def update_visits(cls, item_id, visit_date, visits):
        '''
        Updates the number of visits for a certain resource_id

        :param item_id: resource_id
        :param visit_date: last visit date
        :param visits: number of visits until visit_date
        :return: True for a successful update, otherwise False
        '''
        resource = model.Session.query(cls).filter(cls.resource_id == item_id).filter(cls.visit_date == visit_date).first()
        if resource is None:
            resource = ResourceStats(resource_id=item_id, visit_date=visit_date, visits=visits)
            model.Session.add(resource)
        else:
            resource.visits = visits
            resource.visit_date = visit_date

        model.Session.commit()
        log.debug("Number of visits updated for resource id: %s", item_id)
        model.Session.flush()
        return True

    @classmethod
    def update_downloads(cls, item_id, visit_date, downloads):
        '''
        Updates the number of downloads for a certain resource_id

        :param item_id: resource_id
        :param visit_date: last visit date
        :param downloads: number of downloads until visit_date
        :return: True for a successful update, otherwise False
        '''
        resource = model.Session.query(cls).filter(cls.resource_id == item_id).filter(cls.visit_date == visit_date).first()
        if resource is None:
            resource = ResourceStats(resource_id=item_id, visit_date=visit_date, downloads=downloads)
            model.Session.add(resource)
        else:
            resource.downloads = downloads
            resource.visit_date = visit_date

        model.Session.commit()
        log.debug("Number of downloads updated for resource id: %s", item_id)
        model.Session.flush()
        return True

    @classmethod
    def get_resource_info_by_id(cls, resource_id):
        resource = model.Session.query(model.Resource).filter(model.Resource.id == resource_id).first()
        res_name = None
        res_package_name = None
        res_package_id = None

        if resource is not None:
            res_package_name = resource.package.title or resource.package.name
            res_package_id = resource.package.name

            name_translated_json = resource.extras.get('name_translated')
            if name_translated_json is not None:
                try:
                    name_translated = json.loads(name_translated_json)
                    languages = aslist(config.get('ckan.locales_offered', []))
                    res_name = next((name_translated[lang] for lang in languages
                                     if name_translated.get(lang)), None)
                except json.JSONDecodeError:
                    pass

            res_name = res_name or resource.description or resource.format

        return [res_name, res_package_name, res_package_id]

    @classmethod
    def get_last_visits_by_id(cls, resource_id, num_days=30):
        start_date = datetime.now() - timedelta(num_days)
        resource_visits = model.Session.query(cls).filter(cls.resource_id == resource_id).filter(
            cls.visit_date >= start_date).all()
        # Returns the total number of visits since the beggining of all times
        total_visits = model.Session.query(func.sum(cls.visits)).filter(cls.resource_id == resource_id).scalar()
        total_downloads = model.Session.query(func.sum(cls.downloads)).filter(cls.resource_id == resource_id).scalar()
        visits = {}
        if total_visits is not None or total_downloads is not None:
            visits = ResourceStats.convert_to_dict(resource_visits, total_visits, total_downloads)
        return visits

    @classmethod
    def get_top(cls, limit=20):
        resource_stats = []
        # TODO: Reimplement in more efficient manner if needed (using RANK OVER and PARTITION in raw sql)
        unique_resources = model.Session.query(cls.resource_id, func.count(cls.visits), func.sum(cls.downloads)).group_by(
            cls.resource_id).order_by(func.sum(cls.downloads).desc()).having(func.sum(cls.downloads) > 0).join(
                model.Resource, model.Resource.id == cls.resource_id).limit(limit).all()
        # Adding last date associated to this package stat and filtering out private and deleted packages
        if unique_resources is not None:
            for resource in unique_resources:
                resource_id = resource[0]
                visits = resource[1]
                downloads = resource[2]
                # TODO: Check if associated resource is private
                resource = model.Session.query(model.Resource).filter(model.Resource.id == resource_id).filter_by(
                    state='active').first()
                if resource is None:
                    continue

                last_date = model.Session.query(func.max(cls.visit_date)).filter(cls.resource_id == resource_id).first()

                rs = ResourceStats(resource_id=resource_id, visit_date=last_date[0], visits=visits, downloads=downloads)
                resource_stats.append(rs)
        dictat = ResourceStats.convert_to_dict(resource_stats, None, None)
        return dictat

    @classmethod
    def as_dict(cls, res):
        result = {}
        res_info = ResourceStats.get_resource_info_by_id(res.resource_id)
        result['resource_name'] = res_info[0]
        result['resource_id'] = res.resource_id
        result['package_name'] = res_info[1]
        result['package_id'] = res_info[2]
        result['visits'] = res.visits
        result['downloads'] = res.downloads
        result['visit_date'] = res.visit_date.strftime("%d-%m-%Y")
        return result

    @classmethod
    def convert_to_dict(cls, resource_stats, tot_visits, total_downloads):
        visits = []
        for resource in resource_stats:
            visits.append(ResourceStats.as_dict(resource))

        results = {
            "resources": visits
        }
        if tot_visits is not None:
            results['tot_visits'] = tot_visits

        if total_downloads is not None:
            results['total_downloads'] = total_downloads

        return results

    @classmethod
    def get_last_visits_by_url(cls, url, num_days=30):
        resource = model.Session.query(model.Resource).filter(model.Resource.url == url).first()
        start_date = datetime.now() - timedelta(num_days)
        # Returns the total number of visits since the beggining of all times for the associated resource to the given url
        total_visits = model.Session.query(func.sum(cls.visits)).filter(cls.resource_id == resource.id).first().scalar()
        resource_stats = model.Session.query(cls).filter(cls.resource_id == resource.id).filter(
            cls.visit_date >= start_date).all()
        visits = ResourceStats.convert_to_dict(resource_stats, total_visits)

        return visits

    @classmethod
    def get_last_visits_by_dataset_id(cls, package_id, num_days=30):
        # Fetch all resources associated to this package id
        subquery = model.Session.query(model.Resource.id).filter(model.Resource.package_id == package_id).subquery()

        start_date = datetime.now() - timedelta(num_days)
        resource_stats = model.Session.query(cls).filter(cls.resource_id.in_(subquery)).filter(
            cls.visit_date >= start_date).all()
        total_visits = model.Session.query(func.sum(cls.visits)).filter(cls.resource_id.in_(subquery)).scalar()
        visits = ResourceStats.convert_to_dict(resource_stats, total_visits)

        return visits

    @classmethod
    def get_visits_during_last_calendar_year_by_dataset_id(cls, package_id):
        # Returns a list of visits during the last calendar year.
        last_year = datetime.now().year - 1
        first_day = datetime(year=last_year, day=1, month=1)
        last_day = datetime(year=last_year, day=31, month=12)
        return cls.get_visits_by_dataset_id_between_two_dates(package_id, first_day, last_day)

    @classmethod
    def get_download_count_for_dataset_during_last_12_months(cls, package_id):
        from dateutil.relativedelta import relativedelta

        # Returns a list of visits during the last 12 months.
        first_day = datetime.now() - relativedelta(months=12)
        last_day = datetime.now()

        visits = cls.get_visits_by_dataset_id_between_two_dates(package_id, first_day, last_day)

        return sum(filter(None, [visit.__dict__.get('downloads', 0) for visit in visits]))

    @classmethod
    def get_download_count_for_dataset_during_last_30_days(cls, package_id):
        from dateutil.relativedelta import relativedelta

        # Returns a list of visits during the last 30 days.
        first_day = datetime.now() - relativedelta(days=30)
        last_day = datetime.now()

        visits = cls.get_visits_by_dataset_id_between_two_dates(package_id, first_day, last_day)

        return sum(filter(None, [visit.__dict__.get('downloads', 0) for visit in visits]))

    @classmethod
    def get_visits_by_dataset_id_between_two_dates(cls, package_id, start_date, end_date):
        # Returns a list of visits between the dates
        subquery = model.Session.query(model.Resource.id).filter(model.Resource.package_id == package_id).subquery()
        visits = model.Session.query(cls).filter(cls.resource_id.in_(subquery)).filter(cls.visit_date >= start_date).filter(
            cls.visit_date <= end_date).all()
        return visits

    @classmethod
    def get_all_visits(cls, id):
        visits_dict = ResourceStats.get_last_visits_by_id(id)
        downloads_count = visits_dict.get('total_downloads', 0)
        visits_count = visits_dict.get('tot_visits', 0)
        visits = visits_dict.get('resources', [])
        visit_list = []

        # Creates a weekly grouped list for last year
        current_end_of_week = get_end_of_last_week(datetime.now())
        start_date = get_beginning_of_next_week(current_end_of_week.replace(hour=0, minute=0, second=0, microsecond=0)
                                                - timedelta(days=365))

        while current_end_of_week > start_date:
            current_start_of_week = get_beginning_of_week(current_end_of_week)
            weekly_download_count = 0
            weekly_visit_count = 0
            for visit in visits:
                visit_date = datetime.strptime(visit.get('visit_date'), '%d-%m-%Y')
                # Do nothing if date of visit isn't in period of current week
                if visit_date < current_start_of_week or visit_date > current_end_of_week:
                    continue

                if visit.get('downloads', 0) is not None:
                    weekly_download_count += visit.get('downloads', 0)
                if visit.get('visits', 0) is not None:
                    weekly_visit_count += visit.get('visits', 0)

            visit_list.append({'year': current_end_of_week.year, 'week': current_end_of_week.isocalendar()[1],
                               'visits': weekly_visit_count, 'downloads': weekly_download_count})
            current_end_of_week = current_end_of_week - timedelta(weeks=1)

        # Revert visit list to make it end on previous week
        visit_list = visit_list[::-1]

        results = {
            "downloads": visit_list,
            "downloads_count": downloads_count,
            "visits_count": visits_count,
        }
        return results

    @classmethod
    def get_latest_update_date(cls):
        result = model.Session.query(cls).order_by(cls.visit_date.desc()).first()
        if result is None:
            return None
        else:
            return result.visit_date

    @classmethod
    def get_visit_count_for_resource_during_last_12_months(cls, resource_id):
        from dateutil.relativedelta import relativedelta

        first_day = datetime.now() - relativedelta(months=12)
        last_day = datetime.now()

        visits = cls.get_visits_by_resource_id_between_two_dates(resource_id, first_day, last_day)

        return sum(filter(None, [visit.__dict__.get('visits', 0) for visit in visits]))

    @classmethod
    def get_visit_count_for_resource_during_last_30_days(cls, resource_id):
        from dateutil.relativedelta import relativedelta

        first_day = datetime.now() - relativedelta(days=30)
        last_day = datetime.now()

        visits = cls.get_visits_by_resource_id_between_two_dates(resource_id, first_day, last_day)

        return sum(filter(None, [visit.__dict__.get('visits', 0) for visit in visits]))

    @classmethod
    def get_download_count_for_resource_during_last_12_months(cls, resource_id):
        from dateutil.relativedelta import relativedelta

        first_day = datetime.now() - relativedelta(months=12)
        last_day = datetime.now()

        visits = cls.get_visits_by_resource_id_between_two_dates(resource_id, first_day, last_day)

        return sum(filter(None, [visit.__dict__.get('downloads', 0) for visit in visits]))

    @classmethod
    def get_download_count_for_resource_during_last_30_days(cls, resource_id):
        from dateutil.relativedelta import relativedelta

        first_day = datetime.now() - relativedelta(days=30)
        last_day = datetime.now()

        visits = cls.get_visits_by_resource_id_between_two_dates(resource_id, first_day, last_day)

        return sum(filter(None, [visit.__dict__.get('downloads', 0) for visit in visits]))

    @classmethod
    def get_visits_by_resource_id_between_two_dates(cls, resource_id, start_date, end_date):
        # Returns a list of visits between the dates
        visits = model.Session.query(cls).filter(cls.resource_id == resource_id).filter(cls.visit_date >= start_date).filter(
            cls.visit_date <= end_date).all()
        return visits


class AudienceLocation(Base):
    """
    Contains stats for different visitors locations
    Stores all different countries.
    """
    __tablename__ = 'audience_location'

    id = Column(types.Integer, primary_key=True, autoincrement=True, unique=True)
    location_name = Column(types.UnicodeText, nullable=False, primary_key=True)

    visits_by_date = relationship("AudienceLocationDate", back_populates="location")

    @classmethod
    def get(cls, id):
        return model.Session.query(cls).filter(cls.id == id).first()

    @classmethod
    def update_location(cls, location_name):
        # Check if the location can be found
        location = model.Session.query(cls).filter(cls.location_name == location_name)
        if location is None:
            # Add location if not in db
            location = AudienceLocation(location_name=location_name)
            model.Session.add(location)
            log.debug("New location added: %s", location_name)
        else:
            location.location_name = location_name
            log.debug("Location name updated: %s", location_name)

        model.Session.flush()
        return True


class AudienceLocationDate(Base):
    """
    Contains stats for different visitors locations by date
    Maps user amounts to dates and locations
    """
    __tablename__ = 'audience_location_date'

    id = Column(types.Integer, primary_key=True, autoincrement=True, unique=True)
    date = Column(types.DateTime, default=datetime.now, primary_key=True)

    visits = Column(types.Integer, default=0)
    location_id = Column(types.Integer, ForeignKey('audience_location.id'))

    location = relationship("AudienceLocation", back_populates="visits_by_date")

    @classmethod
    def update_visits(cls, location_name, visit_date, visits):
        '''
        Updates the number of visits for a certain date and location

        :param location_name: location_name
        :param date: last visit date
        :param visits: number of visits until visit_date
        :return: True for a successful update, otherwise False
        '''
        # find location_id by name
        location = model.Session.query(AudienceLocation).filter(AudienceLocation.location_name == location_name).first()

        # if not found add location as new location
        if location is None:
            location = AudienceLocation(location_name=location_name)
            model.Session.add(location)
            model.Session.commit()

        # find if location already has views for that date
        location_by_date = model.Session.query(cls).filter(cls.location_id == location.id).filter(
            cls.date == visit_date).first()
        # if not add them as a new row
        if location_by_date is None:
            location_by_date = AudienceLocationDate(location_id=location.id, date=visit_date, visits=visits)
            model.Session.add(location_by_date)
        else:
            location_by_date.visits = visits

        log.debug("Number of visits updated for location %s" % location_name)
        model.Session.flush()
        return True

    @classmethod
    def get_visits(cls, start_date, end_date):
        '''
        Get all visits items between selected dates
        grouped by date

        returns list of dicst like:
        [
            {
                location_name
                date
                visits
            }
        ]
        '''
        data = model.Session.query(cls.visits, cls.date, cls.location_id) \
            .filter(cls.date >= start_date) \
            .filter(cls.date <= end_date) \
            .order_by(cls.date.desc()) \
            .all()

        return cls.convert_list_to_dicts(data)

    @classmethod
    def get_first_date(cls, start_date=None, end_date=None):
        query = model.Session.query(func.min(cls.date))
        if start_date is not None:
            query = query.filter(cls.date >= start_date)
        if end_date is not None:
            query = query.filter(cls.date <= end_date)
        result = query.one_or_none()
        return result[0] if result is not None else None

    @classmethod
    def get_total_visits(cls, start_date=None, end_date=None):
        '''
        Returns the total amount of visits on the website
        from the start date to the end date

        return dict like:
        {
            total_visits
        }
        '''
        total_visits = model.Session.query(func.sum(cls.visits))

        if start_date is not None:
            total_visits = total_visits.filter(cls.date >= start_date)
        if end_date is not None:
            total_visits = total_visits.filter(cls.date <= end_date)

        return {"total_visits": total_visits.scalar()}

    @classmethod
    def get_total_visits_by_location(cls, start_date, end_date, location_name):
        '''
        Returns amount of visits in the location
        from start_date to end_date

        ! in the beginning of location_name works as NOT

        !Finland = not Finland
        returns everything that is not Finland

        returns list of dicst like:
        [
            {
                location_name
                total_visits
            }
        ]
        '''

        negate = False
        if location_name.startswith('!'):
            location_name = location_name[1:]
            negate = True

        location_id = cls.get_location_id_by_name(location_name)
        if location_id:
            total_visits = model.Session.query(func.sum(cls.visits))\
                .filter(maybe_negate(cls.location_id, location_id, negate)) \
                .filter(cls.date >= start_date) \
                .filter(cls.date <= end_date) \
                .scalar()
        else:
            total_visits = 0

        return {"total_visits": total_visits}

    @classmethod
    def get_total_top_locations(cls, limit=20):
        '''
        Locations sorted by total visits

        returns list of dicts like:
        [
            {
                location_name
                total_visits
            }
        ]
        '''
        locations = model.Session.query(cls.location_id, func.sum(cls.visits).label('total_visits')) \
            .group_by(cls.location_id) \
            .order_by(func.sum(cls.visits).desc()) \
            .limit(limit) \
            .all()

        result = cls.convert_list_to_dicts(locations)
        all_visits = AudienceLocationDate.get_total_visits().get('total_visits', 0) or 0
        result.append({
            'location_name': 'Other',
            'total_visits': all_visits - sum(x.get('total_visits', 0) for x in result)
        })

        for r in result:
            if all_visits != 0:
                r['percent_visits'] = 100.0 * r.get('total_visits', 0.0) / all_visits
            else:
                r['percent_visits'] = 0.0

        return result

    @classmethod
    def special_total_location_to_rest(cls, start_date, end_date, location):
        location_details = cls.get_total_visits_by_location(start_date, end_date, location)
        location_details['location_name'] = location
        rest = cls.get_total_visits_by_location(start_date, end_date, '!' + location)
        rest['location_name'] = 'Other'

        return [
            location_details,
            rest,
        ]

    @classmethod
    def special_total_by_months(cls, start_date=None, end_date=None):
        if end_date is None:
            # last day of last month
            end_date = datetime.today().replace(day=1) - timedelta(days=1)
        if start_date is None:
            start_date = end_date - timedelta(days=365)  # one year

        visits = cls.get_visits(start_date=start_date, end_date=end_date)

        unique_months = []
        results = []

        for item in visits:
            combined_date = str(item['date'].month) + '-' + str(item['date'].year)
            if combined_date in unique_months:
                for x in results:
                    if x['combined_date'] == combined_date:
                        x['visits'] += item['visits']
            else:
                unique_months.append(combined_date)
                results.append({'combined_date': combined_date, 'date': item['date'].__str__(), 'visits': item['visits']})

        results.sort(key=lambda x: x['date'])

        return results

    @classmethod
    def get_location_name_by_id(cls, location_id):
        location = model.Session.query(AudienceLocation).filter(AudienceLocation.id == location_id).first()
        return location.location_name

    @classmethod
    def get_location_id_by_name(cls, location_name):
        location = model.Session.query(AudienceLocation).filter(AudienceLocation.location_name == location_name).first()
        location_id = []
        if location is not None:
            location_id = location.id
        return location_id

    @classmethod
    def get_latest_update_date(cls):
        result = model.Session.query(cls).order_by(cls.date.desc()).first()
        if result is None:
            return None
        else:
            return result.date

    @classmethod
    def as_dict(cls, location):
        result = {}
        tmp_dict = location._asdict()
        location_name = cls.get_location_name_by_id(tmp_dict['location_id'])
        if location_name:
            result['location_name'] = location_name
        if 'date' in tmp_dict:
            result['date'] = tmp_dict['date']
        if 'visits' in tmp_dict:
            result['visits'] = tmp_dict['visits']
        if 'total_visits' in tmp_dict:
            result['total_visits'] = tmp_dict['total_visits']
        return result

    @classmethod
    def convert_list_to_dicts(cls, location_stats):
        visits = []
        for location in location_stats:
            visits.append(AudienceLocationDate.as_dict(location))

        return visits


class SearchStats(Base):
    """
    Contains stats for search terms
    """
    __tablename__ = 'search_terms'

    id = Column(types.Integer, primary_key=True, autoincrement=True, unique=True)
    search_term = Column(types.UnicodeText, nullable=False, primary_key=True)
    date = Column(types.DateTime, default=datetime.now, primary_key=True)
    count = Column(types.Integer, default=0)

    @classmethod
    def get(cls, id):
        return model.Session.query(cls).filter(cls.id == id).first()

    @classmethod
    def get_latest_update_date(cls):
        result = model.Session.query(cls).order_by(cls.date.desc()).first()
        if result is None:
            return None
        else:
            return result.date

    @classmethod
    def update_search_term_count(cls, search_term, date, count):
        '''
        Updates the search term search count

        :param search_term: Search term used in site internal search
        :param count: Number of times the search term was searched
        :return: True for a successful update, otherwise False
        '''
        model.Session.add(SearchStats(search_term=search_term, date=date, count=count))
        model.Session.commit()
        model.Session.flush()
        return True

    @classmethod
    def get_most_popular_search_terms(cls, start_date, end_date, limit=20):
        results = model.Session.query(cls).filter(cls.date >= start_date).filter(cls.date <= end_date).all()
        search_term_counts = {}
        for result in results:
            if result.search_term in search_term_counts:
                search_term_counts[result.search_term]['count'] += result.count
            else:
                search_term_counts[result.search_term] = {'count': result.count}

        search_term_list = []
        for search_term, search_term_info in search_term_counts.items():
            search_term_list.append(
                {"search_term": search_term,
                 "count": search_term_info['count']
                 }
            )

        return sorted(search_term_list, key=lambda search_term: search_term["count"], reverse=True)[:limit]


def maybe_negate(value, inputvalue, negate=False):
    if negate:
        return not_(value == inputvalue)
    return (value == inputvalue)


def init_tables(engine):
    Base.metadata.create_all(engine)
    log.info('Analytics database tables are set-up')


def get_beginning_of_week(date):
    date = date.replace(hour=0, minute=0, second=0, microsecond=0)
    date = date - timedelta(days=date.weekday())
    return date


def get_end_of_week(date):
    date = date.replace(hour=23, minute=59, second=59, microsecond=999999)
    date = date + timedelta(days=6 - date.weekday())
    return date


def get_beginning_of_next_week(date):
    date = get_beginning_of_week(date)
    date = date + timedelta(weeks=1)
    return date


def get_end_of_last_week(date):
    date = get_end_of_week(date)
    date = date - timedelta(weeks=1)
    return date
