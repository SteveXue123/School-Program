from gameRainbow import colors, actions, action, card
from basePlayer import basePlayer
import numpy as np
import random
from time import sleep

# NOTE 以下 BUG 目前不会产生严重影响
# BUG 提示可以提示自己

class playerCard:
    def __init__(self, theCard):
        self.card = theCard.copy()
        self.hint = card(colors.unknown, -1)


class player(basePlayer):
    def __init__(self):
        basePlayer.__init__(self)
        self.onStart.append(self.onStartListener)
        self.onGameEnd.append(self.onGameEndListener)
        self.onTurnStart.append(self.onTurnStartListener)
        self.onHintColor.append(self.onHint)
        self.onHintNumber.append(self.onHint)
        self.onPlayerAction.append(self.resolveTurn)
        self.hands = []
        self.field = []
        self.discard = []
        self.currentPlayer = []
        self.hints = 8
        self.error = 0
        self.score = 0
        for i in range(6):
            self.field.append([])
            self.discard.append([])
        self.deckRemain = []
        self.playerIndex = -1

    def onStartListener(self, handStatus):
        self.hands = [[playerCard(c) for c in cardList] for cardList in handStatus]
        self.deckRemain = 60 - len(handStatus[0]) * len(handStatus)
        for i in range(len(handStatus)):
            if handStatus[i][0].number == -1:
                self.playerIndex = i
                break

    def turn(self):
        print('输入“操作数 目标卡牌/玩家 [操作数=0或1]提示内容”，操作数：0=提示颜色，1=提示数字，2=出牌，3=弃牌')
        res = input().split()
        actionType = actions(int(res[0]))
        target = int(res[1])
        if actionType == actions.hintColor:
            return action(actionType, target, color=colors(int(res[2])))
        elif actionType == actions.hintNumber:
            return action(actionType, target, number=int(res[2]))
        else:
            return action(actionType, target)

    def onGameEndListener(self, reason, score):
        pass

    def onTurnStartListener(self, index):
        self.currentPlayer = index

    # 处理所有提示
    def resolveHintListener(self, target, hintInfo):
        for i, c in enumerate(hintInfo):
            if c.color != colors.unknown:
                self.hands[target][i].hint.color = c.color
            elif c.number != -1:
                self.hands[target][i].hint.number = c.number

    # 处理针对自己的提示
    def onHint(self, hintInfo):
        self.resolveHintListener(self.playerIndex, hintInfo)

    def resolveTurn(self, index, playerAction, **kwargs):
        unknownCard = card(colors.unknown, -1)
        if playerAction.actionType == actions.hintColor:
            self.hints -= 1
            # generates the hint
            hintInfo = []
            for i in self.hands[playerAction.target]:
                if i.card.color == playerAction.color:
                    hintInfo.append(card(playerAction.color, -1))
                else:
                    hintInfo.append(unknownCard.copy())
            self.resolveHintListener(playerAction.target, hintInfo)
        elif playerAction.actionType == actions.hintNumber:
            self.hints -= 1
            # generates the hint
            hintInfo = []
            for i in self.hands[playerAction.target]:
                if i.card.number == playerAction.number:
                    hintInfo.append(card(colors.unknown, playerAction.number))
                else:
                    hintInfo.append(unknownCard.copy())
            self.resolveHintListener(playerAction.target, hintInfo)
        elif playerAction.actionType == actions.discard:
            # discard and draw
            self.hints += 1
            discard = kwargs['discard']
            self.discard[discard.color.value].append(discard.copy())
            if self.deckRemain == 0:
                self.hands[index].pop(playerAction.target)
            else:
                draw = kwargs['draw']
                self.hands[index][playerAction.target] = playerCard(draw)
                self.deckRemain -= 1
        else:
            # attempt to play and draw
            play = kwargs['play']
            if (len(self.field[play.color.value]) == 0 and play.number == 1) or (
                    len(self.field[play.color.value]) != 0 and play.number ==
                    self.field[play.color.value][-1].number + 1):
                self.field[play.color.value].append(play.copy())
                self.score += 1
                if play.number == 5:
                    self.hints += 1
            else:
                self.error += 1
                self.discard[play.color.value].append(play.copy())
            if self.deckRemain == 0:
                self.hands[index].pop(playerAction.target)
            else:
                draw = kwargs['draw']
                self.hands[index][playerAction.target] = playerCard(draw)
                self.deckRemain -= 1


class gambler(player):
    def __init__(self):
        player.__init__(self)

    def turn(self):
        return action(actions.play, 0)


class shuffler(player):
    def __init__(self, playP):
        player.__init__(self)
        self.possibility = playP

    def turn(self):
        if self.hints == 8:
            return action(actions.play, random.randint(0, 4))
        else:
            return random.choices([action(actions.play, random.randint(0, 4)), action(actions.discard, random.randint(0,4))],
                                  weights=[self.possibility, 1 - self.possibility], k=1)[0]


class businessman(gambler):
    def __init__(self):
        player.__init__(self)
        self.age = [0, 0, 0, 0, 0, 0]  # 前五项是牌，最后一项是总回合数
        self.unknownCards = [(colors(c), n) for c in range(6) for n in [1, 1, 1, 2, 2, 3, 3, 4, 4, 5]] # deck + hand
        self.knowledge = [[{colors(a) for a in range(6)}, {b + 1 for b in range(5)}] for n in range(5)] # [[{:colors},{:number}]*5]
        self.player = 0

    def onStartListener(self, handStatus):
        player.onStartListener(self, handStatus)
        self.player = len(self.hands)
        knownCards = []
        for i, p in enumerate(self.hands):
            if i != self.playerIndex:
                knownCards += p
        knownCards = [(c.card.color, c.card.number) for c in knownCards]
        for i in knownCards:
            self.unknownCards.remove(i)

    def turn(self):
        tmp = [c.hint.number for c in self.hands[self.playerIndex]]
        field = np.hstack(self.field)
        # 先提示1
        if 1 in tmp and len(field) == 0:
            return action(actions.play, tmp.index(1))
        if self.age[-1] < 10: # the number that hint wouldn't go to zero
            for i in range(1, self.player):
                h1 = False
                h2 = True
                current = (i + self.playerIndex) % self.player
                fieldColor = [c.color for c in field]
                for j in range(5):
                    if (self.hands[current][j].card.number == 1 and self.hands[current][j].hint.number == -1
                        and not self.hands[current][j].card.color in fieldColor):
                        h1 = True
                    if (self.hands[current][j].card.number == 1
                        and self.hands[current][j].card.color in fieldColor):
                        h2 = False
                if h1 and h2:
                    return action(actions.hintNumber, current, number=1)
        # 出确定牌
        for i in range(5):
            tmp = self.knowledge[i]
            if  len(tmp[0]) == 1 and len(tmp[1]) == 1 and (
                len(self.field[list(tmp[0])[0].value]) == 0 and sum(tmp[1]) == 1 or 
                len(self.field[list(tmp[0])[0].value]) != 0 and sum(tmp[1]) ==
                    self.field[list(tmp[0])[0].value][-1].number + 1):
                return action(actions.play, i)
        return self.otherwise()
    
    def otherwise(self):
        return super().turn()

    def resolveTurn(self, index, playerAction, **kwargs):
        self.age = [i + 1 for i in self.age]
        if index == self.playerIndex and (playerAction.actionType == actions.discard or playerAction.actionType == actions.play):
            self.age[playerAction.target] = 0
        player.resolveTurn(self, index, playerAction, **kwargs)
        if playerAction.actionType == actions.discard and index == self.playerIndex:
            self.unknownCards.remove((kwargs['discard'].color, kwargs['discard'].number))
            self.knowledge[playerAction.target] = [{colors(a) for a in range(6)}, {b + 1 for b in range(5)}]
        elif playerAction.actionType == actions.play and index == self.playerIndex:
            self.unknownCards.remove((kwargs['play'].color, kwargs['play'].number))
            self.knowledge[playerAction.target] = [{colors(a) for a in range(6)}, {b + 1 for b in range(5)}]
        elif playerAction.actionType == actions.hintColor and playerAction.target == self.playerIndex:
            for i, c in enumerate(self.hands[self.playerIndex]):
                if c.hint.color == playerAction.color:
                    self.knowledge[i][0] = {playerAction.color}
                else:
                    self.knowledge[i][0] -= {playerAction.color}
        elif playerAction.actionType == actions.hintNumber and playerAction.target == self.playerIndex:
            for i, c in enumerate(self.hands[self.playerIndex]):
                if c.hint.number == playerAction.number:
                    self.knowledge[i][1] = {playerAction.number}
                else:
                    self.knowledge[i][1] -= {playerAction.number}
        # 在unknowncards属性筛选后从中去除knowledge有交集属性的牌并进行推断
        oldKnowledge = []
        while oldKnowledge != self.knowledge:
            oldKnowledge = self.knowledge
            for i in range(5):
                self.knowledge[i][0] &= {
                                            c[0] 
                                            for c in self.unknownCards 
                                            if c[1] in self.knowledge[i][1]
                                        }
                self.knowledge[i][1] &= {
                                            c[1]
                                            for c in self.unknownCards
                                            if c[0] in self.knowledge[i][0]
                                        }


class elderly(businessman):
    def __init__(self, hintP):
        self.hintP = hintP
        businessman.__init__(self)
    
    def otherwise(self):
        # 弃置废牌
        if self.hints < 8:
            field = np.hstack(self.field)
            available = [i for i in range(5) if len(self.knowledge[i][0]) == 1 and len(self.knowledge[i][1]) == 1 and (
                    self.knowledge[i] in [[{c.color}, {c.number}] for c in field])]
            if available != []:
                return action(actions.discard, random.choice(available))
            Ucol = {
                colors(i)
                for i in range(6)
                if len(self.field[i]) == 5 or [c.number for c in self.discard[i]].count(len(self.field[i]) + 1) == 0
            }
            Unum = {
                n
                for n in range(1, 6)
                if [c.number for c in field].count(n) == 5
            }
            available = [i for i, c in enumerate(self.knowledge) if len(c[0]) == 1 and c[0] in Ucol or len(c[1]) == 1 and c[1] in Unum]
            if len(available) != 0:
                return action(actions.discard, random.choice(available))
        # 提示废牌
        if self.hints > 0 and random.choices([True, False], weights=[self.hintP, 1 - self.hintP], k=1)[0]:
            field = np.hstack(self.field)
            Ucol = {
                colors(i)
                for i in range(6)
                if len(self.field[i]) == 5 or [c.number for c in self.discard[i]].count(len(self.field[i]) + 1) == 0
            }
            Unum = {
                n
                for n in range(1, 6)
                if [c.number for c in field].count(n) == 5
            }
            for i in range(1, self.player):
                current = (i + self.playerIndex) % self.player
                Inum = Unum & {c.card.number for c in self.hands[current]}
                if Inum != set():
                    for i in range(5):
                        if self.hands[current][i].card.number in Inum and self.hands[current][i].hint.number != -1:
                            return action(actions.hintNumber, current, number=random.choice(list(Inum)))
                Icol = Ucol & {c.card.color for c in self.hands[current]}
                if Icol != set():
                    for i in range(5):
                        if self.hands[current][i].card.color in Icol and self.hands[current][i].hint.color != colors.unknown:
                            return action(actions.hintColor, current, color=random.choice(list(Icol)))
        return gambler().turn()


class venturer(elderly):
    def __init__(self, playP):
        super().__init__()
        self.possibility = playP
    
    def otherwise(self):
        return shuffler.turn(self)


class programmer(businessman):
    def __init__(self, tolerance, weight):
        super().__init__()
        self.tolerance = tolerance
        self.weight = weight
        self.hintage = [[-1, -1] for i in range(5)] # [[colorage, numberage]*5]

    def turn(self):
        tmp = [c.hint.number for c in self.hands[self.playerIndex]]
        field = np.hstack(self.field)
        # 开局出一
        if 1 in tmp and len(field) == 0:
            return action(actions.play, tmp.index(1))
        if len(field) == 0 and 1 in [c.card.number for c in self.hands[(self.playerIndex + 1)%3]]:
            return action(actions.hintNumber, (self.playerIndex + 1)%3, number=1)
        elif len(field) == 0 and 1 in [c.card.number for c in self.hands[(self.playerIndex + 2)%3]]:
            return action(actions.hintNumber, (self.playerIndex + 2)%3, number=1)
        # 出确定牌
        for i in range(5):
            tmp = self.knowledge[i]
            if  len(tmp[0]) == 1 and len(tmp[1]) == 1 and (
                len(self.field[list(tmp[0])[0].value]) == 0 and sum(tmp[1]) == 1 or 
                len(self.field[list(tmp[0])[0].value]) != 0 and sum(tmp[1]) ==
                    self.field[list(tmp[0])[0].value][-1].number + 1):
                return action(actions.play, i)
        # 弃置废牌
        if self.hints < 8:
            field = np.hstack(self.field)
            available = [i for i in range(5) if len(self.knowledge[i][0]) == 1 and len(self.knowledge[i][1]) == 1 and (
                    self.knowledge[i] in [[{c.color}, {c.number}] for c in field])]
            if available != []:
                return action(actions.discard, random.choice(available))
            Ucol = {
                colors(i)
                for i in range(6)
                if len(self.field[i]) == 5 or [c.number for c in self.discard[i]].count(len(self.field[i]) + 1) == 0
            }
            Unum = {
                n
                for n in range(1, 6)
                if [c.number for c in field].count(n) == 5
            }
            available = [i for i, c in enumerate(self.knowledge) if len(c[0]) == 1 and c[0] in Ucol or len(c[1]) == 1 and c[1] in Unum]
            if len(available) != 0:
                return action(actions.discard, random.choice(available))
        # 提示废牌
        if self.hints > 0 and random.choices([True, False], weights=[.5, .5], k=1)[0] and self.score > 18:
            field = np.hstack(self.field)
            Ucol = {
                colors(i)
                for i in range(6)
                if len(self.field[i]) == 5 or [c.number for c in self.discard[i]].count(len(self.field[i]) + 1) == 0
            }
            Unum = {
                n
                for n in range(1, 6)
                if [c.number for c in field].count(n) == 5
            }
            for i in range(1, self.player):
                current = (i + self.playerIndex) % self.player
                Inum = Unum & {c.card.number for c in self.hands[current]}
                if Inum != set():
                    for i in range(len(self.hands[current])):
                        if self.hands[current][i].card.number in Inum and self.hands[current][i].hint.number != -1:
                            return action(actions.hintNumber, current, number=random.choice(list(Inum)))
                Icol = Ucol & {c.card.color for c in self.hands[current]}
                if Icol != set():
                    for i in range(len(self.hands[current])):
                        if self.hands[current][i].card.color in Icol and self.hands[current][i].hint.color != colors.unknown:
                            return action(actions.hintColor, current, color=random.choice(list(Icol)))
        return self.otherwise()

    def otherwise(self):
        # 赋分机制
        actionValue = [0, 0, 0, 0]
        playValue = [0, 0, 0, 0, 0]
        discardValue = [0, 0, 0, 0, 0]
        colorValue = [[1, 1, 1, 1, 1, -1] for p in range(self.player - 1)]
        numberValue = [[1, 1, 1, 1, 1] for p in range(self.player - 1)]
        # play and discard
        for i in range(len(self.hands[self.playerIndex])):
            if self.hands[self.playerIndex][i].hint.number in [len(n) + 1 for n in self.field]:
                hintMap = [0, 1.2] + [(self.hintage[i][1] + .5)/7 for j in range(5)]
                playValue[i] = 90*(self.tolerance*(self.error < 2) + self.weight)*hintMap[
                    [n.hint.number for n in self.hands[self.playerIndex]].count(self.hands[self.playerIndex][i].hint.number)]
                discardValue[i] = 96*(1 - self.weight) + 10*max(self.hintage[i])
            elif self.hands[self.playerIndex][i].hint.color != colors.unknown:
                hintMap = [0, 1.2] + [(self.hintage[i][0] + .5)/7 for j in range(5)]
                if len(self.field[self.hands[self.playerIndex][i].hint.color.value]) + 1 in self.knowledge[i][1]:
                    playValue[i] = 90*(self.tolerance*(self.error < 2) + self.weight)*hintMap[
                        [n.hint.color for n in self.hands[self.playerIndex]].count(self.hands[self.playerIndex][i].hint.color)]
                discardValue[i] = 96*(1 - self.weight) + 10*max(self.hintage[i])
            # elif len(self.knowledge[i][1]) == 1:
            #     hintMap = [0, 1] + [(self.hintage[i][1] + .5)/9 for j in range(5)]
            #     playValue[i] = 90*(self.tolerance*(self.error < 2) + 1 - self.weight)*hintMap[
            #         len([n for n in self.knowledge if n[1].issuperset(self.knowledge[i][1])])]
            #     discardValue[i] = 96*0.6 + 10*max(self.hintage[i])
            # elif len(self.knowledge[i][0]) == 1:
            #     hintMap = [0, 1] + [(self.hintage[i][0] + .5)/9 for j in range(3)]
            #     playValue[i] = 90*self.tolerance*(self.error < 2)
            #     discardValue[i] = 96*0.6 + 10*max(self.hintage[i])
            else:
                playValue[i] = 0
                tmpSeries = [3, 2, 2, 2, 1]
                hintsMap = [3, 1.05, .8, .7, .5, .5, .01, .01, 0, 0, 0]
                discardValue[i] = (50 + 2*(self.age[i] - max(self.hintage[i])))*(
                    np.mean([tmpSeries[j - 1] for j in self.knowledge[i][1]]) - 1)*hintsMap[self.hints]
            if self.knowledge[i][1] == {5}:
                discardValue[i] = -1
        # hint
        for i in range(self.player - 1):
            current = (i + self.playerIndex + 1) % self.player
            for j in range(5):
                cardColor = [c.card.color for c in self.hands[current]]
                if cardColor.count(colors(j)) > 0:
                    h1 = False
                    for k in range(len(self.hands[current])):
                        if (self.hands[current][k].card.number == len(self.field[j]) + 1
                            and self.hands[current][k].hint.color == colors.unknown
                            and self.hands[current][k].card.color == colors(j)):
                            h1 = True
                    if h1:
                        colorValue[i][j] = 300 - 20*(cardColor.count(colors(j)) - 1)
                else:
                    colorValue[i][j] = -1
            for j in range(5):
                cardNum = [c.card.number for c in self.hands[current]]
                if cardNum.count(j + 1) > 0:
                    h1 = False
                    h2 = j == 4 and max([len(c) for c in self.field]) < 4
                    h3 = False
                    for k in range(len(self.hands[current])):
                        if (self.hands[current][k].card.number == len(self.field[self.hands[current][k].card.color.value]) + 1
                            and self.hands[current][k].hint.number == -1
                            and self.hands[current][k].card.number == j + 1):
                            h1 = True
                        elif h2 and self.hands[current][k].card.number == 5:
                            h3 = True
                    if h1:
                        numberValue[i][j] = 300 - 20*(cardNum.count(j + 1) - 1)
                    # elif h3:
                    #    numberValue[i][j] = 230
                else:
                    numberValue[i][j] = -1
        actionValue[actions.play.value] = sum(playValue)
        actionValue[actions.discard.value] = sum(discardValue)
        actionValue[actions.hintColor.value] = sum([sum(p) for p in colorValue])/(self.player - 1)
        actionValue[actions.hintNumber.value] = sum([sum(p) for p in numberValue])/(self.player - 1)/5*6
        # 评分机制
        if self.hints == 0:
            actionValue[actions.hintColor.value] = -1
            actionValue[actions.hintNumber.value] = -1
        elif self.hints == 8:
            actionValue[actions.discard.value] = -1
        if self.deckRemain < 3:
            actionValue[actions.discard.value] = -10
            actionValue[actions.play.value] = -.5
        if self.deckRemain == 0:
            actionValue[actions.hintColor.value] = -10
            actionValue[actions.hintNumber.value] = -10
        m = max(actionValue)
        todo = random.choice([actions(i) for i in range(4) if abs(actionValue[i] - m) <= 0])
        if todo == actions.discard:
            m = max(discardValue)
            totarget = random.choice([i for i in range(5) if discardValue[i] == m])
            return action(todo, totarget)
        elif todo == actions.play:
            m = max(playValue)
            totarget = random.choice([i for i in range(5) if playValue[i] == m])
            return action(todo, totarget)
        elif todo == actions.hintColor:
            m = max([sum(i) for i in colorValue])
            for i in range(1, self.player):
                current = (i + self.playerIndex) % self.player
                if sum(colorValue[i - 1]) == m:
                    m = max(colorValue[i - 1])
                    tocolor = random.choice([colors(j) for j in range(6) if colorValue[i - 1][j] == m])
                    return action(todo, current, color=tocolor)
        else:
            m = max([sum(i) for i in numberValue])
            for i in range(1, self.player):
                current = (i + self.playerIndex) % self.player
                if sum(numberValue[i - 1]) == m:
                    m = max(numberValue[i - 1])
                    tonumber = random.choice([j + 1 for j in range(5) if numberValue[i - 1][j] == m])
                    return action(todo, current, number=tonumber)

    def resolveTurn(self, index, playerAction, **kwargs):
        super().resolveTurn(index, playerAction, **kwargs)
        self.hintage = [[i[0] + (0 if i[0] == -1 else 1), i[1] + (0 if i[1] == -1 else 1)] for i in self.hintage]
        if playerAction.target == self.playerIndex:
            if playerAction.actionType == actions.hintColor:
                for i in range(len(self.hands[self.playerIndex])):
                    if self.hands[self.playerIndex][i].hint.color == playerAction.color and self.hintage[i][0] == -1:
                        self.hintage[i][0] = 0
            if playerAction.actionType == actions.hintNumber:
                for i in range(len(self.hands[self.playerIndex])):
                    if self.hands[self.playerIndex][i].hint.number == playerAction.number and self.hintage[i][1] == -1:
                        self.hintage[i][1] = 0
        if index == self.playerIndex and (playerAction.actionType == actions.play or playerAction.actionType == actions.discard):
            self.hintage[playerAction.target] == [-1, -1]

class chemist(programmer):
    def __init__(self, tolerance, weight):
        programmer.__init__(self, tolerance, weight)

    def otherwise(self):
         # 赋分机制
        actionValue = [0, 0, 0, 0]
        playValue = [0, 0, 0, 0, 0]
        discardValue = [0, 0, 0, 0, 0]
        colorValue = [[1, 1, 1, 1, 1, 1] for p in range(self.player - 1)]
        numberValue = [[1, 1, 1, 1, 1] for p in range(self.player - 1)]
        # play and discard
        for i in range(len(self.hands[self.playerIndex])):
            if self.hands[self.playerIndex][i].hint.number in [len(n) + 1 for n in self.field]:
                hintMap = [0, 1.2] + [(self.hintage[i][1] + .5)/7 for j in range(5)]
                playValue[i] = 90*(self.tolerance*(self.error < 2) + self.weight)*hintMap[
                    [n.hint.number for n in self.hands[self.playerIndex]].count(self.hands[self.playerIndex][i].hint.number)]
                discardValue[i] = 96*(1 - self.weight) + 10*max(self.hintage[i])
            elif self.hands[self.playerIndex][i].hint.color != colors.unknown:
                hintMap = [0, 1.2] + [(self.hintage[i][0] + .5)/7 for j in range(5)]
                if len(self.field[self.hands[self.playerIndex][i].hint.color.value]) + 1 in self.knowledge[i][1]:
                    playValue[i]
                    self.hands[self.playerIndex]
                    self.hands[self.playerIndex][i]
                    playValue[i] = 90*(self.tolerance*(self.error < 2) + self.weight)*hintMap[
                        [n.hint.color for n in self.hands[self.playerIndex]].count(self.hands[self.playerIndex][i].hint.color)]
                discardValue[i] = 96*(1 - self.weight) + 10*max(self.hintage[i])
            # elif len(self.knowledge[i][1]) == 1:
            #     hintMap = [0, 1] + [(self.hintage[i][1] + .5)/9 for j in range(5)]
            #     playValue[i] = 90*(self.tolerance*(self.error < 2) + 1 - self.weight)*hintMap[
            #         len([n for n in self.knowledge if n[1].issuperset(self.knowledge[i][1])])]
            #     discardValue[i] = 96*0.6 + 10*max(self.hintage[i])
            # elif len(self.knowledge[i][0]) == 1:
            #     hintMap = [0, 1] + [(self.hintage[i][0] + .5)/9 for j in range(3)]
            #     playValue[i] = 90*self.tolerance*(self.error < 2)
            #     discardValue[i] = 96*0.6 + 10*max(self.hintage[i])
            else:
                playValue[i] = 0
                tmpSeries = [3, 2, 2, 2, 1]
                hintsMap = [3, 1.05, .8, .7, .5, .5, .01, .01, 0, 0, 0]
                discardValue[i] = (50 + 2*(self.age[i] - max(self.hintage[i])))*(
                    np.mean([tmpSeries[j - 1] for j in self.knowledge[i][1]]) - 1)*hintsMap[self.hints]
            if self.knowledge[i][1] == {5}:
                discardValue[i] = -1
        # hint
        for i in range(self.player - 1):
            current = (i + self.playerIndex + 1) % self.player
            for j in range(6):
                cardColor = [c.card.color for c in self.hands[current]]
                if cardColor.count(colors(j)) > 0:
                    h1 = False
                    for k in range(len(self.hands[current])):
                        if (self.hands[current][k].card.number == len(self.field[j]) + 1
                            and self.hands[current][k].hint.color == colors.unknown
                            and self.hands[current][k].card.color == colors(j)):
                            h1 = True
                    if h1:
                        colorValue[i][j] = 300 - 20*(cardColor.count(colors(j)) - 1)
                else:
                    colorValue[i][j] = -1
            for j in range(5):
                cardNum = [c.card.number for c in self.hands[current]]
                if cardNum.count(j + 1) > 0:
                    h1 = False
                    h2 = j == 4 and max([len(c) for c in self.field]) < 4
                    h3 = False
                    for k in range(len(self.hands[current])):
                        if (self.hands[current][k].card.number == len(self.field[self.hands[current][k].card.color.value]) + 1
                            and self.hands[current][k].hint.number == -1
                            and self.hands[current][k].card.number == j + 1):
                            h1 = True
                        elif h2 and self.hands[current][k].card.number == 5:
                            h3 = True
                    if h1:
                        numberValue[i][j] = 300 - 20*(cardNum.count(j + 1) - 1)
                    # elif h3:
                    #    numberValue[i][j] = 230
                else:
                    numberValue[i][j] = -1
        actionValue[actions.play.value] = sum(playValue)
        actionValue[actions.discard.value] = sum(discardValue)
        actionValue[actions.hintColor.value] = sum([sum(p) for p in colorValue])/(self.player - 1)
        actionValue[actions.hintNumber.value] = sum([sum(p) for p in numberValue])/(self.player - 1)
        # 评分机制
        if self.hints == 0:
            actionValue[actions.hintColor.value] = -1
            actionValue[actions.hintNumber.value] = -1
        elif self.hints == 8:
            actionValue[actions.discard.value] = -1
        if self.deckRemain < 4:
            actionValue[actions.discard.value] = -10
            actionValue[actions.play.value] = -.5
        if self.deckRemain == 0:
            actionValue[actions.hintColor.value] = -10
            actionValue[actions.hintNumber.value] = -10
        av = [i for i in actionValue if i > 0]
        if av == []:
            m = max(actionValue)
            todo = random.choice([actions(i) for i in range(4) if abs(actionValue[i] - m) <= 0])
        else:
            todo = random.choices([actions(i) for i in range(4) if actionValue[i] > 0], weights=av, k=1)[0]
        if todo == actions.discard:
            m = max(discardValue)
            totarget = random.choice([i for i in range(5) if discardValue[i] == m])
            return action(todo, totarget)
        elif todo == actions.play:
            m = max(playValue)
            totarget = random.choice([i for i in range(5) if playValue[i] == m])
            return action(todo, totarget)
        elif todo == actions.hintColor:
            m = max([sum(i) for i in colorValue])
            for i in range(1, self.player):
                current = (i + self.playerIndex) % self.player
                if sum(colorValue[i - 1]) == m:
                    m = max(colorValue[i - 1])
                    tocolor = random.choice([colors(j) for j in range(5) if colorValue[i - 1][j] == m])
                    return action(todo, current, color=tocolor)
        else:
            m = max([sum(i) for i in numberValue])
            for i in range(1, self.player):
                current = (i + self.playerIndex) % self.player
                if sum(numberValue[i - 1]) == m:
                    m = max(numberValue[i - 1])
                    tonumber = random.choice([j + 1 for j in range(5) if numberValue[i - 1][j] == m])
                    return action(todo, current, number=tonumber)

class writer(businessman):
    def __init__(self):
        super().__init__()