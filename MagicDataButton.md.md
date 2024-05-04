![The "get data" button](https://www.dropbox.com/scl/fi/ccn6rbuz6j7palgw2j7sy/ExcelPhase1button.png?rlkey=w6b8unkea1nl6rdb2cc49x6ko&raw=1)

# One-click data summoning

### **Client**: 
##### A house-flipping startup
### **Client need**: 
##### Extensive, up-to-date data about all houses listed for sale in their area of interest (location details, price history, house specs, nearby amenities, taxes and expenses etc. for a total of 40 columns.)

### **Result**: 
##### A button for Excel which instantly summons all the relevant data, neatly arranged.

<br/>

I like to think of programming as a kind of magic. That's how it always seemed to me as a kid when the computer would make my letters in my headlines into zany shapes or play my adversary in a strategy game. How did it do it? Well, it was a computer. Computers were magical objects.

So when a client asks me to help make a task easier, the question I want to ask is: 

*What would you do if you had a magic wand?*

![Summoning data with a magic wand](https://www.dropbox.com/scl/fi/rdnuwf1ixy2jwh2coanri/data-magic-small.jpg?rlkey=h9u9806vjjkrvm15xsc5671yn&raw=1)

In this case, my client was a house-flipping startup whose owner was gathering data on real-estate listings manually by browsing the web, looking at the data on the screen and typing it into an Excel spreadsheet. With up to 500 listings of interest at any given time and up to 40 pertinent data points about each, it's easy to grasp the scope of the potential for making this process faster. 

What could the owner do if they had a magic wand? Well, they could simply wave the wand, say "*accio data!*" and all the data would magically appear, up-to-date, in their spreadsheet. That's what this program does.

In order to make the magic happen, needless to say a lot of tedious stuff needs to be going on under the hood. This is how I solved the problem:

1. **Identify the sources** of all the data
2. **Crawl** the listing site to find all current listings
3. **Scrape** data from each source for each current listing and store it as JSON
4. **Migrate** the JSON data to a **SQL database**
5. Create a script for Excel which **imports** the desired data from the database
6. Set up a shell script in the cloud to **update the database daily** so the latest data is always available


## 1. Finding the data
Most of the data comes from the hidden APIs of real estate sites. Rather than trying to scrape their data directly off their websites, which is often made very difficult by arcane HTML structures and Java and Ajax scripts, I investigated the XHR requests made by the browser while rendering the websites and managed to derive the various APIs used by the sites and their request parameters.

![API request in browser inspector view](https://www.dropbox.com/scl/fi/rmo093mjvveo2uybjp7g6/Phase1Inspector.png?rlkey=x8czw2ewm62uk0jq8fhkp1yzg&raw=1)


## 2. Crawling for listings
If I'd needed to scrape all the data from the web, I would have had to use the web scraping gold standard, Scrapy, using the Splash add-on to interact with the websites. In the final *crawler.py* script, however, I was able to get by with the lightweight BeautifulSoup library. All I needed to scrape was the address, zip code and current price of each listing. Then I could do the rest of the work with API requests. <br/>
I would like to stress that no APIs were burdened, no data collected from any competing business, nor any robots.txt violated during the making of this project.

<br/>

![Beautiful Soup](https://www.dropbox.com/scl/fi/6uc4cn2dkr222kixheiyk/beautiful-soup-small.jpg?rlkey=6wzxribde1q8h2xmbts0s3pil&raw=1)

*Scraping data with beautiful soup is a breeze!*

## 3. Calling for data
The *caller.py* script then goes through the data sources one by one, storing the data in a list of dictionaries. Of course not all requests were easily accepted by the APIs so in some cases, I had to use the **curl-cffi** library to get a response. I wrote a custom request function and URL parsing function for this purposes which are part of the contents of *customFuncs.py*.

Having gathered the available data, the caller script then goes on to calculate derived data points. Apart from some simple tax calculations, this involves calculating the distance to nearby amenities such as major roads, schools, train stations and shopping areas. This is done by connecting to the OSRM API which outputs walking or driving distances as well as routes based on data from OpenStreetMap. After downloading location data on all relevant amenities, I was able to use the Shapely library and the OSRM API to calculate the nearest amenity and the distance to it - as further described in *distances.py*.

![Major roads in the area of interest](https://www.dropbox.com/scl/fi/lfcxbwxumf4os2mymuzgs/Stoerre-veje-small.png?rlkey=s49tsp1pm9feg311trpg2rsgx&raw=1)

*All major roads in one of our areas of interest, highlighted. Data pulled from OpenStreetMap.*

Finally, the caller script composes a report on those values it may have failed to find and emails me a summary of the whole operation so I can monitor that it keeps updating as it should every morning.


## 4. Populating the database
The database is in PostgreSQL and it's kept simple. There's one table for all the data and then a trigger-generated table that logs all operations on the main table. Finally, there's a view which filters out impertinent data (such as address ID and exact geographical location) and assigns user-friendly names to all the columns. The schema is in *createtable.sql*. *Populater.py* reads the JSON file created by *caller.py*, inserts new listings into the database and updates listings for which changes in the data have been registered (usually a change in price). Another custom function uses decorators to manage the database connection.


## 5. Importing the data into Excel
Full disclosure: I made my butler (ChatGPT) do this part. It would have been nice to sit down and spend two weeks really understanding Visual Basic and getting good at it. I did not have that time though. I find ChatGPT really useful in cases like this where you know exactly what you need to do but there's some specific knowhow that you lack (in my case: VBA syntax). I started with the prompt:

"*I need to make a script that downloads a .csv file from the web and then imports the data from this .csv file into a range of columns of the Excel sheet. The import function should overwrite anything that's already in the affected columns of the Excel sheet except where a cell is empty in the imported data. In that case, whatever was already in that cell should remain there. Can you show me how such a script might look?*"

This created the skeleton of the script, which was then calibrated through several iterations to take into account:
- character anomalies cause by encoding differences
- empty rows between newly generated rows
- horizontal misalignment caused by the removal of out-of-date listings
- inconsistent date formats
- preserving obsolete data in a separate sheet for statistcs purposes

In the end, the script in *importer.vba* does the job nicely. It's written by ChatGPT with continuous adjustments and updates in collaboration between it and me.

![AI butler](https://www.dropbox.com/scl/fi/qoy9yw9jarmkk69fte4p2/AI-butler-small.jpg?rlkey=5m1s3kmkx8k3k4hqpxwo4dboq&raw=1)

*Me chilling in the couch while my AI butler does my work for me*


## 6. Setting the whole thing up to run daily in the cloud
Since the program is so small and its required bandwidth so limited, it fits nicely into a free tier VM instance at Oracle Cloud. So I set up an instance, installed the necessary applications (Python, Anaconda, Git, and finally Apache to serve the data on the web for the Excel script to download), cloned the program files from this repository, wrote a shell script to run each of the above scripts one after the other, waiting for the previous script to finish before starting the next one (since each depends on files generated by the previous), and added the runscript to the crontab to run each morning.

![Run report](https://www.dropbox.com/scl/fi/02pz1aknq175qnxjz7ori/run-completed-small.png?rlkey=w9m2cfqikdtnc8kxqld103uyu&raw=1)

*After each run, the script emails me a report with the amount of new added listings and details on any data it failed to fetch. No missing values in this run.*

And that was how the magic button came to be!

## New abilities learned:
- PostgreSQL
- Web scraping with Scrapy and BeautifulSoup
- Web scraping with hidden APIs
- Using the Overpass API and the OSRM API for OpenStreetMap
- The Shapely library
- Using a VM instance
- Remote database hosting
- Shell scripts
- Cronjobs
- Some domain knowledge about what matters in the real estate business

## Old abilities improved:
- Python
- SQL in general
- Requests
- Decorator functions
- Project planning
- AI prompting
