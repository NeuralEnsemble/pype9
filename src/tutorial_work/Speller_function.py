'''
Created on Jan 30, 2013

@author: Lisicovas
'''
#Definition of a function that spells a word out
def speller (word):
    for letter in word:
        if letter !=" ":
            call= "Give me "+letter+"!"
            print call
            print letter+"!"
    print word+"!"

x="Happy j"
speller(x)