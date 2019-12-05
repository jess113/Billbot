import urllib, urllib2, json
import datetime
import jinja2, os, webapp2
import logging

# functions #
def dateconvert(x):
    return datetime.datetime.strptime(x, '%Y-%m-%d').strftime('%d %B %Y')

def lowerfirst(s):
   if len(s) == 0:
      return s
   else:
      return s[0].lower() + s[1:]

def pretty(obj):
    return json.dumps(obj, sort_keys=True, indent=2)

headers = {"X-API-Key": "iIhSv9hvM7aFR7GMSPBZz2lznWqqPg31LYPqTOyP"}

def getbillsafe(query, sort="_score", dir="desc"):
    try:
        datadict = {"query": query, "sort": sort, "dir": dir}
        baseurl = "https://api.propublica.org/congress/v1/bills/search.json"
        fullurl = baseurl + "?" + urllib.urlencode(datadict)
        request = urllib2.Request(fullurl, headers=headers)
        result = json.loads(urllib2.urlopen(request).read())
        return result
    except urllib2.URLError as e:
        if hasattr(e, "code"):
            logging.error("The server couldn't fulfill the request.")
            logging.error("Error code: ", e.code)
        else:
            logging.error("Unknown error trying to retrieve data")
        return None

def summarizebillsafe(query):
    result = getbillsafe(query)
    if result is not None:
        billdatalist = result["results"][0]["bills"]
        for billdata in billdatalist:
            if billdata["short_title"] is not None:
                title = billdata["short_title"]
            else:
                title = billdata["title"]
            billsummary = "\n\n{{Infobox U.S. legislation" +\
                          "\n| shorttitle = " + title +\
                          "\n| longtitle = " + billdata["title"] +\
                          "\n| enacted by = " + billdata["bill_id"][-3:] +\
                          "\n| introducedby = [[%s]] (%s-%s)" % (billdata["sponsor_name"], billdata["sponsor_party"],
                                                                 billdata["sponsor_state"]) +\
                          "\n| introduceddate = " + dateconvert(billdata["introduced_date"]) +\
                          "\n| committees = [[%s]]" % (billdata["committees"])
            if billdata["bill_type"] == "hr":
                billsummary += "\n| introducedin = [[United States House of Representatives|House of Representatives]]"\
                               + "\n| introducedbill = {{USBill|%s|H.R.|%s}}" % (billdata["bill_id"][-3:],
                                                                                 billdata["number"][4:])
            elif billdata["bill_type"] == "s":
                billsummary += "\n| introducedin = [[United States Senate|Senate]]" +\
                               "\n| introducedbill = {{USBill|%s|S.|%s}}" % (billdata["bill_id"][-3:],
                                                                             billdata["number"][2:])
            if billdata["enacted"] is not None:
                billsummary += "\n| passedbody1 = [[United States House of Representatives|House]]" +\
                               "\n| passeddate1 = " + dateconvert(billdata["house_passage"]) +\
                               "\n| passedbody2 = [[United States Senate|Senate]]" +\
                               "\n| passeddate2 = " + dateconvert(billdata["senate_passage"]) +\
                               "\n| public law url = " + billdata["gpo_pdf_uri"] +\
                               "\n}}" +\
                               "\nThe '''%s''' is an [[Act of Congress|Act of the United States Congress]] " \
                               "that was enacted on %s." % (title, dateconvert(billdata["enacted"]))
            else:
                billsummary += "\n}}" + \
                               "\n\nThe '''%s''' is an [[Bill (United States Congress)|bill of the United States " \
                               "Congress]] that was introduced on %s by %s [[%s]] but not enacted. On %s, it was %s" \
                               % (title, dateconvert(billdata["introduced_date"]), billdata["sponsor_title"],
                                  billdata["sponsor_name"], dateconvert(billdata["latest_major_action_date"]),
                                  lowerfirst(billdata["latest_major_action"]))
                if billdata["active"] is False:
                    billsummary += "The bill is no longer active."
                if billdata["vetoed"] is not None:
                    billsummary += "The bill was vetoed on " + dateconvert(billdata["vetoed"])
            if billdata["summary"] is not None:
                if billdata["summary"][:len(title)] == title:
                    billsummary += "\n\nThe legislation " + lowerfirst(billdata["summary"][len(title)+3:])
            billsummary += "<ref>[https://projects.propublica.org/api-docs/congress-api/ data collected from " \
                           "ProPublica Congress API]. Retrieved %s</ref>\n\n== References ==\n{{Reflist}}" \
                           % (datetime.date.today().strftime("%B %d, %Y"))
            print(billsummary)
            print("")
    else:
        print("There was an error with this request")

# JINJA statement #
JINJA_ENVIRONMENT = jinja2.Environment(loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
                                           extensions=['jinja2.ext.autoescape'], autoescape=True)

class MainHandler(webapp2.RequestHandler):
    def get(self):
        vals = {}
        vals['page_title'] = "Search by Tag"
        template = JINJA_ENVIRONMENT.get_template('searchform.html')
        self.response.write(template.render(vals))

keywordlist = ["China"]
for keyword in keywordlist:
    summarizebillsafe(keyword)
