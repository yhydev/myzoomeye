from celery import Celery
from zoomeye import Zoomeye, ApiResponseException
import os
import time
import logging
from datetime import date, datetime, timedelta
import sites as mongo_sites
import math
_broker = os.environ['CELERY_BROKER']
_backend = os.environ.get('CELERY_BACKEND', None)
_auth = os.environ['ZOOMEYE_AUTH']
_app = Celery(broker=_broker, backend=_backend)
_zoomeye = Zoomeye(_auth)

logger = logging.getLogger(__name__)

_MAX_TOTAL = 400

def __GET_DATE_BY_YEAR_AND_DAYS(year, days):
    return (datetime(year, 1, 1) + timedelta(days=days)).strftime("%Y-%m-%d")

def __generate_date_query(after: datetime.date, before: datetime.date):
    return 'after:"%s" +before:"%s"' % (after.strftime("%Y-%m-%d"), before.strftime("%Y-%m-%d"))

def __generate_year_date_query(year):
    after = datetime(year, 1, 1).date()
    before = datetime(year + 1, 1, 1).date()
    return __generate_date_query(after, before)

def __generate_year_and_month_date_query(year, month):
    after = datetime(year, month, 1).date()
    if month == 12:
        before = datetime(year + 1, month, 1).date()
    else:
        before = datetime(year, month + 1, 1).date()
    return __generate_date_query(after, before)

@_app.task(name="zoomeye.generate_years_search")
def generate_years_search(search_prefix):
    for year_count in _zoomeye.aggs(search_prefix, 'year')['year']:
        year = year_count['name']
        count = year_count['count']
        if count <= _MAX_TOTAL:
            q = search_prefix + " +" + __generate_year_date_query(year)
            __start_search(q)
        else:
            for month in range(12):
                generate_month_search_by_year.delay(search_prefix, year, month + 1)
        
@_app.task(name="zoomeye.generate_month_search_by_year")
def generate_month_search_by_year(search_prefix, year, month):
    logging.info("generate_month_search_by_year: [%s %s %s]", search_prefix, year, month)
    q = search_prefix + " +" + __generate_year_and_month_date_query(year, month)
    for results in _zoomeye.aggs(q, 'year')['year']:
        count = results['count']
        if count <= _MAX_TOTAL:
            __start_search(q)
        else:
            first_day_of_month = datetime(year, month, 1).date()
            for days in range(1, 32):
                before = first_day_of_month + timedelta(days=days)
                if before.month != first_day_of_month.month and before.day != 1:
                    break
                after = before - timedelta(days=1)
                q = search_prefix + " +" + __generate_date_query(after, before)
                __run_search(q)


@_app.task(name="zoomeye.run_search", rate_limit="60/m", retry_kwargs={'max_retries': 10}, autoretry_for=[ApiResponseException])
def run_search(params):
    total = _zoomeye.aggs(params['q'], 'country')['total']
    if total != 0:
        start_search(params)


@_app.task(name="zoomeye.start_search", rate_limit='1/m', retry_kwargs={'max_retries': 10}, autoretry_for=[ApiResponseException])
def start_search(params):
    pageSize = params.get("pageSize", 50)
    params['pageSize'] = pageSize
    page = params.get("page", 1)
    params['page'] = page
    if page * pageSize > _MAX_TOTAL:
        logging.warning("invalid_search_page: %s", params)
        return
    logging.info("start_search: [%s]", params)
    result = _zoomeye.search(params)
    total = result['total']
    sites = [matche.get("site", matche.get("ip")) for matche in result['matches']]
    if len(sites) > 0:
        mongo_sites.save(params['q'], sites)
    else:
        real_total = _zoomeye.aggs(params['q'], 'country')['total']
        if total != real_total:
            logging.warning("search_result_empty: [%s]", params)
            if os.environ.get("SEARCH_RETRY", "true") != "false":
                logging.warning("search_retry: [%s]", params)
                start_search.delay(params)
        else:
            return
    if len(sites) == pageSize and math.ceil(total / pageSize) >= page + 1:
        params['page'] = page + 1
        start_search.delay(params)

def __start_search(q):
    start_search.delay({
        "q": q,
        "pageSize": 50,
        "page": 1
    })

def __run_search(q):
#    logging.info("run_search: [%s]", q)
    run_search.delay({
        "q": q,
        "pageSize": 50,
        "page": 1
    })

@_app.task(name="zoomeye.generate_search")
def generate_search(q,
                  aggs_targets=[
                       "country",
                      "subdivisions",
                      "city"
                      ]
                  ):

    def to_query(target, value):
        if type(target) == str:
            return '%s:"%s"' % (target, value)
        elif type(target) == dict:
            return target['to_query'](value)

    def get_target_field(target):
        if type(target) == str:
            return target
        elif type(target) == dict:
            return target['field']

    for target in aggs_targets:
        agg_target_field = get_target_field(target)
        agg_result = _zoomeye.aggs(q, agg_target_field)
        if agg_result['total'] <= _MAX_TOTAL:
            __run_search(q)
        else:
            for agg_result_item in agg_result[agg_target_field]:
                agg_result_item_count = agg_result_item['count']
                agg_result_item_name = agg_result_item['name']
                new_sub_q = q + " + " + to_query(target, agg_result_item_name)
                if agg_result_item_count <= _MAX_TOTAL:
                    __start_search(new_sub_q)
                elif len(aggs_targets) <= 1:
                    generate_years_search.delay(new_sub_q)
                else:
                    generate_search.delay(new_sub_q, aggs_targets[1:])
            if len(agg_result[agg_target_field]) == 0:
                if len(aggs_targets) <= 1:
                    generate_years_search.delay(q)
                else:
                    generate_search.delay(q, aggs_targets[1:])
