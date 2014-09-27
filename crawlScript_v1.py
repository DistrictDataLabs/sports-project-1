import urllib2

page_id = 200007;

urlString = "http://www.espnfc.co.uk/gamecast/statistics/id/" + str(page_id) + "/statistics.html"
response = urllib2.urlopen("http://google.de")
page_source = response.read()