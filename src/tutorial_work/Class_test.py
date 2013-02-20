'''
Created on Feb 7, 2013

@author: Lisicovas
'''
# Trying out basic class definitions

class accumulator (object):
    def __init__(self):
        self.word = 'Hello'
        
    def __str__(self):
        return self.word
    
    def changer (self, addition):
        self.word = self.word + ',' + addition

    def __len__(self):
        return self.word.count(',') + 1

#Creating an instance of the class 


sentence = accumulator ()


#Gradually modifying the variable within the instance

sentence.changer('Tim')
print sentence

sentence.changer('Johnzny')
print sentence

sentence.changer('Mark')
print sentence

print len(sentence)