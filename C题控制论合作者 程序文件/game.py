from enum import Enum
import random


class invalidAction(Exception):
    def __init__(self, message):
        self.message = message

    def __str__(self):
        return self.message


class endgames(Enum):
    error = 0
    emtpyDeck = 1
    maxScore = 2


class colors(Enum):
    unknown = -1
    red = 0
    yellow = 1
    blue = 2
    green = 3
    white = 4


class actions(Enum):
    hintColor = 0
    hintNumber = 1
    play = 2
    discard = 3


class card:
    def __init__(self, color, number):
        self.color = color
        self.number = number

    def copy(self):
        return card(self.color, self.number)


class action:
    def __init__(self, actionType, target, **kwargs):
        self.actionType = actionType
        self.target = target
        if self.actionType == actions.hintColor:
            self.color = kwargs['color']
        elif self.actionType == actions.hintNumber:
            self.number = kwargs['number']


class game:
    def __init__(self, display, **kwargs):
        self.deck = [] # 剩余牌
        self.discard = []
        self.field = []
        tmpSeries = [1, 1, 1, 2, 2, 3, 3, 4, 4, 5]
        for i in range(5):
            for j in tmpSeries:
                self.deck.append(card(colors(i), j))
            self.field.append([])
            self.discard.append([])
        random.shuffle(self.deck) # DevSkim: ignore DS148264 until 2024-05-27
        self.maxScore = 25
        if len(kwargs) != 0:
            self.players = kwargs['players']
        else:
            self.players = []
        random.shuffle(self.players) # DevSkim: ignore DS148264 until 2024-05-27
        self.hints = 8
        self.error = 0
        self.hands = []
        self.score = 0
        for player in self.players:
            self.hands.append([])
        self.display = display

    def resolveTurn(self, index, player):
        if self.display:
            m = 0
            for p in player.hands:
                print(m, "手牌:", [[c.card.color, c.card.number] for c in p])
                print(m, "提示:", [[c.hint.color, c.hint.number] for c in p])
                m += 1
            print("出牌堆:", [[[c.color, c.number] for c in cardList] for cardList in self.field])
            print("弃牌堆:", [[[c.color, c.number] for c in cardList] for cardList in self.discard])
            print("提示指示物:", self.hints, "错误指示物:", self.error, "剩余卡牌数:", len(self.deck))
        unknownCard = card(colors.unknown, -1)
        # tell players whose turn it is
        for p in self.players:
            for fun in p.onTurnStart:
                fun(index)
        playerAction = player.turn()
        # players cannot hint if they run out of hints
        if (
                playerAction.actionType == actions.hintColor or playerAction.actionType == actions.hintNumber) and self.hints == 0:
            raise invalidAction('invalid hint: players cannot hint if they run out of hints')
        if playerAction.actionType == actions.discard and self.hints == 8:
            raise invalidAction('invalid discard: players cannot discard cards if they cannot gain more hints')
        if playerAction.actionType == actions.hintColor:
            self.hints -= 1
            # generates the hint
            hintInfo = []
            flag = True
            for i in self.hands[playerAction.target]:
                if i.color == playerAction.color:
                    flag = False
                    hintInfo.append(card(playerAction.color, -1))
                else:
                    hintInfo.append(unknownCard.copy())
            if flag:
                raise invalidAction('invalid hint: no {} cards'.format(playerAction.color))
            # targeted player gets the hint
            for fun in self.players[playerAction.target].onHintColor:
                fun(hintInfo)
            # inform players of the action
            for i, p in enumerate(self.players):
                for fun in p.onPlayerAction:
                    fun(index, playerAction)
        elif playerAction.actionType == actions.hintNumber:
            self.hints -= 1
            # generates the hint
            hintInfo = []
            flag = True
            for i in self.hands[playerAction.target]:
                if i.number == playerAction.number:
                    flag = False
                    hintInfo.append(card(colors.unknown, i.number))
                else:
                    hintInfo.append(unknownCard.copy())
            if flag:
                raise invalidAction('invalid hint: no {} cards'.format(playerAction.number))
            # targeted player gets the hint
            for fun in self.players[playerAction.target].onHintNumber:
                fun(hintInfo)
            # inform players of the action
            for i, p in enumerate(self.players):
                for fun in p.onPlayerAction:
                    fun(index, playerAction)
        elif playerAction.actionType == actions.discard:
            # discard and draw
            discard = self.hands[index][playerAction.target].copy()
            self.discard[discard.color.value].append(discard.copy())
            self.hints += 1
            draw = unknownCard.copy()
            draw.number = 0
            if len(self.deck) == 0:
                self.hands[index].pop(playerAction.target)
            else:
                draw = self.deck.pop().copy()
                self.hands[index][playerAction.target] = draw.copy()
            # broadcast
            for i, p in enumerate(self.players):
                for fun in p.onPlayerAction:
                    fun(index, playerAction, discard=discard.copy(),
                        draw=i == index and unknownCard.copy() or draw.copy())
        else:
            # attempt to play and draw
            play = self.hands[index][playerAction.target].copy()
            if (len(self.field[play.color.value]) == 0 and play.number == 1) or (
                    len(self.field[play.color.value]) != 0 and play.number ==
                    self.field[play.color.value][-1].number + 1):
                self.field[play.color.value].append(play.copy())
                self.score += 1
                if play.number == 5 and self.hints != 8:
                    self.hints += 1
            else:
                self.error += 1
                self.discard[play.color.value].append(play.copy())
            draw = unknownCard.copy()
            draw.number = 0
            if len(self.deck) == 0:
                self.hands[index].pop(playerAction.target)
            else:
                draw = self.deck.pop().copy()
                self.hands[index][playerAction.target] = draw.copy()
            # broadcast
            for i, p in enumerate(self.players):
                for fun in p.onPlayerAction:
                    fun(index, playerAction, play=play.copy(), draw=i == index and unknownCard.copy() or draw.copy())

    def openingHands(self):
        handLimit = [0, 0, 5, 5, 4, 4]
        for index, player in enumerate(self.players):
            for i in range(handLimit[len(self.players)]):
                self.hands[index].append(self.deck.pop())
        # inform players of the opening
        unknownCard = card(colors.unknown, -1)
        unknownHand = []
        for i in range(handLimit[len(self.players)]):
            unknownHand.append(unknownCard.copy())
        for index, player in enumerate(self.players):
            handStatus = self.hands.copy()
            handStatus[index] = unknownHand.copy()
            for fun in player.onStart:
                fun(handStatus)

    def checkEndgame(self, index):
        if self.error >= 3:
            for i, p in enumerate(self.players):
                for fun in p.onGameEnd:
                    fun(endgames.error, self.score)
            return (endgames.error, self.score)
        if len(self.deck) == 0:
            currentIndex = index
            for i in range(len(self.players)):
                currentIndex += 1
                if currentIndex >= len(self.players):
                    currentIndex = 0
                self.resolveTurn(currentIndex, self.players[currentIndex])
            for i, p in enumerate(self.players):
                for fun in p.onGameEnd:
                    fun(endgames.emtpyDeck, self.score)
            return (endgames.emtpyDeck, self.score)
        if self.score == self.maxScore:
            for i, p in enumerate(self.players):
                for fun in p.onGameEnd:
                    fun(endgames.maxScore, self.score)
            return (endgames.maxScore, self.score)
        return -1

    def start(self):
        # deal opening hands
        self.openingHands()
        # the game proceeds until the endgame trigger
        while True:
            for index, player in enumerate(self.players):
                self.resolveTurn(index, player)
                # check for endgame conditions
                result = self.checkEndgame(index)
                if result != -1:
                    print("Game ended because of {},score:{}".format(result[0], result[1]))
                    return result[1]
