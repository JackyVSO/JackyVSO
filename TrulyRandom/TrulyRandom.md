![Headline: random instruction](https://www.dropbox.com/scl/fi/g7ku7f2uryhyxshe68i0r/randominstruction3BIG.png?rlkey=3lhpfhzcwosdu0p657p781yy1&raw=1)
# Truly random
### *How do you generate a completely random but fully coherent sentence?*

## Introduction
It's kind of surprising how in-demand randomness is. It's surprising because randomness is fundamentally useless. Solving problems always seems to come down to doing something distinctly precise and not random. So then why do people keep complaining that the shuffle function on Spotify is "not random enough"? Why is "surprise me!" such a popular request? And why is Monty Python - masters of randomness - the most celebrated comedy group of all time?

I think it's because randomness is freedom. It liberates you from the confines of your own imagination. In fact, it liberates you from the confines of human ingenuity altogether. At the same time, randomness is inherently fair. It liberates you from the stress of dealing bias and ulterior motives.

![Monty Python being random](https://pbs.twimg.com/media/DbVRkAUW4AAta4M.jpg)

Randomness can be inspiring and funny. This is why, when the idea of a system to generate a random sentence popped into my head one day while hiking in Georgia (the country, not the state), I pursued it.

The system I came up with was an analog, glass box system featuring a lot of bowls: 

You start with a blue grammar bowl, from which you draw a card which represents the class of the next word. Let's say you draw a verb card. Then you move over to a green word bowl, specifically the bowl with all the verbs in it. You draw your verb, add it to the sentence, then move to the next grammar bowl containing word classes that may follow a verb, etc. I visualized a maze of carefully interconnected bowls in a big room. Once you've picked the last word, you have a completely random sentence.

The full idea was to make a YouTube concept of drawing completely random instructions from the bowls and then carrying them out.

The code in this project basically implements the digital counterpart of the bowl system. Needless to say, it proved a lot more complicated than I first thought. It did so because, as it turns out, language itself is complex, inconsistent, fluid and counterintuitive. Who knew? It does not want to be squeezed into a box, glass or black. It struggles like a duck might.

Now, before anything else, I want to address the question that's clearly on everyone's mind right now:

### Why don't you just ask ChatGPT to give you random instructions?

I did.

It turns out ChatGPT - for all its talents - is quite terrible at being random. In fact, let me show you how the conversation went:

![Chat transcript](https://www.dropbox.com/scl/fi/ohvco5ieby15395w3ai8j/chatgpt-failing-to-be-random.png?rlkey=bki7j38kju8gapjkocyltpfma&raw=1)

At my first request, it generated a sentence of the category "meaningful things to do", without further context. At my second request, it pulled a response from the set of "completely meaningless but fun things to do". Then, at my last request, it gave me an example of something I could do that would involve randomness.

This should not be surprising. ChatGPT is trained to be relevant - because, as we've established, that's what's useful. It's unable to provide an answer that has no context at all.

What's particularly interesting to me is this: Computer are inherently amazing at being random, but ChatGPT is a computer that has been trained to be like a human and has, in so doing, forfeited its innate capacity for randomness. So, in a sense, ChatGPT is bad at being random for the same reason humans are bad at being random: Our decision-making processes are based on neural networks, and what neural networks do is fundamentally match outputs to inputs. There will always be a causal relation between what goes in and what comes out. 

## How the program works
Now let me explain how I constructed a program to provide true, deadpan randomness in the form of imperative utterances. This section assumes you understand some code. If you're mainly interested in the language angle, just skip past the codey parts.  
The basic logic is simple:

select a class  
select a word from this class  
repeat until end

The pseudocode of the main loop looks like this:

```
    while word.class != 'END':
        nextclass = word.nextclass(word.nextclasses)
        nextname = word.nextname(nextclass)
        word = Word(nextname, nextclass)
        sentence += (word.name)
```

Then we just need to create a dictionary of word classes (for each defining a set of possible classes than can follow after it), a list of words with each having its class assigned to it, and then define a Word object which knows its own name (the actual word) and its own class and has a function for randomly selecting the next class and a function for randomly selecting the next word from the next class. (The astute OOP coder might have a question here: Why does the function to select the next word need to be inside the Word class? We'll get to that.)


### Getting the syntax right
The first challenge, then, is to draw up the grammar. What I expected was something like this:

![Simple grammar graph](https://www.dropbox.com/scl/fi/x8s74j45r955namdmkmpi/simplegrammargraph.png?rlkey=dpcsezcviz0q6svgzoy8htt60&raw=1)

What I ended up with was this:

![Full grammar graph](https://www.dropbox.com/scl/fi/d2ntf2z0yzwunb55k0erv/grammargraph.png?rlkey=h7t5cxd0wj15ax0bmihj85w3z&raw=1)

These are some of the problems I ran into while designing the grammar:

#### Intransitive vs. transitive verbs and manipulative vs. static verbs
Take a verb like "sit". You can sit, alright. You can even sit on a mountain top or sit arrogantly. But you can't sit an object. Sit is an intransitive verb. Then you have verb like "hold". "Hold" wants an object. You can hold a cup or hold a puppy but you can't just hold period. "Hold" is a transitive verb. But there is a third level. While you can hold an object, that doesn't really do anything to the object. You can't hold an object into a lake, for example. But with a verb like "push" or "throw", you can go the full nine yards. You can throw that puppy into the lake. (Don't though). The problem is that instructions starting with each of these respective verbs are differently structured down the line. If I have selected an intransitive verb ("sit"), the next word should not be a noun. If I have selected a transitive but static word ("hold"), the following noun should not be followed by an adverb or a preposition like "through".

#### Subtle differences
Several other subtle issues contributed to making the final grammatical structure so complicated. And I readily admit that even being as complicated as it is, it still only accommodates a fraction of all possible English sentence structures. However, it does accommodate enough that it is able to generate an arbitrarily large number of different sentences, which is all I could hope for.
One thing I needed to take care of was distinguishing between conjunctions between nouns in the same clause and conjunctions between sentences. For example, the "and" in "pick up a duck and a goose" is a different word class than the "and" in "pick up a duck and row across the lake". Another was distinguishing between the syntactical properties of adverbs that are adjectives with "-ly" at the end and adverbs that indicate orientation ("up", "sideways" etc.).

Besides possible next classes, the grammar file also contains weights for each possible next class and a vocabulary for each class. This owes to the fact that I had to resort to creating multiple versions the class "Noun" and some other classes, depending on what kind of verb they came after, but didn't want to associate each word with multiple version of the same class:

```python
    ...
    "MTV": {
        "nexts": ["MART", "MN", "MADJ"],
        "weights": [0.7, 0.15, 0.15],
        "vocabulary": ["MTV"]
        },
    "ART": {
        "nexts": ["N", "ADJ"],
        "weights": [0.5, 0.5],
        "vocabulary": ["ART"]
        }, 
    "ADJ": {
        "nexts": ["N"],
        "weights": [1],
        "vocabulary": ["ADJ"]
        },
    ... etc.
```

The "next class" function also takes care of two extra issues: moderating sentence length by increasing the probability of ending the sentence if it's already very long, and making sure proper nouns are paired only with appropriate prepositions. It's one thing to catch a fish in Canada but you wouldn't wanna catch a fish *with* Canada or *on* Canada:

```python
    def nextpos(self, posnexts, weights, history):
        #--Choose next part of speech--

        #Progressively increase probability of ending sentence if sentence is already very long
        if len(history) > 7 and 'END' in posnexts:
            weights[posnexts.index('END')] += (0.05 * (len(history) - 7))
        
        #Select part of speech
        choice = random.choices(posnexts, weights, k=1)[0]
        
        #If proper noun is selected, check that the incumbent preposition is okay to take a proper noun:
        if choice == 'PN':
            row = wordframe.loc[(wordframe.name.apply(lambda x: x == self.name)) & (wordframe['pos'].isin(grammar[self.pos]['vocabulary']))]
            if 'pn' not in row.nextcats.values[0].split(" "):
                return None

        return choice
```
 
### Getting word selection right
The real tricky part is, once you've selected the next word class, selecting an appropriate word from that class.

#### Word properties
A dollar may be a dollar but a preposition is not simply a preposition. And the same goes for all the other classes. Each word has its own properties. After hours of getting sentences like "sleep wildly in a bicycle" or "pick up a lot of houses while eating a stupid ball", I realized a more sophisticated approach would be necessary. I guess I should appreciate that those sentences really are very random, but they're not something you can actually do.

My approach is to tag each word with a number of properties and with a number of properties that it requires the next word to have. The downside is that this requires meticulous tagging of every word the model uses, but the upside is it allows the necessary fine-tuning. Language is so full of quirks and exceptions that it just doesn't lend itself to the kind of generalized solutions we programmers usually hold so dear.

The word list can be conveniently managed in Excel and then read into the program. In the snippet below, you can see how, for example, the preposition "into" requires the following noun to be tagged as a container, and how the word "across" requires a specific property, "crossable", which "street", below, possesses:

![List of words](https://www.dropbox.com/scl/fi/2dpbersq5lwjyo12041ig/wordlistsnippet.png?rlkey=jbda5na0bscn94b24uiz3rhs3&raw=1)

#### The property hierarchy
A word like "house" is tagged as a container. That goes for anything that it's possible for something else to be "in". Whenever the word "in" is selected, my program knows the next noun must be tagged as "container". Other words are less demanding. For example, the word "draw" merely requires the upcoming noun to be tagged as "physical". Conversely, a more specific word such as "inhabit" might require its noun to be not merely a container but a "dwelling" (unless you're okay inhabiting a matchbox or a trashbin). But "house" lives up to all three requirements. You can draw it, be in it, and inhabit it. Instead of trying to tag each word with all of its property at every level of specificity, I decided to implement a hierarchy. To keep it convenient and scalable, this hierarchy is also maintained in a simple Excel spreadsheet, where for each row, the category in the second column is a subcategory of the category in the first column:

![Hierarchy](https://www.dropbox.com/scl/fi/ilpalixmkc3brhernwxzt/hierarchy.png?rlkey=98js9naorn0y94s6pu7wacefo&raw=1)

This hierarchy is then loaded recursively into a dict so that every time the program needs to find all words that meet the requirement of being in a certain category, it also includes all words tagged with a subcategory of that category (for example, if the word is "draw", which requires the next word to be tagged as "physical", the hierarchy assures that "house", tagged as "container" will also be included because "container" is defined as a subcategory of "physical" in the hierarchy spreadsheet):

```python
#Load hierarchy of word properties
with open('hierarchy.csv', 'r', encoding='utf-8-sig') as hfile:
    edges = list(csv.reader(hfile, delimiter=";"))

def findchildren(cat):
    #--Recursively find all subcategories of input category at all depths-- 
    children = set()
    if cat == '(none)':
        return
    else:
        for edge in edges:
            if edge[1] == cat and edge[0] != '(none)':
                children.add(edge[0])
                children |= findchildren(edge[0])
        return children

#Build hierarchy dictionary to use later for determining the pool of eligible next words when membership of a certain category is required 
hierarchy = {}
for edge in edges:
    if edge[0] not in hierarchy and edge[0] != '(none)':
        hierarchy[edge[0]] = set()
    if edge[1] not in hierarchy:
        hierarchy[edge[1]] = set()
for cat in hierarchy:
    hierarchy[cat] |= findchildren(cat)

...

    def addcats(self, row, wordset=None):
        #If this word requires the next noun to have a specific property, save the list of eligible words
        
        if wordset is None:
            wordset = set()
        
        #Load this word's categories
        categories = []
        value = row.nextcats.values[0]
        if value != '':
            categories.extend(value.split(" "))
        
        #Add all words in either in category or in a subcategory of category
        for category in categories:
            wordset |= self.addwords(category)
        return wordset

    def addwords(self, category, subwordset=None):
        #--Build set of words that belong to a category a.k.a. possess a certain spec--
        
        #Initialize set
        if subwordset is None:
            subwordset = set()

        #Add words that belong to category
        rows = wordframe.loc[(wordframe.spec.apply(lambda x: category in x.split(" ")))]
        subwordset |= set(rows.name.values)
        
        #Also add words that belong to child categories of this category
        for child in hierarchy[category]:
            subwordset |= self.addwords(child)
        return subwordset


```

#### Aligning requirements
Now, allowing each word to make requirements of the next noun introduces another problem: What if the preposition makes one category requirement and then an adjective comes along and makes another and no nouns exist which fulfill both requirements? In such a case, the program should avoid selecting that adjective. Let's look at an example. Take this instruction:

"say a heavy ..."

The set of things you can say has no overlap with the set of things that can be heavy, so the program would crash when it came time to select a noun. This compelled me to write a "matchreqs" function which is triggered whenever a word incurs category requirements of the next noun while other requirements are already registered. The function tests the selected word (usually an adjective) to make sure nouns exist which fulfill both its requirements and the pre-existing ones, discards the word if not, and updates the list of eligible nouns if yes:

```python
def matchreqs(self, words, nextpos):
        #--Avoid adjectives whose requirements of the next noun don't match the antecedent preposition's requirements of the same noun--

        #Initialize variables
        global specwords
        newspecwords = set()
        retries = 0
        if len(specwords) == 0:
            specwords = reservespecwords

        while len(newspecwords) == 0:
            #Initialize set of words that can come after the next word
            choicefrontier = set()

            #Select new word
            choice = random.choice(words)

            #Look up new word in wordlist
            choicerow = self.lookup(name=choice, pos=nextpos)

            #If new word has requirements of next noun, add the eligible words to the choice frontier
            if len(choicerow.nextcats.values) > 1 or (len(choicerow.nextcats.values) == 1 and choicerow.nextcats.values.tolist()[0] != '') or len(choicerow.nextwords.values) > 1:
                choicefrontier |= self.addspecifics(choicerow)
                choicefrontier |= self.addcats(choicerow)

            #If new word has no requirements, we know it's fine to select, so we don't do anything
            else:
                return choice

            #Find the intersection between the current list of suitable next nouns and the list of eligible nouns for the presently selected next word (choice frontier)
            newspecwords = specwords.intersection(choicefrontier)

            #Tally one attempt to find a word that allows the sentence to continue
            retries += 1

            #If 100 chosen words in a row have resulted in no possible next noun, give up
            if retries > 100:
                raise Exception(f"Unable to find any word of the required POS that matches the incumbent requirements")
        
        #Update list of suitable next nouns to be the intersection between the already existing list and the list of words allowed by the chosen next word
        specwords = newspecwords

        #Since we know an intersection exists between the existing requirements and the new requirements, we therefore know the sentence can be continued, and therefore approve the chosen word
        return choice
```

Having the program respond to changes in these three external files ("grammar.json" for syntax, "wordlist.csv" for word classes and properties, and "hierarchy.csv" for relations between properties) makes it scalable and easy to update. The next big task will be to expand the word list to contain thousands of English words all tagged with their relevant properties and their requirements of subsequent words. 


#### Aligning conjunctions
The left-to-right approach - determining the first word first without knowing anything about the rest of the sentence, and so on - is what allows the engine to be transformed into an intuitive analog system later. But it also brings some problems with it that would not have been there if I had used a vertical approach (for example, randomly selecting a valid sentence structure from a predefined formal grammar and then randomly selecting a word for each slot). For example, the model didn't automatically know that nouns that are part of the same conjunction should all fulfill the same property requirements. It would output sentences like:

"write a long poem and a ship"

It realized that a suitable noun had to follow "write", but once that noun ("poem") had been added, it thought all was well and went full throttle on the next one. 
I had to write a function to look through the syntax of the sentence to determine whether the present word is in a conjunction, and then recall the requirements of the previous noun if that was the case. 

### The compromise
There are a few other patches like that, and undoubtedly, more can be added to make the program emulate natural language even more convincingly. As I said in the introduction, the mental image of trying to stuff a live duck into a shoebox and close the lid is what comes to mind when I think about trying to fit human language into a computational model like this, designed for a singular purpose. No matter how much I adapt it, it will inevitably only cover a fraction of the total sum of possible English sentences. 

My goal here has been to build a model that generate an arbitrarily large number of varied and truly random instructions, and which can be implemented in real life as a mechanical system. As far as I am aware, this hasn't been done before.

Now you will have to excuse me, for I have to go and ...

```
move a cake angrily through some nice fields
```
