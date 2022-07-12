import zoomeye
import logging


__AUTH = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1c2VybmFtZSI6IjMxOTE2NDgzIiwiZW1haWwiOiJOb25lIiwiZXhwIjoxNjU3NzIwNTcwLjB9.15dR57C9TEqZq4afo1aHxyphc-pwXhNEmJn6sey2v6A"

def do_request_test():
    zeye = zoomeye.Zoomeye(
        __AUTH,
        "http://httpbin.org"
    )
    resp_json = zeye.do_request(path="/anything", params={"c":"d"}, method="GET").json()
    logging.info("resp_json: [%s]", resp_json)

def aggs_test():
    zeye = zoomeye.Zoomeye(
        __AUTH,
        "https://www.zoomeye.org"
    )
    result = zeye.aggs("app:thinkphp", zoomeye.AggFields.COUNTRY)
    logging.info("agg_result: [%s]", result)

def util_get_search_test():
    result = zoomeye.Util(
        __AUTH
    ).get_search("app:'thinkphp'")
    logging.info("get_search_result: [%s]", result)

def util_get_search_by_year_test():
    result = zoomeye.Util(
        __AUTH
    ).get_search_by_year("app:'thinkphp'")
    logging.info("get_search_result: [%s]", result)

def zoomeye_search():
    ze = zoomeye.Zoomeye(__AUTH)
    result = ze.search({
        "q":'app:"thinkphp"'
    })
    logging.info("zoomeye_search_result: [%s]", result)

def util_get_sites_test():
    with open('targets3','r') as f:
        querys = [line.strip() for line in f.readlines()]
    for query in querys:
        logging.info("query: [%s]", query)
        result = zoomeye.Util(__AUTH).get_sites({
            "q":query
            })
        result = [ "http://" + r for r in result]
        for r in result:
            logging.info("util_get_sites_result: [%s]", r)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    #do_request_test()
    #aggs_test()
    #util_get_search_test()
    #zoomeye_search()
    #util_get_search_by_year_test()
    util_get_sites_test()