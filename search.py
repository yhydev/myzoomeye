import argparse
import zoomeye
import math
def to_target(result):
    ret_res = []
    for target in result:
        if target.get('ssl'):
            proto = "https"
        else:
            proto = "http"
        if target['type'] == "web":
            host = target['site']
        else:
            host = target['ip']
        if target.get("portinfo") and target.get("portinfo").get("port"):
            url = "%s://%s:%s" % (proto, host, target['portinfo']['port'])
        else:
            url = "%s://%s" % (proto, host)
        ret_res.append(url)
    return ret_res

def search(token, query, page=1, pageSize=50):
    ze = zoomeye.Zoomeye(token)
    if page * 50 > 400:
        return []
    params = {
        "pageSize": pageSize,
        "page": page,
        "q": query
    }
    result = ze.search(params)
    total = result['total']
    sites = result['matches']
    results = []
    if len(sites) > 0:
        sites = to_target(sites)
        results.extend(sites)
    if len(sites) == pageSize and math.ceil(total / pageSize) >= page + 1:
        sites = search(token, query, page+1, pageSize)
        results.extend(sites)
    return results
    


    
if __name__ == "__main__":
  import argparse
  ap = argparse.ArgumentParser()
  ap.add_argument('-q','--query', required=True)
  ap.add_argument('-k','--token', required=True)
  args = ap.parse_args()
  r = search(args.token, args.query)
  for t in r:
      print(t)
