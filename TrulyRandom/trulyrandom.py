from word import *
import os

def main():
    #Initialize to placeholder start word
    word = Word("", 'S')
    #Initalize sentence
    sentence = ""
    #Initalize lists of already used words
    used = []
    lastprep = ['']
    #Initialize sequence of parts-of-speech
    history = []
    #Initialize sentence situation dict
    situation = {
        'plural': False,
        'participle': False
    }
    
    #Main loop
    while word.pos != 'END':
        #Add part-of-speech to sentence history
        history.append(word.pos)

        #Add word to used words if noun or verb, or reset last preposition if preposition
        if word.pos in ('IV', 'STV', 'MTV', 'N', 'MN'):
            used.append(word.name)
        if word.pos in ('P', 'MP'):
            lastprep = [word.name]
        
        #Determine the grammatical context of the next word
        if word.pos in ("PART", "MPART"):
            situation['plural'] = True
            print("setting plural to True")
        if word.pos in ("SART", "MSART"):
            situation['plural'] = False
            print("setting plural to False")
        if word.name == "while":
            situation['participle'] = True
        else:
            situation['participle'] = False
        
        #Initialize next part of speech variable
        nextname = None
        nextpos = None
        #Clear screen
        os.system('cls')
        #Choose next part of speech
        while nextpos is None:
            nextpos = word.nextpos(word.posnexts, word.weights, history, lastprep)
        #Choose word from this part of speech
        while nextname is None:
            nextname = word.nextword(nextpos, used, history, lastprep)

        #Initialize next word
        word = Word(nextname, nextpos)
        #Conjugate word if appropriate
        form = word.conjugate(situation)
        #Print sentence
        print(sentence, end='')
        print(form, end=' ')
        sentence += (form + " ")
        input()

if __name__ == "__main__":
    main()

    #TODO:
    #Limit the maximum amount of consecutive preposition clauses ('in mysterious train outside street over lake' etc.)
    #Prevent plural articles ('a lot of', 'three' etc.) from appearing after spatial prepositions specifying the location where an action should be performed ("punch red cake in a lot of heavy shopping kart")
    #Make it so nextcats can process "everything in category EXCEPT subcategory"
    #Update grammar to allow dative objects (with noun predicates: "give a man a fish", "show a man a house", and with verb predicates: "teach a man to sing", "ask a man to dance")
    #Expand lookup function to allow many kinds of lookups