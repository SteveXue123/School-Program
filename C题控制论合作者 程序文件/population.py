from player import player, gambler, businessman, shuffler, elderly, venturer, programmer, chemist
from game import game
import numpy as np
import time
import matplotlib.pyplot as plt
#from scipy import stats

global players

def startGame(display):
    theGame = game(display, players=players)
    return theGame.start() 

if __name__ == "__main__":
    """r = [[] for i in range(21)]
    times = 100
    display = False
    t1 = time.time()
    for k in range(0, 21):
        for i in range(times):
            players = [elderly(k/20), elderly(k/20), elderly(k/20)]
            r[k].append(startGame(display))
    t2 = time.time()
    plt.plot([np.mean(i) for i in r])
    plt.show()
    plt.plot([np.max(i) for i in r])
    plt.show()
    plt.plot([np.var(i) for i in r])
    plt.show()
    plt.plot([np.median(i) for i in r])
    plt.show()"""

    r = []
    times = 50
    display = False
    t1 = time.time()
    for i in range(times):
        players = [shuffler(0.5), programmer(10000,0.625),programmer(10000,0.625)]
        r.append(startGame(display))
    t2 = time.time()
    #plt.boxplot(r)
    #plt.show()
    print(np.median(r))
    
    """x = ["gambler", "shuffler", "businessman", "elderly", "venturer", "programmer", "chemist"]
    data = [0 for i in range(7)]"""
    