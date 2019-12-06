import urllib2, json
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

headers = {"X-API-Key": "YOUR_API"}

def getbillsafe(congress, bill_id):
    try:
        baseurl = "https://api.propublica.org/congress/v1/"
        fullurl = baseurl + congress + "/bills/" + bill_id + ".json"
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

def gettitlesafe(congress, bill_id):
    result = getbillsafe(congress, bill_id)
    if result is not None:
        if result["status"] == "ERROR":
            return None
        else:
            billdata = result["results"][0]
            if billdata["short_title"] is not None:
                title = billdata["short_title"]
            else:
                title = billdata["title"]
            return title

def summarizebillsafe(congress, bill_id):
    result = getbillsafe(congress, bill_id)
    if result is not None:
        if result["status"] == "ERROR":
            return None
        else:
            billdata = result["results"][0]
            title = gettitlesafe(congress, bill_id)
            billsummary = "\n{{Infobox U.S. legislation" +\
                            "\n| shorttitle = " + title +\
                            "\n| longtitle = " + billdata["title"] +\
                            "\n| introducedby = [[%s]] (%s-%s)" % (billdata["sponsor"], billdata["sponsor_party"],
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
                billsummary += "\n| enacted by = " + billdata["bill_id"][-3:] + "th" +\
                                "\n| passedbody1 = [[United States House of Representatives|House]]" +\
                                "\n| passeddate1 = " + dateconvert(billdata["house_passage"]) +\
                                "\n| passedbody2 = [[United States Senate|Senate]]" +\
                                "\n| passeddate2 = " + dateconvert(billdata["senate_passage"]) +\
                                "\n| public law url = " + billdata["gpo_pdf_uri"] +\
                                "\n}}" +\
                                "\nThe '''%s''' is an [[Act of Congress|Act of the United States Congress]] " \
                                "that was enacted on %s." % (title, dateconvert(billdata["enacted"]))
            else:
                billsummary += "\n}}" + \
                                "<p>The '''%s''' is an [[Bill (United States Congress)|bill of the United States " \
                                "Congress]] that was introduced on %s by %s [[%s]] but ''not'' enacted. On %s, it was %s" \
                                % (title, dateconvert(billdata["introduced_date"]), billdata["sponsor_title"],
                                   billdata["sponsor"], dateconvert(billdata["latest_major_action_date"]),
                                   lowerfirst(billdata["latest_major_action"]))
                if billdata["active"] is False:
                    billsummary += "The bill is no longer active."
                if billdata["vetoed"] is not None:
                    billsummary += "The bill was vetoed on " + dateconvert(billdata["vetoed"])
            if billdata["summary"] is not None:
                if billdata["summary"][:len(title)] == title:
                    billsummary += "<p />This legislation " + lowerfirst(billdata["summary"][len(title):])
                else:
                    billsummary += "<p />" + billdata["summary"]
            billsummary += "<ref>Data collected from [https://projects.propublica.org/api-docs/congress-api/ " \
                            "ProPublica Congress API]. Retrieved %s</ref><br /><h2>References</h2>{{Reflist}}" \
                            % (datetime.date.today().strftime("%B %d, %Y"))
            logging.info(billsummary)
            return billsummary
    else:
        logging.info("There was an error with this request")

# JINJA statement #
JINJA_ENVIRONMENT = jinja2.Environment(loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
                                       extensions=['jinja2.ext.autoescape'], autoescape=True)

class MainHandler(webapp2.RequestHandler):
    def get(self):
        vals = {}
        vals['page_title'] = "Search Bills by Keywords"
        template = JINJA_ENVIRONMENT.get_template('templates/searchform.html')
        self.response.write(template.render(vals))

class SearchHandler(webapp2.RequestHandler):
    def get(self):
        vals = {}
        vals['page_title'] = "Search Bills by Keywords"
        template = JINJA_ENVIRONMENT.get_template('templates/searchform.html')
        self.response.write(template.render(vals))
    def post(self):
        vals = {}
        vals['page_title'] = "Wikitext Results"
        congress = self.request.get('congress')
        bill_id = self.request.get('bill_id')
        go = self.request.get('btn')
        logging.info(congress + bill_id)
        logging.info(go)
        if congress and bill_id and summarizebillsafe(congress, bill_id) is not None:
            vals["congress"] = congress
            vals["bill_id"] = bill_id.upper()
            vals["title"] = gettitlesafe(congress, bill_id)
            vals["summary"] = summarizebillsafe(congress, bill_id)
            template = JINJA_ENVIRONMENT.get_template('templates/index.html')
            self.response.write(template.render(vals))
            logging.info('keyword = ' + congress + bill_id)
        else:
            vals['prompt'] = "Please enter a valid Congress meeting and bill ID"
            template =JINJA_ENVIRONMENT.get_template('templates/searchform.html')
            self.response.write(template.render(vals))

application = webapp2.WSGIApplication([('/', MainHandler),('/search', SearchHandler)], debug=True)

