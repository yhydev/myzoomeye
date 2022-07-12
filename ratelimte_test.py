from ratelimit import limits

@limits(calls=1, period=5, raise_on_limit=False)
def a():
    print(111)

a()
a()
a()
