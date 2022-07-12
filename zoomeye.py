import argparse
from asyncio.log import logger
import logging
from time import time
import requests
import time
import math
from datetime import date, datetime, timedelta
from ratelimit import limits

from zoomeye_test import do_request_test

class AggFields:
  COUNTRY = "country"
  SUBDIVSIONS = "subdivisions"
  CITY = "city"
  ORGANIZATION = "organization"
  OS = "os"

class Util:

  _MAX_TOTAL = 400

  def __GET_DATE_BY_YEAR_AND_DAYS(year, days):
    return (datetime(year, 1, 1) + timedelta(days=days)).strftime("%Y-%m-%d")

  def __init__(self, cube_authorization, endpoint="https://www.zoomeye.org") -> None:
    self._zoomeye = Zoomeye(cube_authorization, endpoint)
    pass

  def get_sites(self, params):
    params['pageSize'] = 50
    params['t'] = 'web'
    pages =  math.ceil(Util._MAX_TOTAL / 50)
    site_results = []
    for page in range(1, pages + 1): 
      params['page'] = page
      sites = [matche.get("site", matche.get("ip")) for matche in self._zoomeye.search(params)['matches']]
      site_results.extend(sites)
    return site_results

  def get_search_by_year(self, search_prefix):
    results = []
    for year_count in self._zoomeye.aggs(search_prefix, 'year')['year']:
      year = year_count['name']
      count = year_count['count']
      if count <= Util._MAX_TOTAL:
        result = search_prefix + "+ after:'%s-01-01' + before:'%s-01-01'" % (year, year + 1)
        results.append(result)
        continue
      days = (datetime.now().date() - datetime(year, 1, 1).date()).days
      searchs = [search_prefix + "+ after:'%s' + before:'%s'" % (Util.__GET_DATE_BY_YEAR_AND_DAYS(year, _ + 1), Util.__GET_DATE_BY_YEAR_AND_DAYS(year, _ + 2)) for _ in range(days)]
      results.extend(searchs)
    return list(set(results))

  def get_search(self, q, 
    aggs_targets = [
      "country",
      "subdivisions",
      "city"
      ]
    ):

    def to_query(target, value):
      if type(target) == str:
        return "%s: '%s'" % (target, value)
      elif type(target) == dict:
        return target['to_query'](value)

    def get_target_field(target):
      if type(target) == str:
        return target
      elif type(target) == dict:
        return target['field']

    search = []
    for target in aggs_targets:
      agg_target_field = get_target_field(target)
      agg_result = self._zoomeye.aggs(q, agg_target_field)
      logging.info("aggs_result: [%s] [%s] [%s]", q, target, agg_result)
      if agg_result['total'] <= Util._MAX_TOTAL:
        search.append(q)
      else:          
        for agg_result_item in agg_result[agg_target_field]:
          agg_result_item_count = agg_result_item['count']
          agg_result_item_name = agg_result_item['name']
          new_sub_q = q + " + " +  to_query(target, agg_result_item_name)
          if agg_result_item_count <= Util._MAX_TOTAL:
            search.append(new_sub_q)
          elif len(aggs_targets) <= 1:
            sub_querys = self.get_search_by_year(new_sub_q)
            search.extend(sub_querys)
          else:
            sub_querys = self.get_search(new_sub_q, aggs_targets[1:])
            search.extend(sub_querys)
        if len(agg_result[agg_target_field]) == 0:
          if len(aggs_targets) <= 1:
            sub_querys = self.get_search_by_year(q)
            search.extend(sub_querys)
            pass
          else:
            sub_querys = self.get_search(q, aggs_targets[1:])
            search.extend(sub_querys)
      return search            

class Zoomeye:

  #__ENDPOING = "https://www.zoomeye.org/"

  def __init__(self, cube_authorization, endpoint="https://www.zoomeye.org") -> None:
    self.__cube_auth = cube_authorization
    self.__endpoint = endpoint
    Zoomeye.__NEXT_REQUEST_TIME = 0
    pass
  
  def do_request(self, path, **kw):
    kw["url"] = "%s%s" % (self.__endpoint, path)
    headers = kw.get("headers", {})
    headers['Cube-Authorization'] = self.__cube_auth
    headers['user-agent'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36'
    kw['headers'] = headers
    resp_json = requests.request(**kw).json()
    if resp_json['status'] != 200:
      logging.warning("response_errp: [%s]", resp_json['status'])
    return resp_json

  #@limits(calls=1, period=1)
  def search(self, params):
    """
    curl 'https://www.zoomeye.org/search?q=app%253A%2527thinkphp%2527%2520%252Bcountry%253A%2520%2527%25E7%25A7%2598%25E9%25B2%2581%2527&page=1&pageSize=20&t=v4%2Bv6%2Bweb' \
  -H 'Accept: application/json, text/plain, */*' \
  -H 'Accept-Language: zh-CN,zh;q=0.9,en;q=0.8' \
  -H 'Connection: keep-alive' \
  -H 'Cookie: __jsluid_s=7a7cb0f7ad89491a97d372c914eb7258; SECKEY_ABVK=1cx7edtBXz4E1Mu7wa8Odu9qMHM4Nn6CPJCuc8RAZVA%3D; BMAP_SECKEY=_bLDC4kVZzDtCjdtwcTtALAAjBsujF4Wqo8xD0d7MGNaEhdvQyWeA1pUlB8uXQKBzzYndNSm0mNFSknjwPCRCmxccYYSNB8sOUa9iYXKmRfTgT_jsh73DQoSI4tde68ZpOgBiS6oZDdVyz4nbGFf1Sdu1QK6NelOo3ciGIQRjTIbJePaS-yKLGxhd8AXFJka; __cdnuid_s=bc0ab06b3c368f8d813017127f13a467' \
  -H 'Cube-Authorization: <AUTH>' \
  -H 'Referer: https://www.zoomeye.org/searchResult?q=app%3A%27thinkphp%27%20%2Bcountry%3A%20%27%E7%A7%98%E9%B2%81%27' \
  -H 'Sec-Fetch-Dest: empty' \
  -H 'Sec-Fetch-Mode: cors' \
  -H 'Sec-Fetch-Site: same-origin' \
  -H 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36' \
  -H 'sec-ch-ua: ".Not/A)Brand";v="99", "Google Chrome";v="103", "Chromium";v="103"' \
  -H 'sec-ch-ua-mobile: ?0' \
  -H 'sec-ch-ua-platform: "Windows"' \
  --compressed
    """
    #logging.info("search_params: [%s]", params)
    return self.do_request(
      path="/search",
      params=params,
      method="GET"
      )

  def validate_captcha(self, rnd, code):
    return self.do_request(
        path="/captcha/validate",
        params={
            "rnd": rnd,
            "code": code
        },
        method="GET"
    )

  def aggs(self, search, field):
    return self.do_request(
      path="/analysis/aggs",
      method="GET",
      params={
        "q": search,
        "field": field,
        "language": "zh"
      }
    )
# def get_urls():
#     curl 'https://www.zoomeye.org/analysis/aggs?language=zh&field=country&q=thinkphp%20%2Bnginx' \
#   -H 'Accept: application/json, text/plain, */*' \
#   -H 'Accept-Language: zh-CN,zh;q=0.9,en;q=0.8' \
#   -H 'Connection: keep-alive' \
#   -H 'Cookie: __jsluid_s=7a7cb0f7ad89491a97d372c914eb7258; SECKEY_ABVK=1cx7edtBXz4E1Mu7wa8OdtPQ5WbpNEGQvHmIFEwLM2g%3D; BMAP_SECKEY=_bLDC4kVZzDtCjdtwcTtALM5Qv5D_tVfsW0GzV9bzF9fZQQod-AvuyjDuWM77XlS90XfSCYYdxF0YabfE9VF_bIjZJsCCqoQu02E5Lb950t6NHUK9IhGyIcytQGeawwoyzUYk22Ac5m4Z99Eo86GB_cfug-q5_OwHUSFzt2merFKveIbpb6XCa9rddWaSyyg' \
#   -H 'Cube-Authorization: eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1c2VybmFtZSI6Im9tVkRTd216cXUwWUV4U1d3WWY1UkRrZGtHVmMiLCJlbWFpbCI6InloeWRldkAxNjMuY29tIiwiZXhwIjoxNjU3NjEzNDU1LjB9.wzjVixnHNHYyvChuJ5j41zCclZHaMEpcyovOi30Tips' \
#   -H 'If-None-Match: W/"44bc675065b803378e1bc72d75d7336532715c5c"' \
#   -H 'Referer: https://www.zoomeye.org/toolbar/aggregation' \
#   -H 'Sec-Fetch-Dest: empty' \
#   -H 'Sec-Fetch-Mode: cors' \
#   -H 'Sec-Fetch-Site: same-origin' \
#   -H 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36' \
#   -H 'sec-ch-ua: ".Not/A)Brand";v="99", "Google Chrome";v="103", "Chromium";v="103"' \
#   -H 'sec-ch-ua-mobile: ?0' \
#   -H 'sec-ch-ua-platform: "Windows"' \
#   --compressed

    
if __name__ == "__main__":
  import argparse
  ap = argparse.ArgumentParser()
  ap.add_argument('-q','--query', required=True)
