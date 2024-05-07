from player import player, gambler, shuffler, businessman, elderly, venturer, programmer, chemist
from game import game
import numpy as np
import time
import matplotlib.pyplot as plt
from scipy import stats

global players

def startGame(display):
    theGame = game(display, players=players)
    return theGame.start() 

if __name__ == "__main__":
    #r = [[] for i in range(21)]
    r = []
    times = 100
    display = False
    t1 = time.time()
    #for k in range(0, 21):
    for i in range(times):
        players = [programmer(0, 1), programmer(10000, 0), chemist(10000, 0)]
        r.append(startGame(display))
    t2 = time.time()
    print("mean:", np.mean(r), "mode:", stats.mode(r).mode, "max:", max(r), "mid:", np.median(r))
    print("time:", t2 - t1, "mean:", (t2 - t1)/times)
    #plt.plot([np.mean(i) for i in r])
    # plt.show()
    # plt.plot([np.max(i) for i in r])
    # plt.show()
    # plt.plot([np.var(i) for i in r])
    # #plt.show()
    #plt.plot([np.median(i) for i in r])
    #plt.show()
    