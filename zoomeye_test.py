import zoomeye
import logging
import time

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
    #logging.info("get_search_result: [%s]", result)
    for r in result:
        logging.info("get_search: [%s]", r)

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
    code = "ty48uo"
    rnd = "2a00ef7fa82e7670aa5f7a24fca9e6a61b0d8781ab7b40f43e252762553fdf86f3a7a8662ef5b915fa1ffd45264d5c6c"
    with open('targets3','r') as f:
        querys = [line.strip() for line in f.readlines()]
    ze = zoomeye.Zoomeye(__AUTH)
    for query in querys:
        if ze.aggs(query, "country")['total'] == 0:
            continue
        logging.info("query: [%s]", query)
        while True:
            try:
                result = zoomeye.Util(__AUTH).get_sites({
                    "q":query
                    })
                result = [ "http://" + r for r in result]
                for r in result:
                    logging.info("util_get_sites_result: [%s]", r)
                break
            except Exception as e:
                logging.info("validate_result: %s", resp_json)
                time.sleep(60)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    #do_request_test()
    #aggs_test()
    #util_get_search_test()
    #zoomeye_search()
    #util_get_search_by_year_test()
    util_get_sites_test()