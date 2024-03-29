# MAPPING REMOTENESS IN DENMARK
#### Video Demo:  <https://youtu.be/2dCJXrF9ue0>
#### Description:

I love remote places. Don't you?

That feeling of being really, really far away. That feeling that if someone wanted to bother you, they would have to make a really big effort to reach you.

![remote place](https://cdn.vroomvroomvroom.com/images/vroomvroomvroom-com/cms/sandy-road-nebraska-sandhills-seneca-dp-min.jpg)

Of course that's all an illusion now that everyone has a smart device in their pocket which is connected to a satellite. But still...

![remote place](https://www.printulu.co.za/blog/wp-content/uploads/2019/03/photo-1508690305591-b421948d9d3b.jpg)

It's a really special feeling.

![remote place](https://upload.wikimedia.org/wikipedia/commons/thumb/6/6a/Middle_of_Nowhere_-_panoramio.jpg/1200px-Middle_of_Nowhere_-_panoramio.jpg)

So I thought could be fun to completely ruin the magic by making a program that turns remoteness into a plain number. I wanted to try and figure out what's the very most remote place in... well, the whole world would have been nice. But, being at least somewhat realistic, I limited myself to my rather small home country of Denmark.

Now, Denmark unfortunately cannot pride itself on a richness of wild, desolate reaches untouched by human civilization. But what we *can* pride ourselves on is a richness of public data available through convenient APIs. When I learned that the government provides [a register of all addresses in Denmark](https://dawadocs.dataforsyningen.dk/dok/adresser) including their exact location, I knew it would be possible to calculate a remoteness value for each address by simply measuring how far it is from all the other addresses. And, by extension, I would thus be able to identify the most and least remote addresses in the country. 

That's my basic definition of remoteness for this project: "How far is place X from everywhere else?"

To put it in simple terms, look at this picture:

![instructive drawing](https://i.imgur.com/AUTHupR.png)

The blue cross is the most remote because its average distance to the other three crosses is higher than each of those crosses' average distance to the other three crosses. The red cross is the least remote because its average distance to the others is the lowest of all four crosses.

My project is the same thing, only with 3,834,014 crosses instead of 4.

The sheer size of my dataset was my challenge throughout. I needed to make my code fast enough that it could calculate a remoteness value for all 3,8 million addresses in a reasonable amount of time.

Of course "a reasonable amount of time" is a totally subjective measure, but I think most will agree that "a year" does not constitute it. That was nevertheless the estimated running time for the very first version of my program. It simply went like this:

```
from cs50 import SQL
import requests
import json
import math

URL = "https://api.dataforsyningen.dk/adresser?"
RADII = [50, 100, 200, 400, 800, 1600, 3200]
db = SQL("sqlite:///stryno.db")

with open("stryno.json", "r") as json_data:
    data = json.load(json_data)

for address in data:
    x = str(address["x"])
    y = str(address["y"])
    index = 0
    for radius in RADII:
        xyrad = x + "," + y + "," + str(radius)
        PARAMS = {'cirkel': xyrad, 'struktur':'mini'}
        response = requests.get(url = URL, params = PARAMS)
        allwithincircle = json.loads(response.content)
        amount = len(allwithincircle)
        index += ((1 / math.sqrt(radius)) * amount)
    db.execute("UPDATE addresses SET remoteness = ? WHERE id = ?", index, address["id"])
    
#Running time (N = 220): 480 seconds
```
*By the way, when I started this project, I didn't know how APIs worked at all. That's the case for most concepts I'm talking about here. I learned them for the project.*

The Danish address register API has a function which returns all addresses within a certain radius of a certain set of coordinates, so what I'm doing is that for each address, I'm calling the API and asking: "Hey API, show me the addresses located within 50 meters of this location", then 100 meters, then 200, etc., and then I'm running that through a formula to calculate remoteness, and storing the results in a database.

I was wise enough not to immediately try to crunch the whole country, so to start off, I had limited myself to this cute little island (which I visited this summer):

![Strynø](https://i.imgur.com/Gg29ayk.jpg)
*This is Strynø island. It has 220 addresses on it, which is less than 3,834,014.*

My program took 8 minutes to finish Strynø, which I estimated would translate to about 1 year for all of Denmark. Take note, though, that in terms of correctness/design/style, this algorithm is correct. It does the job. You only have to be really patient. And hope the API keeps servicing you.

### The journey
So now began a long, arduous journey of tweaking my code in many different ways to make it run **a lot** faster. If you'd like to skip this journey and teleport straight to the results, head down to where it says **The results**.

The first thing I did was stop calling the API for every single address. Instead, I downloaded the data into a database and read it from there. That got running time down from 8 minutes to 20 seconds. So far so good. Then I realized databases are also too slow because of the interfacing between Python and SQL. So I sat down with a YouTube tutorial about the NumPy library instead, which was said to be fast as a hungry leopard. 

*Thank God for YouTube tutorials! But not just God. Thanks to [Keith Galli](https://www.youtube.com/c/KGMIT) and [GeoDelta Labs](https://www.youtube.com/channel/UChpH97EqaN9HmdMnQFl7-Kw) specifically. They taught me so much.*

Around the time I learned about NumPy, I also realized that I had been calculating distances wrong all along. It turns out the Earth is a sphere :exploding_head:, which means you can't just use trigonometry to calculate distances. So I had to implement the far more complex Haversine formula. Nevertheless, my program had gotten fast enough that I was ready to leave my micro-island and head to... a bigger island!

![Samsø](https://i.imgur.com/lPXtGWg.jpg)

*This is the lovely island of Samsø. It has 5,070 addresses on it, which is less than 3,834,014 but more than 220.*

My issue now was that even though I was getting reasonable running times for my island, my algorithm was on o(n^2) because every address still had to look for information about every other address. I needed to get it closer to o(n) because otherwise scaling up to all of Denmark would mean my running time increasing not merely thousandfold but rather millionfold. I could not achieve this without sacrificing a tiny bit of accuracy. However, since the purpose of my product lay in the realm of the subjective (e.g. the concept of remoteness), I found it reasonable to sacrifice some accuracy as long as the results would still be more or less the same. So what I did was I divided Samsø (and later Denmark) into zones with known population, and instead of calculating the distance of every address to every other address, I calculated the distance of every address to every zone. This ended up giving me nearly the same quality results but using only one hundredth the computations.

This is known as a domain-specific adjustment. The opposite is called a computational adjustment; something which doesn't change your output but simply computes it more efficiently.

Here's my code that divides Denmark into zones:

```
    #Generate coordinate parameters to send to the API. For each iteration, x and y values are incremented so that the next zone takes up exactly the space adjacent to the previous one:
    for x in range(west, east, width):
        for y in range(south, north, height):
                x1 = round((x - (width / 2)), 5)
                x2 = x1
                x3 = round((x + (width / 2)), 5)
                x4 = x3
                x5 = x1

                y1 = round((y - (height / 2)), 5)
                y2 = round((y + (height / 2)), 5)
                y3 = y2
                y4 = y1
                y5 = y1
                
                #Generate request parameters:
                PARAMS = {'polygon': f"[[[{x1},{y1}],[{x2},{y2}],[{x3},{y3}],[{x4},{y4}],[{x5},{y5}]]]" , 'struktur':'mini', 'srid':'25832'}

                #Send the request to the API and make sure the program doesn't crash if the API goes unresponsive for a second:
                failures = 0
                while True:
                    response = requests.get(url = URL, params = PARAMS)
                    status = response.status_code
                    if status != 200:
                        if failures > 60:
                            return -1
                        else:
                            time.sleep(1)
                            failures += 1
                            continue
                    #Store addresses in zone in a JSON file and store basic zone data (centre point and population) in a database:
                    else:
                        addressesinzone = json.loads(response.content)
                        zonepop = len(addressesinzone)
                        if zonepop > 0:
                            folder = "/CodingLab/Final/zones/zones/bigzonefiles/" + str(int(zones / 1000) + 1) + "/"
                            zonefilename = folder + str(zones) + ".json"
                            if not os.path.exists(folder):
                                os.makedirs(folder)
                            with open(zonefilename, "w") as outfile:
                                json.dump(addressesinzone, outfile)
                            db.execute("INSERT INTO smallzones (id, x, y, population) VALUES (?, ?, ?, ?)", zones, x, y, zonepop)
                            zones += 1
                        break
```

I was now down to a running time of 23 seconds for 5,070 addresses, but this would still translate to about 36 hours for the full dataset. I was at a loss for how to speed it up further. So I did what all good programmers do when they’re at a loss: I went on Stack Overflow. And that’s where I learned about Cython.

Cython basically turns as much of your Python code as possible into C code, which allows it to run much faster. Most of the improvement comes from using typed variables so Python doesn't have to figure out the type of a variable every time it uses it. 

It took a while to wrap my head around Cython, but it did finally bring my running time down to 3 seconds.

That's when I felt confident enough to take on the entire country.

![Denmark](https://i.imgur.com/a87dPZM.png)
*Notwithstanding that the Kingdom of Denmark lost a lot of territory during the Swedish wars of the 1640s and the Prussian invasion of 1864, it's still a fair amount of data to process. My two little training islands are circled in red.*

It turns out that when you’re working with 3,8 million JSON items, you can’t just load them all into memory at the same time. So what I did was I used the administrative division of Denmark –  its 98 municipalities – and loaded those in one by one.

Another key improvement was learning about local projections. It turns out that clever geographers have divided the whole world into zones which each have a set of projected coordinates, making it possible to use Euclidian geometry to calculate distances, as if the Earth was indeed flat! :shushing_face: Another domain-specific improvement.

So, here's my final code. The main program simply loads in the zone data and a few constants. Then it calls Cython to do the hard work:

```
from cs50 import SQL
from cythoncode import cythoncodeOne
import json
import numpy as np

RADIUSLIST = [707, 1187, 1894, 3081, 4976, 8057, 13032, 21089, 44121, 65210, 109331, 174541, 283872]
RADII = np.array(RADIUSLIST, dtype=np.int64)
zonesides = 1000
kommunekoder = ["0155","0147","0101","0151","0153","0157","0159","0161","0163","0165","0167","0169","0173","0175","0183","0185","0187","0190","0201","0210","0217","0219","0223","0230","0240","0250","0253","0259","0260","0265","0269","0270","0306","0316","0320","0326","0329","0330","0336","0340","0350","0360","0370","0376","0390","0400","0410","0411","0420","0430","0440","0450","0461","0479","0480","0482","0492","0510","0530","0540","0550","0561","0563","0573","0575","0580","0607","0615","0621","0630","0657","0661","0665","0671","0706","0707","0710","0727","0730","0740","0741","0746","0751","0756","0760","0766","0773","0779","0787","0791","0810","0813","0820","0825","0840","0846","0849","0851","0860"]

db = SQL("sqlite:///danmark.db")

def main():
    rows = db.execute("SELECT * FROM verysmallzones")

    #Establish amount of zones with addresses in them
    ZONES = len(rows)

    #Initialize matrix with location of the center of each zone and the population of the zone
    zonematrix = np.zeros((ZONES, 3), dtype="float")
    for i, row in enumerate(rows):
        zonematrix[i,:] = row["x"], row["y"], row["population"]

    #Main loop (calculate remoteness index for each address)
    for kommune in kommunekoder:
        filename = "kommuner/adresser" + kommune + ".json"
        with open(filename, "r") as json_data:
            data = json.load(json_data)         
        cythoncodeOne.calcAll(data, kommune, RADII, zonematrix, zonesides)

if __name__ == "__main__":
    main()
```

I had ended up with about 45,000 zones, each 1 square kilometer in size. This appeared to be the most suitable compromise between speed and accuracy. 
(I ended up making several hundred thousand requests to Danish public administration's API over the duration of the project, and I have not heard any complaints.)

...and here's where Cython calculates the remoteness of every address in Denmark:
```
import Cython
import math
import numpy as np
import json
cimport numpy as np
    
def calcAll(data, str kommune, np.ndarray[np.int64_t, ndim=1] RADII, np.ndarray[np.float_t, ndim=2] zonematrix, np.int64_t zonesides):
    
    #Type-define all variables:
    cdef dict indextable = {}
    cdef dict value = {}
    cdef float ax, ay, dlat, dlon, pop, factor, index
    cdef int j, count
    cdef np.ndarray[np.float_t, ndim=2] allwithincircle
    cdef np.ndarray[np.float_t, ndim=2] distances = np.zeros((len(zonematrix), 2))
    cdef str key
    cdef str filename
    
    #Main loop (calculate remoteness value for each address):
    for address in data:
        #Map distances to each zone
        ax = address["x"]
        ay = address["y"]
        for j in range(len(zonematrix)):
            zx = zonematrix[j, 0]
            zy = zonematrix[j, 1]
            dlat = (ay - zy) * (ay - zy)
            dlon = (ax - zx) * (ax - zx)
            distances[j, 0] = math.sqrt(dlat + dlon)
            distances[j, 1] = zonematrix[j, 2]
        
        #Calculate remoteness index
        index = 0.0
        for radius in RADII:
            allwithincircle = distances[distances[:,0] < radius]
            popul = allwithincircle[:,1].sum()
            if radius < 3000:
                #Calculate average within-radius zone population
                count = len(allwithincircle)
                try:
                    factor = popul / count
                except:
                    factor = 0.0
                #Increment remoteness index:
                index += (1 / radius) * factor

            else:
                #Calculate expected amount of zones within circle to offset unregistered empty zones:
                count = (math.pi * (radius * radius)) / (zonesides * zonesides)
                factor = popul / count

                #Increment remoteness index:
                index += (1 / radius) * factor
        
        #Insert index data into dictionary along with address data:
        key = address["id"]
        value = {
            "x" : address["x"],
            "y" : address["y"],
            "betegnelse" : address["betegnelse"],
            "kommune" : kommune,
            "remoteness" : index
}
        indextable[key] = value

    #Write dictionary to file for each municipality:
    filename = "output/index" + kommune + ".json"
    jsonstring = json.dumps(indextable, ensure_ascii=False).encode('utf8')
    with open(filename, "w") as outfile:
        outfile.write(jsonstring.decode())
    indextable.clear()
    print(f"{kommune} loaded.")
        
    return
```

Great! I now had 98 files with all addresses in Denmark in JSON format, including basic data for each as well as my newly calculated remoteness value. The code ultimately took about 8 hours to run, which is less than a year :smirk:

Now I needed to visualize my findings on a map. For this purpose, I crafted a new version of my zone-generating application, this time with slightly bigger zones. This application would then calculate each zone's average remoteness by looking at the remoteness values of a sample of addresses situated within that zone (remember my previous zone application had stored all addresses situated in each zone in separate files so that I was now able to reach them dynamically). This program would then generate a so-called GeoJSON file from the data with the outline and average remoteness of each zone, which could then be loaded into the highly convenient GeoPandas library.

Here's the code that does this:
```
from cs50 import SQL
import json
import os

db = SQL("sqlite:///C:/CodingLab/Final/Danmark/Danmark/danmark.db")

#Define geographic range to divide into zones
west = 436000
east = 898000
north = 6408000
south = 6044000

#Define size of each zone (in meters)
width = 2000
height = 2000

def main():  
    #Initialize list of zones containing the properties of each zone:
    featurelist = []
    #Initialize zone counter:
    zones = 1
    #Initialize zone remoteness variable:
    zonerem = 0.0
    #Variable that indicates whether the previous zone had population or not. This keeps approximated remoteness values for unpopulated zones from spiralling off:
    nz = True

    #Main loop (for each zone, fetch polygon, calculate average remoteness, and store these in dict along with zone ID):
    for x in range(west, east, width):
        for y in range(south, north, height):
            #Define polygon of zone:
            x1 = round((x - (width / 2)), 5)
            x2 = x1
            x3 = round((x + (width / 2)), 5)
            x4 = x3
            x5 = x1

            y1 = round((y - (height / 2)), 5)
            y2 = round((y + (height / 2)), 5)
            y3 = y2
            y4 = y1
            y5 = y1

            #Determine folder in which to find a file containing the remoteness index of this zone
            folder = int(zones / 1000) + 1         

            #Fetch population of zone:
            rows = db.execute("SELECT population FROM smallzones WHERE x = ? AND y = ?", x, y)
            if len(rows) > 0:
                zonepop = rows[0]['population']
            else:
                zonepop = 0

            #If there are no addresses in this zone, average remoteness cannot be calculated. Zone takes average remoteness from adjacent zone but sets it slightly lower because the area is ostensibly even more remote given that it has no addresses in it. Store this zone out of the way to avoid messing up synchronization between zones from the zonefiles and zones in the dataframe that we're making with this program:
            if zonepop == 0:
                print("Nullzone.")
                if nz is False:
                    zonerem = zonerem / 1.5
                id = zones + 100000
                nz = True

            #Calculate average remoteness of zone:
            else:
                nz = False
                #A maximum of 50 addresses are sampled from each zone to calculate an approximate average:
                step = int(zonepop / 50)
                if step == 0:
                    step = 1 
                #Initialize incrementing remoteness sum counter:
                count = 0
                #Determine file containing the remoteness index of this zone:
                zonefilename = "C:/CodingLab/Final/zones/zones/bigzonefiles/" + str(folder) + "/" + str(zones) + ".json"
                #Read remoteness index from file and increment counter:
                with open(zonefilename, "r") as zonefile:
                    json_data = json.load(zonefile)
                    for i in range(0, zonepop, step):
                        kommune = json_data[i]['kommunekode']
                        kommunefilename = "C:/CodingLab/Final/Danmark/Danmark/output/index" + kommune + ".json"
                        with open(kommunefilename, "r") as kommunefile:
                            json_kdata = json.load(kommunefile)
                            try:
                                count += json_kdata[json_data[i]["id"]]["remoteness"]
                            except:
                                continue
                #Calculate average remoteness:
                zonerem = count / (zonepop / step)
                id = zones
                #Increment zone counter
                zones += 1
                print(zones)

            #Append the features of this zone to the list of zones and their features:
            featurelist.append(
            {"type": "Feature",
            "geometry": {
                "type": "Polygon",
                "coordinates": [[[x1,y1],[x2,y2],[x3,y3],[x4,y4],[x5,y5]]]
            },
            "properties": {
                "id": id,
                "remoteness": zonerem
            }})

    #Having added the features of all zones to the featurelist, add the featurelist to GeoJSON dataframe and save to file:
    gdf = {
    "type": "FeatureCollection",
    "crs": {"type": "name", "properties": {"name": "EPSG:25832"}},
    "features": featurelist}

    gdfstring = json.dumps(gdf)

    outfolder = "C:/CodingLab/Final/Danmark/plot/geoJSON/"
    if not os.path.exists(outfolder):
        os.makedirs(outfolder)
    filename = outfolder + 'zonesdataframe3.json'
    with open(filename, 'w') as outfile:
        json.dump(gdfstring, outfile)

    print("Success.")

if __name__ == "__main__":
    main()
```

It was a bit complicated because the zones were just squares while the remoteness values were stored by municipality, as you'll recall. And that’s just the sort of annoying little issue you're constantly running into when dealing with data...

Another great example of the kind of stuff I had to deal with: If you look closely above, you can see I'm using try and except. That's because it turns out that between the time the I calculated the remoteness values of all the addresses and the time I generated the zones I'm using here, someone built a new house. So my program crashed with a KeyError because it found an address that I didn’t have a remoteness value for :man_facepalming:

But now I was on the home stretch!

To plot the data, I had to study a library called GeoPandas (based on the Pandas and MatPlotLib libraries), which is made for just that sort of thing. GeoPandas parses my GeoJSON file, and I then use GeoPandas to spatially plot the data. The outline of Denmark was imported onto the plot from what's known as a shapefile, which is just another item on the long list of stuff I've had to learn about for this project. 
Needless to say I outputted quite a few uncanny-looking maps before I got one that was actually helpful.

And so, without further ado...

### The results
This - I am proud to announce - is the most remote location in Denmark:
(To put it more correctly: It's the most remote location in Denmark *that has an address*)

![most remote place](https://i.imgur.com/kv2k72t.jpg)

Despite vigorous googling, I have not been able to find out what the building is for. It's located on a dam, with the sea on one side and a reservoir on the other, in the southwesternmost corner of Denmark, very close to the German border. I'm definitely planning an expedition there!

This is the second most remote location in Denmark:
![second most remote place](https://i.imgur.com/enC4Q4h.jpg)

The only way to get there is to walk across that narrow sandy dune.

The third most remote location is this lighthouse on a small island:
![third most remote place](https://i.imgur.com/F0zwskM.jpg)

...and the least remote place in all Denmark happens to be this rather nondescript brick building in Nørrebro, Copenhagen:
![least remote place](https://i.imgur.com/o9wOOak.jpg)

When mapping out average local remoteness across all of Denmark, this is what it looks like. The brighter colored areas are the most remote, while black blemishes of non-remoteness are mostly occurring where cities are located:
![the map](https://i.imgur.com/JuveeB6.jpg)


### In conclusion
What feels particularly nice about having finished this project is that I've produced real-world results. I'm contributing a little bit of knowledge about the real world that might be of interest to some.

That said, there's of course nothing absolute about any of my results. One could just as well have defined remoteness in a different way. One could also have used a different formula to calculate it. In 2002, a team of researchers [mapped remoteness in Britain](https://eprints.whiterose.ac.uk/934/1/evansaj7.pdf) using six parameters, of which "distance to everything else" was just one.

But most of all, this project has been a great way of learning. This way of learning is one that I would recommend to everyone: Set yourself a challenge that you think is fun, try to make it difficult but not insurmountable, and then just learn whatever you need to in order to overcome that challenge.

These are just some of the things I've had to learn about in order to complete this project:

- APIs
- The JSON module
- The Requests module
- UTM projections 
- NumPy
- Cython
- VSCode
- Relative imports
- Choropleth maps
- The Pandas library
- Shapefiles
- GeoJSON files
- The GeoPandas library


That's all! From now I'll just be waiting for the day when I'm on a road trip through some far-off part of Denmark and someone says: "Wow, this must be one of the most remote places in all of Denmark!", and I'll respond with: "Actually it's only the 157th most remote place." It will definitely be worth it. :sunglasses:
