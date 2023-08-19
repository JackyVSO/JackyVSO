import pandas as pd
import csv
import json
import random

#Load grammar
with open('grammar.json') as grammarfile:
    grammar = json.load(grammarfile)

#Load word properties
with open('wordlist.csv', 'r') as wordlist:
    wordframe = pd.read_csv(wordlist, delimiter=";", keep_default_na=False)

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

#Initialize set of nouns possessing the necessary properties required by the preceding verb or adjective
specwords = set()

#Inititialize backup set of eligible nouns for use in case of conjunctions
reservespecwords = set()


class Word():
    def __init__(self, name, pos):
        #--Initialize properties (name, part of speech, possible next parts of speech, weight distribution for choosing between parts of speech)--
        self.name = name
        self.pos = pos
        self.posnexts = grammar[self.pos]['nexts']
        self.weights = grammar[self.pos]['weights']

    def nextpos(self, posnexts, weights, history, lastprep):
        #--Choose next part of speech--

        #Progressively increase probability of ending sentence if sentence is already very long
        if len(history) > 7 and 'END' in posnexts:
            weights[posnexts.index('END')] += (0.05 * (len(history) - 7))
        
        #Select part of speech
        choice = random.choices(posnexts, weights, k=1)[0]
        
        #If proper noun is selected, check that the incumbent preposition is okay to take a proper noun:
        if choice == 'PN':
            row = self.lookup()
            if 'pn' not in row.nextcats.values[0].split(" "):
                return None
        
        #Make sure further conjunctions are not made after most prepositions ("in", "on", "near" etc.), only appropriate ones ("with"...)  
        if choice == ("CONJ"):
            for previous in reversed(history):
                if previous in ("IV", "STV", "MTV"):
                    break
                if previous in ("P", "MP"):
                    row = self.lookup(name=lastprep)
                    if len(row.special.values == 0) or (len(row.special.values) > 0 and 'okayconj' not in row.special.values[0].split(" ")):
                        return None
        return choice

    def nextword(self, nextpos, used, history, lastprep):
        #--Choose an appropriate next word from the selected part of speech--
        
        #Initialize global variables and stop condition
        global specwords, reservespecwords
        if nextpos == 'END':
            quit()

        #Initialize pool of possible words
        words = []

        #Look up properties of current word
        row = self.lookup()
        thiswordspecs = set()

        #If this word has a specific list of words that can come after it, add these to the pool
        if len(row.nextwords.values.tolist()) > 0 and row.nextwords.values.tolist()[0] != '':
            thiswordspecs |= self.addspecifics(row)
        
        #If this word requires the next noun to have a specific property, save the list of eligible words:
        if len(row.nextcats.values.tolist()) > 1 or (len(row.nextcats.values.tolist()) == 1 and row.nextcats.values.tolist()[0] != ''):
            thiswordspecs |= self.addcats(row)

        #If previous words already had requirements of next noun, merge these with current word's requirements
        if len(specwords) > 0 and len(thiswordspecs) > 0:
            specwords = specwords.intersection(thiswordspecs)
        elif len(specwords) == 0:
            specwords = thiswordspecs
        
        #Check if next noun is the non-first noun in a conjuncted series:
        conjuncted = self.isconj(history)
        #If this is the case, bring back the requirements of the previous noun and apply them to this one too
        if conjuncted:
            if len(specwords) > 0:
                specwords = specwords.intersection(reservespecwords)
            else:
                specwords = reservespecwords

        #If the next word is going to be a noun, fetch the list of words that match the property required of the noun, if such a list exists:
        if nextpos in ("N", "MN"):
            #If requirements exist, add all words that meet all requirements and also belong to the selected next POS to the pool of eligible next words
            if len(specwords) > 0:
                for word in specwords:
                    row = wordframe.loc[(wordframe.name.apply(lambda x: x == word))]
                    if row.pos.values[0] in grammar[nextpos]['vocabulary']:
                        words.append(word)

                #Reset list of eligible words but store it in another variable in case a conjunction occurs
                reservespecwords = specwords
                specwords = set()
            #Else, if this word does not require the next word to have a specific property, add all words of the selected part of speech (yes, it's there twice. I know...)
            else:
                words.extend(self.addall(nextpos))
        else:
            words.extend(self.addall(nextpos))

        #Remove already used words from pool
        words = self.removeused(words, used, lastprep)
        
        #Avoid adjectives whose requirements of the next noun don't match the antecedent preposition's requirements of the same noun:
        if nextpos in ("ADJ", "MADJ", "P", "MP") and (len(specwords) > 0 or conjuncted):
            return self.matchreqs(words, nextpos)

        #If either there are no incumbent requirements or the current pos can't incur requirements, simply choose word from pool
        return random.choice(words)
    

    def conjugate(self, situation):
        #If noun is in plural
        if self.pos in ("N", "MN") and situation['plural']:
            row = self.lookup()
            #Check for irregular plural form
            if len(row['plural']) > 0 and row.plural.values[0] != '':
                return row.plural.values[0]
            #...or noun ending in -s
            elif self.name[-1] == 's':
                return self.name + 'es'
            #Otherwise just add an s to the word
            else:
                return self.name + 's'
            
        elif self.pos in ("IV", "STV", "MTV") and situation['participle']:
            #If verb is in participle form, check if it ends in -e and strike out the -e if it does
            if self.name[-1] == 'e':
                return self.name[:-1] + 'ing'
            #Otherwise just add -ing to the word
            else:
                return self.name + 'ing'
        else:
            return self.name


    #NEXTWORD HELPER FUNCTIONS:
    def lookup(self, column='name', name=None, pos=None):
        if name is None:
            name = self.name
        if pos is None:
            pos = self.pos
        return wordframe.loc[(wordframe[column].apply(lambda x: x == name)) & (wordframe['pos'].isin(grammar[pos]['vocabulary']))] 
    
    def removeused(self, words, used, lastprep):
        #--Remove already used nouns/verbs and the last used preposition from pool of eligible words--
        for usedword in used:
            if usedword in words and len(words) > 1:
                words.remove(usedword)
        if lastprep[0] in words:
            words.remove(lastprep[0])

        return words

    def addspecifics(self, row):
        #--If this word has a specific list of words that can come after it, add these to the pool--
        
        newwords = set()
        splitwords = row.nextwords.values[0].split(" ")
        
        for word in splitwords:
            if word != '':
                newwords.add(word)
        return newwords

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

    def addall(self, nextpos):
        #--If this word does not require the next word to have a specific property, add all words of the selected part of speech--
        rows = wordframe.loc[wordframe['pos'].isin(grammar[nextpos]['vocabulary'])]
        return rows.name.values.tolist()
    
    def matchreqs(self, words, nextpos):
        #--Avoid adjectives whose requirements of the next noun don't match the antecedent preposition's requirements of the same noun--

        #Initialize variables
        global specwords
        newspecwords = set()
        retries = 0
        if len(specwords) == 0:
            specwords = reservespecwords

        # print(f"Matching reqs. Current specwords: {specwords}")
        while len(newspecwords) == 0:
            #Initialize set of words that can come after the next word
            choicefrontier = set()
            #Select new word
            choice = random.choice(words)
            #Look up new word in wordlist
            choicerow = self.lookup(name=choice, pos=nextpos)
            #If new word has requirements of next noun, add the eligible words to the choice frontier
            if len(choicerow.nextcats.values.tolist()) > 1 or (len(choicerow.nextcats.values.tolist()) == 1 and choicerow.nextcats.values.tolist()[0] != '') or len(choicerow.nextwords.values.tolist()) > 1:
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
        #Since we know an intersection exists between the existing requirements and the new requirements, we therefore know the sentence can be continued, and we therefore approve the chosen word
        return choice
    
    def isconj(self, history):
        #--Check if the current word is the non-first part of a conjunction
        for pos in reversed(history):
            if pos in ("IV", "STV", "MTV", "P", "MP"):
                return False                
            if pos in ("CONJ", "MCONJ"):
                return True
        return False